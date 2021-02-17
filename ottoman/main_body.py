'''
Ottoman: a program to write Zotero select links into Zotero attachment files

Authors
-------

Michael Hucka <mhucka@caltech.edu> -- Caltech Library

Copyright
---------

Copyright (c) 2020 by Michael Hucka and the California Institute of Technology.
This code is open-source software released under a 3-clause BSD license.
Please see the file "LICENSE" for more information.
'''

from   bun import inform, warn, alert, alert_fatal
from   commonpy.file_utils import filename_extension, filename_basename
from   commonpy.file_utils import readable, writable
from   commonpy.string_utils import antiformat
from   os import listdir
from   os.path import isdir, join
from   pathlib import Path
import plistlib
from   plistlib import FMT_XML
import sys
import zipfile
from   zipfile import ZipFile, ZipInfo, ZIP_STORED, ZIP_DEFLATED

from .exceptions import CannotProceed
from .exit_codes import ExitCode
from .metadata_utils import key_for_field, field_for_key, proper_name

if __debug__:
    from sidetrack import log


# Exported classes.
# .............................................................................

class MainBody():
    '''Main body for Ottoman.'''

    def __init__(self, **kwargs):
        '''Initialize internal state.'''

        # Assign parameters to self to make them available within this object.
        for key, value in kwargs.items():
            if __debug__: log(f'parameter value self.{key} = {value}')
            setattr(self, key, value)

        # We expose attribute "exception" that callers can use to find out
        # if the thread finished normally or with an exception.
        self.exception = None


    def run(self):
        '''Run the main body.'''

        if __debug__: log('running MainBody')
        try:
            self._do_preflight()
            self._do_main_work()
        except Exception as ex:
            if __debug__: log(f'exception in main body: {str(ex)}')
            self.exception = sys.exc_info()
        if __debug__: log('finished MainBody')


    def stop(self):
        '''Stop the main body.'''
        if __debug__: log('stopping ...')
        pass


    def _do_preflight(self):
        '''Check the option values given by the user, and do other prep.'''

        # Sanity-check the arguments ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        hint = '(Hint: use -h for help.)'

        if not self.document:
            alert_fatal(f'Need a document to work on. {hint}')
            raise CannotProceed(ExitCode.bad_arg)
        if not filename_extension(self.document) == '.ooutline':
            alert_fatal(f'Not an OmniOutliner document: {self.document}')
            raise CannotProceed(ExitCode.bad_arg)
        if not readable(self.document):
            alert_fatal(f'Cannot read {self.document}')
            raise CannotProceed(ExitCode.file_error)

        if not self.args:
            alert_fatal(f'No arguments given => nothing to do. {hint}')
            raise CannotProceed(ExitCode.bad_arg)

        self.do_modify = any(('=' in v) for v in self.args)

        if self.do_modify and not writable(self.document):
            alert_fatal(f'Cannot write to {self.document}')
            raise CannotProceed(ExitCode.file_error)


    def _do_main_work(self):
        if self.on_metadata:
            if self.do_modify:
                self._edit_metadata()
            else:
                self._print_metadata()
        if self.on_body:
            self._edit_body()


    def _print_metadata(self):
        metadata = {}
        if isdir(self.document):
            # This is the "package" format, i.e., a folder.
            if __debug__: log(f'document has package structure: {self.document}')
            for item in listdir(self.document):
                if item == 'metadata.xml':
                    if __debug__: log(f'reading plist contained in metadata.xml')
                    with open(join(self.document, 'metadata.xml'), 'rb') as f:
                        metadata = plistlib.load(f, fmt = FMT_XML)
                    break
            else:
                inform(f'No metadata found in {self.document}')
                return
        else:
            if __debug__: log(f'document is a zip archive: {self.document}')
            with zipfile.ZipFile(self.document, 'r', ZIP_STORED) as zf:
                if 'metadata.xml' in zf.namelist():
                    if __debug__: log(f'reading plist contained in metadata.xml')
                    f = zf.read('metadata.xml')
                    metadata = plistlib.loads(f, fmt = FMT_XML)
                else:
                    inform(f'No metadata found in {self.document}')
                    return
        if metadata:
            if __debug__: log(f'found nonempty metadata content')
            with_prefix = (len(self.args) > 1)
            for item in self.args:
                print_value(item, metadata, with_prefix)


    def _edit_metadata():
        if self.overwrite:
            warn('Overwrite mode in effect.')
        inform('Will substitute values in metadata:')



# Miscellaneous helpers.
# .............................................................................

def print_value(item, metadata, show_prefix):
    prefix = f'{item}: ' if show_prefix else ''

    # Find the proper kMDItem* dict key, or complain if item is unknown.
    key = key_for_field(item)
    if not key:
        key = field_for_key(item)
    if not key:
        alert(f'Unrecognized metadata field or key: {item}')
        raise CannotProceed(ExitCode.bad_arg)

    # Print the value if there is one, else print nothing.
    if key in metadata:
        print(f'{prefix}{metadata[key]}')
