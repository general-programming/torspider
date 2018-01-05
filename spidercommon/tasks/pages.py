from typing import List, Optional
from urllib.parse import urljoin

from redis import StrictRedis

from spidercommon.model import Domain, sm
from spidercommon.regexes import onion_regex

DEFAULT_HTTP_PORTS = [80, 5000, 5800, 8000, 8008, 8080]


class PageFetcher:
    def __init__(self, redis: StrictRedis, db: sm=None):
        self.db = db
        self.redis = redis

    def fetch_page_for_all_domains(self, page: str):
        if not self.db:
            raise Exception("db is required to run this function.")

        for domain in self.db.query(Domain):
            check_page(self.redis, domain.host, domain.port, page)

    def check_ports_for_all_domains(self, ports: Optional[List[int]]=None):
        if not self.db:
            raise Exception("db is required to run this function.")

        if not ports:
            ports = DEFAULT_HTTP_PORTS.copy()

        for domain in self.db.query(Domain):
            for port in ports:
                check_page(self.redis, domain.host, port)


def check_page(redis: StrictRedis, host: str, port: int=80, path: str="", single: bool=False):
    if port == 80:
        joined_url = f"http://{host}"
    else:
        joined_url = f"http://{host}:{port}"

    joined_url = urljoin(joined_url, path)

    if single:
        redis.sadd("torspider:singleurls", joined_url)
    else:
        redis.sadd("torspider:urls", joined_url)


def find_onions(redis: StrictRedis, content: str):
    if not content:
        return

    try:
        content = str(content)
    except UnicodeDecodeError:
        pass

    onions = onion_regex.findall(content)
    for onion in onions:
        print(f"Adding {onion} to queue.")
        check_page(redis, onion)
