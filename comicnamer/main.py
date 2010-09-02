#!/usr/bin/env python
#encoding:utf-8
#author:Samus
#project:comicnamer
#license:Creative Commons GNU GPL v2
# http://creativecommons.org/licenses/GPL/2.0/

"""Main comicnamer utility functionality
Modified from http://github.com/dbr/tvnamer
"""

import os
import logging

try:
    import readline
except ImportError:
    pass

import simplejson as json
from comicvine_api import Comicvine

import cliarg_parser
from config_defaults import defaults

from unicode_helper import p
from utils import (Config, FileFinder, FileParser, Renamer, warn,
getIssueName, applyCustomInputReplacements, applyCustomOutputReplacements,
formatIssueNumbers, makeValidFilename)

from comicnamer_exceptions import (SeriesNotFound, IssueNotFound,
IssueNameNotFound, UserAbort, InvalidPath, NoValidFilesFoundError,
InvalidFilename, DataRetrievalError)


def log():
    """Returns the logger for current file
    """
    return logging.getLogger(__name__)


def getDestinationFolder(issue):
    """Constructs the location to move/copy the file
    """

    # Calls makeValidFilename on series name, as it must valid for a filename
    destdir = Config['move_files_destination'] % {
        'seriesname': makeValidFilename(issue.seriesname),
        'issuenumbers': makeValidFilename(formatIssueNumbers(issue.issuenumbers))
    }
    return destdir


def doRenameFile(cnamer, newName):
    """Renames the file. cnamer should be Renamer instance,
    newName should be string containing new filename.
    """
    try:
        cnamer.newName(newName)
    except OSError, e:
        warn(unicode(e))


def doMoveFile(cnamer, destDir, getPathPreview = False):
    """Moves file to destDir"""
    if not Config['move_files_enable']:
        raise ValueError("move_files feature is disabled but doMoveFile was called")

    if Config['move_files_destination'] is None:
        raise ValueError("Config value for move_files_destination cannot be None if move_files_enabled is True")

    try:
        return cnamer.newPath(destDir, getPathPreview = getPathPreview)
    except OSError, e:
        warn(unicode(e))


def confirm(question, options, default = "y"):
    """Takes a question (string), list of options and a default value (used
    when user simply hits enter).
    Asks until valid option is entered.
    """
    # Highlight default option with [ ]
    options_str = []
    for x in options:
        if x == default:
            x = "[%s]" % x
        if x != '':
            options_str.append(x)
    options_str = "/".join(options_str)

    while True:
        p(question)
        p("(%s) " % (options_str), end="")
        try:
            ans = raw_input().strip()
        except KeyboardInterrupt, errormsg:
            p("\n", errormsg)
            raise UserAbort(errormsg)

        if ans in options:
            return ans
        elif ans == '':
            return default


def processFile(comicvine_instance, issue):
    """Gets issue name, prompts user for input
    """
    p("#" * 20)
    p("# Processing file: %s" % issue.fullfilename)

    if len(Config['input_filename_replacements']) > 0:
        replaced = applyCustomInputReplacements(issue.fullfilename)
        p("# With custom replacements: %s" % (replaced))

    p("# Detected series: %s (issue: %s)" % (
        issue.seriesname,
        ", ".join([str(x) for x in issue.issuenumbers])))

    try:
        correctedSeriesName, issName = getIssueName(comicvine_instance, issue)
    except (DataRetrievalError, SeriesNotFound), errormsg:
        if Config['always_rename'] and Config['skip_file_on_error'] is True:
            warn("Skipping file due to error: %s" % errormsg)
            return
        else:
            warn(errormsg)
    except (IssueNotFound, IssueNameNotFound), errormsg:
        # Series was found, so use corrected series name
        if Config['always_rename'] and Config['skip_file_on_error'] is True:
            warn("Skipping file due to error: %s" % errormsg)
            return

        warn(errormsg)
        issue.seriesname = correctedSeriesName
    else:
        issue.seriesname = correctedSeriesName
        issue.issuename = issName

    cnamer = Renamer(issue.fullpath)
    newName = issue.generateFilename()

    p("#" * 20)
    p("Old filename: %s" % issue.fullfilename)

    if len(Config['output_filename_replacements']):
        p("Before custom output replacements: %s" % (newName))
        # Only apply to filename, not extension
        newName, newExt = os.path.splitext(newName)
        newName = applyCustomOutputReplacements(newName)
        newName = newName + newExt

    p("New filename: %s" % newName)

    if Config['always_rename']:
        doRenameFile(cnamer, newName)
        if Config['move_files_enable']:
            doMoveFile(cnamer = cnamer, destDir = getDestinationFolder(issue))
        return

    ans = confirm("Rename?", options = ['y', 'n', 'a', 'q'], default = 'y')

    shouldRename = False
    if ans == "a":
        p("Always renaming")
        Config['always_rename'] = True
        shouldRename = True
    elif ans == "q":
        p("Quitting")
        raise UserAbort("User exited with q")
    elif ans == "y":
        p("Renaming")
        shouldRename = True
    elif ans == "n":
        p("Skipping")
    else:
        p("Invalid input, skipping")

    if shouldRename:
        doRenameFile(cnamer, newName)

        if Config['move_files_enable']:
            newPath = getDestinationFolder(issue)
            previewPath = doMoveFile(cnamer = cnamer, destDir = newPath, getPathPreview = True)

            if Config['move_files_confirmation']:
                ans = confirm("Move file?", options = ['y', 'n', 'q'], default = 'y')
            else:
                ans = 'y'

            if ans == 'y':
                p("Moving file")
                doMoveFile(cnamer, newPath)
            elif ans == 'q':
                p("Quitting")
                raise UserAbort("user exited with q")


def findFiles(paths):
    """Takes an array of paths, returns all files found
    """
    valid_files = []

    for cfile in paths:
        cur = FileFinder(
            cfile,
            with_extension = Config['valid_extensions'],
            recursive = Config['recursive'])

        try:
            valid_files.extend(cur.findFiles())
        except InvalidPath:
            warn("Invalid path: %s" % cfile)

    if len(valid_files) == 0:
        raise NoValidFilesFoundError()

    # Remove duplicate files (all paths from FileFinder are absolute)
    valid_files = list(set(valid_files))

    return valid_files


def comicnamer(paths):
    """Main comicnamer function, takes an array of paths, does stuff.
    """
    # Warn about move_files function
    if Config['move_files_enable']:
        import warnings
        warnings.warn("The move_files feature is still under development. "
            "Be very careful with it.\n"
            "It has not been heavily tested, and is not recommended for "
            "general use yet.")

    p("#" * 20)
    p("# Starting comicnamer")

    issues_found = []

    for cfile in findFiles(paths):
        cfile = cfile.decode("utf-8")
        parser = FileParser(cfile)
        try:
            issue = parser.parse()
        except InvalidFilename:
            warn("Invalid filename %s" % cfile)
        else:
            issues_found.append(issue)

    if len(issues_found) == 0:
        raise NoValidFilesFoundError()

    p("# Found %d issue" % len(issues_found) + ("s" * (len(issues_found) > 1)))

    # Sort issues by series name and issue number
    issues_found.sort(key = lambda x: (x.seriesname, x.issuenumbers))

    comicvine_instance = Comicvine(
        interactive=not Config['select_first'])

    for issue in issues_found:
        processFile(comicvine_instance, issue)
        p('')

    p("#" * 20)
    p("# Done")


def main():
    """Parses command line arguments, displays errors from comicnamer in terminal
    """
    opter = cliarg_parser.getCommandlineParser(defaults)

    opts, args = opter.parse_args()

    if opts.verbose:
        logging.basicConfig(
            level = logging.DEBUG,
            format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    else:
        logging.basicConfig()

    # If a config is specified, load it, update the defaults using the loaded
    # values, then reparse the options with the updated defaults.
    default_configuration = os.path.expanduser("~/.comicnamer.json")

    if opts.loadconfig is not None:
        # Command line overrides loading ~/.comicnamer.json
        configToLoad = opts.loadconfig
    elif os.path.isfile(default_configuration):
        # No --config arg, so load default config if it exists
        configToLoad = default_configuration
    else:
        # No arg, nothing at default config location, don't load anything
        configToLoad = None

    if configToLoad is not None:
        p("Loading config: %s" % (configToLoad))
        try:
            loadedConfig = json.load(open(configToLoad))
        except ValueError, e:
            p("Error loading config: %s" % e)
            opter.exit(1)
        else:
            # Config loaded, update optparser's defaults and reparse
            defaults.update(loadedConfig)
            opter = cliarg_parser.getCommandlineParser(defaults)
            opts, args = opter.parse_args()

    # Save config argument
    if opts.saveconfig is not None:
        p("Saving config: %s" % (opts.saveconfig))
        configToSave = dict(opts.__dict__)
        del configToSave['saveconfig']
        del configToSave['loadconfig']
        del configToSave['showconfig']
        json.dump(
            configToSave,
            open(opts.saveconfig, "w+"),
            sort_keys=True,
            indent=4)

        opter.exit(0)

    # Series config argument
    if opts.showconfig:
        for k, v in opts.__dict__.items():
            p(k, "=", str(v))
        return

    # Process values
    if opts.batch:
        opts.select_first = True
        opts.always_rename = True

    # Update global config object
    Config.update(opts.__dict__)

    if len(args) == 0:
        opter.error("No filenames or directories supplied")

    try:
        comicnamer(paths = sorted(args))
    except NoValidFilesFoundError:
        opter.error("No valid files were supplied")
    except UserAbort, errormsg:
        opter.error(errormsg)

if __name__ == '__main__':
    main()
