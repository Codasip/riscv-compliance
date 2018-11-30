# Copyright (c) 2018, Codasip Ltd.
# See LICENSE file for license details.

import os
import shutil
from subprocess import run, PIPE

from _rvtest.utils import to_list

class Tool():
    """General wrapper for executable tool."""
    def __init__(self, executable, name=None, work_dir=None):
        """Constructor.
        
        :param executable: Path to executable.
        :param name: User-friendly tool name.
        :param work_dir: Default working directory of tool.
        :type executable: str
        :type name: str
        :type work_dir: str
        """
        assert os.path.isfile(executable) or shutil.which(executable), f"Executable {executable} not found"
        if os.path.isfile(executable):
            executable = os.path.abspath(executable)
        self.executable = executable
        self.name = name or os.path.splitext(os.path.basename(executable))[0]
        self.work_dir = work_dir

    def run(self, args, ignore_exit_code=False, **kwargs):
        """Execute tool with specific arguments.
        
        :param args: List of arguments for tool.
        :param ignore_exit_code: If ``True``, then, then exception is NOT raised on process error.
            If ``False``, then raises :py:class:`subprocess.CalledProcessError` if process fails.
        :return: CompletedProcess instance.
        :rtype: :py:class:`subprocess.CompletedProcess`
        """
        kwargs.setdefault('cwd', self.work_dir)
        kwargs.setdefault('stdout', PIPE)
        kwargs.setdefault('stderr', PIPE)
        
        result = run([self.executable]+args, **kwargs)
        
        if not ignore_exit_code:
            result.check_returncode()
        
        return result


class Compiler(Tool):
    """Simple wrapper for compiler."""
    class Result():
        def __init__(self, output, exit_code):
            self.exit_code = exit_code
            self.output = output

    def __init__(self, path, name='Compiler', **kwargs):
        super(Compiler, self).__init__(path, name, **kwargs)
        self.args = []
    
    def run(self, sources, output, metadata):
        """Execute compiler.
        
        :param sources: List of source file to compile.
        :param output: Path to output executable.
        :param metadata: Additional metadata (not implemented yet).
        """
        sources = to_list(sources)
        
        args = sources
        args += self.args
        
        for include in self.execution_environment.environment.get_headers() or []:
            args += ['-I', include]
        
        linker_script = self.environment.linker_script
        if linker_script:
            args += ['-T', linker_script]
        
        args += ['-o', output]
        
        result = Tool.run(self, args)
        
        return self.Result(result.returncode, output)
