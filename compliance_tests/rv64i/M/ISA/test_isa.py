import os
import pytest

from _rvtest import RiscVExtensions
from _rvtest import ISAS

@pytest.mark.find_files(path=os.path.join('rv64i', 'M', 'ISA'), pattern='\.S$')
@pytest.mark.architecture(isa=[ISAS.RV64I], extensions=[RiscVExtensions.M])
def test_rv64i_m_isa(file, reference, user, work_dir):
    output_ref = os.path.join(work_dir, os.path.basename(file)+'.ref.xexe')
    output_test = os.path.join(work_dir, os.path.basename(file)+'.test.xexe')
    
    metadata = {'isa': 'rv64im'}
    
    reference.compiler.run(file, output_ref, metadata)
    user.compiler.run(file, output_test, metadata)

    reference = reference.model.run(output_ref, metadata)
    actual = user.model.run(output_test, metadata)
    
    assert reference.signature == actual.signature, "Signature mismatch"
