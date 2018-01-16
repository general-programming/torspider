# coding=utf-8
import hashlib
from typing import Union

from spidercommon.util.compat import to_bytes


def md5(content: Union[bytes, str]):
    return hashlib.md5(to_bytes(content)).hexdigest()


def sha256(content: Union[bytes, str]):
    return hashlib.sha256(to_bytes(content)).hexdigest()
