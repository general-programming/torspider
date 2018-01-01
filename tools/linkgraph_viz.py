import json
import random
import re
from collections import defaultdict
from io import BytesIO

from lxml import etree

from spidercommon.db import Domain, Page, sm
from spidercommon.regexes import onion_regex
from spidercommon.urls import ParsedURL

htmlparser = etree.HTMLParser()
db = sm()
nodes = []
edges = []

# Make domain ID graph
domains_by_id = {}
for domain in db.query(Domain):
    domains_by_id[domain.id] = domain
print(f"{len(domains_by_id)} domains in DB.")

# Iterate all pages
link_iters = defaultdict(lambda: defaultdict(lambda: 0))
used_domains = set()

for page in db.query(Page).filter(Page._content != None).order_by(Page.id):
    page_content = page.content
    if isinstance(page_content, str):
        page_content = page_content.encode("utf8")

    if page.id % 250 == 0:
        print(f"Currently at ID {page.id}.")

    title = f"{domains_by_id[page.domain_id].host}\n{domains_by_id[page.domain_id].title or 'No title.'}"
    if page.domain_id not in used_domains:
        nodes.append({
            "id": domains_by_id[page.domain_id].host + ":" + str(domains_by_id[page.domain_id].port),
            "label": title
        })
        used_domains.add(page.domain_id)

    tree = etree.parse(BytesIO(page_content), htmlparser)
    links = tree.xpath('//a/@href')
    for link in links:
        parsed = ParsedURL(link)

        if not onion_regex.match(parsed.host):
            continue

        # XXX: This is bad.
        exists = False
        for _id, domain in domains_by_id.items():
            if parsed.host == domain.host:
                exists = True
                break
        if not exists:
            continue

        link_iters[domains_by_id[page.domain_id].host + ":" + str(domains_by_id[page.domain_id].port)][parsed.host + ":" + str(parsed.port)] += 1

print(f"{len(nodes)} nodes graphed.")

# Construct vis data.
for parent_node, child_link_list in link_iters.items():
    for child_link, child_count in child_link_list.items():
        # Prevent self looping.
        if parent_node == child_link:
            continue

        edges.append({
            "from": parent_node,
            "to": child_link,
            "value": child_count
        })

print(f"{len(edges)} edges graphed.")

vis_data = {
    "nodes": nodes,
    "edges": edges
}

with open("data.js", "w+") as f:
    f.write("var data = ")
    json.dump(vis_data, f)
    f.write(";")
