# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Author: Mathijs Dumon
# This work is licensed under the Creative Commons Attribution-ShareAlike 3.0 Unported License. 
# To view a copy of this license, visit http://creativecommons.org/licenses/by-sa/3.0/ or send
# a letter to Creative Commons, 444 Castro Street, Suite 900, Mountain View, California, 94041, USA.

import csv

from gtkmvc import Observable

class ObjectListStoreChildMixin(object):
    
    __list_store__ = None
        
    def liststore_item_changed(self):
        if self.__list_store__ != None:
            self.__list_store__.on_item_changed(self)
            
    pass #end of class
    
class ObjectListStoreParentMixin(object):

    def parse_liststore_arg(self, arg, tm_type, child_type):
        if arg==None:
            return tm_type(child_type)
        elif isinstance(arg, tm_type):
            return arg
        elif isinstance(arg, dict):
            return tm_type.from_json(parent=self, **arg['properties'])
        else:
            raise ValueError, "Could not parse a TreeModel argument: %s" % arg
            
class CSVMixin(object):
    
    __csv_storables__ = [] #list of tuples "label", "property_name"

    @classmethod
    def save_as_csv(type, filename, items):
        atl_writer = csv.writer(open(filename, 'wb'), delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)      
        labels, props = zip(*type.__csv_storables__)
        atl_writer.writerow(labels)
        for item in items:
            prop_row = []
            for prop in props:
                prop_row.append(getattr(item, prop))
            atl_writer.writerow(prop_row)
           
    @classmethod 
    def get_from_csv(type, filename, callback = None):
        atl_reader = csv.reader(open(filename, 'rb'), delimiter=',', quotechar='"')
        labels, props = zip(*type.__csv_storables__)
        header = True
        items = []
        for row in atl_reader:
            if not header:
                kwargs = dict()
                for i, prop in enumerate(props):
                    kwargs[prop] = row[i]
                new_item = type(**kwargs)
                if callback is not None and callable(callback):
                    callback(new_item)
                items.append(new_item)
            header = False
        return items
    
    pass #end of class
