#!/usr/bin/env python
#encoding:utf-8
#author:Samus
#project:comicnamer
#license:Creative Commons GNU GPL v2
# http://creativecommons.org/licenses/GPL/2.0/

"""Holds default config values
Modified from http://github.com/dbr/tvnamer
"""

defaults = {
    # Select first series search result
    'select_first': False,

    # Always rename files
    'always_rename': False,

    # Batch (same as select_first and always_rename)
    'batch': False,

    # Fail if error finding show data (thetvdb.com is down etc)
    # Only functions when always_rename is True
    'skip_file_on_error': True,

    # Verbose mode (debugging info)
    'verbose': False,

    # Recurse more than one level into folders. When False, only
    # desends one level.
    'recursive': False,

    # When non-empty, only look for files with this extension.
    # No leading dot, for example: ['cbr', 'cbz']
    'valid_extensions': [],

    # Force Windows safe filenames (always True on Windows)
    'windows_safe_filenames': False,

    # Replace accented unicode characters with ASCII equivalents,
    # removing characters than can't be translated.
    'normalize_unicode_filenames': False,

    # Replacement characters for invalid filename characters
    'replace_invalid_characters_with': '_',

    # Replacements performed on input file before parsing.
    'input_filename_replacements': [
    ],

    # Replacements performed on files after the new name is generated.
    'output_filename_replacements': [
    ],

    # Replacements are performed on the full path used by move_files feature,
    # including the filename
    'move_files_fullpath_replacements': [
    ],

    # Move renamed files to directory?
    'move_files_enable': False,

    # Seperation confirmation of moving or copying renamed file?
    # If False, will move files when renaming.
    'move_files_confirmation': True,

    # Destination to move files to. Trailing slash is not necessary.
    # Use forward slashes, even on Windows. Realtive paths are realtive to
    # the existing file's path (not current working dir). A value of '.' will
    # not move the file anywhere.
    #
    # Use Python's string formatting to add dynamic paths. Available variables:
    # - %(seriesname)s
    # - %(seasonnumber)d
    # - %(issuenumbers)s (Note: this is a string, formatted with config
    #                       variable issue_single and joined with issue_separator)
    'move_files_destination': '.',

    # Patterns to parse input filenames with
    'filename_patterns': [
        # [group] Series - 01-02 [Etc]
        '''^\[.+?\][ ]? # group name
        (?P<seriesname>.*?)[ ]?[-_][ ]?          # show name, padding, spaces?
        (?P<issuenumberstart>\d+)              # first issue number
        ([-_]\d+)*                               # optional repeating issues
        [-_](?P<issuenumberend>\d+)            # last issue number
        [^\/]*$''',

        # [group] Series - 01 [Etc]
        '''^\[.+?\][ ]? # group name
        (?P<seriesname>.*) # show name
        [ ]?[-_][ ]?(?P<issuenumber>\d+)
        [^\/]*$''',

        # foo s01e23 s01e24 s01e25 *
        '''
        ^((?P<seriesname>.+?)[ \._\-])?          # show name
        [Ss](?P<seasonnumber>[0-9]+)             # s01
        [\.\- ]?                                 # separator
        [Ee](?P<issuenumberstart>[0-9]+)       # first e23
        ([\.\- ]+                                # separator
        [Ss](?P=seasonnumber)                    # s01
        [\.\- ]?                                 # separator
        [Ee][0-9]+)*                             # e24 etc (middle groups)
        ([\.\- ]+                                # separator
        [Ss](?P=seasonnumber)                    # last s01
        [\.\- ]?                                 # separator
        [Ee](?P<issuenumberend>[0-9]+))        # final issue number
        [^\/]*$''',

        # foo.s01e23e24*
        '''
        ^((?P<seriesname>.+?)[ \._\-])?          # show name
        [Ss](?P<seasonnumber>[0-9]+)             # s01
        [\.\- ]?                                 # separator
        [Ee](?P<issuenumberstart>[0-9]+)       # first e23
        ([\.\- ]?                                # separator
        [Ee][0-9]+)*                             # e24e25 etc
        [\.\- ]?[Ee](?P<issuenumberend>[0-9]+) # final issue num
        [^\/]*$''',

        # foo.1x23 1x24 1x25
        '''
        ^((?P<seriesname>.+?)[ \._\-])?          # show name
        (?P<seasonnumber>[0-9]+)                 # first season number (1)
        [xX](?P<issuenumberstart>[0-9]+)       # first issue (x23)
        ([ \._\-]+                               # separator
        (?P=seasonnumber)                        # more season numbers (1)
        [xX][0-9]+)*                             # more issue numbers (x24)
        ([ \._\-]+                               # separator
        (?P=seasonnumber)                        # last season number (1)
        [xX](?P<issuenumberend>[0-9]+))        # last issue number (x25)
        [^\/]*$''',

        # foo.1x23x24*
        '''
        ^((?P<seriesname>.+?)[ \._\-])?          # show name
        (?P<seasonnumber>[0-9]+)                 # 1
        [xX](?P<issuenumberstart>[0-9]+)       # first x23
        ([xX][0-9]+)*                            # x24x25 etc
        [xX](?P<issuenumberend>[0-9]+)         # final issue num
        [^\/]*$''',

        # foo.s01e23-24*
        '''
        ^((?P<seriesname>.+?)[ \._\-])?          # show name
        [Ss](?P<seasonnumber>[0-9]+)             # s01
        [\.\- ]?                                 # separator
        [Ee](?P<issuenumberstart>[0-9]+)       # first e23
        (                                        # -24 etc
             [\-]
             [Ee]?[0-9]+
        )*
             [\-]                                # separator
             (?P<issuenumberend>[0-9]+)        # final issue num
        [\.\- ]                                  # must have a separator (prevents s01e01-720p from being 720 issues)
        [^\/]*$''',

        # foo.1x23-24*
        '''
        ^((?P<seriesname>.+?)[ \._\-])?          # show name
        (?P<seasonnumber>[0-9]+)                 # 1
        [xX](?P<issuenumberstart>[0-9]+)       # first x23
        (                                        # -24 etc
             [\-][0-9]+
        )*
             [\-]                                # separator
             (?P<issuenumberend>[0-9]+)        # final issue num
        ([\.\- ].*                               # must have a separator (prevents 1x01-720p from being 720 issues)
        |
        $)''',

        # foo.[1x09-11]*
        '''^(?P<seriesname>.+?)[ \._\-]          # show name and padding
        \[                                       # [
            ?(?P<seasonnumber>[0-9]+)            # season
        [xX]                                     # x
            (?P<issuenumberstart>[0-9]+)       # issue
            (- [0-9]+)*
        -                                        # -
            (?P<issuenumberend>[0-9]+)         # issue
        \]                                       # \]
        [^\\/]*$''',

        # foo.s0101, foo.0201
        '''^(?P<seriesname>.+?)[ \._\-]
        [Ss](?P<seasonnumber>[0-9]{2})
        [\.\- ]?
        (?P<issuenumber>[0-9]{2})
        [^0-9]*$''',

        # foo.1x09*
        '''^((?P<seriesname>.+?)[ \._\-])?       # show name and padding
        \[?                                      # [ optional
        (?P<seasonnumber>[0-9]+)                 # season
        [xX]                                     # x
        (?P<issuenumber>[0-9]+)                # issue
        \]?                                      # ] optional
        [^\\/]*$''',

        # foo.s01.e01, foo.s01_e01
        '''^((?P<seriesname>.+?)[ \._\-])?
        [Ss](?P<seasonnumber>[0-9]+)[\.\- ]?
        [Ee]?(?P<issuenumber>[0-9]+)
        [^\\/]*$''',

        # foo.2010.01.02.etc
        '''
        ^((?P<seriesname>.+?)[ \._\-])?         # show name
        (?P<year>\d{4})                          # year
        [ \._\-]                                 # separator
        (?P<month>\d{2})                         # month
        [ \._\-]                                 # separator
        (?P<day>\d{2})                           # day
        [^\/]*$''',

        # Foo - S2 E 02 - etc
        '''^(?P<seriesname>.+?)[ ]?[ \._\-][ ]?
        [Ss](?P<seasonnumber>[0-9]+)[\.\- ]?
        [Ee]?[ ]?(?P<issuenumber>[0-9]+)
        [^\\/]*$''',

        # Series - issue 9999 [S 12 - Ep 131] - etc
        '''
        (?P<seriesname>.+)                       # Seriesname
        [ ]-[ ]                                  # -
        [Ee]pisode[ ]\d+                         # issue 1234 (ignored)
        [ ]
        \[                                       # [
        [sS][ ]?(?P<seasonnumber>\d+)            # s 12
        ([ ]|[ ]-[ ]|-)                          # space, or -
        ([eE]|[eE]p)[ ]?(?P<issuenumber>\d+)   # e or ep 12
        \]                                       # ]
        .*$                                      # rest of file
        ''',

        # foo.103*
        '''^(?P<seriesname>.+)[ \._\-]
        (?P<seasonnumber>[0-9]{1})
        (?P<issuenumber>[0-9]{2})
        [\._ -][^\\/]*$''',

        # foo.0103*
        '''^(?P<seriesname>.+)[ \._\-]
        (?P<seasonnumber>[0-9]{2})
        (?P<issuenumber>[0-9]{2,3})
        [\._ -][^\\/]*$''',

        # show.name.e123.abc
        '''^(?P<seriesname>.+?)                  # Series name
        [ \._\-]                                 # Padding
        [Ee](?P<issuenumber>[0-9]+)            # E123
        [\._ -][^\\/]*$                          # More padding, then anything
        ''',

    ],

    # Formats for renamed files. Variations for with/without issue,
    # and with/without season number.
    'filename_with_issue':
     '%(seriesname)s - [%(seasonno)02dx%(issue)s] - %(issuename)s%(ext)s',
    'filename_without_issue':
     '%(seriesname)s - [%(seasonno)02dx%(issue)s]%(ext)s',
     'filename_with_issue_no_season':
      '%(seriesname)s - [%(issue)s] - %(issuename)s%(ext)s',
     'filename_without_issue_no_season':
      '%(seriesname)s - [%(issue)s]%(ext)s',

    # Used to join multiple issue names together
    'multiiss_join_name_with': ', ',

    # Format for numbers (python string format), %02d does 2-digit
    # padding, %d will cause no padding
    'issue_single': '%02d',

    # String to join multiple number
    'issue_separator': '-',
}
