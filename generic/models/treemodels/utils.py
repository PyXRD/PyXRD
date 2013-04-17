# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import os
import csv
import gtk

################################################################################
# Array-like item repositioning:
################################################################################
def repos(ln, old_pos, new_pos):
    """
        Return a new list in which each item contains the index of the item
        in the old order.
        Uses the ranges approach (best for large arrays).
    """
    lb = min(new_pos, old_pos)
    ub = max(new_pos, old_pos)
    adj_range = []
    if new_pos < old_pos:
        adj_range.append(old_pos)
        adj_range += range(lb, ub)
    else:
        adj_range += range(lb+1, ub+1)
        adj_range.append(old_pos)
    return range(0,lb) + adj_range + range(ub,ln-1)
    
def simple_repos(ln, old_pos, new_pos):
    """
        Return a new list in which each item contains the index of the item
        in the old order.
        Uses the delete/insert approach (best for small arrays).
    """
    r1 = range(ln)
    val = r1[old_pos]
    del r1[old_pos]
    r1.insert(new_pos, val)
    return r1
    
def smart_repos(ln, old_pos, new_pos):
    """
        Return a new list in which each item contains the index of the item
        in the old order.
        Decides which algorithm to use based on the size of the arrays.
    """
    if ln > 65:
        return repos(ln, old_pos, new_pos)
    else:
        return simple_repos(ln, old_pos, new_pos)
        
################################################################################
# Treestore creation from filesystem
################################################################################
def create_valuestore_from_file(filename, data_type=float):
    liststore = gtk.ListStore(str, data_type)
    with open(filename, 'r') as f:
        reader = csv.reader(f)
        reader.next() #skip header
        for row in reader:
            row[1] = data_type(row[1])
            liststore.append(row)
    return liststore
    
def create_treestore_from_directory(directory, extension):
    treestore = gtk.TreeStore(str,str, bool)
    treestore.append(None, ("", "", True))
    ext_len = len(extension)
    parents = {}
    for root, dirnames, filenames in os.walk(directory):
        for dirname in dirnames:
            parents[os.path.join(root, dirname)] = treestore.append(parents.get(root, None), (dirname, "", False))
        for filename in filenames:
            treestore.append(parents.get(root, None), (filename[:-ext_len], "%s/%s" % (root, filename), True))   
    return treestore
