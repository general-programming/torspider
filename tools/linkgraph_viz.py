import re
import json
from spidercommon.db import sm, Page, Domain
from lxml import etree
from io import StringIO
from urllib.parse import urlparse
from collections import defaultdict

htmlparser = etree.HTMLParser()
db = sm()
nodes = []
edges = []

# Make domain ID graph
domains_by_id = {}
for domain in db.query(Domain):
    domains_by_id[domain.id] = domain

# Iterate all pages
link_iters = defaultdict(lambda: defaultdict(lambda: 0))
used_domains = set()

for page_domain_id, page_content, page_url in db.query(Page.domain_id, Page.content, Page.url).filter(Page.content != ""):
    title = f"{domains_by_id[page_domain_id].host}\n{domains_by_id[page_domain_id].title or 'No title.'}"
    if page_domain_id not in used_domains:
        nodes.append({
            "id": domains_by_id[page_domain_id].host + ":" + str(domains_by_id[page_domain_id].port),
            "label": title
        })
        used_domains.add(page_domain_id)

    tree = etree.parse(StringIO(page_content), htmlparser)
    links = tree.xpath('//a/@href')
    for link in links:
        parsed_url = urlparse(link)
        parsed_host = parsed_url.hostname
        parsed_port = parsed_url.port
        parsed_ssl = parsed_url.scheme == "https://"
        if not parsed_port:
            if parsed_ssl:
                parsed_port = 443
            else:
                parsed_port = 80

        if not re.match("[a-zA-Z0-9.]+\.onion$", str(parsed_host)):
            continue

        # XXX: This is bad.
        exists = False
        for _id, domain in domains_by_id.items():
            if parsed_host == domain.host:
                exists = True
                break
        if not exists:
            continue


        link_iters[domains_by_id[page_domain_id].host + ":" + str(domains_by_id[page_domain_id].port)][parsed_url.hostname + ":" + str(parsed_port)] += 1

# Construct vis data.
for parent_node, child_link_list in link_iters.items():
    for child_link, child_count in child_link_list.items():
        edges.append({
            "from": parent_node,
            "to": child_link,
            "value": child_count
        })

vis_data = {
    "nodes": nodes,
    "edges": edges
}
with open("vis_data.json", "w+") as f:
    json.dump(vis_data, f)
