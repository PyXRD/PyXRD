#!/usr/bin/python

# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

from pyxrd.generic.models.treemodels import IndexListStore
from pyxrd.project.models import Project
from pyxrd.atoms.models import AtomType
from pyxrd.data import settings

def run(args):
    if args and args.filename != "":
        project = Project.load_object(args.filename)

        default_atoms = IndexListStore(AtomType)

        AtomType.get_from_csv(
            settings.DATA_REG.get_file_path("ATOM_SCAT_FACTORS"),
            default_atoms.append
        )

        for i, atom in enumerate(project.atom_types.iter_objects()):

            default_atom = default_atoms.get_item_by_index(atom.name)

            atom.charge = default_atom.charge
            atom.debye = default_atom.debye

        project.save_object(args.filename + ".def")

        del project

        print "Finished!"
