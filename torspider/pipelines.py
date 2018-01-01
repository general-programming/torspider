# -*- coding: utf-8 -*-

import time
from datetime import datetime

from scrapy.exceptions import DropItem

from spidercommon.db import Domain, Page, db_session
from spidercommon.redis import create_redis
from spidercommon.urls import ParsedURL
from spidercommon.util import lock_single, md5

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html


class DatabasePipeline(object):
    def __init__(self):
        self.redis = create_redis()

    @db_session
    def process_item(self, item, spider, db=None):
        if not item:
            raise DropItem("Somehow got a blank item dict.")

        if not Domain.is_onion_url(item["url"]):
            raise DropItem(f"{item['url']} is not an onion.")

        now = datetime.now()
        parsed = ParsedURL(item["url"])

        # Get or create domain and update info.
        domain = Domain.find_stub_by_url(item["url"], db)
        domain.last_crawl = now
        if item["frontpage"]:
            if not (domain.title != '' and item["title"] == ''):
                domain.title = item["title"]
        db.commit()

        # Get or create page.
        page = db.query(Page).filter(Page.url == item["url"]).scalar()

        if not page:
            if lock_single(self.redis, "page:" + md5(item["url"])):
                page = Page(
                    url=item["url"],
                    domain_id=domain.id,
                    title=item["title"],
                    status_code=item["status_code"],
                    last_crawl=now,
                    is_frontpage=item["frontpage"],
                    size=item["size"],
                    path=parsed.path
                )
                db.add(page)
            else:
                time.sleep(1.5)
                page = db.query(Page).filter(Page.url == item["url"]).scalar()

        # Update domain information.
        page.status_code = item["status_code"]
        page.last_crawl = now
        page.size = item["size"]
        if page.content != item["content"]:
            page.content = item["content"]
        page.header_server = item["server"]
        page.header_powered_by = item["powered_by"]

        # Update links to.
        page.links_to = list(item["links_to"])

        db.commit()
        return item
