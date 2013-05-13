# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.  

from generic.exceptions import AlreadyRegistered, NotRegistered

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
        self._base_dir = ""
        for name, path, parent in dirs:
            self.register_data_directory(name, path, parent=parent)
            
        for name, path, parent in files:
            self.register_data_file(name, path, parent=parent)
      
    def __parse_parent(self, path, parent=None):
        #Adds parent path:
        if parent!=None:
            if parent in self.__data_directories: 
                path = "%s/%s" % (self.__data_directories[parent], path)
            else:
                from generic.exceptions import NotRegistered
                raise NotRegistered, "the data directory named '%s' was not found in the registry" % name
        return path
       
    def register_data_file(self, name, path, parent=None):
        """
            Registers a data file at 'path' called 'name'.
            If this file is inside a registered data directory, you
            can use a relative path by setting the 'parent' keyword argument
            to the name of the parent data-directory. The parent path
            will then be appended to the file's path. If parent is set to None
            (the default) and the path does not start with a '/', the file's
            path is considered to be relative to the base directory.
            
            Note: names are always made full-caps!
            
            If you try to re-register an existing data file, an AlreadyRegistered
            exception will be raised. Similarily if you pass in an unregistered
            parent directory name, NotRegistered will be raised.
        """
        name = name.upper()
        if not name in self.__data_files:
            import sys
            
            path = self.__parse_parent(path, parent=parent)
            
            self.__data_files[name] = path
        else:
            from generic.exceptions import AlreadyRegistered
            raise AlreadyRegistered, "the data file named '%s' was already registered" % name
       
    def __register_data_directory(self, name, path, parent=None):
        name = name.upper()
        if not name in self.__data_directories:
            import sys
            
            path = self.__parse_parent(path, parent=parent)
                    
            #Check if this is the BASE DIR or not:
            if name=="BASE":
                self._base_dir = path
            else:
                self.__data_directories[name] = path
        else:
            from generic.exceptions import AlreadyRegistered
            raise AlreadyRegistered, "the data directory named '%s' was already registered" % name

    def register_data_directory(self, name, path, parent=None):
        """
            Registers a data directory at 'path' called 'name'.
            If this is a sub-directory of another registered data directory, you
            can use a relative path by setting the 'parent' keyword argument
            to the name of the parent data-directory. The parent path
            will then be appended to the childs path. If parent is set to None
            (the default) and the path does not start with a '/', the path is
            considered to be relative to the base directory.
            
            Note: names are always made full-caps!
            
            If you try to re-register an existing data directory, an AlreadyRegistered
            exception will be raised. Similarily if you pass in an unregistered
            parent directory name, NotRegistered will be raised. If you try to
            register "BASE_DIR" a ValueError will be raised, use set_base_directory
            instead (this can be called multiple times)
        """
        name = name.upper()
        if name=="BASE":
            raise ValueError, "the base directory should not be registered but set using 'set_base_directory'"
        else:
            self.__register_data_directory(name, path, parent=parent)
    
    def set_base_directory(self, base_dir):
        """
            Sets the project path
        """
        self.__register_data_directory("BASE", base_dir)
        
    def get_directory_path(self, name):
        """
            Gets the absolute path to a data directory named 'name'
        """
        if name in self.__data_directories:
            path = self.__data_directories[name]
            if path.startswith("/"):
                return path
            else:
                return "%s/%s" % (self._base_dir, path)
        elif name == "BASE":
            return self._base_dir
        else:
            raise NotRegistered, "the data directory named '%s' was not found in the registry" % name
                    
    def get_all_directories(self):
        """
            Returns a generator looping over all directories in the registry,
            excluding the project path.
        """
        for path in self.__data_directories.values():
            yield "%s/%s" % (self._base_dir, path)
            
    def get_file_path(self, name):
        """
            Gets the absolute path to a data file named 'name'
        """
        if name in self.__data_files:
            path = self.__data_files[name]
            if path.startswith("/"):
                return path
            else:
                return "%s/%s" % (self._base_dir, path)
        else:
            raise NotRegistered, "the data file named '%s' was not found in the registry" % name
            
    def get_all_files(self):
        """
            Returns a generator looping over all directories in the registry,
            excluding the project path.
        """
        for path in self.__data_directories:
            yield "%s/%s" % (self._base_dir, path)
