from torspider.spiders.base import SpiderBase

class LinkSpider(SpiderBase):
    """
        Spider that grabs single links and does not follow them.
    """

    name = "torlink"

    custom_settings = {
        # Scrapy
        'DOWNLOAD_MAXSIZE': (1024 * 1024) * 2,
        # Middleware
        'MAX_PAGES_PER_DOMAIN' : -1,
        # scrapy_redis middleware
        'REDIS_START_URLS_AS_SET': True,
        'REDIS_START_URLS_KEY': 'torspider:singleurls',
    }

    def parse(self, *args, **kwargs):
        return super().parse(follow_links=False, *args, **kwargs)
