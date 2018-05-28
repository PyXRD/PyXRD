# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

try:
    from lxml import ET
except ImportError:
    try:
        # Python 2.5
        import xml.etree.cElementTree as ET
    except ImportError:
        try:
            # Python 2.5
            import xml.etree.ElementTree as ET
        except ImportError:
            try:
                # normal cElementTree install
                import cElementTree as ET
            except ImportError:
                try:
                    # normal ElementTree install
                    import elementtree.ElementTree as ET
                except ImportError:
                    print("Failed to import ElementTree from any known place") 

class XMLParserMixin(object):
    """
        XML Parser Mixin class
    """

    @classmethod
    def get_xml_for_string(cls, s):
        """ Returns a tuple containing the XML tree and root objects """
        root = ET.fromstring(s)
        return ET.ElementTree(element=root), root

    @classmethod
    def get_xml_for_file(cls, f):
        """ Returns a tuple containing the XML tree and root objects """
        tree = ET.parse(f)
        return tree, tree.getroot()

    @classmethod
    def get_val(cls, root, path, attrib, default=None):
        """ Returns the attribute `attrib` from the first element found in
        `root` using the given `path`or default if not found """
        element = root.find(path)
        if element is not None:
            return element.get(attrib)
        else:
            return default

    pass #end of class
