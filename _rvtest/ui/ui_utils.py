# Copyright (c) 2018, Codasip Ltd.
# See LICENSE file for license details.

import os

from _rvtest import ISAS, RiscVExtensions
from _rvtest.models import RVModel
from _rvtest.plugin_generator.generator import PluginGenerator
from _rvtest.utils import error, to_list

class Interface():
    """Interface between user interface(s) and plugin generator 
    """
    def __init__(self):
        self.generator = PluginGenerator()
    
    def add_property(self, p_type, value):
        try:
            self.generator.add_property(p_type, value)
        except Exception as e:
            error("generator: Invalid value")
            raise
        
        return 0
    
    def remove_property(self, p_type, value):
        try:
            self.generator.remove_property(p_type, value)
        except Exception as e:
            error("generator: Invalid value")
            raise
            #return -1
        
        return 0