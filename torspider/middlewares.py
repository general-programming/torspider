# -*- coding: utf-8 -*-

# Define here the models for your spider middleware
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/spider-middleware.html

import logging
from urllib.parse import urlparse
from collections import defaultdict
from scrapy import signals
from scrapy.exceptions import IgnoreRequest

from spidercommon.db import Domain, db_session

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
        parsed_url = urlparse(request.url)
        host = parsed_url.hostname
        if self.counter[host] < self.max_pages:
            self.counter[host] += 1
            spider.logger.info('Page count is %d for %s' % (self.counter[host], host))
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

    @db_session
    def process_request(self, request, spider, db=None):
        if not Domain.is_onion_url(request.url):
            return None

        parsed_url = urlparse(request.url)
        host = parsed_url.hostname
        subdomains = host.count(".")
        if subdomains > 2:
            raise IgnoreRequest('Too many subdomains (%d > 2)' % subdomains)

        return None


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
