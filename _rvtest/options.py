# Copyright (c) 2018, Codasip Ltd.
# See LICENSE file for license details.

from collections import Iterable
from copy import copy, deepcopy

from _rvtest.exceptions import MarkerArgumentException, MarkerOptionTypeMismatch
from _rvtest.utils import is_iterable, warning

class MarkerGroup():
    """
    Class for detecting and processing Pytest markers.
    
    :ivar marker_name: Pytest marker name.
    :ivar varargs: ``True`` if marker supports variable arguments.
    :ivar varkwargs: ``True`` if marker supports variable keyword arguments.
    :ivar values:
    :ivar args: Marker arguments.
    :ivar kwargs: Marker keyword arguments. 
    :ivar markers: Instances of :py:class:`MarkerOption` which are supported by
    this Marker Group.
    :ivar _options: Set of supported option names.
    :vartype marker_name: str
    :vartype varargs: bool
    :vartype varkwargs: bool
    :vartype values: dict
    :vartype args: tuple
    :vartype kwargs: dict
    :vartype markers: set
    :vartype _options: set
    
    """

    def __init__(self, marker_name, *args, **kwargs):
        self.marker_name = marker_name
        self.varargs = kwargs.get('varargs', False)
        self.varkwargs = kwargs.get('varkwargs', False)
        self.values = {}
        self.args = ()
        self.kwargs = {}
        self.markers = set()
        self._options = set()
        
        for marker_option in args:
            self.add_option(*marker_option)
    
    def add_option(self, *args, **kwargs):
        """Add support for marker option.
        
        Argument ``args`` contains either MarkerOption instance or arguments
        for it's initialization. See :py:class:`MarkerOption` for available
        arguments. Note that ``marker_name`` is automatically inherited from
        ``MarkerGroup``. 
        """
        if args and isinstance(args[0], MarkerOption):
            option = args[0]
            assert option.marker_name == self.marker_name, """Marker names of MarkerGroup 
                                                            and Marker Option must match.
                                                           """
        else:
            option = MarkerOption(self.marker_name, *args, **kwargs)
        
        self.markers.add(option)
        self._options.add(option.option_name)
    
    def find_options(self, metafunc, filter_known_kwargs=True):
        """
        Find marker options for pytest function with type checking.
        
        :param metafunc: Pytest Metafunc object.
        :param filter_known_args: If ``True``, then delete registered options
        from marker keywords and preserve only unregistered ones.
        :type filter_known_args: bool
        :return: :py:class:`MarkerGroup` instance with detected marker option values.
        :rtype: :py:class:`MarkerGroup`
        """
        # Create copy, so this object is reusable.
        result = copy(self)
        # Detect option values and validate types
        for marker_option in self.markers:
            result.values[marker_option.option_name] = marker_option.find_option(metafunc)
        
        # Detect variable arguments and keyword arguments
        marker_obj = getattr(metafunc.function, self.marker_name, None)
        if marker_obj:
            m_args, m_kwargs = deepcopy(marker_obj.args), deepcopy(marker_obj.kwargs)
            
            if not self.varargs and m_args:
                msg = 'Variable argument are not supported by this marker, got: {}.'
                raise MarkerArgumentException(result, metafunc, msg, ', '.join(map(str, m_args)))
        
            if not self.varkwargs:
                errorous = [key for key in m_kwargs if key not in self._options]
                if errorous:
                    msg = 'Variable keyword arguments are not supported by this marker, unknown keys: {}.'
                    raise MarkerArgumentException(result, metafunc, msg, ', '.join(errorous))
            
            # Remove registered options from keyword arguments
            if filter_known_kwargs:
                for kw in marker_obj.kwargs:
                    if kw in self._options:
                        del m_kwargs[kw]
            
            result.args = m_args
            result.kwargs = m_kwargs
        
        return result
    
    def get(self, key):
        """Get marker option"""
        return self.values.get(key)
    
    def get_value(self, option, default=None):
        """Syntax sugar for option value extraction
        
        :param option: Option name.
        :param default: Default value if option is not found.
        :return: Extracted value or default if option is not found.
        """
        res = self.get(option)
        if res is None:
            return default
        return res.value

    def get_values(self, *options):
        """Extract option values.
        
        :param options: Options to extract. 
        :return: Dictionary containing ``options`` as keys and extracted values
        for each corresponding option. If option's value is ``None``, then
        that option is skipped and is not present in the returned dictionary.
        :rtype: dict
        """
        if not options:
            options = self._options
        return {option: self.get_value(option) for option in options 
                if self.get_value(option) is not None}
    
    def get_scope(self, option, default=None):
        """Syntax sugar for option scope extraction
        
        :param option: Option name.
        :param default: Default scope if option is not found.
        :return: Extracted scope or default if option is not found.
        """        
        res = self.get(option)
        if res is None:
            return default
        return res.scope
    
    def get_scopes(self, *options):
        """Extract option scopes.
        
        :param options: Options to extract. 
        :return: Dictionary containing ``options`` as keys and extracted scopes
        for each corresponding option.
        :rtype: dict
        """
        if not options:
            options = self._options
        return {option: self.get_value(option) for option in options 
                if self.get_value(option) is not None}        
        if not options:
            options = self._options
        return {option: self.get_scope(option) for option in options}
    
    def __repr__(self):
        return 'MarkerGroup(marker_name=%s, varargs=%s, varkwargs=%s, options=%s)' % (self.marker_name, self.varargs, self.varkwargs, self._options)


class MarkerOption():
    """Single pytest marker option representation.
    
    :ivar marker_name: Pytest marker name.
    :ivar option_name: Option name (keyword argument of marker).
    :ivar static_name: Static variable name for class and module scopes.
    :ivar types: List of supported types for option.
    :ivar value: Extracted option value.
    :ivar scope: Extracted value scope.
    """

    def __init__(self, marker_name, option_name=None, static_name=None, valid_types=None, choices=None):
        """Constructor
    
        :param marker_name: Pytest marker name.
        :param option_name: Option name (keyword argument of marker).
        :param static_name: Static variable name for class and module scopes.
        :param valid_types: List of supported types for option.
        :type marker_name: str
        :type option_name: str
        :type static_name: str
        :type valid_types: tuple or list
        """
        self.marker_name = marker_name
        self.option_name = option_name
        self.static_name = static_name
        self.types = valid_types
        self.choices = choices
        
        self.value = None
        self.scope = None
    
    def __repr__(self):
        return 'MarkerOption(name=%s, option=%s, static_name=%s, types=%s' % (
            self.marker_name, self.option_name, self.static_name, self.types)
    
    def find_option(self, metafunc):
        """Extract 
        
        :param metafunc: Pytest metafunc object.
        :return: :py:class:`MarkerOption` with extracted values and scope.
        :rtype: :py:class:`MarkerOption`
        """
        value, scope = self._get_value(metafunc)
        
        # Copy self to make MarkerOption reusable.
        result = copy(self)
        result.value = value
        result.scope = scope
        
        if value is None:
            return result
        
        # Check value type
        invalid_values = self.validate_type(value)
        if invalid_values:
            raise MarkerOptionTypeMismatch(result, metafunc)
        
        invalid_values = self.validate_value(value)
        if invalid_values:
            raise MarkerArgumentException(result, metafunc)
        
        return result
    
    def _get_value(self, metafunc):
        """
        Process options set on testcase to find most priority one. First markers on function or class
        with given name and option (e.g. @pytest.mark.marker_name(option_name=....) ) are used, then 
        static variable in class or module named ``static_name`` is searched for. If option is not found,
        None is returned. For each option extract it's scope as well.
        """
        value, scope = None, None
        # highest priority has marker on the test case
        if hasattr(metafunc.function, self.marker_name):
            marker = getattr(metafunc.function, self.marker_name)
            value, scope = marker.kwargs.get(self.option_name), 'function'
        if value is None:
            # next priority is class static variable
            value, scope = getattr(metafunc.cls, self.static_name, None), 'class'
        if value is None:
            # last priority is module global variable
            value, scope = getattr(metafunc.module, self.static_name, None), 'module'
        if value is None:
            scope = None
    
        return value, scope
    
    def validate_type(self, value):
        """Check if value is valid.
        
        :param: Value to validate. Can be either single value
        or an iterable (list, tuple, set).
        :return: List of invalid values.
        :rtype: list of invalid values.
        """
        # Nothing to check, all types are allowed
        if self.types is None:
            return []
        
        option_types = self.types[:]
        # Detect if iterable objects are supported
        iterable = (Iterable in option_types)

        # Value cannot be iterable, but it is.
        if not iterable and is_iterable(value):
            return value
        
        if not is_iterable(value):
            value = [value]
        
        if iterable:
            option_types.remove(Iterable)
        
        invalid_values = []
        for v in value:
            if any([isinstance(v, t) for t in option_types]):
                continue
            invalid_values.append(v)
        
        return invalid_values
    
    def validate_value(self, value):
        if not self.choices:
            return []
        
        if not is_iterable(value):
            value = [value]
            
        return [v for v in value if v not in self.choices]
        
    
class OptionFinder():
    """Class for options detection.
    
    """

    def __init__(self, marker_groups):
        assert all([isinstance(group, MarkerGroup) for group in marker_groups])
        
        self.groups = marker_groups
        
        self._marker_names = set([group.marker_name for group in marker_groups])
    
    def find_options(self, metafunc, options=None, filter_known_kwargs=True):
        # Find all available options
        if options is None:
            options = self._marker_names
        else:
            # Get slice of available options
            if not is_iterable(options):
                options = [options]
            _options = set()
            
            for o in options:
                if o not in self._marker_names:
                    warning('Unknown marker option {}, ignoring.'.format(o))
                    continue
                _options.add(o)
            options = _options
        
        if not options:
            warning("No options to detect, either got empty options list unsupported " \
                    "options have been passed")
            return None

        # Detect options
        result = {}
        for marker_name in options:
            group = self.find_group(marker_name)
            result[marker_name] = group.find_options(metafunc, filter_known_kwargs)
        
        # Do not return dict when single option was requested.
        if len(options) == 1:
            return result[marker_name]
        
        return result

    def find_group(self, name):
        for g in self.groups:
            if g.marker_name == name:
                return g