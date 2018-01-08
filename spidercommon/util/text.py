# coding=utf-8
import re

from spidercommon.regexes import (compress_ws_regex, script_tag_regex,
                                  style_tag_regex)


def strip_html(text: str):
    """
        HTML stripper from the original freshonions project.
        Sometimes it's better not to reinvent this particular wheel until a better solution comes.

    :param text: The HTML to strip script, style, and other tags away.
    :return: Stripped HTML content.
    """

    cleaned = re.sub(script_tag_regex, '', text)
    cleaned = re.sub(style_tag_regex, '', cleaned)
    cleaned = re.sub('<[^<]+?>', '', cleaned)
    cleaned = re.sub(compress_ws_regex, "\n", cleaned)

    return cleaned
