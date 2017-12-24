# -*- coding: utf-8 -*-

import os

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

# Configure maximum concurrent requests performed by Scrapy (default: 16)
#CONCURRENT_REQUESTS = 32

# Configure a delay for requests for the same website (default: 0)
# See http://scrapy.readthedocs.org/en/latest/topics/settings.html#download-delay
# See also autothrottle settings and docs
#DOWNLOAD_DELAY = 3
# The download delay setting will honor only one of:
#CONCURRENT_REQUESTS_PER_DOMAIN = 16
#CONCURRENT_REQUESTS_PER_IP = 16

# Disable cookies (enabled by default)
COOKIES_ENABLED = False

# Disable Telnet Console (enabled by default)
TELNETCONSOLE_ENABLED = False

# Override the default request headers:
DEFAULT_REQUEST_HEADERS = {
  'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
  'Accept-Language': 'en-US,en;q=0.5',
}

# Enable or disable spider middlewares
# See http://scrapy.readthedocs.org/en/latest/topics/spider-middleware.html
SPIDER_MIDDLEWARES = {
   'TorspiderSpiderMiddlewarescrapy.spidermiddlewares.depth.DepthMiddleware': 100,
}

# Enable or disable downloader middlewares
# See http://scrapy.readthedocs.org/en/latest/topics/downloader-middleware.html
DOWNLOADER_MIDDLEWARES = {
    'torspider.middlewares.FilterDomainByPageLimitMiddleware' : 551,
    'torspider.middlewares.FilterTooManySubdomainsMiddleware' : 550,
}

# Enable or disable extensions
# See http://scrapy.readthedocs.org/en/latest/topics/extensions.html
EXTENSIONS = {}

# Configure item pipelines
# See http://scrapy.readthedocs.org/en/latest/topics/item-pipeline.html
#ITEM_PIPELINES = {
#    'torspider.pipelines.TorspiderPipeline': 300,
#}

# Our special sauce
RETRY_TIMES = 1
DOWNLOAD_TIMEOUT = 90 # XXX: Why is 90 seconds the timeout?
DEPTH_PRIORITY = 8
CONCURRENT_REQUESTS = 32
REACTOR_THREADPOOL_MAXSIZE = 32
CONCURRENT_REQUESTS_PER_DOMAIN = 4
RETRY_HTTP_CODES = [500, 502, 503, 504, 408, 400]

# Redis
SCHEDULER = "scrapy_redis.scheduler.Scheduler"
SCHEDULER_PERSIST = True
DUPEFILTER_CLASS = "torspider.middlewares.RedisCustomDupeFilter"
REDIS_HOST = os.environ.get('REDIS_PORT_6379_TCP_ADDR', os.environ.get('REDIS_HOST', '127.0.0.1'))
REDIS_PORT = int(os.environ.get('REDIS_PORT', 6379))

# SENTRY
SENTRY_DSN = os.environ.get("SENTRY_DSN", None)
if SENTRY_DSN:
    EXTENSIONS["scrapy_sentry.extensions.Errors"] = 10
