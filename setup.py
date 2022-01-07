# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

with open("requirements.txt") as f:
	install_requires = f.read().strip().split("\n")

# get version from __version__ variable in gspl/__init__.py
from gspl import __version__ as version

setup(
	name="gspl",
	version=version,
	description="GSPL",
	author="GSPL",
	author_email="info@gspl.com",
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
