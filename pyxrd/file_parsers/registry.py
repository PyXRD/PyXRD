# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

from .base_group_parser import BaseGroupBarser

class ParserNamespace(object):
    """
        ParserNamespace instances can be used to register parsers and bundle
        them for easier retrieval of file filters etc.
    """

    def __init__(self, name, group_description="All supported files"):
        self._parsers = []
        self.name = name
        self.group_description = group_description

    def register_parser(self, first=False):
        """ 
            Register a parsers to this namespace
        """
        def wrapped_register(cls):
            if first:
                self._parsers.insert(0, cls)
            else:
                self._parsers.append(cls)
            self._update_group_parser()
            return cls
        return wrapped_register

    def get_file_filters(self):
        """ 
            Returns all the file filter object for the parsers registered in 
            this namespace 
        """
        for parser in [self._group_parser, ] + self._parsers:
            yield parser.file_filter

    def get_export_file_filters(self):
        for parser in self._parsers:
            if parser.can_write:
                yield parser.file_filter

    def get_import_file_filters(self):
        for parser in [self._group_parser, ] + self._parsers:
            if parser.can_read:
                yield parser.file_filter

    def _update_group_parser(self):
        """
            Factory function for creating BaseGroupParser sub-classes,
            using the namespace's name as the class name and the list of parser
            classes as arguments.
        """
        self._group_parser = type(self.name, (BaseGroupBarser,), dict(
             description=self.group_description,
             parsers=self._parsers
        ))

    pass #end of class
