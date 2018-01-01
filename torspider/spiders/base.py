import time
import re
from datetime import datetime
import scrapy
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

    max_parse_size_kb = 2048

    def setup_redis(self, *args, **kwargs):
        super().setup_redis(*args, **kwargs)

        if not self.server.exists("torspider:firstrun"):
            self.server.set("torspider:firstrun", 1)
            self.server.sadd("torspider:urls", *self.clean_start_urls)
            self.server.execute_command("BF.RESERVE", "spider:visitedurls", 0.001, 100000000)

        if hasattr(self, "passed_url"):
            #pylint: disable=E1101
            self.server.sadd("torspider:urls", self.passed_url)

    def update_page_info(self, response, db=None, follow_links: bool=False):
        """
            Updates the page meta information in DB.
            Creates the DB objects if they do not exist.

            Updates:
                - Title
                - Hostname
                - Last status code
                - Server header
                - Powered By headers
                - Linked to pages

            Returns:
                Parsed URL object and Page model object.
        """

        # Grab the title of the page.
        title = ''
        try:
            title = response.css('title::text').extract_first()
        except AttributeError:
            pass
        except scrapy.exceptions.NotSupported:
            self.log(f"Skipping non-text file {response.url}")
            return None, None

        # Get tor URL "hostname"
        parsed = ParsedURL(response.url)

        self.log('Got %s (%s)' % (response.url, title))
        is_frontpage = Page.is_frontpage_request(response.request)
        size = len(response.body)
        
        page, domain = self._update_page_info(response.url, parsed.host, title, response.status, response.text, is_frontpage, size, db)
        if not page:
            return None, None

        # Domain headers
        if page.got_server_response:
            if response.headers.get("Server"):
                domain.header_server = str(response.headers.get("Server"))
            if response.headers.get("X-Powered-By"):
                domain.header_powered_by = str(response.headers.get("X-Powered-By"))
            if response.headers.get("Powered-By"):
                domain.header_powered_by = str(response.headers.get("Powered-By"))

        is_text = False
        content_type = str(response.headers.get("Content-Type"))
        if page.got_server_response and content_type and re.match('^text/', content_type.strip()):
            is_text = True
        
        # Update links_to
        link_to_list = []

        if parsed.host not in self.spider_exclude:
            for url in response.xpath('//a/@href').extract():
                fullurl = response.urljoin(url)

                if follow_links:
                    yield scrapy.Request(fullurl, callback=self.parse)

                if page.got_server_response and Domain.is_onion_url(fullurl):
                    try:
                        parsed_link = ParsedURL(fullurl)
                    except:
                        continue
                    link_host = parsed_link.host
                    if parsed.host != link_host:
                        link_to_list.append(fullurl)

            self.log("link_to_list %s" % link_to_list)
                
            if page.got_server_response:
                small_body = response.body[:(1024 * self.max_parse_size_kb)]
                links_to = set()
                for url in link_to_list:
                    if url not in page.links_to:
                        links_to.add(url)
                    page.links_to = list(links_to)

            db.commit()

        return parsed, page

    def _update_page_info(self, url: str, host: str, title: str, status_code: int, content, is_frontpage: bool=False, size: int=0, db=None):
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
