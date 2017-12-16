# -*- coding: utf-8 -*-

# Define here the models for your spider middleware
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/spider-middleware.html

import logging
import time
from collections import defaultdict

from scrapy import signals
from scrapy.dupefilters import BaseDupeFilter
from scrapy.exceptions import IgnoreRequest
from scrapy.utils.request import request_fingerprint
from scrapy_redis.connection import get_redis_from_settings

from spidercommon.db import Domain, db_session
from spidercommon.urls import ParsedURL


class FilterDomainByPageLimitMiddleware(object):
    def __init__(self, max_pages):
        logger = logging.getLogger()
        logger.info("FilterDomainbyPageLimitMiddleware loaded with MAX_PAGES_PER_DOMAIN = %d", max_pages)
        self.max_pages = max_pages
        self.counter = defaultdict(int)

    @classmethod
    def from_crawler(cls, crawler):
        settings = crawler.settings
        spider_name = crawler.spider.name
        max_pages = settings.get('MAX_PAGES_PER_DOMAIN')
        o = cls(max_pages)
        return o

    def process_request(self, request, spider):
        parsed = ParsedURL(request.url)
        if self.counter[parsed.host] < self.max_pages:
            self.counter[parsed.host] += 1
            spider.logger.info('Page count is %d for %s' % (self.counter[parsed.host], parsed.host))
            return None
        else:
            raise IgnoreRequest('MAX_PAGES_PER_DOMAIN reached, filtered %s' % request.url)


class FilterTooManySubdomainsMiddleware(object):
    def __init__(self):
        logger = logging.getLogger()

    @classmethod
    def from_crawler(cls, crawler):
        o = cls()
        return o

    def process_request(self, request, spider):
        if not Domain.is_onion_url(request.url):
            return None

        parsed = ParsedURL(request.url)
        subdomains = parsed.host.count(".")
        if subdomains > 2:
            raise IgnoreRequest('Too many subdomains (%d > 2)' % subdomains)

        return None


class RedisCustomDupeFilter(BaseDupeFilter):
    """
    See https://github.com/rmax/scrapy-redis/blob/master/src/scrapy_redis/dupefilter.py for original code.
    Changes are made to ensure that duplicates are done on seperate keys and expire after a day.
    """

    """Redis-based request duplicates filter.
    This class can also be used with default Scrapy's scheduler.
    """

    def __init__(self, server, key, debug=False):
        """Initialize the duplicates filter.
        Parameters
        ----------
        server : redis.StrictRedis
            The redis server instance.
        key : str
            Spider name for fingerprint storage prefix.
        debug : bool, optional
            Whether to log filtered requests.
        """
        self.server = server
        self.key = key
        self.debug = debug
        self.logdupes = True
        self.logger = logging.getLogger()

    @classmethod
    def from_settings(cls, settings):
        """Returns an instance from given settings.
        This uses by default the key ``dupefilter:<timestamp>``. When using the
        ``scrapy_redis.scheduler.Scheduler`` class, this method is not used as
        it needs to pass the spider name in the key.
        Parameters
        ----------
        settings : scrapy.settings.Settings
        Returns
        -------
        RFPDupeFilter
            A RFPDupeFilter instance.
        """
        server = get_redis_from_settings(settings)
        # XXX: This creates one-time key. needed to support to use this
        # class as standalone dupefilter with scrapy's default scheduler
        # if scrapy passes spider on open() method this wouldn't be needed
        # TODO: Use SCRAPY_JOB env as default and fallback to timestamp.
        # XXX: The hack of a hack uses a str of an int to remove decimals.
        key = str(int(time.time()))
        debug = settings.getbool('DUPEFILTER_DEBUG')
        return cls(server, key=key, debug=debug)

    @classmethod
    def from_crawler(cls, crawler):
        """Returns instance from crawler.
        Parameters
        ----------
        crawler : scrapy.crawler.Crawler
        Returns
        -------
        RFPDupeFilter
            Instance of RFPDupeFilter.
        """
        return cls.from_settings(crawler.settings)

    @property
    def dupes_key(self):
        """Returns the Redis dupes key of the crawler spider.
        Returns
        -------
        str
        """
        return "torspider:dupekeys:" + self.key

    def request_seen(self, request):
        """Returns True if request was already seen.
        Parameters
        ----------
        request : scrapy.http.Request
        Returns
        -------
        bool
        """
        fp = self.request_fingerprint(request)
        crawl_key = "torspider:crawled:" + self.key + ":" + fp

        # Check for the key's existance.
        if self.server.exists(crawl_key):
            return True

        # Create the key if it has never been seen.
        added = self.server.setex(
            crawl_key,
            60 * 60 * 24,
            request.url
        )

        self.server.sadd(
            self.dupes_key,
            crawl_key
        )

        return False

    def request_fingerprint(self, request):
        """Returns a fingerprint for a given request.
        Parameters
        ----------
        request : scrapy.http.Request
        Returns
        -------
        str
        """
        return request_fingerprint(request)

    @classmethod
    def from_spider(cls, spider):
        settings = spider.settings
        server = get_redis_from_settings(settings)
        key = spider.name
        debug = settings.getbool('DUPEFILTER_DEBUG')
        return cls(server, key=key, debug=debug)

    def close(self, reason=''):
        """Delete data on close. Called by Scrapy's scheduler.
        Parameters
        ----------
        reason : str, optional
        """
        self.clear()

    def clear(self):
        """Clears fingerprints data."""
        keys = self.server.smembers(self.dupes_key)
        for key in keys:
            self.server.delete(key)

    def log(self, request, spider):
        """Logs given request.
        Parameters
        ----------
        request : scrapy.http.Request
        spider : scrapy.spiders.Spider
        """
        if self.debug:
            msg = "Filtered duplicate request: %(request)s"
            self.logger.debug(msg, {'request': request}, extra={'spider': spider})
        elif self.logdupes:
            msg = ("Filtered duplicate request %(request)s"
                   " - no more duplicates will be shown"
                   " (see DUPEFILTER_DEBUG to show all duplicates)")
            self.logger.debug(msg, {'request': request}, extra={'spider': spider})
            self.logdupes = False


class TorspiderSpiderMiddleware(object):
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the spider middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        # Called for each response that goes through the spider
        # middleware and into the spider.

        # Should return None or raise an exception.
        return None

    def process_spider_output(self, response, result, spider):
        # Called with the results returned from the Spider, after
        # it has processed the response.

        # Must return an iterable of Request, dict or Item objects.
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        # Called when a spider or process_spider_input() method
        # (from other spider middleware) raises an exception.

        # Should return either None or an iterable of Response, dict
        # or Item objects.
        pass

    def process_start_requests(self, start_requests, spider):
        # Called with the start requests of the spider, and works
        # similarly to the process_spider_output() method, except
        # that it doesn’t have a response associated.

        # Must return only requests (not items).
        for r in start_requests:
            yield r

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)
