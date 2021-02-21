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
from   io import BytesIO
from   os import listdir
from   os.path import isdir, join, abspath, dirname
from   pathlib import Path
import plistlib
from   plistlib import FMT_XML
import safer
import sys
from   tempfile import TemporaryFile
import zipfile
from   zipfile import ZipFile, ZipInfo, ZIP_STORED, ZIP_DEFLATED

from .exceptions import CannotProceed
from .exit_codes import ExitCode
from .oo_utils import md_key, md_type, md_match, md_set
from .oo_utils import document_list, close_document, open_document, save_document

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
        metadata = self._document_metadata()
        if metadata:
            if __debug__: log(f'found nonempty metadata content')
            with_prefix = (len(self.args) > 1)
            for item in self.args:
                print_value(item, metadata, with_prefix)
        else:
            inform(f'No metadata found in {self.document}')


    def _edit_metadata(self):
        # Check if the values are already there & don't touch the file if so,
        # to avoid having OO close & reopen the file unnecessarily.
        names_and_values = [pair.split('=') for pair in self.args]
        metadata = self._document_metadata() or {}
        if metadata:
            # Check if we need to change anything & exit if not.
            for name_or_key, new_value in names_and_values:
                key = md_key(name_or_key)
                if key in metadata and not md_match(metadata, key, new_value):
                    break
                elif key not in metadata and new_value:
                    break
            else:                     # Note: this "else" is on the for loop.
                if not self.overwrite:
                    if __debug__: log(f'no metadata changes necessary')
                    return

        # OK, we're doing it. First close the document (which prompts a save).
        reopen = False
        if abspath(self.document) in document_list():
            try:
                close_document(self.document)
            except:
                warn(f'Aborting because document was left unsaved: {self.document}')
                raise CannotProceed(ExitCode.user_interrupt)
            reopen = True

        # Rewrite the metadata we read from the document with new values.
        for name_or_key, value in names_and_values:
            if __debug__: log(f'changing metadata {name_or_key} to "{value}"')
            md_set(metadata, name_or_key, value)

        # Write out the modified document.
        if isdir(self.document):
            # In the package case, we only need to rewrite the metadata file.
            if __debug__: log(f'writing plist contained in metadata.xml')
            with open(join(self.document, 'metadata.xml'), 'wb') as f:
                plistlib.dump(metadata, f, fmt = FMT_XML)
        else:
            # As of Python 3.9, there's no facility in the zipfile package to
            # replace items in-place.  Have to do it ourselves.
            tmp = BytesIO()
            with zipfile.ZipFile(tmp, 'w') as new_zip:
                # Use our new metadata to create metadata.xml in the zip file.
                metadata_plist = plistlib.dumps(metadata, fmt = FMT_XML)
                new_zip.writestr('metadata.xml', metadata_plist)
                # Copy the other .xml files from the original OO document.
                with zipfile.ZipFile(self.document, 'r', ZIP_STORED) as orig_zip:
                    for item in orig_zip.namelist():
                        if item == 'metadata.xml':
                            continue
                        data = orig_zip.read(item)
                        new_zip.writestr(item, data)
            with safer.open(self.document, 'wb') as f:
                f.write(tmp.getvalue())

        # If we closed it, reopen it.
        if reopen:
            open_document(self.document)


    def _document_metadata(self):
        '''Return the metadata content of the document as a dict.'''
        # Two formats of OO documents: package (directory), or a zip file.
        if isdir(self.document):
            if __debug__: log('document has package structure')
            for item in listdir(self.document):
                if item == 'metadata.xml':
                    if __debug__: log(f'reading plist contained in metadata.xml')
                    with open(join(self.document, 'metadata.xml'), 'rb') as f:
                        return plistlib.load(f, fmt = FMT_XML)
        else:
            if __debug__: log('document is a zip archive')
            with zipfile.ZipFile(self.document, 'r', ZIP_STORED) as zf:
                if 'metadata.xml' in zf.namelist():
                    if __debug__: log(f'reading plist contained in metadata.xml')
                    return plistlib.loads(zf.read('metadata.xml'), fmt = FMT_XML)


# Miscellaneous helpers.
# .............................................................................

def print_value(item, metadata, show_prefix):
    key = md_key(item)
    if not key:
        alert(f'Unrecognized metadata field or key: {item}')
        raise CannotProceed(ExitCode.bad_arg)
    # Print the value if there is one, else print nothing.
    if key in metadata:
        prefix = f'{item}: ' if show_prefix else ''
        print(f'{prefix}{metadata[key]}')
