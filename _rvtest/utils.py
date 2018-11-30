# Copyright (c) 2018, Codasip Ltd.
# See LICENSE file for license details.

import argparse
from enum import Enum, IntEnum
import os
import re
import shutil
import sys

class ArgumentParser(argparse.ArgumentParser):
    """Customized argument parser.
    
    Parser is able to ignore unknown arguments.
    """
    
    def parse_args(self, args=None, namespace=None, ignore_unknown=True):
        """Parse arguments.
        
        When ``args`` is ``None``, then arguments from commandline are used by parser.
        
        :param args: Arguments to parse. If ``None``, then `sys.argv` is used.
        :param namespace: Namespace instance. If ``None``, then a new instance will be 
            created.
        :param ignore_unknown: If ``True`` then do not throw error on unknown arguments.
        :param auto_split: If ``True`` then split argument value by ``,`` symbol. This is applied
            only when argument's action is **append**.
        :type args: list
        :type namespace: :py:class:`~argparse.Namespace`
        :type ignore_unknown: bool
        :type auto_split: bool
        :return: Tuple (args, argv) if ``ignore_unknown`` is ``True`` else args. Args are parsed known
            arguments. Argv is a list containing unknown arguments.
        """
        args, argv = self.parse_known_args(args, namespace)
        
        if argv and not ignore_unknown:
            msg = _('unrecognized arguments: %s')
            self.error(msg % ' '.join(argv))

        return (args, argv) if ignore_unknown else args

class ConvertibleEnum(Enum):
    @classmethod
    def names(cls):
        l = []
        for item in cls:
            l.append(item.name)
        return l
        
    @classmethod
    def values(cls):
        l = []
        for item in cls:
            l.append(item.value)
        return l
    
    @classmethod
    def dict(cls, full_name=True):
        d = {}
        for item in cls:
            name = item.name
            if full_name:
                name = '.'.join([cls.__name__, name])
            d[name] = item.value
        return d

class ConvertibleIntEnum(IntEnum):
    @classmethod
    def names(cls):
        l = []
        for item in cls:
            l.append(item.name)
        return l
        
    @classmethod
    def values(cls):
        l = []
        for item in cls:
            l.append(item.value)
        return l
    
    @classmethod
    def dict(cls, full_name=True):
        d = {}
        for item in cls:
            name = item.name
            if full_name:
                name = '.'.join([cls.__name__, name])
            d[name] = item.value
        return d

def copy(src, dest, copy_root=False):
    """Copy file or directory.
    
    If ``dest`` directory doesn't exist, it is automatically created.
    If ``src`` is file, ``src`` is copied with same basename into destination directory.
    If src is directory, content of the directory is copied into ``dest``. 
    
    :param src: Source file or directory.
    :param dest: Destination.
    :param copy_root: If ``True``, entire directory include its root dir is copied into ``dest``.
    :type src: str
    :type dest: str
    :type copy_root: bool
    
    """
    if os.path.isfile(src):
        if not os.path.isdir(dest):
            os.makedirs(dest)
        
        shutil.copy(src, dest)
    else:
        if copy_root:
            dest = os.path.join(dest, os.path.basename(src))
        shutil.copytree(src, dest)


def find_files(path, pattern=None, exclude=None):
    for root, _, files in os.walk(path):
        for fname in files:
            absp = os.path.join(root, fname)
            search_path = os.path.relpath(absp, path)
            
            if pattern is None or re.search(pattern, search_path):
                if exclude is None or not re.search(exclude, search_path):
                    yield absp

class Verbosity():
    """Verbosity levels for info."""
    ALWAYS = 0
    DEFAULT = 1
    LOW = 2
    DEBUG = 3
    ALL = 4

class _Logger():
    """Logging class."""
    def __init__(self, verbosity=Verbosity.DEFAULT, out=None):
        self.verbosity = verbosity
        self.out = out

    def log(self, type, msg, *args, **kwargs):
        verb = Verbosity.DEFAULT
        
        if (type != 'info' or verb >= self.verbosity):
            msg = msg.format(*args, **kwargs)
            if (not msg.endswith('\n')):
                msg += '\n'
            out = self.out
            if not out:
                out = sys.stdout
            out.write('{0}: {1}'.format(type, msg))
            # Flush automatically
            if hasattr(out, 'flush'):
                out.flush()            

def debug(msg, *args, **kwargs):
    if '--debug' not in sys.argv:
        return
    _Logger().log('debug', msg, *args, **kwargs)
        
def info(msg, *args, **kwargs):
    """Create info log entry with verbosity level."""
    verbosity = kwargs.pop('verbosity', None)
    if type(msg) is int:
        verbosity = msg
        msg = args[0]
        args = args[1:]
    elif not verbosity:
        verbosity = Verbosity.DEFAULT
    _Logger(verbosity).log('info', msg, *args, **kwargs)

def warning(msg, *args, **kwargs):
    """Create warning log entry."""
    _Logger().log('warning', msg, *args, **kwargs)
    
def error(msg, *args, **kwargs):
    """Create error log entry."""
    _Logger(out=sys.stderr).log('error', msg, *args, **kwargs)
    
def fatal(msg, *args, **kwargs):
    """Create fatal log entry and terminate the script execution."""
    _Logger(out=sys.stderr).log('fatal', msg, *args, **kwargs)


def find_riscv_tool(pattern):
    path = os.getenv('RISCV')
    assert path, "RISCV variable not defined"
    path = os.path.join(path, 'bin')
    
    files = list(find_files(path, pattern))
    
    if len(files) == 1:
        return files[0]
    raise ValueError(f"None or multiple RISCV tool(s) specified by pattern '{pattern}' were found")
     

def is_iterable(item):
    return isinstance(item, (list, set, tuple))

def rmtree(dir, content_only=False):
    if dir == '/':
        raise RuntimeError("Cannot remove root")
    
    shutil.rmtree(dir)
    
    if content_only and not os.path.exists(dir):
        os.makedirs(dir)

def str2int(value):
    if isinstance(value, int):
        return value
    if not value:
        return 0

    base = 10
    if value.startswith('0x'):
        base = 16
        value = value[2:]
    elif value.startswith('0b'):
        base = 2
        value = value[2:]
    elif value.startswith('0') and len(value) > 1:
        base = 8
        value = value[1:]
    
    try:
        value = int(value, base)
    except ValueError:
        value = None
    return value

def string_to_path(value):
    """
    Normalizes string and converts non-alpha characters and spaces to hyphens.
    """
    return re.sub('[^\w\s\.()]+', '-', value).strip(' \t\r\n-')

def to_list(item):
    if item is None:
        return
    if is_iterable(item):
        return list(item)
    return [item]

        