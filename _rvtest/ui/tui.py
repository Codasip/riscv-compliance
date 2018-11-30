# Copyright (c) 2018, Codasip Ltd.
# See LICENSE file for license details.

import glob
import os
import re
import sys
from collections import OrderedDict
import readline

from _rvtest import PlatformProperties
from _rvtest.exceptions import ConfigError
from _rvtest.utils import error, fatal
from _rvtest.ui.ui_utils import Interface


# Autocomplete path when setting plugin destination
def complete(text, state):
    return (glob.glob(text + '*') + [None])[state]


readline.set_completer_delims(' \t\n;')
readline.parse_and_bind("tab: complete")
readline.set_completer(complete)


class TUI():
    OPTIONS = OrderedDict([(PlatformProperties.ISA, {'prompt': "Set ISA architecure",
                                    'required': True,
                                    'split': False,
                                    'type': 'list'}),
                           (PlatformProperties.EXTENSION, {'prompt': "Select supported standard extensions",
                                           'split': True,
                                           'type': 'list'}),
                           (PlatformProperties.MODE, {'prompt': "Select supported modes",
                                           'split': True,
                                           'required': True,
                                           'type': 'list'}),
                           (PlatformProperties.MEMORY_RANGE, {'prompt': "Set memory (size, program_start, data_start)",
                                           'type': 'list', 'required': True, 'split': True}),
                           (PlatformProperties.MEMORY_MISALIGNED, {'prompt': "Misaligned memory access support",
                                           'type': 'bool'}),
                           (PlatformProperties.INTERRUPT_SUPPORT, {'prompt': "Interrupt support",
                                           'type': 'bool'}),
                           (PlatformProperties.CAUSE, {'prompt': "Select supported causes",
                                           'split': True,
                                           'type': 'list'}),
                           (PlatformProperties.CSR, {'prompt': "Select supported csrs",
                                           'split': True,
                                           'type': 'list'}),
                           ('target', {'prompt': 'Select predefined target',
                                       'type': 'path',
                                       }),
                           ('destination', {'prompt': "Select destination path",
                                            'type': 'path',
                                            'required': True}),
                           ])

    def __init__(self):
        self.interface = Interface()
                
        self.caption = "Welcome to the plugin generator for RISC-V compliance framework."

    def input_string(self, prompt, required, split):
        """
        Read path from user input
        """
        prompt = "{} ({}): ".format(prompt, 'required' if required else 'optional')
        inp = input(prompt)
        if required:
            if not len(inp):
                print("This field is required.")
                return False, None 
        if split:
            inp = re.split(',', inp)
            inp = list(map(lambda x:x.strip(), inp))
            if len(inp) == 1 and not inp[0]:
                inp = '' 
        return True, inp

    def input_confirm(self, text):
        """
        Read answer yes/no from user
        """
        prompt = "{} [y/N]: ".format(text)
        inp = input(prompt)
        success = inp.lower() in ['y', 'yes', 'n', 'no']
        
        return success, (inp.lower() in ['y', 'yes'])

    def read_values_and_generate(self):
        """
        Read values from user and generate plugin
        """
        destination = '.' 
        target = None
        for key, opt in self.OPTIONS.items():
            prompt = opt.get('prompt')
            required = opt.get('required')
            split = opt.get('split')
            
            success = False
            while not success:  
                type = opt.get('type')
                if type == 'list':
                    success, value = self.input_string(prompt, required, split)
                elif type == 'bool':
                    success, value = self.input_confirm(opt.get('prompt'))
                elif type == 'path':    
                    success, value = self.input_string(prompt, required, split)
                else:
                    fatal("Unknown type '{type}' for key '{key}'")
                    break    
                if not success:
                    continue
                if not value:
                    break
                if key == 'destination':
                    destination = value
                elif key == 'target':
                    target = value
                else:
                    success = self._check_state(self.interface.add_property, key, value)
        
        destination = os.path.abspath(destination)    
        self.interface.generator.generate(destination, target)
        
    def run(self):
        print(self.caption)
        self.read_values_and_generate()

    def _check_state(self, method, *args, **kwargs):
        
        try:
            method(*args, **kwargs)
        except ConfigError as e:
            error("Configuration Error: " + str(e))
            return False
        except (AssertionError, TypeError, ValueError) as e:
            error("Unexpected error: " + str(e))
            return False    
        return True        


def main():
    tui = TUI()
    tui.run()

        
