# Copyright (c) 2018, Codasip Ltd.
# See LICENSE file for license details.

import os

from _rvtest.tools import Compiler, Tool
from _rvtest.models import RVModel
from _rvtest.utils import to_list

class RiscVCompiler(Compiler):
    """RISC-V GCC compiler wrapper used for assembly compilation for golden model."""
    class Result():
        def __init__(self, output):
            self.output = output

    def __init__(self, path, **kwargs):
        super(RiscVCompiler, self).__init__(path, 'RISC-V GCC compiler', **kwargs)
        self.args = ['-static',
                     '-mcmodel=medany',
                     '-nostartfiles',
                     '-fvisibility=hidden'
                     ]

    def run(self, sources, output, metadata):
        """Compile sources.
        
        :param sources: List of sources to compile,
        :param output: Path to generated executable file.
        :param metadata: Additional metadata about current test. Metadata should contain
            additional information, e.g. what is this test testing, for instance - if we
            are testing control and status registers, metadata should specify what bits
            must be implemented.
        :type sources: str or list
        :type output: str
        :type metadata: dict
        :return: ``Result`` object.
        """
        sources = to_list(sources)
        
        args = sources
        args += self.args
        configuration_string = self.execution_environment.model.configuration_string
        # it is not possible to turn off compression manually
        # remove "C" extension if it isnt needed for compilation
        if ('c' not in metadata.get('isa')):
            configuration_string = configuration_string.replace("c","")

        args += ['-march=%s' % configuration_string]
        if "64" in metadata.get('isa'):
            args += ['-mabi=lp64']
        else:
            args += ['-mabi=ilp32']
        
        environment = self.execution_environment.environment
        # For now golden model's environment does not have the same structure as plugin environment.
        # Therefore we search header files in environment root path as well.
        if os.path.isdir(environment.include_dir):
            args += ['-I', environment.include_dir]
        else:
            args += ['-I', environment.path]
        
        # Detect linker script and parametrize compiler
        linker_script = environment.get_linker_script()
        if linker_script:
            args += ['-T', linker_script]
        
        args += ['-o', output]
        
        # Execute compilation
        Tool.run(self, args, timeout=10)
        
        return self.Result(output=output)

class Spike(RVModel):
    """Wrapper for Spike, which is currently used as golden model.
    
    Golden model does not contain any configuration (ISA, extensions, ...)
    as it's configuration is automatically derived from tested model. 
    """

    def __init__(self, path, work_dir=None):
        """Constructor
        
        :param path: Path to Spike executable.
        :param work_dir: Path from which Spike should be executed. By default
            process working directory is used.
        :type path: str
        :type work_dir: str
        """
        RVModel.__init__(self, path, 'spike', work_dir)
    
    def get_signature(self, signature_file):
        """Extract signature after Spike execution.
        
        When Spike simulation is complete, a signature file is created, there
        only the content is read and returned.
        
        :param signature_file: Path to signature file.
        :type signature_file: str
        """
        with open(signature_file, 'r') as fr:
            signature = fr.read()
        return signature

    def run(self, executable, metadata):
        """Execute spike and extract signature.
        
        :param executable: Path to executable which is going to be simulated.
        :param metadata: Additional metadata about current test. Metadata should contain
            additional information, e.g. what is this test testing, for instance - if we
            are testing control and status registers, metadata should specify what bits
            must be implemented.
        :type executable: str
        :type metadata: dict
        """
        signature_file = executable + '.sig'
        args = ['--isa=%s' % self.configuration_string, '+signature=%s' % signature_file, executable]
        Tool.run(self, args, timeout=30)
        
        signature = self.get_signature(signature_file)
        return self.Result(signature)
