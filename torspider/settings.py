# -*- coding: utf-8 -*-

import os
from raven import Client
from twisted.python import log

# Scrapy settings for torspider project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     http://doc.scrapy.org/en/latest/topics/settings.html
#     http://scrapy.readthedocs.org/en/latest/topics/downloader-middleware.html
#     http://scrapy.readthedocs.org/en/latest/topics/spider-middleware.html

BOT_NAME = 'torspider'

HTTP_PROXY = 'http://127.0.0.1:8123'

SPIDER_MODULES = ['torspider.spiders']
NEWSPIDER_MODULE = 'torspider.spiders'

# Crawl responsibly by identifying yourself (and your website) on the user-agent
USER_AGENT = 'Mozilla/5.0 (Windows NT 6.1; rv:52.0) Gecko/20100101 Firefox/52.0'

# Obey robots.txt rules
ROBOTSTXT_OBEY = False

# Disable cookies (enabled by default)
COOKIES_ENABLED = False

# Enable telnet console if TELNET_ENABLE in environ. (Enabled by default)
TELNETCONSOLE_ENABLED = "TELNET_ENABLE" in os.environ

# Override the default request headers:
DEFAULT_REQUEST_HEADERS = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
}

# Enable or disable spider middlewares
# See http://scrapy.readthedocs.org/en/latest/topics/spider-middleware.html
SPIDER_MIDDLEWARES = {
    'scrapy.spidermiddlewares.depth.DepthMiddleware': 100,
}

# Enable or disable downloader middlewares
# See http://scrapy.readthedocs.org/en/latest/topics/downloader-middleware.html
DOWNLOADER_MIDDLEWARES = {
    'torspider.middlewares.FilterTooManySubdomainsMiddleware': 300,
    'torspider.middlewares.FilterDomainByPageLimitMiddleware': 550,
}

# Enable or disable extensions
# See http://scrapy.readthedocs.org/en/latest/topics/extensions.html
EXTENSIONS = {}

# Configure item pipelines
# See http://scrapy.readthedocs.org/en/latest/topics/item-pipeline.html
ITEM_PIPELINES = {
    'torspider.pipelines.DatabasePipeline': 100,
}

# Our special sauce
RETRY_TIMES = 1
DOWNLOAD_TIMEOUT = 90  # XXX: Why is 90 seconds the timeout?
DEPTH_PRIORITY = 8
CONCURRENT_REQUESTS = 128
REACTOR_THREADPOOL_MAXSIZE = 32
CONCURRENT_REQUESTS_PER_DOMAIN = 8
RETRY_HTTP_CODES = [500, 502, 503, 504, 408, 400]

# Redis
SCHEDULER = "scrapy_redis.scheduler.Scheduler"
SCHEDULER_PERSIST = True
SCHEDULER_QUEUE_KEY = "zqueue:%(spider)s"
DUPEFILTER_CLASS = "torspider.middlewares.RedisCustomDupeFilter"
REDIS_HOST = os.environ.get('REDIS_PORT_6379_TCP_ADDR', os.environ.get('REDIS_HOST', '127.0.0.1'))
REDIS_PORT = int(os.environ.get('REDIS_PORT', 6379))

# Sentry https://github.com/llonchj/scrapy-sentry/issues/6
SENTRY_DSN = os.environ.get("SENTRY_DSN", None)
if SENTRY_DSN:
    client = Client(dsn=SENTRY_DSN)


    def log_sentry(dictionary):
        if dictionary.get('isError') and 'failure' in dictionary:
            try:
                # Raise the failure
                dictionary['failure'].raiseException()
            except:
                # so we can capture it here.
                client.captureException()


    log.addObserver(log_sentry)

# Tor socks
DOWNLOAD_HANDLERS = {
    'http': 'torspider.transports.TorDownloadHandler',
    'https': 'torspider.transports.TorDownloadHandler'
}
