# coding=utf-8
import random as _random

try:
    random = _random.SystemRandom()
except:
    random = _random
