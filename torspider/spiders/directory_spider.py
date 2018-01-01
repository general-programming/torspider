# Credits to https://github.com/dirtyfilthy/freshonions-torscraper/blob/master/torscraper/spiders/tor_scrapy.py for basic framework

import random
import re
import time
from datetime import datetime, timedelta

import scrapy
import timeout_decorator
from sqlalchemy import and_

from spidercommon.db import Domain, Page, db_session, sm
from spidercommon.urls import ParsedURL
from torspider.spiders.base import SpiderBase


class DirectorySpider(SpiderBase):
    name = "tordirectory"

    custom_settings = {
        # Scrapy
        'DOWNLOAD_MAXSIZE': (1024 * 1024) * 2,
        # Middleware
        'MAX_PAGES_PER_DOMAIN' : 2000,
        # scrapy_redis middleware
        'REDIS_START_URLS_AS_SET': True,
        'REDIS_START_URLS_KEY': 'torspider:urls',
    }

    def parse(self, *args, **kwargs):
        return super().parse(follow_links=True, *args, **kwargs)
