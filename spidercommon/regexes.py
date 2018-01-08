# coding=utf-8
import re

onion_regex = re.compile(r"([a-zA-Z0-9.]+\.onion)", re.IGNORECASE)
script_tag_regex = re.compile(r"<script.*?</script>", re.IGNORECASE | re.DOTALL)
style_tag_regex = re.compile(r"<style.*?</style>", re.IGNORECASE | re.DOTALL)
compress_ws_regex = re.compile(r"[\r\t ]*\n[\r\t\n ]*", re.IGNORECASE | re.DOTALL)
