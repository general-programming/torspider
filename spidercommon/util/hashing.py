# coding=utf-8
import hashlib
from typing import Union


def md5(content: Union[bytes, str]):
    # XXX: make tobytes function util
    try:
        content = content.encode("utf8")
    except (UnicodeEncodeError, AttributeError):
        pass

    return hashlib.md5(content).hexdigest()


def sha256(content: Union[bytes, str]):
    # XXX: make tobytes function util
    try:
        content = content.encode("utf8")
    except (UnicodeEncodeError, AttributeError):
        pass

    return hashlib.sha256(content).hexdigest()
