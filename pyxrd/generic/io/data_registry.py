# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import os
from pkg_resources import resource_filename # @UnresolvedImport

from pyxrd.generic.exceptions import AlreadyRegistered, NotRegistered

class DataRegistry(object):
    """
        Class for registering data directories and files so they're
        not hard-coded everywhere.
    """

    __data_directories = None
    __data_files = None
    _base_dir = None

    def __init__(self, dirs=[], files=[], *args, **kwargs):
        super(DataRegistry, self).__init__(*args, **kwargs)
        self.__data_directories = {}
        self.__data_files = {}
        for name, path, parent in dirs:
            self.register_data_directory(name, path, parent=parent)

        for name, path, parent in files:
            self.register_data_file(name, path, parent=parent)

    def __parse_parent(self, path, parent=None):
        # Adds parent path:
        if parent is not None:
            if parent is not None:
                try:
                    path = os.path.join(self.__data_directories[parent], path)
                except KeyError:
                    raise NotRegistered, "The data directory named '%s' was not found in the registry" % parent
        elif path.startswith("./"):
            path = resource_filename("pyxrd.data", path)
        return path

    def register_data_file(self, name, path, parent=None):
        """
            Registers a data file at 'path' called 'name'.
            If this file is inside a registered data directory, you
            can use a relative path by setting the 'parent' keyword argument
            to the name of the parent data-directory. The parent path
            will then be appended to the file's path. Paths are considered to be
            relative to data package.
            
            Note: names are always made full-caps!
            
            If you try to re-register an existing data file, an AlreadyRegistered
            exception will be raised. Similarly if you pass in an unregistered
            parent directory name, NotRegistered will be raised.
        """
        name = name.upper()
        if not name in self.__data_files:
            path = self.__parse_parent(path, parent=parent)
            self.__data_files[name] = path
        else:
            raise AlreadyRegistered, "the data file named '%s' was already registered" % name

    def register_data_directory(self, name, path, parent=None):
        """
            Registers a data directory at 'path' called 'name'.
            If this is a sub-directory of another registered data directory, you
            can use a relative path by setting the 'parent' keyword argument
            to the name of the parent data-directory. The parent path
            will then be appended to the child's path. Paths are considered to be
            relative to data package.
            
            Note: names are always made full-caps!
            
            If you try to re-register an existing data directory, an AlreadyRegistered
            exception will be raised. Similarly if you pass in an unregistered
            parent directory name, NotRegistered will be raised.
        """
        name = name.upper()
        if not name in self.__data_directories:
            path = self.__parse_parent(path, parent=parent)
            self.__data_directories[name] = path
            try: # Try to create this path:
                os.makedirs(path)
            except OSError:
                pass
        else:
            raise AlreadyRegistered, "The data directory named '%s' was already registered" % name

    def get_directory_path(self, name):
        """
            Gets the absolute path to a data directory named 'name'
        """
        try:
            path = self.__data_directories[name]
            if not os.path.isdir(path):
                return path
            else:
                return path
        except KeyError:
            raise NotRegistered, "The data directory named '%s' was not found in the registry" % name

    def get_all_directories(self):
        """
            Returns a generator looping over all directories in the registry,
            excluding the project path.
        """
        for path in self.__data_directories.values():
            yield path

    def get_file_path(self, name):
        """
            Gets the absolute path to a data file named 'name'
        """
        try:
            return self.__data_files[name]
        except KeyError:
            raise NotRegistered, "The data file named '%s' was not found in the registry" % name

    def get_all_files(self):
        """
            Returns a generator looping over all directories in the registry,
            excluding the project path.
        """
        for path in self.__data_directories.values():
            yield resource_filename("pyxrd.data", path)

    pass # end of class
