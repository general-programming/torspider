import re
import json
from spidercommon.db import sm, Page, Domain
from spidercommon.urls import ParsedURL
from lxml import etree
from io import BytesIO
import random
from collections import defaultdict

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

for page_id, page_domain_id, page_content, page_url in db.query(Page.id, Page.domain_id, Page.content, Page.url).filter(Page.content != ""):
    if page_id % random.randint(1500, 2000) < 10:
        print(f"Currently at ID {page_id}.")

    title = f"{domains_by_id[page_domain_id].host}\n{domains_by_id[page_domain_id].title or 'No title.'}"
    if page_domain_id not in used_domains:
        nodes.append({
            "id": domains_by_id[page_domain_id].host + ":" + str(domains_by_id[page_domain_id].port),
            "label": title
        })
        used_domains.add(page_domain_id)

    if isinstance(page_content, str):
        page_content = page_content.encode("utf8")

    tree = etree.parse(BytesIO(page_content), htmlparser)
    links = tree.xpath('//a/@href')
    for link in links:
        parsed = ParsedURL(link)

        if not re.match("[a-zA-Z0-9.]+\.onion$", parsed.host):
            continue

        # XXX: This is bad.
        exists = False
        for _id, domain in domains_by_id.items():
            if parsed.host == domain.host:
                exists = True
                break
        if not exists:
            continue


        link_iters[domains_by_id[page_domain_id].host + ":" + str(domains_by_id[page_domain_id].port)][parsed.host + ":" + str(parsed.port)] += 1

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
