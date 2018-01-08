# coding=utf-8
import os
from datetime import datetime

from elasticsearch import Elasticsearch
from elasticsearch_dsl import (Boolean, Date, DocType, Index, Integer, Text,
                               analyzer, connections)

from spidercommon.util.hashing import md5
from spidercommon.util.text import strip_html

if "ELASTICSEARCH_URL" in os.environ:
    connections.create_connection(hosts=[os.environ["ELASTICSEARCH_URL"]], timeout=30)


class PageDocument(DocType):
    html_strip = analyzer('html_strip',
        tokenizer="standard",
        filter=["standard", "lowercase", "stop", "snowball", "asciifolding"],
        char_filter=["html_strip"]
    )

    db_id = Integer()
    domain_id = Integer()

    url = Text()
    title = Text(analyzer='snowball')
    first_crawl = Date()
    last_crawl = Date()
    is_frontpage = Boolean()
    status_code = Integer()

    content = Text()
    clean_content = Text(analyzer=html_strip, term_vector="with_positions_offsets")

    class Meta:
        name = 'page'
        doc_type = 'page'

    @classmethod
    def get_indexable(cls):
        return cls.get_model().get_objects()

    @classmethod
    def from_obj(cls, obj):
        return cls(
            meta={
                'id': md5(obj.url),
                'routing': obj.domain_id,
            },
            db_id=obj.id,
            domain_id=obj.domain_id,
            url=obj.url,
            title=obj.title,
            first_crawl=obj.first_crawl,
            last_crawl=obj.last_crawl,
            is_frontpage=obj.is_frontpage,
            status_code=obj.status_code,
            content=obj.content,
            clean_content=strip_html(obj.content),
        )


def get_index(create: bool=False):
    if "ELASTICSEARCH_URL" not in os.environ:
        raise Exception("ELASTICSEARCH_URL is not defined.")

    index = Index('torspider')
    index.doc_type(PageDocument)
    if create:
        index.create()

    return index


def get_client():
    if "ELASTICSEARCH_URL" not in os.environ:
        raise Exception("ELASTICSEARCH_URL is not defined.")

    return Elasticsearch([os.environ["ELASTICSEARCH_URL"]], timeout=30)
