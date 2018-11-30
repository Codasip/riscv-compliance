import os
import pytest

from _rvtest import RiscVExtensions
from _rvtest import Modes
from _rvtest import ISAS

@pytest.mark.find_files(path=os.path.join('rv32i', 'F', 'U'), pattern='\.S$')
@pytest.mark.architecture(isa=[ISAS.RV32I], extensions=[RiscVExtensions.F], modes=[Modes.USER])
def test_rv32i_f_u(file, reference, user, work_dir):
    output_ref = os.path.join(work_dir, os.path.basename(file)+'.ref.xexe')
    output_test = os.path.join(work_dir, os.path.basename(file)+'.test.xexe')
    
    metadata = {'isa': 'rv32if'}
    
    reference.compiler.run(file, output_ref, metadata)
    user.compiler.run(file, output_test, metadata)

    reference = reference.model.run(output_ref, metadata)
    actual = user.model.run(output_test, metadata)
    
    assert reference.signature == actual.signature, "Signature mismatch"
