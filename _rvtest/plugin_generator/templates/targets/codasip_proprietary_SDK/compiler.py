import os

from _rvtest.tools import Tool
from _rvtest.utils import to_list

class Compiler(Tool):
    class Result():
        def __init__(self, output, exit_code):
            self.exit_code = exit_code
            self.output = output

    def __init__(self, path, **kwargs):
        super(Compiler, self).__init__(path, 'User compiler', **kwargs)
        self.args = ['-nostdlib']
    
    def run(self, sources, output, metadata):
        sources = to_list(sources)
        
        args = sources
        args += self.args
        
        environment = self.execution_environment.environment
        
        if os.path.isdir(environment.include_dir):
            args += ['-I', environment.include_dir]
        else:
            args += ['-I', environment.path]
        
        linker_script = environment.get_linker_script()
        if linker_script:
            args += ['-T', linker_script]
        
        args += ['-o', output]
        
        result = Tool.run(self, args, timeout=10)
        
        return self.Result(result.returncode, output)
