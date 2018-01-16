# coding=utf-8
import hashlib


def md5(content: str):
    return hashlib.md5(content.encode("utf8")).hexdigest()


def sha256(content: str):
    return hashlib.sha256(content.encode("utf8")).hexdigest()
