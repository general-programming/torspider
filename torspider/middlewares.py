# -*- coding: utf-8 -*-

# Define here the models for your spider middleware
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/spider-middleware.html

import logging
import time
import traceback

from scrapy import signals
from scrapy.dupefilters import BaseDupeFilter
from scrapy.exceptions import IgnoreRequest
from scrapy.utils.request import request_fingerprint
from scrapy_redis.connection import get_redis_from_settings
from twisted.internet.error import TimeoutError as TwistedTimeoutError

from spidercommon.model import Domain
from spidercommon.redis import create_redis
from spidercommon.urls import ParsedURL
from spidercommon.util.hashing import md5

logger = logging.getLogger(__name__)

MAX_PAGES_SCRIPT = """
local domain = ARGV[1]
local max_pages = tonumber(ARGV[2])
local page_count = tonumber(redis.call("HGET", "spider:pagecount", domain))

if page_count == nil or page_count <= max_pages then
    local new_page_count = redis.call("HINCRBY", "spider:pagecount", domain, 1)
    return new_page_count
else
    return page_count
end
""".strip()


class FilterDomainByPageLimitMiddleware(object):
    def __init__(self, max_pages):
        logger.info("FilterDomainbyPageLimitMiddleware loaded with MAX_PAGES_PER_DOMAIN = %d", max_pages)
        self.max_pages = max_pages
        self.redis = create_redis()
        self.pages_script = self.redis.register_script(MAX_PAGES_SCRIPT)

    @classmethod
    def from_crawler(cls, crawler):
        settings = crawler.settings
        max_pages = settings.get('MAX_PAGES_PER_DOMAIN')

        return cls(max_pages)

    def process_request(self, request, spider):
        # Allow requests if the max pages is disabled.
        if self.max_pages == -1:
            return None

        parsed = ParsedURL(request.url)
        page_count = self.pages_script(args=[parsed.host, self.max_pages])
        if page_count < self.max_pages:
            spider.logger.info('Page count is %d for %s' % (page_count, parsed.host))
            return None
        else:
            raise IgnoreRequest('MAX_PAGES_PER_DOMAIN reached, filtered %s' % request.url)

    def process_exception(self, request, exception, spider):
        parsed = ParsedURL(request.url)
        if exception:
            self.redis.hincrby("spider:pagecount", parsed.host, -1)

        return None


class FilterTooManySubdomainsMiddleware(object):
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


class ExceptionHandlerMiddleware(object):
    def __init__(self):
        self.redis = create_redis()

    @classmethod
    def from_crawler(cls, crawler):
        settings = crawler.settings

        return cls()

    def process_exception(self, request, exception, spider):
        parsed = ParsedURL(request.url)

        if isinstance(exception, TwistedTimeoutError):
            self.redis.incr("timeouts:" + md5(parsed.host), 1)
            self.redis.expire("timeouts:" + md5(parsed.host), 60 * 60 * 24)
        elif exception:
            logging.error("Caught unhandled exception in handler.")
            logging.error(traceback.format_exc())

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
            Used to be the spider key. Fixed to 'dupefilter' now.
        debug : bool, optional
            Whether to log filtered requests.
        """
        self.server = server
        self.key = "dupefilter"
        self.debug = debug
        self.logdupes = True

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
        return "spider:visitedurls"

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

        # Check the filter for the fingerprint..
        if self.server.execute_command("BF.EXISTS", self.dupes_key, fp) == 1:
            return True

        # Add the fingerprint if it has never been seen.
        self.server.execute_command("BF.ADD", self.dupes_key, fp)

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
        self.server.delete(self.dupes_key)
        self.server.execute_command("BF.RESERVE", self.dupes_key, 0.001, 100000000)

    def log(self, request, spider):
        """Logs given request.
        Parameters
        ----------
        request : scrapy.http.Request
        spider : scrapy.spiders.Spider
        """
        if self.debug:
            msg = "Filtered duplicate request: %(request)s"
            logger.debug(msg, {'request': request}, extra={'spider': spider})
        elif self.logdupes:
            msg = ("Filtered duplicate request %(request)s"
                   " - no more duplicates will be shown"
                   " (see DUPEFILTER_DEBUG to show all duplicates)")
            logger.debug(msg, {'request': request}, extra={'spider': spider})
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
