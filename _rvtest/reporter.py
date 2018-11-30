# Copyright (c) 2018, Codasip Ltd.
# See LICENSE file for license details.

import os
import pytest
import re
from subprocess import CalledProcessError

from _rvtest import PlatformProperties
from _rvtest.utils import copy, rmtree, string_to_path

class Reporter():
    def __init__(self, config):
        self.config = config
        self.node = None 
    
    def add_metadata(self, name, value, title=None):
        """
        Automatically add metadata to the pytest item.
        :param name:  Unique XML valid ID of the metadata.
        :param value: Value to be stored. If not string, will be converted to string.
        :param title: Title of the metadata for the user. If not set, name will be used.
        """
        if self.node is None:
            return 
        try:
            metadata = self.node.metadata
        except AttributeError:
            setattr(self.node, 'metadata', [])
            metadata = self.node.metadata
        if not title:
            title = name
    
        metadata.append({'name': name, 'value': str(value), 'title': title})
        
    def pytest_report_header(self, config):
        metadata = {'ISA': config._user_model.get_property(PlatformProperties.ISA),
                    'Toolchain': config._toolchain_path,
                    'Plugin path': os.path.realpath(config._user_plugin.__file__),
                    'RISC-V model path': config._model_path,
                    'Reference environment': config._reference_env.path,
                    }
        
        msg = ""
        for k, v in metadata.items():
            msg += f'{k}: {v}\n'
        msg = msg.strip()
        
        # Update metadata for report
        if not hasattr(config, '_metadata') or config._metadata is None:
            config._metadata = {}
        config._metadata.update(metadata)
             
        return msg
    
    def pytest_runtest_setup(self, item):
        # Register current node for latter identification
        self.node = item 
        
    @pytest.hookimpl(tryfirst=True)
    def pytest_runtest_logreport(self, report):
        """
        Parse metadata and redirect them to reporting plugins
        """
        # collect metadata for testcase call only, skip setup and teardown
        if report.when != "call":
            return
    
        # some tests might not generate metadata
        metadata = getattr(report, 'metadata', None)
        if not metadata:
            return
        
        # add properties to JUnit XML report
        xml = getattr(pytest.config, "_xml", None)
        if xml is not None:
            node_reporter = xml.node_reporter(report)
            for md in metadata:
                node_reporter.add_property(md['name'], md['value'])
    
        # prevent adding custom section on both xdist slave and master
        if not hasattr(pytest.config, 'slaveinput'):
            meta_str = ''
            for md in metadata:
                meta_str += '{}: {}\n'.format(md['title'], md['value'])
            report.sections.append(("Metadata", meta_str))
    
    @pytest.hookimpl(tryfirst=True, hookwrapper=True)
    def pytest_runtest_makereport(self, item, call):
        outcome = yield
        report = outcome.get_result()
        
        # Filtering and timeouts
        if call.excinfo:
            excval = call.excinfo.value
            report.timedout = False
            report.stdout = report.stderr = None

            if hasattr(excval, 'stdout') and excval.stdout:
                report.sections.append(('Captured stdout', excval.stdout.decode('utf-8')))
                report.stdout = excval.stdout.decode('utf-8')
            if hasattr(excval, 'stderr') and excval.stderr:
                report.sections.append(('Captured stderr', excval.stderr.decode('utf-8')))
                report.stderr = excval.stderr.decode('utf-8')

        if report.failed:
            source = item.funcargs.get('work_dir')
            if source:
                # normalize testcase ID to be used as path
                item_path = string_to_path(item.name)
                target = os.path.join(self.config._work_dir, 'failed', item_path)

                if os.path.isdir(target):
                    rmtree(target)
                copy(source, target)


    @pytest.hookimpl(trylast=True)
    def pytest_report_teststatus(self, report):
        if report.when == 'call':
            if hasattr(report, 'tool'):
                group = 'failed'
                abbrv = 'F'
                cause = 'failed ' + report.tool
                if report.timedout:
                    abbrv = 'T'
                    cause = 'timeout'
                return (group, abbrv, cause.upper())
    
    @pytest.hookimpl(trylast=True) 
    def pytest_terminal_summary(self, terminalreporter):
        tr = terminalreporter
        reports = [x for y in tr.stats.values() for x in y]
        # Collect results
        passed = {}
        failed = {}
        for r in reports:
            if not hasattr(r, 'outcome') or r.outcome == 'skipped':
                continue
            if r.when != 'call':
                continue
            m = re.search('{0}(\w){0}'.format(os.sep), r.nodeid)
            
            key = m.group(1) if m else 'others'
            failed.setdefault(key, 0)
            passed.setdefault(key, 0)
            
            if r.outcome == 'passed':
                passed[key] += 1
            else:
                failed[key] += 1
        
        model = self.config._user_model
        tr.write_line(f"{model.name} with ISA configuration: {model.configuration_string.upper()}")
        
        # Print base ISA results first
        for base_isa_key in ['E', 'I']:
            if base_isa_key in passed:
                passed_count = passed[base_isa_key]
                failed_count = failed[base_isa_key]
                self._write_report_line(tr, "Base ISA", passed_count, failed_count)
                del passed[base_isa_key]
                del failed[base_isa_key]
                break

        for extension, passed_count in passed.items():
            failed_count = failed.get(extension)
            self._write_report_line(tr, extension, passed_count, failed_count)
            
    def _write_report_line(self, tr, name, passed_count, failed_count):
        total = passed_count + failed_count
        tr.write(f'{name}: {passed_count}/{total} passed ')
        if failed_count:
            tr.write_line('(NOT compliant)', red=True)
        else:
            tr.write_line('(OK)', green=True)
        
        
        
