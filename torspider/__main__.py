from scrapy.crawler import CrawlerRunner
from twisted.internet import reactor
from torspider.spiders.directory_spider import DirectorySpider
from torspider.spiders.link_spider import LinkSpider

if __name__ == "__main__":
    runner = CrawlerRunner()
    runner.crawl(DirectorySpider)
    runner.crawl(LinkSpider)
    d = runner.join()
    d.addBoth(lambda _: reactor.stop())

    reactor.run()
