# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

class DataObject(object):
    """
        A generic class holding all the information retrieved from a file
        using a BaseParser class.
    """

    # general information
    filename = None

    def __init__(self, *args, **kwargs):
        super(DataObject, self).__init__()
        self.update(**kwargs)

    def update(self, **kwargs):
        for key, value in kwargs.iteritems():
            setattr(self, key, value)

    pass # end of class