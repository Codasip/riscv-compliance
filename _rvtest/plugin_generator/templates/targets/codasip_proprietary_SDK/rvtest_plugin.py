#!/usr/bin/python3
import copy
import os
import pytest
import sys

from _rvtest import Causes, CSRS, Modes, RiscVExtensions, ISAS, PlatformProperties
from _rvtest.environment import Environment
from _rvtest.models import RVModel
from _rvtest.utils import find_files

from compiler import Compiler

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
    
    def get_signature(self, process_result):
        return process_result.stdout.decode('utf-8')

    def run(self, file, metadata):
        """Executes model and returns result's signature.
        
        :param file: Path to executable test file.
        :param metadata: Test metadata for further configuration.
        """
        # Build arguments for model
        args = ['-r', file, '--info', '5']
        
        # Execute model and extract memory signature
        result = super().run(args, timeout=30)
        signature = self.get_signature(result)
        
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
