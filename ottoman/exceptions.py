'''
exceptions.py: exceptions defined by Ottoman

Authors
-------

Michael Hucka <mhucka@caltech.edu> -- Caltech Library

Copyright
---------

Copyright (c) 2021 by Michael Hucka and the California Institute of Technology.
This code is open-source software released under a 3-clause BSD license.
Please see the file "LICENSE" for more information.
'''


# Base class.
# .............................................................................
# The base class makes it possible to use a single test to distinguish between
# exceptions generated by Ottoman and exceptions generated by something else.

class OttomanException(Exception):
    '''Base class for Ottoman exceptions.'''
    pass


# Exception classes.
# .............................................................................

class CannotProceed(OttomanException):
    '''A recognizable condition caused an early exit from the program.'''
    pass

class UserCancelled(OttomanException):
    '''The user elected to cancel/quit the program.'''
    pass

class InternalError(OttomanException):
    '''Unrecoverable problem involving Ottoman itself.'''
    pass

class FileError(OttomanException):
    '''Problem reading or writing a file or its attributes.'''
    pass
