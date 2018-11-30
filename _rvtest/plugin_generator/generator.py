# Copyright (c) 2018, Codasip Ltd.
# See LICENSE file for license details.
from enum import Enum, IntEnum
from glob import glob
import os
import shutil
from string import Formatter

from _rvtest import (Causes, CSRS, RiscVExtensions, ISAS, Modes, PlatformProperties,
                     GOLDEN_MODEL, MANDATORY_HEADER_FILES, MANDATORY_PYTHON_FILES)
from _rvtest.environment import Environment
from _rvtest.exceptions import ConfigError
from _rvtest.models import RVModel
from _rvtest.utils import error, info, warning
from _rvtest.plugin_generator import TARGET_DIR, TEMPLATE_DIR

class TemplateValue():
    """ Class representing single template value 
    
    :ivar name: Template symbol which will be substituted by this template.
    :ivar choices: List of available choices for value.
    :ivar types: List of allowed value data types.   
    :ivar required: ``True`` If this template value must contain any value.
    :ivar default: Default value, if None is set.
    :ivar one_per_line: If ``True`` and value is a list of multiple values,
                        then each value will be generated on separated line.
    :ivar _value: Set value.
    :type name: str
    :type choices: list
    :type types: list
    :type required: bool
    :type one_per_line: bool
    """
    
    def __init__(self, name, choices=None, types=None, required=False, default=None, 
                 one_per_line=True):
        """ Constructor """
        self.name = name
        self.choices = choices
        self.types = types
        self.required = required
        self.default = default
        self.one_per_line = one_per_line
        
        self._value = None
        
    def set(self, value):
        """ Set value of an instance.
        
        Performs validity check if there are any specified constraints.
        Contraint may be list of allowed values and/or data types. 
        
        :param value: Value to set.
        :return: ``True`` on success else ``False``.
        """
        l_value = value
        if not isinstance(l_value, list):
            l_value = [l_value]
        
        # Check validity 
        for v in l_value:
            if self.choices and v not in self.choices:
                return False
            elif self.types and not isinstance(v, tuple(self.types)):
                return False

        self._value = value
        return True
    
    def get_value(self):
        """Return value for template. 
        
        If None has been set, then default is returned.
        """
        return self._value or self.default
    
    def to_string(self, template, separator='\n'):
        """
        Substitute template value into string specified by ``template``
        parameter. If ``one_per_line`` is ``True``, then separator for
        each value may be specified.
        
        :param template: Template which will be used for substitution. It must
                         contain symbol ``value`` for valid substitution.
                         Optionally, ``name`` symbol may be contained in template.
                         If so, then it is replaced with ``TemplateValue`` instance name. 
        :param separator: Separator which will be used to separate multiple values. Applied
                          only when ``one_per_line`` is ``True``.
        :type template: str
        :type: separator: str 
        """
        value = self.get_value()
        # Nothing to substitute
        if not self.required and value is None:
            return ''
        
        # Get symbols from template
        names = [fn for _, fn, _, _ in Formatter().parse(template) if fn is not None]
        
        # Dictionary used for substitution
        dct = {}
        if 'name' in names:
            dct['name'] = self.name
        
        
        if isinstance(value, (list, tuple, set)):
            tmp = []
            for v in value:
                # Strings must be quoted
                if isinstance(v, str):
                    v = self.quote(v)
                tmp.append(v)
        elif isinstance(value, str):
            tmp = [self.quote(value)]
        else:
            tmp = value

        
        dct['value'] = tmp
        # Convert list of values to separate lines in template 
        if self.one_per_line:
            if isinstance(tmp, (list, tuple, set)):
                replaced = []
                for t in tmp:
                    dct['value'] = t
                    replaced.append(template.format(**dct))
                replaced = separator.join(replaced)
            else:
                replaced = template.format(**dct)
        else:
            replaced = template.format(**dct)
        return replaced
    
    def quote(self, text):
        """Add quotes to string.
        
        :param text: Text to quote.
        :type text: str
        """
        if ((text.startswith('"') and text.endsswith('"')) or
            (text.startswith("'") and text.startswith("'"))):
            return text
        
        return "'" + text + "'"
    
class EnumTemplateValue(TemplateValue):
    def __init__(self, name, *args, **kwargs):
        name = name.__class__.__name__ + '.' + name.name
        super(EnumTemplateValue, self).__init__(name, *args, **kwargs)
    
    def _to_string(self):
        return TemplateValue._to_string(self)
    
    
class PluginGenerator():
    """ Generates plugins for RISC-V Compliance Framework
    
    :ivar _model: Dummy model, which is used for values validity checks.
    :ivar raise_on_error: If ``True``, then exception is raised when configuration
                          is invalid.
    :ivar _values: Dictionary containing available values.
    :type _model: RVModel
    :type raise_on_error: bool
    :type _values: dict
    """
    
    DEFAULT_TARGET = 'default'
    
    def __init__(self, raise_on_error=True):
        # Create dummy platform
        self._model = RVModel(os.path.abspath(__file__), 'dummy')
        self._raise_on_error = raise_on_error
        self._values = {PlatformProperties.ISA.name: EnumTemplateValue(name=PlatformProperties.ISA, types=[ISAS, str], required=True),
                        PlatformProperties.MODE.name: EnumTemplateValue(name=PlatformProperties.MODE, types=[Modes, set]),
                        PlatformProperties.EXTENSION.name: EnumTemplateValue(name=PlatformProperties.EXTENSION, types=[RiscVExtensions, set]),
                        PlatformProperties.MEMORY_RANGE.name: EnumTemplateValue(name=PlatformProperties.MEMORY_RANGE, 
                                                                     types=[list, tuple, set, int], required=True, 
                                                                     one_per_line=False),
                        PlatformProperties.CAUSE.name: EnumTemplateValue(name=PlatformProperties.CAUSE, types=[Causes, set]),
                        PlatformProperties.CSR.name: EnumTemplateValue(name=PlatformProperties.CSR, types=[CSRS, set]),                        
                        PlatformProperties.MEMORY_MISALIGNED.name: TemplateValue(name=PlatformProperties.MEMORY_MISALIGNED, types=[bool], default=False),                        
                        PlatformProperties.INTERRUPT_SUPPORT.name: TemplateValue(name=PlatformProperties.INTERRUPT_SUPPORT, types=[bool], default=False),
                        'name': TemplateValue(name='name', types=[str], default='RISC-V model'),
                        'compiler': TemplateValue(name='compiler', types=[bool], default=True),
                        }
    
    def add_property(self, p_type, value):
        """ Add property to generator. Performs validity check
        by simulating the same action on real RVModel instance.
        
        :param p_type: Property type, must be one from enum PlatformProperties.    
        :param value: Value to set.
        :return: ``True`` if operation succeeded else ``False``.   
        :rtype: bool 
        """
        exc = None
        try:
            updated = self._model.add_property(p_type, value)
        except AssertionError as e:
            exc = e
        
        if exc:
            if self._raise_on_error:
                raise ConfigError(str(exc))
            return False

        self._values[p_type.name].set(updated)
        return True

    def remove_property(self, p_type, value):
        """ Remove property to generator. Performs validity check
        by simulating the same action on real RVModel instance.
        
        :param p_type: Property type, must be one from enum PlatformProperties.    
        :param value: Value to remove.
        :return: ``True`` if operation succeeded else ``False``.   
        :rtype: bool 
        """
        exc = None
        try:
            updated = self._model.remove_property(p_type, value)
        except AssertionError as e:
            exc = e
        
        if exc:
            if self._raise_on_error:
                raise ConfigError(str(exc))
            return False
        
        self._values[p_type.name].set(updated)
        return True
                            
    def generate(self, output, target=None):
        """ Generate plugin for RISC-V Compliance Framework.
      
        :param output: Path where the plugin will be generated. If path
                       already exists, then plugin content will be rewritten.
        :param
        :type output: str
        """
        info("Generating plugin")
        output = os.path.abspath(output)

        if target is None:
            target = 'default'
        target_dir = os.path.join(TARGET_DIR, target)
        if not os.path.exists(target_dir):
            raise RuntimeError(f"Plugin generator failed: Target directory {target_dir} does not exist")

        if os.path.isfile(output):
            error("Selected path is existing file, canceling generation")
            return
        elif os.path.isdir(output):
            info(f"Output directory {output} already exists, content will be rewritten.")
        else:
            info(f"Creating output directory {output}")
            os.makedirs(output)

        # Create empty __init__ file
        with open(os.path.join(output, "__init__.py"), 'w'):
            pass
        
        # Prepare environment directory 
        env_path = os.path.join(output, 'environment')
        headers_path = os.path.join(env_path, Environment.INCLUDES_FOLDERNAME)
        if not os.path.exists(env_path):
            os.makedirs(env_path)
        if not os.path.exists(headers_path):
            os.makedirs(headers_path)
        
        # Copy header files
        target_files = set([f for f in os.listdir(target_dir)])
        golden_model_files = set([f for f in os.listdir(GOLDEN_MODEL)])
        for header_file in MANDATORY_HEADER_FILES:
            src = None
            if header_file in target_files:
                src = os.path.join(target_dir, header_file)
                target_files.remove(header_file)
            elif header_file in golden_model_files:
                src = os.path.join(GOLDEN_MODEL, header_file)
            
            if src:
                info(f"Copying header file {src}.")
                shutil.copy(src, headers_path)
            else:
                warning(f"Unable to find mandatory header file {header_file}!")
        
        # Copy linker script
        linker_scripts = [f for f in target_files if f.endswith('.ld')]
        for ld in linker_scripts:
            info(f"Copying linker script: {ld}.")
            target_files.remove(ld)
            shutil.copy(os.path.join(target_dir, ld), env_path)
        
        # Apply and copy Python templates
        default_templates = [f for f in os.listdir(os.path.join(TARGET_DIR, self.DEFAULT_TARGET))]
        for python_file in MANDATORY_PYTHON_FILES:
            src = None
            if python_file in target_files:
                src = os.path.join(target_dir, python_file)
                target_files.remove(python_file)
            elif python_file in default_templates:
                src = os.path.join(TARGET_DIR, self.DEFAULT_TARGET, python_file)
            if src:
                print(f"Applying template {src}")
                self._fill_template(src, output)
            else:
                warning(f"Unable to find mandatory template {python_file}!")

        # Copy custom files
        for custom_file in target_files:
            abs_path = os.path.join(target_dir, custom_file)
            if os.path.isdir(abs_path):
                info(f"Copying custom directory {custom_file}")
                shutil.copytree(abs_path, output)
            else:
                info(f"Copying custom file {custom_file}")
                shutil.copy(os.path.join(target_dir, custom_file), output)

    def _fill_template(self, template, output_dir):
        template_name = os.path.basename(template)
        with open(template, 'r') as fr:
            template = fr.read()
        
        substituted = self.subst_vars(template)
        with open(os.path.join(output_dir, template_name), 'w') as fw:
            fw.write(substituted)
        
    def set_name(self, value):
        self._values['name'] = self.quote(value)
    
    def set_compiler(self, value):
        self.values['compiler'] = bool(value)

    def subst_vars(self, text):
        """Substitute template symbols by real values."""
        spaces = '    '
        # Get template keywords
        names = [fn for _, fn, _, _ in Formatter().parse(text) if fn is not None]
        # Available keys
        keys = [k for k in self._values if k in names]

        dct = {}
        for key in keys:
            template_value = self._values.get(key)
            if key in ['name']:
                string = self.quote(template_value.get_value())
            else:
                string = template_value.to_string('model.add_property({name}, {value})', separator='\n'+spaces)
                if string is None:
                    continue
                string = spaces + string

            dct[key] = string

        return text.format(**dct)
    
    def quote(self, text, once=True):
        if not isinstance(text, str):
            return text
        if (once and (text.startswith('"') and text.endsswith('"')) or
            (text.startswith("'") and text.startswith("'"))):
            return text
        return "'" + text + "'"

            
if __name__ == '__main__':
    # Simple generator test
    generator = PluginGenerator()
    generator.add_property(PlatformProperties.ISA, ISAS.RV32I)
    generator.add_property(PlatformProperties.EXTENSION, RiscVExtensions.A)
    generator.add_property(PlatformProperties.EXTENSION, RiscVExtensions.M)
    generator.remove_property(PlatformProperties.EXTENSION, RiscVExtensions.M)
    generator.add_property(PlatformProperties.MEMORY_RANGE, (1, 0, 0))
    generator.generate('test_plugin')
