# Copyright (c) 2018, Codasip Ltd.
# See LICENSE file for license details.

from collections import Iterable

from _rvtest import ISAS, RiscVExtensions, Modes
from _rvtest.options import MarkerGroup

MARKER_OPTIONS = [MarkerGroup('find_files', ('name', 'FIND_FILES_NAME', [str]),
                                            ('path', 'FIND_FILES_PATH', [str]),
                                            ('pattern', 'FIND_FILES_PATTERN', [Iterable, str]),
                                            ('exclude', 'FIND_FILES_EXCLUDE', [Iterable, str]),
                             ),
                  MarkerGroup('architecture', ('isa', 'ARCHITECTURE_ISA', [Iterable, ISAS]),
                                              ('isa_not', 'ARCHITECTURE_ISA_NOT', [Iterable, ISAS]),
                                              ('extensions', 'ARCHITECTURE_EXTENSIONS', [Iterable, RiscVExtensions]),
                                              ('extensions_not', 'ARCHITECTURE_EXTENSIONS_NOT', [Iterable, RiscVExtensions]),
                                              ('modes', 'ARCHITECTURE_MODES', [Iterable, Modes]),
                                              ('modes_not', 'ARCHITECTURE_MODES_NOT', [Iterable, Modes]),
                             ),
                  MarkerGroup('memory', ('minimum_size', 'MEMORY_MINIMUM_SIZE', [int]),
                                        ('misaligned', 'MEMORY_MISALIGNED', [bool]),
                             ),
                  MarkerGroup('exceptions', ('interrupt_support', 'EXCEPTIONS_INTERRUPT_SUPPORT', [bool]),
                              varargs=True
                             ),
                  MarkerGroup('status_registers', varargs=True),
                  ]