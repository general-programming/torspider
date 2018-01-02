# This Python file uses the following encoding: utf-8
import datetime
import os
import re
import time
from functools import wraps
from typing import Union

import brotli
from sqlalchemy import (ARRAY, Boolean, Column, DateTime, ForeignKey, Integer,
                        LargeBinary, String, Unicode, UnicodeText, and_,
                        create_engine, func)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import (relationship, scoped_session, sessionmaker,
                            validates)
from sqlalchemy.pool import NullPool
from sqlalchemy.schema import Index

from spidercommon.constants import GOOD_STATUS_CODES
from spidercommon.redis import create_redis
from spidercommon.regexes import onion_regex
from spidercommon.urls import ParsedURL
from spidercommon.util import lock_single, md5

debug = os.environ.get('DEBUG', False)

engine = create_engine(
    os.environ["POSTGRES_URL"],
    convert_unicode=True,
    poolclass=NullPool,
)

redis = create_redis()

if debug:
    engine.echo = True

sm = sessionmaker(autocommit=False,
                  autoflush=False,
                  bind=engine)

base_session = scoped_session(sm)

Base = declarative_base()
Base.query = base_session.query_property()

def now():
    return datetime.datetime.now()

def db_session(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Call the function normally if it already has a DB object.
        if kwargs.get("db", None):
            return f(*args, **kwargs)

        db = sm()

        try:
            return f(db=db, *args, **kwargs)
        finally:
            db.close()
    return decorated_function

class Page(Base):
    __tablename__ = "pages"
    id = Column(Integer, primary_key=True)
    domain_id = Column(ForeignKey("domains.id"), nullable=False)

    url = Column(Unicode, nullable=False)
    path = Column(Unicode)

    first_crawl = Column(DateTime(), nullable=False, default=now)
    last_crawl = Column(DateTime(), nullable=False, default=now)
    status_code = Column(Integer, nullable=False, default=1234)
    is_frontpage = Column(Boolean, nullable=False, default=False)
    post_process_version = Column(Integer, nullable=False, default=0)

    title = Column(Unicode, default="")
    size = Column(Integer, default=0)
    links_to = Column(ARRAY(String), default=[])

    _content = Column("content", LargeBinary)

    domain = relationship("Domain")

    @property
    def content(self):
        if not self._content:
            return None

        decompressed = brotli.decompress(self._content)
        try:
            decompressed = decompressed.decode("utf8")
        except UnicodeDecodeError:
            pass

        return decompressed

    @content.setter
    def content(self, content) -> Union[str, bytes]:
        if isinstance(content, str):
            content = content.encode("utf8")

        self._content = brotli.compress(content)

    @classmethod
    def find_stub_by_url(cls, url: str, db):
        now = datetime.datetime.now()
        page = db.query(Page).filter(Page.url == url).scalar()

        if not page:
            domain = Domain.find_stub_by_url(url, db)
            if lock_single(redis, "page:" + md5(url)):
                page = cls(url=url, domain_id=domain.id)
                db.add(page)
                db.commit()
            else:
                time.sleep(1)
                page = db.query(Page).filter(Page.url == url).scalar()

        return page

    @property
    def got_server_response(self):
        return (self.status_code in GOOD_STATUS_CODES)

    @staticmethod
    def is_frontpage_url(url):
        parsed = ParsedURL(url)
        if parsed.path == '/':
            return True

        return False

    @classmethod
    def is_frontpage_request(cls, request):
        if cls.is_frontpage_url(request.url):
            return True

        if request.meta.get('redirect_urls'):
            for url in request.meta.get('redirect_urls'):
                if cls.is_frontpage_url(url):
                    return True

        return False

class Domain(Base):
    __tablename__ = "domains"
    id = Column(Integer, primary_key=True)

    host = Column(String, nullable=False)
    port = Column(Integer, nullable=False)
    secure = Column(Boolean, nullable=False)

    first_crawl = Column(DateTime(), nullable=False, default=now)
    last_crawl = Column(DateTime(), nullable=False, default=now)
    alive = Column(Boolean, server_default='f')

    title = Column(Unicode)
    header_server = Column(Unicode)
    header_powered_by = Column(Unicode)

    @classmethod
    def find_stub(cls, host, port, ssl, db):
        domain = db.query(Domain).filter(and_(
            Domain.host == host,
            Domain.port == port,
            Domain.secure == ssl
        )).scalar()

        if not domain:
            if lock_single(redis, "domain:" + md5(f"{host}:{port}:{ssl}")):
                domain = cls(host=host, port=port, secure=ssl, last_crawl=now())
                db.add(domain)
                db.commit()
            else:
                time.sleep(1)
                domain = db.query(Domain).filter(and_(
                    Domain.host == host,
                    Domain.port == port,
                    Domain.secure == ssl
                )).scalar()

        return domain

    @classmethod
    def find_stub_by_url(cls, url, db):
        parsed = ParsedURL(url)
        return cls.find_stub(parsed.host, parsed.port, parsed.secure, db)

    @property
    def is_subdomain(self):
        if self.host.count(".") > 1:
            return True

    @staticmethod
    def is_onion_url(url: str):
        url = url.strip()
        if not re.match(r"http[s]?://", url):
            return False

        try:
            parsed_url = ParsedURL(url)
            if onion_regex.match(parsed_url.host):
                return True
            else:
                return False
        except:
            return False

class OnionListPage(Base):
    """
        Page model for grabs of big onion lists.
    """

    __tablename__ = "onion_listpages"
    id = Column(Integer, primary_key=True)

    url = Column(String, nullable=False)
    first_crawl = Column(DateTime(), nullable=False, default=now)
    last_crawl = Column(DateTime(), nullable=False, default=now)

    _content = Column("content", LargeBinary)

    @property
    def content(self):
        if not self._content:
            return None

        decompressed = brotli.decompress(self._content)
        try:
            decompressed = decompressed.decode("utf8")
        except UnicodeDecodeError:
            pass

        return decompressed

    @content.setter
    def content(self, content) -> Union[str, bytes]:
        if isinstance(content, str):
            content = content.encode("utf8")

        self._content = brotli.compress(content)


class OnionBlacklist(Base):
    """
        Model to store hashed blacklisted onions.
    """

    __tablename__ = "onion_blacklist"
    id = Column(Integer, primary_key=True)

    hexhash = Column(String, nullable=False)
    source = Column(String, nullable=False)

# Indexes
Index("index_domain_host", Domain.host)
Index("index_page_url", Page.url)
Index("index_page_domain_id", Page.domain_id)
Index("index_blacklist_hash", OnionBlacklist.hexhash)
