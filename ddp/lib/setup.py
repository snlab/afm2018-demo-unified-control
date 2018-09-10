#!/usr/bin/env python3

from setuptools import setup, find_packages
from os import path, listdir


def read(fname):
    return open(path.join(path.dirname(__file__), fname)).read()


def files(dirname):
    return [path.join(dirname, filename) for filename in listdir(dirname)]


setup(
    name="DDP with Update Algebra",
    version="0.2",
    description="DDP with Update Algebra",
    url="https://snlab.org",
    author="SNLab",
    author_email="user@snlab.org",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        "Development Status :: 2 - Pre-Alpha",
        "Intented Audience :: Developers",
        "Topic :: System :: Tools",
    ],
    license="MIT",
    long_description=read("README.rst"),
    packages=find_packages(),
    package_data={},
    install_requires=read('requirements.txt').splitlines(),
    # scripts=files('bin'),
    zip_safe=False
)
