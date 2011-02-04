#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Gentle TP-DA92 - Debugging Wrapper Data Store Module.
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

from   hashlib import sha256

from   . import data_store_interfaces
from   .utilities import *


class _LoggerWrapper(object):

    def __init__(self, logger, prefix):
        self.logger = logger
        self.prefix = prefix

    def __call__(self, msg):
        self.logger.write("%s %s\n" % (self.prefix, msg))


class _GentleDB(data_store_interfaces._GentleDB):

    def __init__(self, db):
        super(_GentleDB, self).__init__()
        self.db = db

    def __getitem__(self, identifier):
        self.log("GET << %r" % identifier)
        content = self.db[identifier]
        self.log("GET >> ok: (len) %u" % len(content))
        return content

    def __delitem__(self, identifier):
        self.log("DEL << %r" % identifier)
        validate_identifier_format(identifier)
        del self.db[identifier]
        self.log("DEL >> ok")

    def find(self, partial_identifier=""):
        self.log("FIND << %r" % partial_identifier)
        identifiers = self.db.find(partial_identifier)
        self.log("FIND >> ok: (len) %u" % len(identifiers))
        return identifiers

    def __contains__(self, identifier):
        self.log("CONTAINS << %r" % identifier)
        result = identifier in self.db
        self.log("CONTAINS >> ok: %r" % result)
        return result


class _GentleContentDB(data_store_interfaces._GentleContentDB, _GentleDB):

    def __init__(self, db, logfile):
        super(_GentleContentDB, self).__init__(db)
        self.log = _LoggerWrapper(logfile, "C:")
        self.log("INIT >> ok")

    def __add__(self, byte_string):
        self.log("ADD << (len) %u" % len(byte_string))
        content_identifier = self.db + byte_string
        self.log("ADD >> ok: %r" % content_identifier)
        return content_identifier


class _GentlePointerDB(data_store_interfaces._GentlePointerDB, _GentleDB):

    def __init__(self, db, logfile):
        super(_GentlePointerDB, self).__init__(db)
        self.log = _LoggerWrapper(logfile, "P:")
        self.log("INIT >> ok")

    def __setitem__(self, pointer_identifier, content_identifier):
        self.log("SET << %r %r" % (pointer_identifier, content_identifier))
        validate_identifier_format(pointer_identifier)
        validate_identifier_format(content_identifier)
        self.db[pointer_identifier] = content_identifier
        self.log("SET >> ok")
        return pointer_identifier


class GentleDataStore(data_store_interfaces.GentleDataStore):

    def __init__(self, data_store, logfile):
        super(GentleDataStore, self).__init__()
        self.content_db = _GentleContentDB(data_store.content_db, logfile)
        self.pointer_db = _GentlePointerDB(data_store.pointer_db, logfile)
