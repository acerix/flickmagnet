#!/usr/bin/env python3

# Always prefer setuptools over distutils
from setuptools import setup, find_packages
# To use a consistent encoding
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='flickmagnet',

    # Versions should comply with PEP440.  For a discussion on single-sourcing
    # the version across setup.py and the project code, see
    # https://packaging.python.org/en/latest/single_source_version.html
    version='0.0.3',

    description='HTTP server similar to Netflix and PopcornTime which streams public domain videos from torrent files',
    keywords='netflix streaming movie tv',
    long_description=long_description,
    url='http://flickmag.net/',
    author='acerix',
    author_email='acerix@flickmag.net',
    license='MIT',

    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        'Programming Language :: Python :: 3',
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: End Users/Desktop',
        'Topic :: Communications :: File Sharing',
        'Topic :: Internet :: WWW/HTTP :: Indexing/Search',
        'Topic :: Multimedia :: Video',
        'License :: OSI Approved :: MIT License',
        'Environment :: No Input/Output (Daemon)',
        'Operating System :: POSIX :: Linux',
    ],

    packages=['flickmagnet'],

    package_data={
        'flickmagnet': [
            'examples/*',
            'htdocs/*.*',
            'htdocs/static/*',
            'templates/*'
        ],
    },

    install_requires=[
        'pyxdg',
        'daemonocle',
        'pytoml',
        'cherrypy',
        'mako',
        'requests',
        'beautifulsoup4',
        'python-libtorrent',
    ],

    dependency_links = [
        'http://sourceforge.net/projects/libtorrent/files/latest/download#egg=python-libtorrent',
    ],

)
