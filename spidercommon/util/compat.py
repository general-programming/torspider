# coding=utf-8
import random as _random
from typing import Union

try:
    random = _random.SystemRandom()
except:
    random = _random


def to_bytes(content: Union[bytes, str]):
    try:
        content = content.encode("utf8")
    except (UnicodeEncodeError, AttributeError):
        pass

    return content
