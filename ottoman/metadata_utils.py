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

from requests.structures import CaseInsensitiveDict


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
    { x[1][0]:(x[0], x[1][1]) for x in _METADATA_BY_FIELD.items() }
)


# Exported functions.
# .............................................................................

def key_for_field(name):
    return _METADATA_BY_FIELD[name][0] if name in _METADATA_BY_FIELD else None


def field_for_key(key):
    return _METADATA_BY_KEY[key][0] if key in _METADATA_BY_KEY else None
