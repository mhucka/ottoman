'''
Ottoman: Omnioutliner Text TransfOrMAtioNs

Authors
-------

Michael Hucka <mhucka@caltech.edu> -- Caltech Library

Copyright
---------

Copyright (c) 2021 by Michael Hucka and the California Institute of Technology.
This code is open-source software released under a 3-clause BSD license.
Please see the file "LICENSE" for more information.
'''

from   boltons.debugutils import pdb_on_signal
from   bun import UI, inform, warn, alert, alert_fatal
from   commonpy.data_utils import timestamp
from   commonpy.interrupt import config_interrupt
from   commonpy.string_utils import antiformat
import plac
import signal
import sys

import ottoman
from   ottoman import print_version
from   ottoman.exceptions import *
from   ottoman.exit_codes import ExitCode
from   ottoman.main_body import MainBody

if __debug__:
    from sidetrack import set_debug, log, logr


# Main program.
# .............................................................................

@plac.annotations(
    document  = ('the OmniOutliner document to modify (required)',    'option', 'd'),
    metadata  = ('act on the document metadata',                      'flag',   'm'),
    overwrite = ('forcefully overwrite previous metadata content',    'flag',   'o'),
    save_as   = ('write a new document (default: modify in place)',   'option', 's'),
    text      = ('act on the text in the document',                   'flag',   't'),
    version   = ('print version info and exit',                       'flag',   'V'),
    no_color  = ('do not color-code terminal output',                 'flag',   'Z'),
    debug     = ('write detailed trace to "OUT" ("-" means console)', 'option', '@'),
    args      = 'keywords or keyword-value pairs',
)

def main(document = 'D', metadata = False, overwrite = False, save_as = 'S',
         text = False, version = False, no_color = False, debug = 'OUT', *args):
    '''Print or manipulate metadata or text in an OmniOutliner document.

The option -d is required, and its value should be the path to the OmniOutliner
file to modify.  At least one of the options -m and/or -t is also required,
to tell Ottoman whether to act on the document metadata or document text.  The
original document is modified unless the option -s is given to make Ottoman
write a new document.  These possibilities and more are explained below.

The --metadata option for manipulating metadata
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The option -m tells Ottoman to act on the OmniOutliner document metadata.
This is the content shown in the Document Inspector of the OmniOutliner app.
The recognized metadata fields are as follows:

    Field          Apple name              Value type
    -----          --------------          ----------
    Authors        kMDItemAuthors          list
    Comments       kMDItemComment          string
    Copyright      kMDItemCopyright        string
    Description    kMDItemDescription      string
    Keywords       kMDItemKeywords         list
    Languages      kMDItemLanguages        list
    Organizations  kMDItemOrganizations    list
    Projects       kMDItemProjects         list
    Subject        kMDItemSubject          string
    Version        kMDItemVersion          string

In the list above, the "Field" column shows the title they are given in the
Document Inspector panel, whereas the "Apple name" is the name of the
attribute key in the metadata property list stored in the document.  Ottoman
recognizes either form of the name, so that

  ottoman -d test.ooutline -m Comments="this is my comment"

is the same as

  ottoman -d test.ooutline -m kMDItemComment="this is my comment"

Note that these metadata fields are distinct from the macOS file metadata (and
in particular, the "Comments" field in the OmniOutliner metadata is NOT the
same as the Comments field in the macOS Finder info panel).

When working with metadata, Ottoman has two alternative modes of operation:

  1) If the argument to Ottoman includes an equals ('=') symbol, then the
     interpretation is that the value on the right of the equal sign should
     be appended to the metadata field (or if -o is given, then it should
     ovewrite the existing value of the metadata field).

  2) If the argument does not include an equals symbol, then Ottoman merely
     prints the current value of the field.

For example, the following will print the value of the Projects metadata field:

  ottoman -d test.ooutline -m Projects

More than one metadata field can be given as arguments at once.  When printing
values of fields, they will be prefixed by their names if Ottoman is asked to
print more than one.  As an example, let us suppose that

  ottoman -d test.ooutline -m Authors

might print the string "S. User" by itself, without a prefix. However,

  ottoman -d test.ooutline -m Authors Projects

would print will print multiple lines beginning with the field names:

  Authors: S. User
  Projects: My project

When setting metadata values, each field name or name=value combination must be
separated by white space; consequently, when setting values, you must surround
the values with quotes if they contain any spaces or other white space
characters.  Field name comparisons are done in a case-insensitive manner,
which means "Authors" is the same as "authors" and "kmditemauthors".

As mentioned above, when writing metadata, Ottoman will append values to the
given metadata fields unless given the option -o to overwrite previous values.

The --text option for modifying contents
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The option -t tells Ottoman to act on the text of the OmniOutliner document.
This makes Ottoman look through the text of the document for the given
keyword(s) surrounded by three "at" characters, i.e., @@@.  For example,

  @@@something@@@

would act as a placeholder for the keyword "something" in a document, and

  ottoman -d somefile.ooutline -t something="this is the value"

would cause Ottoman to replace every occurrence of the string @@@something@@@
in the document with the value "this is my value" (without the quotes).
The syntax of the placeholder is strict: it must be a single word without
spaces between the @@@ characters, to minimize the risk of accidentally
performing unwanted substitutions on other content in the body of the
document.

Modifying documents in-place versus saving as new documents
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Without the -s option, Ottoman replaces the original document with a modified
version; that is, the document is modified in-place.  If given the -s option,
Ottoman will instead save the rewritten document as a new document and leave
the original untouched.  This has the benefit of avoiding the potential for
data corruption in the original document.

Additional command-line arguments
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If given the -V option, this program will print the version and other
information, and exit without doing anything else.

If given the -@ argument, this program will output a detailed trace of
what it is doing. The debug trace will be sent to the given destination,
which can be '-' to indicate console output, or a file path to send the
output to a file.

When -@ has been given, Ottoman also installs a signal handler on signal
SIGUSR1 that will drop Ottoman into the pdb debugger if the signal is sent
to the running process.

Return values
~~~~~~~~~~~~~

This program exits with a return code of 0 if no problems are encountered.
It returns a nonzero value otherwise. The following table lists the possible
return values:

  0 = success -- program completed normally
  1 = the user interrupted the program's execution
  2 = encountered a bad or missing value for an option
  3 = file error -- encountered a problem with a file
  4 = an exception or fatal error occurred

Command-line arguments summary
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
'''
    # Set up debug logging as soon as possible, if requested ------------------

    if debug != 'OUT':
        if __debug__: set_debug(True, debug)
        import faulthandler
        faulthandler.enable()
        if not sys.platform.startswith('win'):
            # Even with a different signal, I can't get this to work on Win.
            pdb_on_signal(signal.SIGUSR1)

    # Preprocess arguments and handle early exits -----------------------------

    ui = UI('Ottoman', 'Omnioutliner Text TransfOrMAtioNs',
            show_banner = False, use_color = not no_color)
    ui.start()

    if version:
        print_version()
        exit(int(ExitCode.success))

    # Do the real work --------------------------------------------------------

    if __debug__: log('='*8 + f' started {timestamp()} ' + '='*8)
    body = exception = None
    try:
        body = MainBody(document    = document if document != 'D' else None,
                        destination = save_as if saveas != 'S' else None,
                        on_text     = text,
                        on_metadata = metadata,
                        args        = args,
                        overwrite   = overwrite)
        config_interrupt(body.stop, UserCancelled(ExitCode.user_interrupt))
        body.run()
        exception = body.exception
    except Exception as ex:
        exception = sys.exc_info()

    # Try to deal with exceptions gracefully ----------------------------------

    exit_code = ExitCode.success
    if exception:
        if __debug__: log(f'main body raised exception: {antiformat(exception)}')
        if exception[0] == CannotProceed:
            exit_code = exception[1].args[0]
        elif exception[0] == FileError:
            alert_fatal(antiformat(exception[1]))
            exit_code = ExitCode.file_error
        elif exception[0] in [KeyboardInterrupt, UserCancelled]:
            warn('Interrupted.')
            exit_code = ExitCode.user_interrupt
        else:
            msg = antiformat(exception[1])
            alert_fatal(f'Encountered error {exception[0].__name__}: {msg}')
            exit_code = ExitCode.exception
            if __debug__:
                from traceback import format_exception
                details = ''.join(format_exception(*exception))
                logr(f'Exception: {msg}\n{details}')

    # And exit ----------------------------------------------------------------

    if __debug__: log('_'*8 + f' stopped {timestamp()} ' + '_'*8)
    if __debug__: log(f'exiting with exit code {exit_code}')
    exit(int(exit_code))


# Main entry point.
# .............................................................................

# The following entry point definition is for the console_scripts keyword
# option to setuptools.  The entry point for console_scripts has to be a
# function that takes zero arguments.
def console_scripts_main():
    plac.call(main)

# The following allows users to invoke this using "python3 -m handprint".
if __name__ == '__main__':
    plac.call(main)
