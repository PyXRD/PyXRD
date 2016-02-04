# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import csv

class CSVMixin(object):
    """
        Model mixin providing CSV export and import functionality
    """

    class Meta():
        csv_storables = [] # list of tuples "label", "property_name"

    @classmethod
    def save_as_csv(cls, filename, items):
        atl_writer = csv.writer(open(filename, 'wb'), delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        labels, props = zip(*cls.Meta.csv_storables)
        atl_writer.writerow(labels)
        for item in items:
            prop_row = []
            for prop in props:
                prop_row.append(getattr(item, prop))
            atl_writer.writerow(prop_row)

    @classmethod
    def get_from_csv(cls, filename, parent=None):
        atl_reader = csv.reader(open(filename, 'rb'), delimiter=',', quotechar='"')
        labels, props = zip(*cls.Meta.csv_storables) # @UnusedVariable
        header = True
        for row in atl_reader:
            if not header:
                kwargs = dict()
                for i, prop in enumerate(props):
                    kwargs[prop] = row[i]
                yield cls(parent=parent, **kwargs)
            header = False

    pass # end of class
