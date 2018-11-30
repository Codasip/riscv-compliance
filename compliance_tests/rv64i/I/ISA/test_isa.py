import os
import pytest
from _rvtest import ISAS, RiscVExtensions

FIND_FILES_PATH = os.path.join('rv64i', 'I', 'ISA')
ARCHITECTURE_ISA = [ISAS.RV64I]

def run_test(file, reference, user, work_dir):
    output_ref = os.path.join(work_dir, os.path.basename(file)+'.ref.xexe')
    output_test = os.path.join(work_dir, os.path.basename(file)+'.test.xexe')
    
    metadata = {'isa': 'rv64i'}
    
    reference.compiler.run(file, output_ref, metadata)
    user.compiler.run(file, output_test, metadata)

    reference = reference.model.run(output_ref, metadata)
    actual = user.model.run(output_test, metadata)
    
    assert reference.signature == actual.signature, "Signature mismatch"

@pytest.mark.find_files(pattern='\.S$')
def test_rv64i_i_isa(file, reference, user, work_dir):
    run_test(file, reference, user, work_dir)
