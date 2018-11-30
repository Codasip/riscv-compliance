import os
import pytest
from _rvtest import ISAS, RiscVExtensions

FIND_FILES_PATH = os.path.join('rv32i', 'I', 'ISA')
ARCHITECTURE_ISA = [ISAS.RV32I]

def run_test(file, reference, user, work_dir):
    output_ref = os.path.join(work_dir, os.path.basename(file)+'.ref.xexe')
    output_test = os.path.join(work_dir, os.path.basename(file)+'.test.xexe')
    
    metadata = {'isa': 'rv32i'}
    
    reference.compiler.run(file, output_ref, metadata)
    user.compiler.run(file, output_test, metadata)

    reference = reference.model.run(output_ref, metadata)
    actual = user.model.run(output_test, metadata)
    
    assert reference.signature == actual.signature, "Signature mismatch"

@pytest.mark.find_files(pattern='\.S$', exclude='MISALIGN')
def test_rv32i_i_isa(file, reference, user, work_dir):
    run_test(file, reference, user, work_dir)

@pytest.mark.memory(misaligned=False)
@pytest.mark.find_files(pattern='MISALIGN_LDST')
def test_rv32i_i_isa_misalign_ldst(file, reference, user, work_dir):
    run_test(file, reference, user, work_dir)

@pytest.mark.memory(misaligned=False)
@pytest.mark.architecture(extensions_not=[RiscVExtensions.C])
@pytest.mark.find_files(pattern='MISALIGN_JMP')
def test_rv32i_i_isa_misalign_jmp(file, reference, user, work_dir):
    run_test(file, reference, user, work_dir)
