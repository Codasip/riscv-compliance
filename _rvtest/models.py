# Copyright (c) 2018, Codasip Ltd.
# See LICENSE file for license details.

from _rvtest import Causes, CSRS, RiscVExtensions, ISAS, PlatformProperties, Modes, CONFIGURATION_STRING_FORMAT
from _rvtest.platform_properties import (PropertyISA, PropertyExtensions, PropertyMemorySize,
                                         PropertyMemoryMisaligned, PropertyInterruptSupport,
                                         PropertyCauses, PropertyCSRS, PropertyModes)
from _rvtest.tools import Tool

class Platform():
    """Processor configuration.
    
    Platform specifies the configuration of tested processor. It stores the configuration
    and implements method for configuration modification such as setting, removing and
    getting property values.
    """
    def __init__(self):
        self._properties = {}
        
        self._register_property(PropertyISA(required=True, choices=ISAS))
        self._register_property(PropertyExtensions(choices=RiscVExtensions, multiple=True, default=[]))
        self._register_property(PropertyModes(required=True, choices=Modes, multiple=True, default=[]))
        self._register_property(PropertyMemorySize(required=True, types=[tuple, list]))
        self._register_property(PropertyMemoryMisaligned(types=[bool]))
        self._register_property(PropertyInterruptSupport(types=[bool]))
        self._register_property(PropertyCauses(multiple=True, choices=Causes, default=[]))
        self._register_property(PropertyCSRS(multiple=True, choices=CSRS, default=[]))
    
    def _register_property(self, prop):
        """Add property to supported properties. 
        
        :param prop: Property instance to register.
        :type prop: :py:class`~_rvtest.platform_properties.PlatformProperty`
        """
        class_name = prop.__class__.__name__
        assert getattr(prop, 'NAME', None), f"Property {class_name} does not have NAME attribute"
        assert prop.NAME not in self._properties, f"Property {prop.NAME} already registered"
        
        self._properties[prop.NAME] = prop
        
    def add_property(self, p_type, value):
        """Set property value.
        
        :param p_type: Property type (``NAME`` attribute of the property class).
        :param value: Value to be set or added (depends on property implementation).
        :type p_type: str
        :return: Current value of property.
        """
        p_type = getattr(p_type, 'name', None) or p_type
        assert p_type in self._properties, "Invalid property type"
        return self._properties[p_type].set(value)

    def remove_property(self, p_type, value=None):
        """Remove property value.
        
        :param p_type: Property type (``NAME`` attribute of the property class).
        :param value: Value to be removed.
        :type p_type: str
        :return: Current value of property.
        """
        p_type = getattr(p_type, 'name', None) or p_type
        assert p_type in self._properties, "Invalid property type"
        
        return self._properties[p_type].remove(value)
    
    def get_property(self, p_type, get_value=True):
        """Get property value.
        
        :param p_type: Property type (``NAME`` attribute of the property class).
        :type p_type: str
        :return: Current value of property.
        """
        p_type = getattr(p_type, 'name', None) or p_type
        assert p_type in self._properties, "Invalid property type"
        
        result = self._properties[p_type]
        if get_value:
            result = result.get_value()

        return result
    
    @property
    def configuration_string(self):
        """Build configuration string according to ISA and supported standard extensions.
        
        Configuration string is in standard format, see :py:data:`~_rvtest.CONFIGURATION_STRING_FORMAT`.
        
        .. note::
        
            All letters in configuration string are lower case.

        """
        isa = self.get_property(PlatformProperties.ISA)
        
        if isa is None:
            return
        
        format_values = {'isa': isa.value}
        
        extensions = self.get_property(PlatformProperties.EXTENSION)
        for ext in RiscVExtensions:
            format_values[ext.name] = ext.name.lower() if ext in extensions else ''
        
        return CONFIGURATION_STRING_FORMAT.format(**format_values)

    def get_misa(self):
        config_string = self.configuration_string.upper()
        property_mode = self.get_property(PlatformProperties.MODE, get_value=False)

        import string
        # ignore "rv**"
        config_string = config_string[4:]

        # set all bits to zero
        bits = 32 * ["0"]

        # check for extensions
        for index, letter in enumerate(string.ascii_uppercase):
            if letter in config_string:
                bits[-1-index] = '1'
                continue
            # check for privileged mode
            try:
                mode = Modes(letter)
                if letter != 'M' and letter in property_mode:
                    bits[-1-index] = '1'
            except ValueError:
                pass

        # return string in hex
        return hex(int(''.join(bits), 2))
    
    def get_configuration(self):
        """Extract current platform configuration.
        
        :return: Dictionary containing current platform configuration. Only values which were
            set before or have default value are present in configuration dictionary.
        :rtype: dict
        """
        return {p_type: p.get_value() for p_type, p in self._properties.items() if p.get_value()}
            
    def set_configuration(self, configuration):
        """Set configuration from dictionary.
        
        :param configuration: 
        :type configuration: dict
        """
        for p_type, value in configuration.items():
            self.add_property(p_type, value)

class RVModel(Tool, Platform):
    """Wrapper for RISC-V model."""

    class Result():

        def __init__(self, signature):
            self.signature = signature

    def __init__(self, path, name='RISC-V model', work_dir=None):
        Platform.__init__(self)
        Tool.__init__(self, path, name, work_dir)

    def _self_check(self):
        """Check that current configuration meets the RISC-V standard."""
        raise NotImplementedError("Self check method not implemented")


def test():
    platform = RVModel('ls', 'name')
    platform.add_property(PlatformProperties.ISA, ISAS.RV32E)
    platform.add_property(PlatformProperties.EXTENSION, [RiscVExtensions.M, RiscVExtensions.C, RiscVExtensions.B])
    platform.add_property(PlatformProperties.MEMORY_RANGE, [20,10,0])
    platform.add_property(PlatformProperties.MEMORY_MISALIGNED, True)
    
    platform_new = RVModel('ls', 'name')
    platform_new.set_configuration(platform.get_configuration())

    assert platform.get_property(PlatformProperties.ISA) == platform_new.get_property(PlatformProperties.ISA)
    assert platform.get_property(PlatformProperties.EXTENSION) == platform_new.get_property(PlatformProperties.EXTENSION)
    assert platform.get_property(PlatformProperties.MEMORY_RANGE) == platform_new.get_property(PlatformProperties.MEMORY_RANGE)
    assert platform.get_property(PlatformProperties.MEMORY_MISALIGNED) == platform_new.get_property(PlatformProperties.MEMORY_MISALIGNED)
    
    print("OK")

if __name__ == '__main__':
    test()

