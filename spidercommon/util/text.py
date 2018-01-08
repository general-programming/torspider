# coding=utf-8
import json
import re
from datetime import date, datetime

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


class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        """JSON serializer for objects not serializable by default json code"""

        if isinstance(obj, (datetime, date)):
            return obj.isoformat()

        return json.JSONEncoder.default(self, obj)
