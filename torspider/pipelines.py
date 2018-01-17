# -*- coding: utf-8 -*-

import time
from datetime import datetime

from scrapy.exceptions import DropItem
from sqlalchemy.dialects.postgresql import insert

from spidercommon.constants import BAD_STATUS_CODES, BLACKLISTED_BLANK
from spidercommon.model import Domain, File, Page, db_session
from spidercommon.redis import create_redis
from spidercommon.urls import ParsedURL
from spidercommon.util.distribution import lock_single
from spidercommon.util.hashing import md5, sha256
from spidercommon.util.storage import HashedFile

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html


class DatabasePipeline(object):
    def __init__(self):
        self.redis = create_redis()

    @db_session
    def process_item(self, item, spider, db=None):
        # Sanity checks
        if not item:
            raise DropItem("Somehow got a blank item dict.")

        if not Domain.is_onion_url(item["url"]):
            raise DropItem(f"{item['url']} is not an onion.")

        now = datetime.now()
        parsed = ParsedURL(item["url"])

        # Get or create domain and update info.
        domain = Domain.find_stub_by_url(item["url"], db)
        domain.last_crawl = now
        domain.alive = item["status_code"] not in BAD_STATUS_CODES
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
                    path=parsed.path
                )
                db.add(page)
            else:
                time.sleep(1.5)
                page = db.query(Page).filter(Page.url == item["url"]).scalar()

        # Update domain information.
        page.status_code = item["status_code"]
        page.last_crawl = now
        page.header_server = item["server"]
        page.header_powered_by = item["powered_by"]
        page.title = item["title"]

        # Update links to.
        page.links_to = list(item["links_to"])

        db.commit()
        return item


class FilePipeline(object):
    def __init__(self):
        self.redis = create_redis()

    @db_session
    def process_item(self, item, spider, db=None):
        # Get domain and parsed URL info.
        domain = Domain.find_stub_by_url(item["url"], db)
        parsed = ParsedURL(item["url"])
        now = datetime.now()

        # Get or create file.
        file_row = db.query(File).filter(File.url == item["url"]).scalar()

        if not file_row:
            statement = insert(File).values(
                url=item["url"],
                domain_id=domain.id,
                last_crawl=now,
                size=item["size"],
                path=parsed.path
            ).on_conflict_do_nothing(index_elements=["url"])
            db.execute(statement)
            time.sleep(1)
            file_row = db.query(File).filter(File.url == item["url"]).scalar()

        # Update file information.
        file_store = HashedFile.from_data(item["content"], save=False)

        file_row.last_crawl = now

        if domain.blacklisted:
            # Override the old file before replacing the content.
            file_store.write(BLACKLISTED_BLANK)
            file_row.content = BLACKLISTED_BLANK
        elif file_store.read() != item["content"]:
            file_row.content = item["content"]

        db.commit()

        return item
