# coding=utf-8
import os

import coloredlogs

if 'COLORLOG' in os.environ:
    coloredlogs.install(level='DEBUG')
else:
    coloredlogs.install(level='INFO')
