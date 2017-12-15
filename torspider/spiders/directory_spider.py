# Credits to https://github.com/dirtyfilthy/freshonions-torscraper/blob/master/torscraper/spiders/tor_scrapy.py for basic framework

import scrapy
import timeout_decorator
from datetime import datetime, timedelta
import random
import re
from urllib.parse import urlparse

from sqlalchemy import and_

from spidercommon.db import db_session, Page, Domain

class DirectorySpider(scrapy.Spider):
    name = "tor"
    allowed_domains = ['onion']

    start_urls = [
        'http://gxamjbnu7uknahng.onion/',
        'http://mijpsrtgf54l7um6.onion/',
        'http://dirnxxdraygbifgc.onion/',
        'http://torlinkbgs6aabns.onion/'
    ]

    spider_exclude = [
        'blockchainbdgpzk.onion',
        'ypqmhx5z3q5o6beg.onion'
    ]

    custom_settings = {
        # Scrapy
        'DOWNLOAD_MAXSIZE': (1024 * 1024) * 2,
        # Middleware
        'MAX_PAGES_PER_DOMAIN' : 1000,
    }

    scrap_directories = [
        "zlal32teyptf4tvi.onion"
    ]

    def __init__(self, *args, **kwargs):
        super(DirectorySpider, self).__init__(*args, **kwargs)

        if hasattr(self, "passed_url"):
            self.start_urls = [self.passed_url]
        elif hasattr(self, "whole_site"):
            self.start_requests = [self.whole_site]
            self.allowed_domains = [self.whole_site]

    @db_session
    def parse(self, response, recent_alive_check=False, db=None):
        MAX_PARSE_SIZE_KB = 2048

        # Grab the title of the page.
        title = ''
        try:
            title = response.css('title::text').extract_first()
        except AttributeError:
            pass

        # Get tor URL "hostname"
        parsed_url = urlparse(response.url)
        host = parsed_url.hostname

        # Skip directories that are made by scrapping.
        if host in self.scrap_directories:
            return

        self.log('Got %s (%s)' % (response.url, title))
        is_frontpage = Page.is_frontpage_request(response.request)
        size = len(response.body)
        
        page, domain = self.update_page_info(response.url, host, title, response.status, response.text, is_frontpage, size, db)
        if not page:
            return

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
        
        link_to_list = []
        self.log("Finding links...")

        if host not in DirectorySpider.spider_exclude:
            for url in response.xpath('//a/@href').extract():
                fullurl = response.urljoin(url)
                yield scrapy.Request(fullurl, callback=self.parse)
                if page.got_server_response and Domain.is_onion_url(fullurl):
                    try:
                        parsed_link = urlparse(fullurl)
                    except:
                        continue
                    link_host = parsed_link.hostname
                    if host != link_host:
                        link_to_list.append(fullurl)

            self.log("link_to_list %s" % link_to_list)
                
            if page.got_server_response:
                small_body = response.body[:(1024 * MAX_PARSE_SIZE_KB)]
                links_to = set()
                for url in link_to_list:
                    link_to = Page.find_stub_by_url(url, db)
                    if link_to not in page.links_to:
                        links_to.add(url)
                    page.links_to = list(links_to)

                db.commit()

    def update_page_info(self, url, host, title, status_code, content, is_frontpage=False, size=0, db=None):
        if not Domain.is_onion_url(url):
            return False

        now = datetime.now()
        parsed_url = urlparse(url)
        path = '/' if parsed_url.path == '' else parsed_url.path

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
            page = Page(url=url, domain_id=domain.id, title=title, status_code=status_code, last_crawl=now, is_frontpage=is_frontpage, size=size, path=path)
            db.add(page)

        # Update domain information.
        page.status_code = status_code
        page.last_crawl = now
        page.size = size
        if page.content != content:
            page.content = content
        db.commit()

        return page, domain
