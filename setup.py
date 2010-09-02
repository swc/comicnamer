"""Setup tools for comicnamer
Modified from http://github.com/dbr/tvnamer
"""

from setuptools import setup
setup(
name = 'comicnamer',
url='http://github.com/swc/comicnamer',
version='1.0',

author='swc/Steve',
author_email='iam@attractive.com',
description='Automatic TV episode file renamer, uses data from thetvdb.com via tvdb_api',
license='GPLv2',

long_description="""\
Automatically names downloaded comic issues, by parsing filenames and
retrieving issue names from www.comicvine.com
""",

packages = ['comicnamer'],

entry_points = {
    'console_scripts': [
        'comicnamer = comicnamer.main:main',
    ],
},

install_requires = ['comicvine_api>=1.04', 'simplejson'],

classifiers=[
    "Environment :: Console",
    "Intended Audience :: End Users/Desktop",
    "License :: OSI Approved :: GNU General Public License (GPL)",
    "Natural Language :: English",
    "Operating System :: OS Independent",
    "Programming Language :: Python",
    "Topic :: Multimedia",
    "Topic :: Utilities",
],
)
