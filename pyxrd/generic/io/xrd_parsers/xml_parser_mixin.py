# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import xml.etree.ElementTree as ET

class XMLParserMixin(object):
    """
        XML Parser Mixin class
    """

    @classmethod
    def get_xml_for_file(cls, f):
        """ Returns a tuple containing the XML tree and root objects """
        tree = ET.parse(f)
        return tree, tree.getroot()

    pass #end of class
