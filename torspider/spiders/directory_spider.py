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

    @db_session
    def parse(self, response, recent_alive_check=False, db=None):
        parsed, page = self.update_page_info(response, db, follow_links=True)

        if not page:
            return

        # XXX Make this code work.
        """ See how useful random path checking can be later.
        # Add some randomness to the check
        path_event_horizon = datetime.now() - timedelta(days=14 + random.randint(0, 14))

        # Interesting paths
        if domain.is_up and domain.path_scanned_at < path_event_horizon:
            domain.path_scanned_at = datetime.now()
            commit()
            for url in interesting_paths.construct_urls(domain):
                yield scrapy.Request(url, callback=self.parse)

        # /description.json
        if domain.is_up and domain.description_json_at < path_event_horizon:
            domain.description_json_at = datetime.now()
            commit()
            yield scrapy.Request(domain.construct_url("/description.json"), callback=self.description_json)
        """
