# Copyright (c) 2018, Codasip Ltd.
# See LICENSE file for license details.
import os

TEMPLATE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            'templates')
TARGET_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            'templates', 'targets')

PLUGIN_TARGETS = [d for d in os.listdir(TARGET_DIR)]
