#!/usr/bin/python

# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import unittest
from mock import Mock

from test.utils import create_object_attribute_test

from pyxrd.atoms.models import Atom

__all__ = [
    'TestAtom',
]

class TestAtom(unittest.TestCase):

    atom_type = None

    def setUp(self):
        self.atom = Atom()

    def tearDown(self):
        del self.atom

    def test_not_none(self):
        self.assertIsNotNone(self.atom)

    def test_data_object(self):
        self.assertIsNotNone(self.atom.data_object)

    test_name = create_object_attribute_test("atom", "name", "Test Name")
    test_pn = create_object_attribute_test("atom", "pn", 3)
    test_default_z = create_object_attribute_test("atom", "default_z", 5.3)
    test_stretch_values = create_object_attribute_test("atom", "stretch_values", True)

    def test_parent(self):
        parent_atom = Atom(name="Parent")
        self.atom.parent = parent_atom
        self.assertEqual(self.atom.parent, parent_atom)

    def test_z_calculations(self):
        # Checks wether the atom can calculate stretched values:
        # 1. When everything is set up the way it should be:
        default_z = 9.0
        lattice_d = 5.4
        factor = 0.5
        
        parent = Mock()
        parent.configure_mock(**{
            'get_interlayer_stretch_factors.return_value': (lattice_d, factor)
        })
        
        atom = Atom(parent=parent)
        atom.stretch_values = True
        atom.default_z = default_z
        z = atom.z
        self.assertEqual(z, lattice_d + (default_z - lattice_d) * factor)
        # 2. When no component is set, but stretched is True: should not raise an error, but simple ignore the stretching
        atom.parent = None
        z = atom.z

    def test_structure_factors(self):
        import numpy as np
        rng = 2.0 * np.sin(np.arange(30)) / 0.154056
        res = self.atom.get_structure_factors(rng)
        self.assertIsNotNone(res)
        
    def test_loads_atom_type_by_name(self):
        atom_json_dict = {
            "uuid": "878341b04e9e11e2b238150ae229a525", 
            "name": "O", 
            "default_z": 0.66, 
            "pn": 6.0, 
            "atom_type_name": "O1-"
        }
        
        oxygen = Mock()
        oxygen.name = "O1-"
        hydrogen = Mock()
        hydrogen.name = "H+"
                
        project = Mock()
        project.atom_types = [oxygen, hydrogen]
        phase = Mock()
        phase.attach_mock(project, 'project')
        component = Mock()
        component.attach_mock(phase, 'phase')
        
        atom = Atom.from_json(parent = component, **atom_json_dict)
        atom.resolve_json_references()
        self.assertEqual(atom.atom_type, oxygen)
        

    pass # end of class
