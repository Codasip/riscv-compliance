# Copyright (c) 2018, Codasip Ltd.
# See LICENSE file for license details.

import os

class Environment():
    """Simple wrapper for environment.
    
    Environment is one of the compoenents of rvtest plugin. It contains files which are
    used for assembly source compilation and linking. 
    
    .. seealso::
    
        See :py:data:`_rvtest.MANDATORY_HEADER_FILES` for set of files which must be 
        included in any valid Environment.
    """
    INCLUDES_FOLDERNAME = 'include'
    HEADER_SUFFIX = '.h'
    LDSCRIPT_SUFFIX = '.ld'
    
    def __init__(self, path):
        """Constructor
        
        :path: Path to Environment root directory
        :type path: str
        :raise AssertionError: If ``path`` is not a directory.
        """
        self.path = path
        self.include_dir = os.path.join(path, self.INCLUDES_FOLDERNAME)
        assert os.path.isdir(path), f"Environment path {path} does not exist"

    def get_headers(self, rel_path=''):
        """Get list of header files.
        
        :param rel_path: Relative path from Environment ``path``. If passed, then header files
            will be searched in that path.
        :type rel_path: str
        :return: List of header files in the specified location.
        """
        search = os.path.join(self.include_dir, rel_path)
        return [os.path.join(search, h) for h in os.listdir(search) if h.endswith(self.HEADER_SUFFIX)]
    
    def get_linker_script(self, rel_path=''):
        """Get linker script from the specified location.
        
        :param rel_path: Relative path from Environment ``path``. If passed, then linker script
            will be searched in that path.
        :type rel_path: str
        :return: Linker script in the specified location or ``None`` if not found.
        """
        search = os.path.join(self.path, rel_path)
        scripts = [os.path.join(search, ld) for ld in os.listdir(search) if ld.endswith(self.LDSCRIPT_SUFFIX)]
        return scripts[0] if scripts else None
