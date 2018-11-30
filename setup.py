#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

from setuptools import setup, find_packages


setup(name='rvtest',
      version='0.1',
      description='RISC-V Compliance Framework', 
      url='https://bitbucket.org/mountdoom/rvtest',
      author='Milan Skala',
      author_email='mountdoom@centrum.cz',
      install_requires=[
          'pytest',
          'pytest-html'
      ],
      license='MIT',
      packages=find_packages(),
zip_safe=False)