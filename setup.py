# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

install_requires = [
    'numpy',
    'pandas',
    'quantities',
    'neo>=0.7.1',
    # 'elephant>=0.6.2',  # TODO uncomment when dev dependencies don't clash
    'ephyviewer',
    'ipywidgets',
    'pylttb',
    'pyyaml',
    'tqdm',
]

entry_points = {
    'console_scripts': [
        'neurotic=neurotic.scripts:launch_standalone'
    ]
}

long_description = open('README.rst').read()  # TODO update for package

setup(
    name='neurotic',
    # version='',  # TODO
    # description='',  # TODO
    packages=find_packages(),
    install_requires=install_requires,
    entry_points=entry_points,
    long_description=long_description,
    author='Jeffrey Gill',
    author_email='jeffrey.p.gill@gmail.com',
    license='MIT',
    url='https://github.com/jpgill86/analysis',
    classifiers = [
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
    ],
)
