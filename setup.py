#!/usr/bin/env python
import os
import sys
from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))

if sys.version_info < (3, 6):
    sys.exit(
        'Python < 3.6 is not supported. You are using Python {}.{}.'.format(
            sys.version_info[0], sys.version_info[1])
    )

version = {}
with open(os.path.join(here, '__version__.py')) as f:
    exec(f.read(), version)

with open('README.md') as readme_file:
    readme = readme_file.read()
    
setup(
    name="nfs4-share",
    packages=['nfs4_share'],
    package_dir={'': 'src/'},
    description="Share data without data duplication using nfs4_acls and hard links",
    version=version['__version__'],
    entry_points={
        'console_scripts': [
            'nfs4_share = nfs4_share.cli:entry_point',
        ]
    },
    author="Chris van Run",
    author_email='genomicscore@prinsesmaximacentrum.nl',
    url='https://github.com/princessmaximacenter/network-filesystem-shares',
    long_description=readme + '\n\n',
    long_description_content_type="text/markdown",
    zip_safe=False,
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: System Administrators',
        'Topic :: Communications :: File Sharing',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3.6',
    ],
    python_requires='>=3.6.0',
    include_package_data=True,
    license="MIT",
    extras_require={'test': ['pytest', 'pycodestyle']},
)
