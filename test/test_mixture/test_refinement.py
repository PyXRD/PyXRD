#!/usr/bin/python

# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import unittest

from pkg_resources import resource_filename # @UnresolvedImport
from test.setup import SKIP_REFINEMENT_TEST

from pyxrd.project.models import Project

__all__ = [
    'TestRefinement',
]

# Requires properly working:
#  - Phase
#  - Specimen
#  - Project
#  - Mixture

class TestRefinement(unittest.TestCase):

    atom_type = None

    def setUp(self):
        self.project = Project.load_object(resource_filename("test.test_mixture", "test refinement.pyxrd"))
        self.mixture = self.project.mixtures[0]

    def tearDown(self):
        del self.mixture
        del self.project

    def test_not_none(self):
        self.assertIsNotNone(self.mixture)

    def test_data_object(self):
        self.assertIsNotNone(self.mixture.data_object)

    @unittest.skipIf(SKIP_REFINEMENT_TEST, "Skipping refinement test")
    def test_refine_methods(self):
        for index, method in enumerate(self.mixture.Meta.all_refine_methods):
            self.mixture.refine_method = index
            self.mixture.randomize()
            self.mixture.setup_refine_options()
            self.mixture.refiner.setup_context()
            self.mixture.refiner.refine(stop=None)



    # TODO:
    #  - set_data_object
    #  - optimize
    #  - apply_current_data_object
    #  - update
    #  - get_refinement_method
    #  - setup_refine_options

    pass # end of class


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()