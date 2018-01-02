import os

from scrapy.core.downloader.handlers.http11 import (HTTP11DownloadHandler,
                                                    ScrapyAgent)
from scrapy.core.downloader.webclient import _parse
from scrapy.xlib.tx import TCP4ClientEndpoint
from twisted.internet import reactor
from txtorcon import web as txtorcon_web


class TorDownloadHandler(HTTP11DownloadHandler):
    def download_request(self, request, spider):
        """Return a deferred for the HTTP download"""
        agent = ScrapySocks5Agent(contextFactory=self._contextFactory, pool=self._pool)
        return agent.download_request(request)

class ScrapySocks5Agent(ScrapyAgent):
    def _get_agent(self, request, timeout):
        bindAddress = request.meta.get('bindaddress') or self._bindAddress
        proxy = os.environ.get("SOCKS_PROXY", request.meta.get('proxy'))
        _proxy_protocol, _proxy_hostport, proxyHost, proxyPort, _proxy_params = _parse(proxy)

        proxy_endpoint = TCP4ClientEndpoint(
            reactor,
            proxyHost,
            proxyPort,
            timeout=timeout, 
            bindAddress=bindAddress
        )
        agent = txtorcon_web.tor_agent(reactor, socks_endpoint=proxy_endpoint)

        return agent
