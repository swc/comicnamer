#!/usr/bin/env python
#encoding:utf-8
#author:Samus
#project:comicnamer
#license:Creative Commons GNU GPL v2
# http://creativecommons.org/licenses/GPL/2.0/

"""Exceptions used through-out comicnamer
Modified from http://github.com/dbr/tvnamer
"""


class BaseComicnamerException(Exception):
    """Base exception all comicnamers exceptions inherit from
    """
    pass


class InvalidPath(BaseComicnamerException):
    """Raised when an argument is a non-existent file or directory path
    """
    pass


class NoValidFilesFoundError(BaseComicnamerException):
    """Raised when no valid files are found. Effectively exits tvnamer
    """
    pass


class InvalidFilename(BaseComicnamerException):
    """Raised when a file is parsed, but no issue info can be found
    """
    pass


class UserAbort(BaseComicnamerException):
    """Base exception for config errors
    """
    pass


class BaseConfigError(BaseComicnamerException):
    """Base exception for config errors
    """
    pass


class ConfigValueError(BaseConfigError):
    """Raised if the config file is malformed or unreadable
    """
    pass


class DataRetrievalError(BaseComicnamerException):
    """Raised when an error (such as a network problem) prevents comicnamer
    from being able to retrieve data such as issue name
    """


class SeriesNotFound(DataRetrievalError):
    """Raised when a series cannot be found
    """
    pass


class IssueNotFound(DataRetrievalError):
    """Raised when issue cannot be found
    """
    pass


class IssueNameNotFound(DataRetrievalError):
    """Raised when the name of the issue cannot be found
    """
    pass
