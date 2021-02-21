'''
metadata_utils.py: utilities for working with OmniOutliner metadata

Authors
-------

Michael Hucka <mhucka@caltech.edu> -- Caltech Library

Copyright
---------

Copyright (c) 2021 by Michael Hucka and the California Institute of Technology.
This code is open-source software released under a 3-clause BSD license.
Please see the file "LICENSE" for more information.
'''

from appscript import app
from requests.structures import CaseInsensitiveDict

from .exceptions import *

if __debug__:
    from sidetrack import log


# Internal constants.
# .............................................................................

# I derived the list of metadata fields by looking at the document inspector
# in OmniOutliner 5, and inspecting the keys put into metadata.xml inside an
# OmniOutliner document.  Note: the addition of some entries with and without
# trailing "s" characters is to cope with common mistakes.

_METADATA_BY_FIELD = CaseInsensitiveDict({
    'Authors'       : ('kMDItemAuthors',       list),
    'Comment'       : ('kMDItemComment',       str),
    'Comments'      : ('kMDItemComment',       str),
    'Copyright'     : ('kMDItemCopyright',     str),
    'Description'   : ('kMDItemDescription',   str),
    'Keywords'      : ('kMDItemKeywords',      list),
    'Languages'     : ('kMDItemLanguages',     list),
    'Organizations' : ('kMDItemOrganizations', list),
    'Project'       : ('kMDItemProjects',      list),
    'Projects'      : ('kMDItemProjects',      list),
    'Subject'       : ('kMDItemSubject',       str),
    'Version'       : ('kMDItemVersion',       str),
})

_METADATA_BY_KEY = CaseInsensitiveDict(
    { row[1][0]:(row[0], row[1][1]) for row in _METADATA_BY_FIELD.items() }
)


# Exported functions.
# .............................................................................

def md_key(given):
    if given in _METADATA_BY_KEY.keys():
        return given
    elif given in _METADATA_BY_FIELD.keys():
        return _METADATA_BY_FIELD[given][0]
    else:
        return None


def md_type(name_or_key):
    key = md_key(name_or_key)
    if key:
        return _METADATA_BY_KEY[key][1]
    else:
        return None


def md_match(metadata, name_or_key, value):
    key = md_key(name_or_key)
    if key not in metadata:
        return False
    if md_type(key) == list:
        return any(value == list_value for list_value in metadata[key])
    else:
        return value == metadata[key]


def md_set(metadata, name_or_key, new_value):
    key = md_key(name_or_key)
    if md_type(key) == list:
        if key in metadata:
            metadata[key].append(new_value)
        else:
            metadata[key] = [new_value]
    else:
        metadata[key] = new_value


def key_for_field(name):
    return _METADATA_BY_FIELD[name][0] if name in _METADATA_BY_FIELD else None


def field_for_key(key):
    return _METADATA_BY_KEY[key][0] if key in _METADATA_BY_KEY else None


def document_list():
    documents = app('OmniOutliner').documents()
    return [doc.file().path for doc in documents]


def close_document(doc_path):
    for doc in app('OmniOutliner').documents():
        if doc.file().path == doc_path:
            if __debug__: log(f'telling OO to close {doc_path}')
            try:
                app('OmniOutliner').close(doc)
            except Exception as ex:
                raise UserCancelled(f'Document not saved: {doc_path}')
            return


def open_document(doc_path):
    if __debug__: log(f'telling OO to open {doc_path}')
    try:
        app('OmniOutliner').open(doc_path)
    except Exception as ex:
        raise FileError(f'Unable to get OmniOutliner to open {doc_path}')


def save_document(doc_path):
    for doc in app('OmniOutliner').documents():
        if doc.file().path == doc_path:
            if __debug__: log(f'telling OO to save {doc_path}')
            try:
                app('OmniOutliner').save(doc)
            except Exception as ex:
                if ex.args[2].errornumber == -10000:
                    if __debug__: log(f'ignoring error -10000')
                    # I can't figure out what causes this AppleScript error,
                    # but the save operation does work, so ...
                    return
                else:
                    raise
