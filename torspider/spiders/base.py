import time
from datetime import datetime

from scrapy_redis.spiders import RedisSpider

from spidercommon.db import Domain, Page
from spidercommon.urls import ParsedURL
from spidercommon.util import lock_single, md5


class SpiderBase(RedisSpider):
    allowed_domains = ['onion']

    spider_exclude = [
        'blockchainbdgpzk.onion',
        'ypqmhx5z3q5o6beg.onion'
    ]

    clean_start_urls = [
        'http://gxamjbnu7uknahng.onion/',
        'http://mijpsrtgf54l7um6.onion/',
        'http://dirnxxdraygbifgc.onion/',
        'http://torlinkbgs6aabns.onion/'
    ]

    def setup_redis(self, *args, **kwargs):
        super().setup_redis(*args, **kwargs)

        if not self.server.exists("torspider:firstrun"):
            self.server.set("torspider:firstrun", 1)
            self.server.sadd("torspider:urls", *self.clean_start_urls)
            self.server.execute_command("BF.RESERVE", "spider:visitedurls", 0.001, 100000000)

        if hasattr(self, "passed_url"):
            #pylint: disable=E1101
            self.server.sadd("torspider:urls", self.passed_url)

    def update_page_info(self, url, host, title, status_code, content, is_frontpage=False, size=0, db=None):
        if not Domain.is_onion_url(url):
            return None, None

        now = datetime.now()
        parsed = ParsedURL(url)

        # Get or create domain and update info.
        domain = Domain.find_stub_by_url(url, db)
        domain.last_crawl = now
        if is_frontpage:
            if not (domain.title != '' and title == ''):
                domain.title = title
        db.commit()

        # Get or create page.
        page = db.query(Page).filter(Page.url == url).scalar()

        if not page:
            if lock_single(self.server, "page:" + md5(url)):
                page = Page(url=url, domain_id=domain.id, title=title, status_code=status_code, last_crawl=now, is_frontpage=is_frontpage, size=size, path=parsed.path)
                db.add(page)
            else:
                time.sleep(1.5)
                page = db.query(Page).filter(Page.url == url).scalar()

        # Update domain information.
        page.status_code = status_code
        page.last_crawl = now
        page.size = size
        if page.content != content:
            page.content = content
        db.commit()

        return page, domain
