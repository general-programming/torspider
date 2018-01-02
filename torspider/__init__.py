import os
import coloredlogs

if 'COLORLOG' in os.environ:
    coloredlogs.install(level='DEBUG')
