#!/usr/bin/env python3

from setuptools import setup, find_packages
from os import path, listdir


def read(fname):
    return open(path.join(path.dirname(__file__), fname)).read()


def files(dirname):
    return [path.join(dirname, filename) for filename in listdir(dirname)]


setup(
    name="nccontainer",
    version="0.1",
    description="Network Consistency Container",
    url="https://github.com/fno2010/nccontainer",
    author="Jensen Zhang",
    author_email="hack@jensen-zhang.site",
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
    scripts=files('bin'),
    zip_safe=False
)
