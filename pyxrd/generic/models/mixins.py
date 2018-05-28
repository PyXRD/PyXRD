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

    @classmethod
    def save_as_csv(cls, filename, items):
        atl_writer = csv.writer(open(filename, 'w'), delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        labels = [prop.label for prop in cls.Meta.get_local_persistent_properties()]
        atl_writer.writerow(labels)
        for item in items:
            prop_row = []
            for label in labels:
                prop_row.append(getattr(item, label))
            atl_writer.writerow(prop_row)

    @classmethod
    def get_from_csv(cls, filename, parent=None):
        with open(filename, 'r') as csvfile:
            atl_reader = csv.DictReader(csvfile, delimiter=',', quotechar='"')
            labels = [prop.label for prop in cls.Meta.get_local_persistent_properties()]
            for row in atl_reader:
                yield cls(parent=parent, **{
                    prop: row[prop] for prop in labels if prop in row
                })

    pass # end of class
