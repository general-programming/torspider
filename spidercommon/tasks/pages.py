from typing import List, Optional
from urllib.parse import urljoin

from redis import StrictRedis

from spidercommon.model import Domain, session_scope
from spidercommon.regexes import onion_regex
from spidercommon.tasks import WorkerTask, celery
from spidercommon.util.distribution import queue_url

DEFAULT_HTTP_PORTS = [80, 5000, 5800, 8000, 8008, 8080]


@celery.task(base=WorkerTask)
def fetch_page_for_all_domains(page: str):
    redis = fetch_page_for_all_domains.redis

    with session_scope() as db:
        for domain in db.query(Domain):
            check_page(redis, domain.host, domain.port, page)


@celery.task(base=WorkerTask)
def check_ports_for_all_domains(ports: Optional[List[int]]=None):
    redis = check_ports_for_all_domains.redis

    if not ports:
        ports = DEFAULT_HTTP_PORTS.copy()

    with session_scope() as db:
        for domain in db.query(Domain):
            for port in ports:
                check_page(redis, domain.host, port)


def check_page(redis: StrictRedis, host: str, port: int=80, path: str="", single: bool=False):
    if port == 80:
        joined_url = f"http://{host}"
    else:
        joined_url = f"http://{host}:{port}"

    joined_url = urljoin(joined_url, path)

    if single:
        queue_url(redis, 0, "singleurls", joined_url)
    else:
        queue_url(redis, 0, "urls", joined_url)


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
