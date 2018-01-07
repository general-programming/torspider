# coding=utf-8
from scrapy.crawler import CrawlerRunner
from scrapy.utils.log import configure_logging
from scrapy.utils.project import get_project_settings
from twisted.internet import defer, reactor

from torspider.spiders.directory_spider import DirectorySpider
from torspider.spiders.link_spider import LinkSpider

configure_logging(install_root_handler=False)
runner = CrawlerRunner(get_project_settings())


@defer.inlineCallbacks
def crawl():
    runner.crawl(DirectorySpider)
    runner.crawl(LinkSpider)
    d = runner.join()
    d.addBoth(lambda _: reactor.stop())
    yield d


if __name__ == "__main__":
    crawl()
    reactor.run()
