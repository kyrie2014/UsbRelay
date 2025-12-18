# -*- coding: utf-8 -*-
"""
Setup script for USB Relay Controller
"""
from setuptools import setup, find_packages
import os

# Read the contents of README file
this_directory = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

# Read requirements
with open('requirements.txt') as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]

setup(
    name='usb-relay-controller',
    version='1.0.0',
    author='Kyrie Liu',
    author_email='your.email@example.com',
    description='USB Relay Controller for automated device testing and ADB recovery',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/yourusername/UsbRelay',
    packages=find_packages(),
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Testing',
        'Topic :: System :: Hardware :: Universal Serial Bus (USB)',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Operating System :: Microsoft :: Windows',
    ],
    python_requires='>=2.7, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*, !=3.4.*, !=3.5.*',
    install_requires=requirements,
    entry_points={
        'console_scripts': [
            'relay-server=relay.cli.server:main',
            'relay-init=relay.cli.initialize:main',
            'relay-recover=relay.cli.recover:main',
        ],
    },
    project_urls={
        'Bug Reports': 'https://github.com/yourusername/UsbRelay/issues',
        'Source': 'https://github.com/yourusername/UsbRelay',
        'Documentation': 'https://github.com/yourusername/UsbRelay#readme',
    },
    keywords='usb relay automation testing adb android hardware-control',
    include_package_data=True,
    zip_safe=False,
)

