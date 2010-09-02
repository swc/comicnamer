#!/usr/bin/env python
#encoding:utf-8
#author:Samus
#project:comicnamer
#repository:http://github.com/dbr/comicnamer
#license:Creative Commons GNU GPL v2
# http://creativecommons.org/licenses/GPL/2.0/

"""Utilities for comicnamer, including filename parsing
Modified from http://github.com/dbr/tvnamer
"""

import datetime
import os
import re
import sys
import shutil
import logging
import platform

from comicvine_api import (comicvine_error, comicvine_seriesnotfound,
comicvine_issuenotfound, comicvine_attributenotfound, comicvine_userabort)

from unicode_helper import p

from config import Config
from comicnamer_exceptions import (InvalidPath, InvalidFilename,
SeriesNotFound, DataRetrievalError, IssueNotFound,
IssueNameNotFound, ConfigValueError, UserAbort)


def log():
    """Returns the logger for current file
    """
    return logging.getLogger(__name__)


def warn(text):
    """Displays message to sys.stdout
    """
    p(text, file = sys.stderr)


def getIssueName(comicvine_instance, issue):
    """Queries the comicvine_api.Comicvine instance for issue name and corrected
    series name.
    If series cannot be found, it will warn the user. If the issue is not
    found, it will use the corrected series name and not set an issue name.
    If the site is unreachable, it will warn the user. If the user aborts
    it will catch comicvine_api's user abort error and raise comicnamer's
    """
    try:
        series = comicvine_instance[issue.seriesname]
    except comicvine_error, errormsg:
        raise DataRetrievalError("Error contacting www.comicvine.com: %s" % errormsg)
    except comicvine_seriesnotfound:
        # No such series found.
        raise SeriesNotFound("Series %s not found on www.comicvine.com" % issue.seriesname)
    except comicvine_userabort, error:
        raise UserAbort(unicode(error))
    else:
        # Series was found, use corrected series name
        correctedSeriesName = series['seriesname']

    issnames = []
    for cissno in issue.issuenumbers:
        try:
            issueinfo = series[cissno]

        except comicvine_issuenotfound:
            raise IssueNotFound(
                "Issue %s of series %s could not be found" % (
                    cissno,
                    issue.seriesname))

        except comicvine_attributenotfound:
            raise IssueNameNotFound(
                "Could not find issue name for %s" % issue)
        else:
            issnames.append(issueinfo['issuename'])

    return correctedSeriesName, issnames


def _applyReplacements(cfile, replacements):
    """Applies custom replacements.

    Argument cfile is string.

    Argument replacements is a list of dicts, with keys "match",
    "replacement", and (optional) "is_regex"
    """
    for rep in replacements:
        if 'is_regex' in rep and rep['is_regex']:
            cfile = re.sub(rep['match'], rep['replacement'], cfile)
        else:
            cfile = cfile.replace(rep['match'], rep['replacement'])

    return cfile


def applyCustomInputReplacements(cfile):
    """Applies custom input filename replacements, wraps _applyReplacements
    """
    return _applyReplacements(cfile, Config['input_filename_replacements'])


def applyCustomOutputReplacements(cfile):
    """Applies custom output filename replacements, wraps _applyReplacements
    """
    return _applyReplacements(cfile, Config['output_filename_replacements'])


def applyCustomFullpathReplacements(cfile):
    """Applies custom replacements to full path, wraps _applyReplacements
    """
    return _applyReplacements(cfile, Config['move_files_fullpath_replacements'])


def cleanRegexedSeriesName(seriesname):
    """Cleans up series name by removing any . and _
    characters, along with any trailing hyphens.

    Is basically equivalent to replacing all _ and . with a
    space, but handles decimal numbers in string, for example:

    >>> cleanRegexedSeriesName("an.example.1.0.test")
    'an example 1.0 test'
    >>> cleanRegexedSeriesName("an_example_1.0_test")
    'an example 1.0 test'
    """
    seriesname = re.sub("(\D)[.](\D)", "\\1 \\2", seriesname)
    seriesname = re.sub("(\D)[.]", "\\1 ", seriesname)
    seriesname = re.sub("[.](\D)", " \\1", seriesname)
    seriesname = seriesname.replace("_", " ")
    seriesname = re.sub("-$", "", seriesname)
    return seriesname.strip()


class FileFinder(object):
    """Given a file, it will verify it exists. Given a folder it will descend
    one level into it and return a list of files, unless the recursive argument
    is True, in which case it finds all files contained within the path.

    The with_extension argument is a list of valid extensions, without leading
    spaces. If an empty list (or None) is supplied, no extension checking is
    performed.
    """

    def __init__(self, path, with_extension = None, recursive = False):
        self.path = path
        if with_extension is None:
            self.with_extension = []
        else:
            self.with_extension = with_extension
        self.recursive = recursive

    def findFiles(self):
        """Returns list of files found at path
        """
        if os.path.isfile(self.path):
            if self._checkExtension(self.path):
                return [os.path.abspath(self.path)]
            else:
                return []
        elif os.path.isdir(self.path):
            return self._findFilesInPath(self.path)
        else:
            raise InvalidPath("%s is not a valid file/directory" % self.path)

    def _checkExtension(self, fname):
        if len(self.with_extension) == 0:
            return True

        _, extension = os.path.splitext(fname)
        for cext in self.with_extension:
            cext = ".%s" % cext
            if extension == cext:
                return True
        else:
            return False

    def _findFilesInPath(self, startpath):
        """Finds files from startpath, could be called recursively
        """
        allfiles = []
        for subf in os.listdir(unicode(startpath)):
            if not self._checkExtension(subf):
                continue
            newpath = os.path.join(startpath, subf)
            newpath = os.path.abspath(newpath)
            if os.path.isfile(newpath):
                allfiles.append(newpath)
            else:
                if self.recursive:
                    allfiles.extend(self._findFilesInPath(newpath))
                #end if recursive
            #end if isfile
        #end for sf
        return allfiles


class FileParser(object):
    """Deals with parsing of filenames
    """

    def __init__(self, path):
        self.path = path
        self.compiled_regexs = []
        self._compileRegexs()

    def _compileRegexs(self):
        """Takes issue_patterns from config, compiles them all
        into self.compiled_regexs
        """
        for cpattern in Config['filename_patterns']:
            try:
                cregex = re.compile(cpattern, re.VERBOSE)
            except re.error, errormsg:
                warn("WARNING: Invalid issue_pattern, %s. %s" % (
                    errormsg, cregex.pattern))
            else:
                self.compiled_regexs.append(cregex)

    def parse(self):
        """Runs path via configured regex, extracting data from groups.
        Returns an IssueInfo instance containing extracted data.
        """
        _, filename = os.path.split(self.path)

        filename = applyCustomInputReplacements(filename)

        for cmatcher in self.compiled_regexs:
            match = cmatcher.match(filename)
            if match:
                namedgroups = match.groupdict().keys()

                if 'issuenumber1' in namedgroups:
                    # Multiple issues, have issuenumber1 or 2 etc
                    issnos = []
                    for cur in namedgroups:
                        issnomatch = re.match('issuenumber(\d+)', cur)
                        if issnomatch:
                            issnos.append(int(match.group(cur)))
                    issnos.sort()
                    issuenumbers = issnos

                elif 'issuenumberstart' in namedgroups:
                    # Multiple issues, regex specifies start and end number
                    start = int(match.group('issuenumberstart'))
                    end = int(match.group('issuenumberend'))
                    if start > end:
                        # Swap start and end
                        start, end = end, start
                    issuenumbers = range(start, end + 1)

                elif 'issuenumber' in namedgroups:
                    issuenumbers = [int(match.group('issuenumber')), ]

                elif 'year' in namedgroups or 'month' in namedgroups or 'day' in namedgroups:
                    if not all(['year' in namedgroups, 'month' in namedgroups, 'day' in namedgroups]):
                        raise ConfigValueError(
                            "Date-based regex must contain groups 'year', 'month' and 'day'")
                    match.group('year')

                    issuenumbers = [datetime.date(int(match.group('year')),
                                                    int(match.group('month')),
                                                    int(match.group('day')))]

                else:
                    raise ConfigValueError(
                        "Regex does not contain issue number group, should"
                        "contain issuenumber, issuenumber1-9, or"
                        "issuenumberstart and issuenumberend\n\nPattern"
                        "was:\n" + cmatcher.pattern)

                if 'seriesname' in namedgroups:
                    seriesname = match.group('seriesname')
                else:
                    raise ConfigValueError(
                        "Regex must contain seriesname. Pattern was:\n" + cmatcher.pattern)

                if seriesname != None:
                    seriesname = cleanRegexedSeriesName(seriesname)

                issue = IssueInfo(
                    seriesname = seriesname,
                    issuenumbers = issuenumbers,
                    filename = self.path)
                return issue
        else:
            raise InvalidFilename(self.path)


def formatIssueName(names, join_with):
    """Takes a list of issue names, formats them into a string.
    If two names are supplied, such as "Pilot (1)" and "Pilot (2)", the
    returned string will be "Pilot (1-2)"

    If two different issue names are found, such as "The first", and
    "Something else" it will return "The first, Something else"
    """
    if len(names) == 1:
        return names[0]

    found_names = []
    numbers = []
    for cname in names:
        number = re.match("(.*) \(([0-9]+)\)$", cname)
        if number:
            issname, issno = number.group(1), number.group(2)
            if len(found_names) > 0 and issname not in found_names:
                return join_with.join(names)
            found_names.append(issname)
            numbers.append(int(issno))
        else:
            # An issue didn't match
            return join_with.join(names)

    names = []
    start, end = min(numbers), max(numbers)
    names.append("%s (%d-%d)" % (found_names[0], start, end))
    return join_with.join(names)


def makeValidFilename(value, normalize_unicode = False, windows_safe = False, custom_blacklist = None, replace_with = "_"):
    """
    Takes a string and makes it into a valid filename.

    normalize_unicode replaces accented characters with ASCII equivalent, and
    removes characters that cannot be converted sensibly to ASCII.

    windows_safe forces Windows-safe filenames, regardless of current platform

    custom_blacklist specifies additional characters that will removed. This
    will not touch the extension separator:

        >>> makeValidFilename("T.est.cbr", custom_blacklist=".")
        'T_est.cbr'
    """

    if windows_safe:
        # Allow user to make Windows-safe filenames, if they so choose
        sysname = "Windows"
    else:
        sysname = platform.system()

    # If the filename starts with a . prepend it with an underscore, so it
    # doesn't become hidden.

    # This is done before calling splitext to handle filename of "."
    # splitext acts differently in python 2.5 and 2.6 - 2.5 returns ('', '.')
    # and 2.6 returns ('.', ''), so rather than special case '.', this
    # special-cases all files starting with "." equally (since dotfiles have)
    if value.startswith("."):
        value = "_" + value

    # Treat extension seperatly
    value, extension = os.path.splitext(value)

    # Remove any null bytes
    value = value.replace("\0", "")

    # Blacklist of characters
    if sysname == 'Darwin':
        # : is technically allowed, but Finder will treat it as / and will
        # generally cause weird behaviour, so treat it as invalid.
        blacklist = r"/:"
    elif sysname in ['Linux', 'FreeBSD']:
        blacklist = r"/"
    else:
        # platform.system docs say it could also return "Windows" or "Java".
        # Failsafe and use Windows sanitisation for Java, as it could be any
        # operating system.
        blacklist = r"\/:*?\"<>|"

    # Append custom blacklisted characters
    if custom_blacklist is not None:
        blacklist += custom_blacklist

    # Replace every blacklisted character with a underscore
    value = re.sub("[%s]" % re.escape(blacklist), replace_with, value)

    # Remove any trailing whitespace
    value = value.strip()

    # There are a bunch of filenames that are not allowed on Windows.
    # As with character blacklist, treat non Darwin/Linux platforms as Windows
    if sysname not in ['Darwin', 'Linux']:
        invalid_filenames = ["CON", "PRN", "AUX", "NUL", "COM1", "COM2",
        "COM3", "COM4", "COM5", "COM6", "COM7", "COM8", "COM9", "LPT1",
        "LPT2", "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9"]
        if value in invalid_filenames:
            value = "_" + value

    # Replace accented characters with ASCII equivalent
    if normalize_unicode:
        import unicodedata
        value = unicode(value) # cast data to unicode
        value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore')

    # Truncate filenames to valid/sane length.
    # NTFS is limited to 255 characters, HFS+ and EXT3 don't seem to have
    # limits, FAT32 is 254. I doubt anyone will take issue with losing that
    # one possible character, and files over 254 are pointlessly unweidly
    max_len = 254

    if len(value + extension) > max_len:
        if len(extension) > len(value):
            # Truncate extension instead of filename, no extension should be
            # this long..
            new_length = max_len - len(value)
            extension = extension[:new_length]
        else:
            new_length = max_len - len(extension)
            value = value[:new_length]

    return value + extension


def formatIssueNumbers(issuenumbers):
    """Format issue number(s) into string, using configured values
    """
    if len(issuenumbers) == 1:
        issno = Config['issue_single'] % issuenumbers[0]
    else:
        issno = Config['issue_separator'].join(
            Config['issue_single'] % x for x in issuenumbers)

    return issno

class IssueInfo(object):
    """Stores information (issue number, issue name), and contains
    logic to generate new name
    """

    def __init__(self,
        seriesname = None,
        issuenumbers= None,
        issuename = None,
        filename = None):

        self.seriesname = seriesname
        self.issuenumbers = issuenumbers
        self.issuename = issuename
        self.fullpath = filename

    def fullpath_get(self):
        return self._fullpath

    def fullpath_set(self, value):
        self._fullpath = value
        if value is None:
            self.filename, self.extension = None, None
        else:
            self.filepath, self.filename = os.path.split(value)
            self.filename, self.extension = os.path.splitext(self.filename)
            self.extension = self.extension.replace(".", "")

    fullpath = property(fullpath_get, fullpath_set)

    @property
    def fullfilename(self):
        return u"%s.%s" % (self.filename, self.extension)

    def generateFilename(self):
        """
        Uses the following config options:
        filename_with_issue # Filename when issue name is found
        filename_without_issue # Filename when no issue can be found
        issue_single # formatting for a single issue number
        issue_separator # used to join multiple issue numbers
        """
        # Format issue number into string, or a list
        issno = Config['issue_single'] % self.issuenumbers[0]

        # Data made available to config'd output file format
        if self.extension is None:
            prep_extension = ''
        else:
            prep_extension = '.%s' % self.extension

        issdata = {
            'seriesname': self.seriesname,
            'issue': issno,
            'issuename': self.issuename,
            'ext': prep_extension}

        if (self.issuename is None or (isinstance(self.issuename, list) and self.issuename[0] is None)):
            fname = Config['filename_without_issue'] % issdata
        else:
            if isinstance(self.issuename, list):
                issdata['issuename'] = formatIssueName(
                    self.issuename,
                    join_with = Config['multiiss_join_name_with']
                )

            fname = Config['filename_with_issue'] % issdata

        return makeValidFilename(
            fname,
            normalize_unicode = Config['normalize_unicode_filenames'],
            windows_safe = Config['windows_safe_filenames'],
            replace_with = Config['replace_invalid_characters_with'])

    def __repr__(self):
        return "<%s: %s>" % (
            self.__class__.__name__,
            self.generateFilename())


def same_partition(f1, f2):
    """Returns True if both files or directories are on the same partition
    """
    return os.stat(f1).st_dev == os.stat(f2).st_dev


def delete_file(fpath):
    raise NotImplementedError("delete_file not yet implimented")


class Renamer(object):
    """Deals with renaming of files
    """

    def __init__(self, filename):
        self.filename = os.path.abspath(filename)

    def newName(self, newName, force = False):
        """Renames a file, keeping the path the same.
        """
        filepath, filename = os.path.split(self.filename)
        filename, _ = os.path.splitext(filename)

        newpath = os.path.join(filepath, newName)

        if os.path.isfile(newpath):
            # If the destination exists, raise exception unless force is True
            if not force:
                raise OSError("File %s already exists, not forcefully renaming %s" % (
                    newpath, self.filename))

        os.rename(self.filename, newpath)
        self.filename = newpath

    def newPath(self, new_path, force = False, always_copy = False, always_move = False, create_dirs = True, getPathPreview = False):
        """Moves the file to a new path.

        If it is on the same partition, it will be moved (unless always_copy is True)
        If it is on a different partition, it will be copied.
        If the target file already exists, it will raise OSError unless force is True.
        """

        if always_copy and always_move:
            raise ValueError("Both always_copy and always_move cannot be specified")

        old_dir, old_filename = os.path.split(self.filename)

        # Join new filepath to old one (to handle realtive dirs)
        new_dir = os.path.abspath(os.path.join(old_dir, new_path))

        # Join new filename onto new filepath
        new_fullpath = os.path.join(new_dir, old_filename)

        if len(Config['move_files_fullpath_replacements']) > 0:
            p("Before custom full path replacements: %s" % (new_fullpath))
            new_fullpath = applyCustomFullpathReplacements(new_fullpath)
            new_dir = os.path.dirname(new_fullpath)

        p("New path: %s" % new_fullpath)

        if getPathPreview:
            return new_fullpath

        if create_dirs:
            p("Creating %s" % new_dir)
            try:
                os.makedirs(new_dir)
            except OSError, e:
                if e.errno != 17:
                    raise

        if os.path.isfile(new_fullpath):
            # If the destination exists, raise exception unless force is True
            if not force:
                raise OSError("File %s already exists, not forcefully moving %s" % (
                    new_fullpath, self.filename))

        if same_partition(self.filename, new_dir):
            if always_copy:
                # Same partition, but forced to copy
                p("copy %s to %s" % (self.filename, new_fullpath))
                shutil.copyfile(self.filename, new_fullpath)
            else:
                # Same partition, just rename the file to move it
                p("move %s to %s" % (self.filename, new_fullpath))
                os.rename(self.filename, new_fullpath)
        else:
            # File is on different partition (different disc), copy it
            p("copy %s to %s" % (self.filename, new_fullpath))
            shutil.copyfile(self.filename, new_fullpath)
            if always_move:
                # Forced to move file, we just trash old file
                p("Deleting %s" % (self.filename))
                delete_file(self.filename)

        self.filename = new_fullpath
