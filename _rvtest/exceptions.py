# Copyright (c) 2018, Codasip Ltd.
# See LICENSE file for license details.

class ConfigError(Exception):
    pass

class MarkerArgumentException(Exception):
    """
    General exception class to throw when marker arguments are errorous.
    
    :ivar marker: Option marker which had caused an error.
    :ivar metafunc: Pytest metafunc object.
    :ivar message: Message to show.
    :ivar _args: Arguments for ``message`` formatting.
    :ivar _kwargs: Keyword arguments for ``message`` formatting.
    :vartype marker: :py:class:`~mastermind.internal.MarkerGroup`
    :vartype message: str
    :vartype _args: tuple
    :vartype _kwargs: dict
    """
    def __init__(self, marker, metafunc, message='', *args, **kwargs):
        super(MarkerArgumentException, self).__init__(message)
        self.marker = marker
        self.metafunc = metafunc
        self.message = message
        
        self._args = args
        self._kwargs = kwargs
    
    def __str__(self):
        mark = self.marker
        name = (self.metafunc.function.__name__ + 
                ((' in class {}'.format(self.metafunc.cls.__name__)) if self.metafunc.cls else ''))
        
        msg = self.message.format(*self._args, **self._kwargs) if self.message else 'Marker argument exception\n'
        
        msg_vals = (name, mark.marker_name, msg)
        return "Function {}: Invalid arguments for marker '{}'. {}".format(*msg_vals)


class MarkerOptionTypeMismatch(Exception):
    """
    An exception class to throw when marker option type is invalid.
    
    :ivar marker: Option marker which had caused an error.
    :ivar metafunc: Pytest metafunc object.
    :ivar message: Message to show.
    :ivar _args: Arguments for ``message`` formatting.
    :ivar _kwargs: Keyword arguments for ``message`` formatting.
    :vartype marker: :py:class:`~mastermind.internal.MarkerOption`
    :vartype message: str
    :vartype _args: tuple
    :vartype _kwargs: dict
    """
    def __init__(self, marker, metafunc, message='', *args, **kwargs):
        super(MarkerOptionTypeMismatch, self).__init__(message)
        self.marker = marker
        self.metafunc = metafunc
        self.message = message
        
        self._args = args
        self._kwargs = kwargs
    
    def __str__(self):
        mark = self.marker
        name = (self.metafunc.function.__name__ + 
                ((' in class {}'.format(self.metafunc.cls.__name__)) if self.metafunc.cls else ''))
        
        
        msg = self.message.format(*self._args, **self._kwargs) if self.message else 'MarkerOption type mismatch'
        expected = ', '.join([t.__name__ for t in mark.types])
        
        msg_vals = (name, mark.option_name, mark.static_name, mark.marker_name, expected, type(mark.value).__name__)
        
        if not msg.endswith('\n'):
            msg += '\n'
            
        msg += "Function {}: Invalid type for option '{}' or {} for marker '{}'. Expected {}, got type '{}'".format(
            *msg_vals)
        
        return msg

class PlatformPropertyException(Exception):
    """Raised when performing invalid operation for PlatformProperty."""
    pass
