#!/usr/bin/env python3
# -*- coding:utf-8 -*-
"""Packaging Setup."""
from setuptools import setup

if __name__ == "__main__":
    setup(
        use_scm_version=True,
        setup_requires=['setuptools_scm'],
    )
