# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

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
        """
        Can be used to transform an argument passed to a __init__ method of a
        Storable (sub-)class containing a JSON dict into the actual 
        _BaseObjectListStore it is representing. Raises an ValueError if a arg 
        contains a _BaseObjectListStore sub-class which is not a tm_type
        
        *arg* the passed argument
        
        *tm_type* the _BaseObjectListStore's type (e.g. ObjectListStore)
        
        *child_type* the type of children the _BaseObjectListStore has
        
        :rtype: an empty tree model (argument was None), the argument
        (argument was a 'tm_type' instance), the actual object (argument was a 
        JSON dict)
        """
        if arg==None:
            return tm_type(child_type)
        elif isinstance(arg, tm_type):
            return arg
        elif isinstance(arg, dict):
            return tm_type.from_json(parent=self, **arg['properties'])
        else:
            raise ValueError, "Could not parse argument as TreeModel: %s" % arg
            
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
