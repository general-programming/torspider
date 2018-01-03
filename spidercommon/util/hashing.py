import hashlib


def md5(content: str):
    return hashlib.md5(content.encode("utf8")).hexdigest()
