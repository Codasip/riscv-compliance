# Copyright (c) 2018, Codasip Ltd.
# See LICENSE file for license details.

import copy
import os
import pytest

from _rvtest import ISAS, PlatformProperties, COMPLIANCE_TESTSDIR, GOLDEN_MODEL
from _rvtest.reporter import Reporter
from _rvtest.utils import find_files, rmtree, to_list
from _rvtest.environment import Environment
from _rvtest.options import OptionFinder
from _rvtest.utils import find_riscv_tool, rmtree
from _rvtest.markers import MARKER_OPTIONS
from _rvtest.golden_model import RiscVCompiler, Spike


def requires_attributes(*attributes):
    def wrapper(func):

        def wrapper2(self, *args, **kwargs):
            missing = []
            for attr in attributes:
                if not hasattr(self, attr):
                    missing.append(attr)
            raise ValueError(f"{func.__name__} requires: {missing}")
            return func(self, *args, **kwargs)

        return wrapper2

    return wrapper


class ExecutionEnvironment():
    """Execution environment gather all tools neccessary for test execution in a single object.
    In the current state it holds: RISC-V model instance, Compiler instance and Environment
    instance, which contains header files and/or linker script(s).
    
    """

    def __init__(self):
        self._features = {}
        
    def add_feature(self, name, item):
        # Create reference to self
        item.execution_environment = self
        self._features[name] = item
    
    def add_compiler(self, compiler):
        self.add_feature('compiler', compiler)
        
    def add_environment(self, environment):
        self.add_feature('environment', environment)
        
    def add_model(self, model):
        self.add_feature('model', model)
    
    @requires_attributes('compiler')
    def compile(self):
        pass

    @requires_attributes('model')
    def execute(self):
        pass
    
    def __getattr__(self, name):
        return self._features.get(name)

def filter_test(item, required, property_type, must_match, skip_message):
    """Add ``pytest.mark.skip`` mark automatically if test does not meet
    the requirements specified by markers.
    
    :param item: Pytest ``Item`` instance (holds metadata for test).
    :param required: List of values, which are required for test execution.
    :param must_match: If ``True`` then required values must match property values from tested model,
        otherwise required must NOT match tested model properties.
    :param skip_message: Message which will be written in report as skipped reason.
    :type required: list
    :type property_type: str
    :type must_match: bool
    :type skip_message: str
    """
    if required is None:
        return
    
    required = to_list(required)
    supported_values = to_list(item.config._user_model.get_property(property_type))
    
    if supported_values is None:
        return
    
    if property_type == PlatformProperties.MEMORY_RANGE:
        if supported_values[0] < required[0]:
            item.add_marker(pytest.mark.skip(reason=skip_message.format(required[0])))
        return
    missing = []
    for req in required:
        if must_match and req not in supported_values:
            missing.append(req)
        elif not must_match and req in supported_values:
            missing.append(req)
    
    if missing:
        item.add_marker(pytest.mark.skip(reason=skip_message.format(', '.join(map(str, missing)))))


def pytest_addoption(parser):
    group = parser.getgroup('RV Compliance')
    group.addoption('--model', action='store', help='Path to RISC-V model executable or script which implementst the model interface')
    group.addoption('--environment', action='store', default=GOLDEN_MODEL, help='Path to reference environment containing header files for compilation')
    group.addoption('--work-dir', action='store', default=os.path.join(os.getcwd(), 'rv_compliance_work'), help="Working directory of testsuite")
    group.addoption('--cores', action='store', type=int, help='Specify number of cores of DUT (not implemented yet)')
    group.addoption('--toolchain', action='store', help='Path to custom toolchain if needed. By default RISC-V toolchain is used')
    # Following arguments are here, so they would be displayed in help, but
    # they are preprocessed by RVComplianceTestsuite (before pytest execution)
    group.addoption('--build-toolchain', action='store_true', help='Build RISC-V toolchain and golden model (Spike)')
    group.addoption('--plugin', action='store', help='Path to root directory of plugin (containing rvtest_plugin.py)')
    group.addoption('--generator', action="store_true", help="Start RISC-V Compliance Framework Generator for automated plugin generation")
    group.addoption('--gui', action="store_true", help="Start plugin generator in Graphical mode (by default starts in text mode)")

    
def pytest_addhooks(pluginmanager):
    from _rvtest import newhooks
    # avoid warnings with pytest-2.8
    method = getattr(pluginmanager, "add_hookspecs", None)
    if method is None:
        method = pluginmanager.addhooks
    method(newhooks)

    
def pytest_configure(config):

    if config.getoption('help'):
        return

    assert os.getenv('RISCV'), 'Environmental variable RISCV not set, exiting'
    assert config.getoption('model'), "Missing mandatory option --model"
    
    config._work_dir = config.getoption('work_dir')
    config._cores = config.getoption('cores')
    config._model_path = config.getoption('model')
    config._reference_env = Environment(config.getoption('environment'))
    config._toolchain_path = config.getoption('toolchain') or os.path.join(os.getenv('RISCV'), 'bin')
    config._marker_finder = OptionFinder(MARKER_OPTIONS)
    
    rep = Reporter(config)
    config.pluginmanager.register(rep, 'rvtest_reporter')
    # Call hook in user's plugin to initialize tested RISC-V model
    user_model = config.hook.pytest_rvtest_model_init(config=config, model_path=config._model_path)
    if user_model is None:
        raise RuntimeError("Plugin does not contain pytest_rvtest_model_init hook or it does not return anything")
    
    config._testdir = COMPLIANCE_TESTSDIR
    config._user_model = user_model
    config._user_plugin = config.pluginmanager.getplugin('rvtest_plugin')
    config._user_environment = os.path.join(os.path.dirname(config._user_plugin.__file__), 'environment')
    
    if os.path.isdir(config._work_dir):
        rmtree(config._work_dir)
    else:
        os.makedirs(config._work_dir)


def pytest_generate_tests(metafunc):
    """Parametrize tests with source files."""
    finder = metafunc.config._marker_finder
    if 'file' in metafunc.fixturenames:
        options = finder.find_options(metafunc, 'find_files').get_values()
        
        # Update path to search files in direcotory containing test sources
        # If 'path' option is absolute path, then it overrides COMPLIANCE_TESTDIR
        path = os.path.join(COMPLIANCE_TESTSDIR, options.get('path', ''))
        options['path'] = path
        files = list(find_files(**options))
        
        if files:
            metafunc.parametrize('file', files, ids=[os.path.basename(f) for f in files])
        else:
            metafunc.parametrize('file', [pytest.skip('No files found')])

def pytest_collection_modifyitems(config, items):
    """Filter items based on marker options"""
    finder = config._marker_finder
     
    for item in items:
        # architecture marker options
        architecture = finder.find_options(item, 'architecture')
        isa = architecture.get_value('isa')
        isa_not = architecture.get_value('isa_not')
        extensions = architecture.get_value('extensions')
        extensions_not = architecture.get_value('extensions_not')
        modes = architecture.get_value('modes')
        modes_not = architecture.get_value('modes_not')

        # memory marker options
        memory = finder.find_options(item, 'memory')
        minimum_size = memory.get_value('minimum_size')
        misaligned = memory.get_value('misaligned')
        
        # exceptions marker options
        exceptions = finder.find_options(item, 'exceptions')
        interrupt_support = exceptions.get_value('interrupt_support')
        # status_registers marker options
        status_registers = finder.find_options(item, 'status_registers')
        
        filter_test(item, isa, PlatformProperties.ISA, True,
                    "Test requires architecture {}")
        filter_test(item, extensions, PlatformProperties.EXTENSION, True,
                    "Test requires extension(s) {}")
        filter_test(item, modes, PlatformProperties.MODE, True,
                    "Test requires mode(s) {}")
        filter_test(item, minimum_size, PlatformProperties.MEMORY_RANGE, True,
                    "Test minimum memory size {} Bytes")
        filter_test(item, misaligned, PlatformProperties.MEMORY_MISALIGNED, True,
                    "Test requires misaglined memory access set to {}")
        filter_test(item, interrupt_support, PlatformProperties.INTERRUPT_SUPPORT, True,
                    "Test requires interrupt support set to {}")
        filter_test(item, exceptions.args, PlatformProperties.CAUSE, True,
                    "Test requires following exception(s) support: {}")
        filter_test(item, status_registers.args, PlatformProperties.CSR, True,
                    "Test requires following control or status register(s) support {}")

        filter_test(item, isa_not, PlatformProperties.ISA, False,
                    "Test is skipped for architecture {}")
        filter_test(item, extensions_not, PlatformProperties.EXTENSION, False,
                    "Test is skipped for extension(s) {}")
        filter_test(item, modes_not, PlatformProperties.MODE, False,
                    "Test is skipped for mode(s) {}")
       
@pytest.fixture
def environment_path(request):
    return request.config._user_environment

@pytest.fixture(scope='session')
def configured_user_model(request):
    return request.config._user_model

@pytest.fixture
def model_path(request):
    return request.config._model_path

@pytest.fixture
def reference_compiler_path(work_dir):
    path = find_riscv_tool('gcc(.exe)?$')
    if path:
        return path
    pytest.skip("Unable to find reference compiler executable")

@pytest.fixture
def reference_environment_path(request):
    return request.config._reference_env.path


@pytest.fixture
def reference_model_path(work_dir):
    path = find_riscv_tool('^spike(.exe)?$')
    if path:
        return path
    pytest.skip("Unable to find reference model executable")


@pytest.fixture
def reference(work_dir, user_model, reference_compiler_path, 
              reference_environment_path, reference_model_path):
    """Create reference execution environment"""
    compiler = RiscVCompiler(reference_compiler_path, work_dir=work_dir)
    environment = Environment(reference_environment_path)
    model = Spike(reference_model_path, work_dir=work_dir)
    # Configure golden model - it shares the same configuration as tested model
    model.set_configuration(user_model.get_configuration())

    ref = ExecutionEnvironment()
    ref.add_compiler(compiler)
    ref.add_environment(environment)
    ref.add_model(model)
    
    return ref


@pytest.fixture
def user(user_model, work_dir, user_compiler, user_environment):
    """Create user execution environment"""
    compiler = copy.deepcopy(user_compiler)
    environment = copy.deepcopy(user_environment)
    model = copy.deepcopy(user_model)
    
    compiler.work_dir = work_dir
    model.work_dir = work_dir
    
    us = ExecutionEnvironment()
    us.add_compiler(compiler)
    us.add_environment(environment)
    us.add_model(model)    
    return us
    
@pytest.fixture
def reporter(request):
    tr = request.config.pluginmanager.getplugin('rvtest_reporter')
    tr.node = request.node
    return tr


@pytest.fixture
def testdir(request):
    return str(request.node.fspath())


@pytest.fixture
def toolchain_path(request):
    return request.config._toolchain_path

@pytest.fixture(autouse=True)
def work_dir(request, worker_id):
    """Working directory of single test.
    
    :param worker_id: ID of xdist worker (gw0, gw1, ...) or 'master' for master worker. 
    """
    # worker_id = 'master'
    work = os.path.join(request.config._work_dir, 'work', worker_id)
    
    if os.path.exists(work):
        rmtree(work, content_only=True)
    else:
        os.makedirs(work)
    
    return work
