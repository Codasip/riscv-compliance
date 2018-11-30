# Copyright (c) 2018, Codasip Ltd.
# See LICENSE file for license details.

import os
from os import path

from _rvtest.utils import ConvertibleEnum, ConvertibleIntEnum

ROOT_PACKAGE =  os.path.dirname(os.path.dirname(os.path.realpath(__file__)))

COMPLIANCE_TESTSDIR = path.join(path.dirname(path.dirname(path.realpath(__file__))), 'compliance_tests')
"""Path to assembly and pytest files"""
GOLDEN_MODEL = path.join(path.dirname(path.dirname(path.realpath(__file__))), 'golden_model', 'p')
"""Paht to golden model environment. Path must contain header files for compilation and/or linker script"""
CONFIGURATION_STRING_FORMAT = '{isa}{M}{A}{F}{D}{Q}{C}{L}{B}{J}{T}{P}{V}{N}'
MANDATORY_HEADER_FILES = {'encoding.h', 'riscv_test.h', 'compliance_io.h', 'compliance_test.h', 'test_macros.h', 'aw_test_macros.h'}
"""Set of files which are neccessary for test compilation (assemblies include them)"""
MANDATORY_PYTHON_FILES = {'compiler.py', 'rvtest_plugin.py'}
"""Set of files which must be present in valid rvtest plugin"""

class PlatformProperties(ConvertibleEnum):
    ISA = 'isa'
    EXTENSION = 'extension'
    MODE = 'mode'
    MEMORY_RANGE = 'memory_range'
    MEMORY_MISALIGNED = 'memory_misaligned'
    INTERRUPT_SUPPORT = 'interrupt_support'
    CAUSE = 'cause'
    CSR = 'control_state_register'

class ISAS(ConvertibleEnum):
    RV32E = 'rv32e'
    RV32I = 'rv32i'
    RV64E = 'rv64e'
    RV64I = 'rv64i'
    RV128E = 'rv128e'
    RV128I = 'rv128i'

class RiscVExtensions(ConvertibleEnum):
    M = 'M'
    A = 'A'
    F = 'F'
    D = 'D'
    Q = 'Q'
    L = 'L'
    C = 'C'
    B = 'B'
    J = 'J'
    T = 'T'
    P = 'P'
    V = 'V'
    N = 'N'

class MemoryProperties(ConvertibleIntEnum):
    SIZE = 0
    PROGRAM_START = 1
    DATA_START = 2
    
class Modes(ConvertibleEnum):
    USER = 'U'
    SUPERVISOR = 'S'
    H = 'H'
    MACHINE = 'M'

class Causes(ConvertibleEnum):
    MISALIGNED_FETCH = "misaligned fetch"
    FETCH_ACCESS = "fetch access"
    ILLEGAL_INSTRUCTION = "illegal instruction"
    BREAKPOINT = "breakpoint"
    MISALIGNED_LOAD = "misaligned load"
    LOAD_ACCESS = "load access"
    STORE_ACCESS = "store access"
    USER_ECALL = "user_ecall"
    SUPERVISOR_ECALL = "supervisor_ecall"
    HYPERVISOR_ECALL = "hypervisor_ecall"
    MACHINE_ECALL = "machine_ecall"
    FETCH_PAGE_FAULT = "fetch page fault"
    LOAD_PAGE_FAULT = "load page fault"
    STORE_PAGE_FAULT = "store page fault"

class CSRS(ConvertibleEnum):
    FFLAGS = 'fflags'
    FRM = 'frm'
    FCSR = 'fcsr'
    CYCLE = 'cycle'
    TIME = 'time'
    SSTATUS = 'instret'
    INSTRET = 'sstatus'
    SIE = 'sie'
    STVEC = 'stvec'
    SCOUNTEREN = 'scounteren'
    SSCRATCH = 'sscratch'
    SEPC = 'sepc'
    SCAUSE = 'scause'
    STVAL = 'stval'
    SIP = 'sip'
    SATP = 'satp'
    MSTATUS = 'mstatus'
    MISA = 'misa'
    MEDELEG = 'medeleg'
    MIDELEG = 'mideleg'
    MIE = 'mie'
    MTVEC = 'mtvec'
    MCOUNTEREN = 'mcounteren'
    MSCRATCH = 'mscratch'
    MEPC = 'mepc'
    MCAUSE = 'mcause'
    MTVAL = 'mtval'
    MIP = 'mip'
    MCYCLE = 'mcycle'
    MINSTRET = 'minstret'
