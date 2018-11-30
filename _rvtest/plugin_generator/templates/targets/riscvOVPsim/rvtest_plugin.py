#!/usr/bin/python3
import copy
import os
import pytest
import sys

from _rvtest import Causes, CSRS, Modes, RiscVExtensions, ISAS, PlatformProperties
from _rvtest.environment import Environment
from _rvtest.models import RVModel
from _rvtest.tools import Tool
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
        RVModel.__init__(self, path=path, name='OVPsim')
    
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
        sig_file = os.path.join(self.work_dir, 'test_signature.sig')
        # Build arguments for model
        args = ['--variant', self.configuration_string.upper()[:5],
                '--program', file,
                '--signaturedump', '--customcontrol', 
                '--override', 'riscvOVPsim/cpu/sigdump/SignatureFile='+sig_file,
                '--override', 'riscvOVPsim/cpu/sigdump/ResultReg=3',
                '--override', 'riscvOVPsim/cpu/simulateexceptions=T',
                '--override', 'riscvOVPsim/cpu/defaultsemihost=F',
                '--logfile',  os.path.join(self.work_dir, 'runtime_log.txt'),
                '--override', 'riscvOVPsim/cpu/user_version=2.3',
                '--override', 'riscvOVPsim/cpu/priv_version=1.11',
                '--override', 'riscvOVPsim/cpu/misa_Extensions=%s'%self.get_misa()]
        
        # Execute model and extract memory signature
        result = super().run(args, timeout=30)
        signature = self.get_signature(result, sig_file)
        
        return self.Result(signature=signature)

@pytest.fixture
def user_compiler(request, toolchain_path, work_dir):
    compiler_path = list(find_files(toolchain_path, pattern='gcc$'))
    assert compiler_path, "Compiler not found in %s"%(toolchain_path)
    compiler = Compiler(compiler_path[0], work_dir=work_dir)
    return compiler

@pytest.fixture
def user_model(configured_user_model):
    return copy.deepcopy(configured_user_model)

@pytest.fixture
def user_environment(request, environment_path, work_dir):
    environment = Environment(environment_path)
    return environment
