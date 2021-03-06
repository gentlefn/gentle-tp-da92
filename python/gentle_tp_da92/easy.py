#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Gentle TP-DA92 - The Easy Module.

Provides simplified access to a Gentle TP-DA92 data store from Python.  This
module is suitable for interactive usage.  Examples:

    >>> from gentle_tp_da92 import *
    >>> g = easy.Gentle()
    >>> g.getdir()
    '/home/user/.gentle_tp_da92_default_data_store'

It is recommended to use this module in applications, instead of directly using
the data store implementation modules.
"""
# Copyright (C) 2010, 2011  Felix Rabe
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this program.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import print_function

from   functools import partial
import os
import sys

from   .data_store_interfaces import GentleDataStore
from   .utilities import *

isvalid = is_identifier_format_valid
rnd = random


class _InitSimplifiers(object):
    """
    Simplifies initialization arguments of the GentleDataStore class based on
    the data store module in question.  Do not use this class in application
    code.

    Usage:
    >>> _init_simplifiers = _InitSimplifiers()
    >>> from gentle_tp_da92 import fs_based
    >>> (a, k) = _init_simplifiers[fs_based]()
    >>> g = fs_based
    """

    def __getitem__(self, module):
        # Get the module's name:
        name = module.__name__

        # Get the corresponding method name:
        name = "simplify__" + name.replace(".", "__")

        # If such a method exists, return it, or else return _passthrough:
        if hasattr(self, name):
            return partial(getattr(self, name), module)
        else:
            return self._passthrough

    @staticmethod
    def _passthrough(*a, **k):
        return (a, k)

    ## SIMPLIFICATION FOR gentle_tp_da92.fs_based ##

    USER_HOME = os.path.expanduser("~")
    FS_DEFAULT_DIRECTORY = os.path.join(USER_HOME, ".gentle_tp_da92_default_datastore")
    FS_DEFAULT_ENVIRON_KEY = "GENTLE_TP_DA92_DIR"

    @classmethod
    def simplify__gentle_tp_da92__fs_based(cls, fs_based, directory=True,
                                           environ_key=True, *a, **k):
        """
        Convert arguments to be passed to fs_based.GentleDataStore().
        """
        # 'directory' is 'None' only if 'None' has been specified explicitly:
        if directory is None:  # bypass environment variables and just use default dir
            directory = cls.FS_DEFAULT_DIRECTORY
        if directory is True:  # i.e. not specified, use environment variable if set
            directory = cls.FS_DEFAULT_DIRECTORY
            # 'environ_key' is 'None' only if 'None' has been specified explicitly:
            if environ_key is not None:
                if environ_key is True:  # i.e. not specified
                    environ_key = cls.FS_DEFAULT_ENVIRON_KEY
                directory = os.environ.get(environ_key, directory)
        directory = os.path.abspath(directory)
        k["mkdir"] = k.get("mkdir", True)  # default to True instead of to False
        return ((directory,) + a, k)


_init_simplifiers = _InitSimplifiers()


class _GentleEasyDataStoreWrapper(object):
    """
    Simplifies the usage of a GentleDataStore by combining the methods of the
    content and pointer databases.  Also, the methods of this class accept
    partial identifiers where the GentleDB's don't.

    Use the Gentle() factory function in this module to create instances of this
    class.
    """

    def __init__(self, gentle_data_store):
        self.ds = self.data_store = gentle_data_store
        self.c  = self.content_db = self.ds.content_db
        self.p  = self.pointer_db = self.ds.pointer_db

    def find(self, partial_identifier=""):
        """
        Find identifiers in both databases starting with partial_identifier.

        Return an unsorted list of all identifiers found.
        """
        content_identifiers = self.c.find(partial_identifier)
        pointer_identifiers = self.p.find(partial_identifier)
        all_identifiers = content_identifiers + pointer_identifiers
        return all_identifiers

    def __getitem__(self, identifier):
        """
        Get an item from either database.

        The given identifier may be a partial identifier.

        Return the content of the found item as a string if exactly one item is
        found whose identifier starts with the given identifier, otherwise
        return a list of the identifiers that start with the given identifier.
        """
        content_identifiers = self.c.find(identifier)
        pointer_identifiers = self.p.find(identifier)
        all_identifiers = content_identifiers + pointer_identifiers
        if len(all_identifiers) != 1:
            return all_identifiers  # a list
        if content_identifiers:
            return self.c[content_identifiers[0]]  # a string
        else:
            return self.p[pointer_identifiers[0]]  # a string

    @staticmethod
    def __find_one(gentle_db, identifier):
        if is_identifier_format_valid(identifier):
            return identifier
        identifiers = gentle_db.find(identifier)
        if len(identifiers) != 1:
            raise InvalidIdentifierException(identifier)
        return identifiers[0]

    def __setitem__(self, pointer_identifier, content_identifier):
        pointer_identifier = self.__find_one(self.p, pointer_identifier)
        content_identifier = self.__find_one(self.c, content_identifier)
        self.p[pointer_identifier] = content_identifier

    def __add__(self, content):
        return self.c + content

    def __delitem__(self, identifier):
        """
        Remove an item from either database.

        The given identifier may be a partial identifier.  In that case, there
        must be exactly one identifier in both databases combined that starts
        with the given identifier.
        """
        content_identifiers = self.c.find(identifier)
        pointer_identifiers = self.p.find(identifier)
        all_identifiers = content_identifiers + pointer_identifiers
        if len(all_identifiers) != 1:
            raise InvalidIdentifierException(identifier)
        if content_identifiers:
            del self.c[content_identifiers[0]]
        else:
            del self.p[pointer_identifiers[0]]

    def __contains__(self, identifier):
        """
        Return True if either database contains content for the specified
        identifier, and False otherwise.

        The given identifier may be a partial identifier.  In that case, return
        True if either database contains content for some identifier starting
        with the given identifier.
        """
        # Look up the identifier in the pointer database first, as the pointer
        # database is:
        #   1. smaller, and:
        #   2. more likely to be the target of the enquiry.
        pointer_identifiers = self.p.find(identifier)
        if pointer_identifiers: return True
        content_identifiers = self.c.find(identifier)
        if content_identifiers: return True
        return False


def Gentle(implementation="gentle_tp_da92.fs_based", *a, **k):
    """
    Factory function that returns a Gentle TP-DA92 data store object.

    The user may provide an implementation module as the first argument, either
    a string or a module.  It defaults to gentle_tp_da92.fs_based.
    """
    if isinstance(implementation, basestring):
        __import__(implementation)
        implementation = sys.modules[implementation]

    if not isinstance(implementation, GentleDataStore):  # then make it one
        # Simplify arguments based on the implementation_module:
        a, k = _init_simplifiers[implementation](*a, **k)
        implementation = implementation.GentleDataStore(*a, **k)
    gentle = _GentleEasyDataStoreWrapper(implementation)  # wrap it
    return gentle
