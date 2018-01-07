# coding=utf-8
# Credits to https://github.com/dirtyfilthy/freshonions-torscraper/blob/master/torscraper/spiders/tor_scrapy.py for basic framework

from torspider.spiders.base import SpiderBase


class DirectorySpider(SpiderBase):
    """
        Spider that follows every link until exhaustion.
    """

    name = "tordirectory"

    custom_settings = {
        # Scrapy
        'DOWNLOAD_MAXSIZE': (1024 * 1024) * 2,
        # Middleware
        'MAX_PAGES_PER_DOMAIN': 2000,
        # scrapy_redis middleware
        'REDIS_START_URLS_AS_SET': True,
        'REDIS_START_URLS_KEY': 'queue:urls',
    }

    follow_links = True
