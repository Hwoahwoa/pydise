#!/usr/bin/env python3
# -*- coding:utf-8 -*-
"""Packaging Setup."""
from setuptools import setup
import os
import datetime

if __name__ == "__main__":
    try:
        setup(
            use_scm_version=True,
            setup_requires=["setuptools_scm"],
        )
    except Exception:
        now = datetime.datetime.now()
        date_as_version = str(now.strftime("%Y.%m.%d.%H.%M.%S"))

        version = os.environ.get("CI_COMMIT_TAG")
        version = version if version else date_as_version
        setup(version=version)
