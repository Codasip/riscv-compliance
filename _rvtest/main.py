# Copyright (c) 2018, Codasip Ltd.
# See LICENSE file for license details.

import copy
import os
from subprocess import run
import sys

from _rvtest import COMPLIANCE_TESTSDIR, ROOT_PACKAGE
from _rvtest.utils import ArgumentParser, fatal


class RVComplianceTestsuite():
    """Main testuite object.
    
    Build arguments from commandline and execute Pytest process.
    """
    
    DEFAULT_WORKDIR = 'rvtest_work'
    """Path to Testsuite working directory. Relative from current process work."""
    PLUGIN_NAME = 'rvtest_plugin'
    REPORTDIR = 'report'
    
    def __init__(self, work_dir=None):
        self.work_dir = work_dir or os.path.join(os.getcwd(), self.DEFAULT_WORKDIR)
        
        self.args = [sys.executable,
            '-m', 'pytest', '--tb=short', '-s', '-v', '--disable-pytest-warnings',
            COMPLIANCE_TESTSDIR]
        
        self.plugins = ['_rvtest.plugin']
    
    def _parse_args(self, args):
        """Parse testsuite arguments from cmdline.
        
        :param args: List of arguments to parse.
        :type args: list
        :return: Pair of values ``(parsed, argv)``, where ``parsed`` is instance of 
            :py:class:`argparse.Namespace` class and ``argv`` is a list of unparsed arguments,
            which are then added to arguments passed to Pytest.
        """
        parser = ArgumentParser(add_help=False)
        parser.add_argument('--build-toolchain', action='store', default=False, nargs='?')
        parser.add_argument('--work-dir', action="store", default=self.work_dir)
        parser.add_argument('--plugin', action="store")
        parser.add_argument('--generator', action="store_true")
        parser.add_argument('--gui', action="store_true")
        parser.add_argument('-h', '--help', action="store_true")
        
        return parser.parse_args(args)
    
    def _run_plugin_generator(self, gui):
        if gui:
            from _rvtest.ui.gui import main as run_generator
        else:     
            from _rvtest.ui.tui import main as run_generator
        return run_generator()
    
    def _setup(self, args):
        # Preprocess arguments
        parsed, argv = self._parse_args(args)
        
        self.work_dir = parsed.work_dir
        argv += ['--work-dir', self.work_dir]
        # Set reporting
        argv += ['--junitxml', os.path.join(self.work_dir, self.REPORTDIR, 'report.xml')]
        argv += ['--html', os.path.join(self.work_dir, self.REPORTDIR, 'report.html'),
                 '--self-contained-html']
        
        for p in self.plugins:
            argv += ['-p', p]

        args = self.args + argv
        
        env = os.environ.copy()
        # Add this package to PYTHONPATH so it is importable
        env['PYTHONPATH'] = env.get('PYTHONPATH', '') + os.pathsep + ROOT_PACKAGE
        
        # Add user plugin to PYTHONPATH, otherwise pytest is unable to register it
        plugin_path = os.path.abspath(parsed.plugin) if parsed.plugin else ''
        if plugin_path and os.path.isdir(plugin_path):
            env['PYTHONPATH'] = env['PYTHONPATH'] + os.pathsep + plugin_path
            args += ['-p', self.PLUGIN_NAME]

        return parsed, args, env
        
    def run(self, args=None):
        """Execute testsuite.
        
        :param args: List of arguments from commandline.
        """
        if args is None:
            args = copy.copy(sys.argv[1:])
        
        parsed, argv, env = self._setup(args)

        if parsed.help:
            argv +=  ['--help']
        elif parsed.generator:
            return self._run_plugin_generator(parsed.gui)
        elif parsed.build_toolchain is not False:
            from _rvtest.builder import RVToolchainBuilder
            builder = RVToolchainBuilder()
            return builder.build(parsed.build_toolchain)
        
        # Prepare plugin for pytest registration
        plugin_path = os.path.abspath(parsed.plugin) if parsed.plugin else None
        if parsed.help:
            pass
        elif plugin_path is None:
            fatal("Missing mandatory --plugin argument")
            sys.exit(1)
        elif not os.path.isdir(plugin_path):
            fatal(f"Plugin path {plugin_path} is not a directory")
            sys.exit(1)
        elif self.PLUGIN_NAME+'.py' not in os.listdir(plugin_path):
            fatal(f"Plugin path does not contain {self.PLUGIN_NAME}.py file")
            sys.exit(1)
        
        print(f"Pytest arguments: {argv}")
        result = run(argv, env=env)
        return result.returncode

def main(args=None):
    return RVComplianceTestsuite().run(args)
    