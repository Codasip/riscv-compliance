# Copyright (c) 2018, Codasip Ltd.
# See LICENSE file for license details.

from enum import Enum, IntEnum

from _rvtest import PlatformProperties, ISAS, RiscVExtensions, Modes, Causes, CSRS
from _rvtest.exceptions import PlatformPropertyException
from _rvtest.utils import to_list, str2int, is_iterable

class PlatformProperty():
    NAME = None

    def __init__(self, required=False, multiple=False, unique=True,
                 choices=None, types=None, default=None):
        """Constructor.
        
        :param required: If ``True``, then property cannot have empty value.
        :param multiple: If ``True``, then property can hold multiple values at once.
        :param unique: If ``True``, then each stored value must be unique. Unique
            is applied only when ``multiple`` is set to ``True``. When trying to add
            duplicite value, that value is skipped (no exception is raised, but it is
            guaranteed that property contains that value).
        :param choices: Some properties have limited possible values. ``choices``
            specify constraints on property value(s). ``choices`` can be either an iterable
            or ``Enum`` class. If ``Enum`` class is passed, then only its members are allowed.
        :param types: List of supported types for property.
        :param default: Default value for property if it's value is not set yet.
        :type required: bool
        :type multiple: bool
        :type unique: bool
        :type choices: Iterable, Enum or IntEnum
        :type types: list
        """
        assert self.NAME is not None, "Property name not set"
        self._value = None
        self._enum_class = None
        self._default_value = default
        self.required = required
        self.multiple = multiple
        self.unique = unique
        self.choices = self._load_choices(choices)
        self.types = types

    def _load_choices(self, choices):
        if choices is None:
            return None
        # Unpack Enum values
        if issubclass(choices, (Enum, IntEnum)):
            self._enum_class = choices
            choices = [i for i in choices]
        return to_list(choices)

    def validate_value(self, value):
        """Default implementation does not have any special constraints.
        Each property should override this method if that property requires
        special format of it's value.
        """
        return True, ''

    def set(self, *values, append=True):
        """Set property value (or multiple values if supported).
        
        :param *values: List of values to set.
        :param append: If ``False``, then property value is reset before setting.
        :type append: bool
        :return: Current property value (after setting).
        """
        if not values:
            raise PlatformPropertyException("No value to set")
        if not self.multiple and len(values) > 1:
            raise PlatformPropertyException("Too many values to set")
        # Reset value before adding/setting new one.
        if not append:
            self.reset()
        if self.multiple:
            _values = []
            # Unpack iterable values
            for v in values:
                if is_iterable(v):
                    _values.extend(v)
                else:
                    _values.append(v)
            values = _values
        for value in values:
            # If property allowes only values from enumeration, then
            # value can be set with 'pure' value or an Enum item instance.
            if self._enum_class:
                value = self._value2enumitem(value)
            self._set_single(value)
        return self.get_value()
    
    def _set_single(self, value):
        # Validate constraints
        if self.choices and value not in self.choices:
            valid_values = ', '.join(map(str, self.choices))
            raise PlatformPropertyException(f"Invalid value {value}, valid values are: {valid_values}")
        # Validate data type
        if self.types and not any([isinstance(value, t) for t in self.types]):
            valid_types = ', '.join(self.types)
            raise PlatformPropertyException(f"Invalid type of value {value}, valid types are: {valid_types}")
        # Call custom validation method
        valid, error_msg = self.validate_value(value)
        if not valid:
            raise PlatformPropertyException(f"Invalid value {value} ({error_msg})")

        if self.multiple:
            self._value = self._value or []
            if not self.unique or (self.unique and value not in self._value):
                self._value.append(value)
        else:
            self._value = value
        return self.get_value()
        
    def get_value(self, default=None):
        """Property value getter.
        
        At first try get previously set value. If it's empty try value passed by `default` 
        parameter. If it's empty as well, return default value for property.
        """
        if self._value is not None:
            return self._value
        if default is not None:
            return default
        return self._default_value

    def reset(self):
        self._value = None
    
    def _value2enumitem(self, value):
        """Convert value to enum instance"""
        if self._enum_class is None or isinstance(value, self._enum_class.__class__):
            return value
        return self._enum_class(value)
    
        #for item in self._enum_class:
        #    if value == item.value:
        #        return item
        return value
    
    def __contains__(self, value):
        """Suppport ``in`` operator. 
        
        E.g. ``if 'val' in property``.
        """
        if not self.multiple:
            raise PlatformPropertyException("Property does not support operator in")
        value = self._value2enumitem(value)
        
        return bool(self._value and value in self._value)
    
    def __iter__(self):
        """Support iteration."""
        return to_list(self._value)

    def remove(self, value=None):
        if value and not self.multiple:
            raise PlatformProperties("Cannot remove specific value from single-value property")
        if value is None:
            self.reset()
        else:
            value = self._value2enumitem(value)
            if value in self._value:
                self._value.remove(value)
        return self.get_value()

class PropertyISA(PlatformProperty):
    """Property for ISA specification."""
    NAME = PlatformProperties.ISA.name
 
class PropertyExtensions(PlatformProperty):
    """Property for standard extension specification."""
    NAME = PlatformProperties.EXTENSION.name

class PropertyModes(PlatformProperty):
    """Property for mode specification."""
    NAME = PlatformProperties.MODE.name

class PropertyMemoryMisaligned(PlatformProperty):
    """Property for specifying if model supports misaligned memory access."""
    NAME = PlatformProperties.MEMORY_MISALIGNED.name
    
class PropertyMemorySize(PlatformProperty):
    """Property for memory specification.
    
    It's value is represented as a triple in format 
    (memory_size, program_start_address, data_start_address) 
    """
    NAME = PlatformProperties.MEMORY_RANGE.name
    
    def set(self, *values, append=True):
        """Allow setting memory size as property.set((x,x,x))"""
        if values and is_iterable(values[0]):
            values = tuple(map(str2int, values[0]))

        return super().set(values, append=append)
        
    def validate_value(self, value):
        """Validate memory size
        
        * All 3 values must be specified.
        * program start and data start must be within memory size range.
        """
        if len(value) != 3:
            return False, 'Memory property value must be a triplet <size, program_start, data_start>'
        
        size, program, data = str2int(value[0]), str2int(value[1]), str2int(value[2])
        
        if any(i is None for i in [size, program, data]):
            return False, "Invalid value format for memory range"
        if size <= 0 or not (0 <= program < size) or not (0 <= data < size):
            return False, "Invalid memory properties ranges. Size must be > 0, and program and data adress must be within range"
    
        return True, ''

class PropertyInterruptSupport(PlatformProperty):
    """Property for specifying if model supports interrupts."""
    NAME = PlatformProperties.INTERRUPT_SUPPORT.name
    
class PropertyCauses(PlatformProperty):
    """Property for supported causes/trap specification."""
    NAME = PlatformProperties.CAUSE.name

class PropertyCSRS(PlatformProperty):
    """Property for supported control and status registers specification."""
    NAME = PlatformProperties.CSR.name

def test():
    isa = PropertyISA(required=True, choices=ISAS)
    extensions = PropertyExtensions(choices=RiscVExtensions, multiple=True)
    modes = PropertyModes(required=True, choices=Modes, multiple=True)
    memory_size = PropertyMemorySize(required=True, types=[tuple, list])
    memory_misaligned = PropertyMemoryMisaligned(types=[bool])
    causes = PropertyCauses(multiple=True, choices=Causes)
    csrs = PropertyCSRS(multiple=True, choices=CSRS)
    
    assert isa.set('rv32i') == ISAS.RV32I
    assert isa.set('rv64i') == ISAS.RV64I
    assert isa.set('rv64e') == ISAS.RV64E
    assert isa.get_value() == ISAS.RV64E
    
    assert extensions.set('M', 'A', 'F') == [RiscVExtensions.M, RiscVExtensions.A, RiscVExtensions.F]
    assert RiscVExtensions.M in extensions
    assert 'M' in extensions 
    assert extensions.remove('M') == [RiscVExtensions.A, RiscVExtensions.F]
    assert 'M' not in extensions
    
    assert memory_size.set((1, 0, 0)) == (1,0,0)
    assert memory_size.set(('1', '', '')) == (1,0,0)
    
    assert memory_misaligned.set(True) is True
    assert memory_misaligned.get_value() is True
    
    print("OK")
    
    
if __name__ == '__main__':
    test()
    
