# This Python file uses the following encoding: utf-8
import datetime
import os
import re
from urllib.parse import urlparse

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Unicode, UnicodeText, ARRAY, create_engine, and_
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, scoped_session, sessionmaker, validates
from sqlalchemy.schema import Index
from functools import wraps

debug = os.environ.get('DEBUG', False)

engine = create_engine(
    os.environ["POSTGRES_URL"],
    convert_unicode=True,
    pool_recycle=3600,
    pool_size=25,
    max_overflow=25
)

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

    content = Column(UnicodeText)

    domain = relationship("Domain")

    @classmethod
    def find_stub_by_url(cls, url, db):
        now = datetime.datetime.now()
        page = db.query(Page).filter(Page.url == url).scalar()
        if not page:
            domain = Domain.find_stub_by_url(url, db)
            page = cls(url=url, domain_id=domain.id)
            db.add(page)
            db.commit()

        return page

    @property
    def got_server_response(self):
        responded = [200, 401, 403, 500, 302, 304, 206]
        return (self.status_code in responded)

    @staticmethod
    def is_frontpage_url(url):
        parsed_url = urlparse(url)
        path  = '/' if parsed_url.path=='' else parsed_url.path
        if path == '/':
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
            domain = cls(host=host, port=port, secure=ssl, last_crawl=now())
            db.add(domain)
            db.commit()

        return domain

    @classmethod
    def find_stub_by_url(cls, url, db):
        parsed_url = urlparse(url)
        host = parsed_url.hostname
        port = parsed_url.port
        ssl  = parsed_url.scheme == "https://"
        if not port:
            if ssl:
                port = 443
            else:
                port = 80

        return cls.find_stub(host, port, ssl, db)

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
            parsed_url = urlparse(url)
            host = parsed_url.hostname
            if re.match("[a-zA-Z0-9.]+\.onion$", host):
                return True
            else:
                return False
        except:
            return False


# Indexes
Index("index_domain_host", Domain.host)
Index("index_page_url", Page.url)
Index("index_page_domain_id", Page.domain_id)
