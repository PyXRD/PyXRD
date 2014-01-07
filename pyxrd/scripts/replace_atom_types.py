#!/usr/bin/python

# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

from pyxrd.project.models import Project
from pyxrd.atoms.models import AtomType
from pyxrd.data import settings

def run(args):
    if args and args.filename != "":
        project = Project.load_object(args.filename)

        default_atoms = []

        AtomType.get_from_csv(
            settings.DATA_REG.get_file_path("ATOM_SCAT_FACTORS"),
            default_atoms.append
        )

        for atom in project.atom_types.iter_objects():

            default_atom = None
            for def_atom in default_atoms:
                if atom.name == def_atom.name:
                    default_atom = def_atom
            assert default_atom is not None

            atom.charge = default_atom.charge
            atom.debye = default_atom.debye

        project.save_object(args.filename + ".def")

        del project

        print "Finished!"
