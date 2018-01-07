import json
import os
import re
from urllib.parse import urljoin

import scrapy
from scrapy.exceptions import CloseSpider
from scrapy_redis.spiders import RedisSpider
from scrapy_redis.utils import bytes_to_str
from twisted.internet.error import TimeoutError as TwistedTimeoutError

from spidercommon.constants import GOOD_STATUS_CODES
from spidercommon.model import Domain, Page
from spidercommon.urls import ParsedURL
from spidercommon.util.distribution import queue_url
from spidercommon.util.hashing import md5


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

    follow_links = False

    def setup_redis(self, *args, **kwargs):
        super().setup_redis(*args, **kwargs)

        if "SOCKS_PROXY" not in os.environ:
            raise CloseSpider("Refusing to run spider without a SOCKS proxy setup.")

        if not self.server.exists("torspider:firstrun"):
            self.server.set("torspider:firstrun", 1)
            queue_url(self.server, 0, "tordirectory", *self.clean_start_urls)
            self.server.execute_command("BF.RESERVE", "spider:visitedurls", 0.001, 100000000)

        if hasattr(self, "passed_url"):
            #pylint: disable=E1101
            queue_url(self.server, 0, "tordirectory", self.passed_url)

    def make_request_from_data(self, data):
        try:
            data = json.loads(data)
            if not isinstance(data, dict):
                self.logger.warn("Somehow got a %s instead of a dict for data." % (type(data)))
                raise TypeError("Data is not a dict.")
        except (json.JSONDecodeError, TypeError):
            return super().make_request_from_data(self, data)

        request = self.make_requests_from_url(data["url"])
        request.priority = data.get("priority", 0)

        return request

    def parse(self, response):
        page_metadata = self.parse_page_info(response)

        if not page_metadata:
            return None

        if self.follow_links:
            for link in page_metadata["links_to"]:
                yield scrapy.Request(link, callback=self.parse)

            for link in page_metadata["other_links"]:
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

    def parse_page_info(self, response):
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
            "links_to": set(),
            "other_links": set()
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
                # Split thhe URL for any onion to clean out web to onion services if they exist.
                fullurl_parts = response.urljoin(url).split(".onion", 1)

                # Skip this URL if it has only one part. Onions should have two parts.
                if len(fullurl_parts) == 1:
                    self.logger.debug(f"Stage 1 dropping non-onion URL '{fullurl_parts[0]}'.")
                    continue

                # Some people did things like qwertyuiop.onion.onion/index.php. No idea why but this happened.
                while fullurl_parts[1].startswith(".onion"):
                    fullurl_parts[1] = fullurl_parts[1].lstrip(".onion")

                # Merge the parts back together.
                fullurl = urljoin(fullurl_parts[0] + ".onion", fullurl_parts[1])

                # Do additional checks post-merge just in case things happen.
                if not got_server_response:
                    self.logger.debug(f"Did not get server response from '{fullurl}'.")
                elif not Domain.is_onion_url(fullurl):
                    self.logger.debug(f"Stage 2 dropping non-onion URL '{fullurl_parts[0]}'.")

                # Parse the link and update the lists.
                try:
                    parsed_link = ParsedURL(fullurl)
                    link_host = parsed_link.host
                except:
                    continue

                if parsed.host != link_host:
                    page_metadata["links_to"].add(fullurl)
                else:
                    page_metadata["other_links"].add(fullurl)

            if len(page_metadata["links_to"]) <= 5:
                self.logger.debug("link_to_list len %s %s" % (len(page_metadata["links_to"]), page_metadata["links_to"]))
            else:
                self.logger.debug("link_to_list len %s truncated" % (len(page_metadata["links_to"])))

        return page_metadata

    def process_exception(self, response, exception, spider):
        parsed = ParsedURL(response.url)

        if isinstance(exception, TwistedTimeoutError):
            self.server.incr("timeouts:" + md5(parsed.host), 1)
            self.server.expire("timeouts:" + md5(parsed.host), 60 * 60 * 24)
