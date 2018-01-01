import re

import scrapy
from scrapy_redis.spiders import RedisSpider

from spidercommon.db import Domain, Page, db_session
from spidercommon.urls import ParsedURL
from torspider.constants import GOOD_STATUS_CODES


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

    @db_session
    def parse(self, response, follow_links=False, db=None):
        page_metadata = self.parse_page_info(response, db)

        if not page_metadata:
            return None

        if follow_links:
            for link in page_metadata["links_to"]:
                yield scrapy.Request(link, callback=self.parse)

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

        yield page_metadata

    def parse_page_info(self, response, db=None):
        """
            Parses the page meta information for the pipeline.

            Example return:
                {
                    "host": "someonionpagehostname.onion",
                    "url": "someonionpagehostname.onion/",
                    "status_code": 200,
                    "size": 420,
                    "server": "TotallyReal Server",
                    "powered_by": "IE 6.0",
                    "title": "Page title",
                    "frontpage": True,
                    "content": "<h1>Under Construction</h1>",
                    "links_to": set()
                }
        """

        page_metadata = {
            # HTTP headers
            "host": "",
            "url": response.url,
            "status_code": response.status,
            "size": 0,
            "server": "",
            "powered_by": "",

            # Parsed from page
            "title": "",
            "frontpage": False,
            "content": response.text,
            "links_to": set()
        }

        # Grab the title of the page.
        try:
            page_metadata["title"] = response.css('title::text').extract_first()
        except AttributeError:
            pass
        except scrapy.exceptions.NotSupported:
            self.log(f"Skipping non-text file {response.url}")
            return None

        # Get tor URL "hostname"
        parsed = ParsedURL(response.url)

        self.log('Got %s (%s)' % (response.url, page_metadata["title"]))
        page_metadata["frontpage"] = Page.is_frontpage_request(response.request)
        page_metadata["size"] = len(response.body)
        page_metadata["host"] = parsed.host

        # XXX: Make a constant for this.
        got_server_response = response.status in GOOD_STATUS_CODES

        # Domain headers
        if got_server_response:
            if response.headers.get("Server"):
                page_metadata["server"] = str(response.headers.get("Server"))
            if response.headers.get("X-Powered-By"):
                page_metadata["powered_by"] = str(response.headers.get("X-Powered-By"))
            if response.headers.get("Powered-By"):
                page_metadata["powered_by"] = str(response.headers.get("Powered-By"))

        is_text = False
        content_type = str(response.headers.get("Content-Type"))
        if got_server_response and content_type and re.match('^text/', content_type.strip()):
            is_text = True
        
        # Update links_to
        if parsed.host not in self.spider_exclude:
            for url in response.xpath('//a/@href').extract():
                fullurl = response.urljoin(url)

                if got_server_response and Domain.is_onion_url(fullurl):
                    try:
                        parsed_link = ParsedURL(fullurl)
                    except:
                        continue
                    link_host = parsed_link.host
                    if parsed.host != link_host:
                        page_metadata["links_to"].add(fullurl)

            self.log("link_to_list %s" % page_metadata["links_to"])

            db.commit()

        return page_metadata
