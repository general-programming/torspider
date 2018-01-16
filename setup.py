# coding=utf-8
from setuptools import find_packages, setup

setup(
    name="torspider",
    packages=find_packages(exclude=["*.tests", "*.tests.*", "tests.*", "tests"]),
    zip_safe=True,
    setup_requires=["pytest-runner"],
    tests_require=["pytest"],
)
