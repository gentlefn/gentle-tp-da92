#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Gentle Technology Preview (da92de4118f6fa91) - Core Module

Unique Gentle identifier for this Gentle Technology Preview:
    da92de4118f6fa915b6bdd73f090ad57dc153082600855e5c7a85e8fe054c5a1

The functionality of the Gentle Core is the result of years of development and
careful design.  The explicit goal of Gentle is to drastically simplify
computer programming and user interfaces.
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

import glob
import os
import sys


class Gentle(object):

    # Locations of the content and pointer databases:
    USER_HOME = os.path.expanduser("~")
    DEFAULT_DATA_DIR = os.path.join(USER_HOME, ".gentle_da92de4118f6fa91")
    ENVIRON_DATA_DIR_KEY = "GENTLE_DA92DE41_DIR"

    def __init__(self, data_dir=None):
        super(Gentle, self).__init__()

        if data_dir is None:
            data_dir = os.environ.get(self.ENVIRON_DATA_DIR_KEY, self.DEFAULT_DATA_DIR)
        self.data_dir = os.path.abspath(data_dir)
        self.content_dir = os.path.join(self.data_dir, "content_db")
        self.pointer_dir = os.path.join(self.data_dir, "pointer_db")

        # Make sure the database directories exist.
        for directory in (self.data_dir, self.content_dir, self.pointer_dir):
            if not os.path.exists(directory):
                os.mkdir(directory, 0700)

    def getdir(self):
        return self.data_dir

    @staticmethod
    def sha256(byte_string):
        """
        Return the SHA-256 hash value of the given byte_string in hexadecimal
        representation.

        Used for entering content into the content database.
        """
        from hashlib import sha256
        sha256_object = sha256()
        sha256_object.update(byte_string)
        return sha256_object.hexdigest()

    sha = sha256

    @staticmethod
    def random():
        """
        Return a random-generated 256-bit number in hexadecimal representation.

        Useful for creating pointers in the pointer database.
        """
        return os.urandom(256 / 8).encode("hex")

    def full(self, identifier):
        """
        Return the full version of a possibly abbreviated identifier.

        The identifier must match the beginning of the key of exactly one entry in
        either one database.
        """
        contents = glob.glob(os.path.join(self.content_dir, identifier) + "*")
        pointers = glob.glob(os.path.join(self.pointer_dir, identifier) + "*")
        matches = contents + pointers
        if len(matches) == 0:
            raise Exception("neither content nor pointer found for identifier '%s'" % identifier)
        if len(matches) > 1:
            raise Exception("multiple identifiers found starting with '%s'" % identifier)
        directory, identifier = os.path.split(matches[0])
        return (directory, identifier)

    def put(self, a, b=None):
        """
        Enter content into the content database, or change a pointer in the pointer
        database.

        Example:
        >>> gentle.put("content")
        'ed7002b439e9ac845f22357d822bac1444730fbdb6016d3ec9432297b9ec9f73'
        >>> gentle.random()
        '80834436d97b9327eb8138c907f57c205b3d7ba9a962d7cf72849993e909c299'
        >>> gentle.put("80834436d97b9327eb8138c907f57c205b3d7ba9a962d7cf72849993e909c299", "ed7002")
        '80834436d97b9327eb8138c907f57c205b3d7ba9a962d7cf72849993e909c299'

        In the first usage, return the SHA-256 hash value of the entered content.
        """
        if b is None:  # write new content
            byte_string = a
            hash_value = self.sha256(byte_string)
            filename = os.path.join(self.content_dir, hash_value)
            if not os.path.exists(filename):
                # Git also gives pre-existing immutable content priority for a reason.
                with os.fdopen(os.open(filename, os.O_CREAT | os.O_WRONLY, 0400), "wb") as f:
                    f.write(byte_string)
            return hash_value
        else:  # write new pointer or change it
            pointer_key, identifier = a, b
            directory, hash_value = self.full(identifier)
            if directory != self.content_dir:
                raise TypeError("second argument must be a content hash value")
            filename = os.path.join(self.pointer_dir, pointer_key)
            with os.fdopen(os.open(filename, os.O_CREAT | os.O_WRONLY, 0600), "wb") as f:
                f.write(hash_value)
            # Returning the pointer key enables (assuming the 'g' alias):
            #   Python: content_ptr = g.put(g.random(), g.put(content))
            #   Bash:   g put $(g random) $(g put < content) > content.ptr
            return pointer_key

    __setitem__ = put

    def get(self, identifier):
        """
        Get content from the content database, or follow a pointer from the
        pointer database.

        Example:
        >>> gentle.get("808344")
        'ed7002b439e9ac845f22357d822bac1444730fbdb6016d3ec9432297b9ec9f73'
        >>> gentle.get("ed7002")
        'content'

        The identifier must match the beginning of the key of exactly one entry in
        either one database.
        """
        directory, identifier = self.full(identifier)
        filename = os.path.join(directory, identifier)
        # This 'if' statement is not strictly necessary, but it illustrates the
        # nature of the returned value:
        if directory == self.content_dir:
            byte_string = open(filename, "rb").read()
            return byte_string
        else:
            hash_value = open(filename, "rb").read()
            return hash_value

    __getitem__ = get

    def rm(self, *identifiers):
        """
        Remove content from the content database or from the pointer database.

        The identifier must match the beginning of the key of exactly one entry in
        either one database.
        """
        for identifier in identifiers:
            directory, identifier = self.full(identifier)
            filename = os.path.join(directory, identifier)
            os.remove(filename)

    def type_(self, identifier):
        try:
            directory, identifier = self.full(identifier)
            if directory == self.content_dir:
                return "content"
            elif directory == self.pointer_dir:
                return "pointer"
        except:
            pass
        return None

    def _cli_get_method(self, method_name):
        try:
            m = getattr(self, method_name)
        except:
            # e.g. function_name == "import" -> def import_(...): ...
            m = getattr(self, method_name + "_")
        return m, getattr(m, "__func__", m)

    def _cli(self, method_name, *args):
        """
        Command line interface.
        """
        m, f = self._cli_get_method(method_name)
        if f in (Gentle.sha256, Gentle.put.__func__) and len(args) == 0:
            byte_string = sys.stdin.read()
            print m(byte_string)
            return
        elif f == Gentle.get.__func__:
            directory, identifier = self.full(args[0])
            if directory == self.content_dir:
                byte_string = m(*args)
                sys.stdout.write(byte_string)
                return
        elif f == self.full.__func__:
            # On the command line, I simply want to expand an abbreviation:
            print m(*args)[1]
            return
        result = m(*args)
        if result is not None:
            print result


def main(argv):
    """
    Command line interface.
    """
    gentle = Gentle()
    return gentle._cli(*argv[1:])

if __name__ == "__main__":
    main(sys.argv)
