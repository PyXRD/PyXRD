# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

class MetaParser(type):
    """
        Metatype for the parser sub classes, allowing for auto file filter
        creation.
    """
    def __new__(meta, name, bases, attrs): # @NoSelf
        res = super(MetaParser, meta).__new__(meta, name, bases, attrs)
        res.setup_file_filter()
        return res