# coding=utf-8
from setuptools import find_packages, setup

setup(
    name="torspider",
    packages=find_packages(),
    zip_safe=False,
    setup_requires=["pytest-runner"],
    tests_require=["pytest"],
)
