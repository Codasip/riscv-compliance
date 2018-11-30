#!/usr/bin/python3
import copy
import os
import pytest
import sys
import shutil
from subprocess import run, PIPE

from _rvtest import Causes, CSRS, Modes, RiscVExtensions, ISAS, PlatformProperties
from _rvtest.environment import Environment
from _rvtest.models import RVModel
from _rvtest.utils import find_files

try:
    from compiler import Compiler
except (ModuleNotFoundError, ImportError):
    from _rvtest.golden_model import RiscVCompiler as Compiler

def pytest_rvtest_model_init(config, model_path):
    model = RISCVComplianceModel(model_path)
    
    # Specify ISA
{ISA}
    # Specify supported modes
{MODE}     
    # Specify RISCV extensions
{EXTENSION}
    # Set memory range. Tuple of (memory_size, program_start, data_start)
{MEMORY_RANGE}
    # Does misaligned memory access support 
{MEMORY_MISALIGNED}
    # Set interrupt support 
{INTERRUPT_SUPPORT}
    # Set supported exception causes
{CAUSE}
    # Set implemented control and status registers
{CSR}
    return model

class RISCVComplianceModel(RVModel):
    def __init__(self, path):
        """Constructor"""
        RVModel.__init__(self, path=path, name={name})
    
    def get_signature(self, process_result, sig_file):
        signature = -1
        with open(sig_file, 'r') as fr:
            signature = fr.read()
        return signature

    def run(self, file, metadata):
        """Executes model and returns result's signature.
        
        :param file: Path to executable test file.
        :param metadata: Test metadata for further configuration.
        """

        process_result = run(["objdump", file, '-x'], stdout=PIPE)
        stdout = process_result.stdout.decode('utf-8')
        sign_start, sign_end = None, None

        # get signature start and end address
        for line in stdout.split(os.linesep):
            #print(line)
            if 'begin_signature' in line:
                sign_start = int(line.split(' ')[0], 16)
            elif 'end_signature' in line:
                sign_end = int(line.split(' ')[0], 16)

        # generate hex program
        with open (os.path.join(os.path.dirname(self.executable), 'program.hex'), 'w') as hex_file:
            run(["elf2hex", "1", "16384", file, '0x80'], stdout=hex_file)
        
        # Build arguments for model
        args = ['-i', os.path.join(os.path.dirname(self.executable), 'program.hex'), '-s', str(sign_start), '-e', str(sign_end)]

        # Execute model
        result = super().run(args)

        # get signature file
        sig_file = os.path.join(self.work_dir, 'test_signature.sig')

        # Extract memory signature
        signature = self.get_signature(result, sig_file)
        
        return self.Result(signature=signature)

@pytest.fixture
def user_compiler(toolchain_path, work_dir):
    compiler_path = list(find_files(toolchain_path, pattern='gcc$'))
    assert compiler_path, "Compiler not found in %s"%(toolchain_path)
    compiler = Compiler(compiler_path[0], work_dir=work_dir)
    return compiler

@pytest.fixture
def user_model(configured_user_model):
    return copy.deepcopy(configured_user_model)

@pytest.fixture
def user_environment(environment_path, work_dir):
    environment = Environment(environment_path)
    return environment
