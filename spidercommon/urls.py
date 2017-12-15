from urllib.parse import urlparse


class ParsedURL(object):
    """
    Wrapper for urlparse that removes the copy/paste work of hostname, port, ssl, and path.
    """
    __slots__ = ["url", "host", "port", "path", "secure", "path", "urlparse"]
    def __init__(self, url: str):
        self.url = url
        self.urlparse = urlparse(url)

        self.host = str(self.urlparse.hostname)
        self.secure = self.urlparse.scheme == "https://"

        # try/except because of URLs like http://127.0.0.1:4986&#8243
        try:
            self.port = int(self.urlparse.port)
        except (ValueError, TypeError):
            self.port = None

        # Fill in the port if no ports are given.
        if not self.port:
            if self.secure:
                self.port = 443
            else:
                self.port = 80

        self.path = '/' if self.urlparse.path == '' else self.urlparse.path
