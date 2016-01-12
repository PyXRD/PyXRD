#!/usr/bin/python

# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import unittest

from test.utils import create_object_attribute_test

from pyxrd.data import settings
from pyxrd.project.models import Project

__all__ = [
    'TestProject',
]

class TestProject(unittest.TestCase):

    project = None

    def setUp(self):
        settings.initialize()
        self.project = Project(name="Test Project")

    def tearDown(self):
        del self.project

    def test_not_none(self):
        self.assertIsNotNone(self.project)

    test_name = create_object_attribute_test("project", "name", "Test Name")
    test_date = create_object_attribute_test("project", "date", "19/09/1987")
    test_description = create_object_attribute_test("project", "description", "Test Description")
    test_author = create_object_attribute_test("project", "author", "Test Author")
    test_layout_mode = create_object_attribute_test("project", "layout_mode", "FULL")
    test_display_marker_align = create_object_attribute_test("project", "display_marker_align", "right")
    test_display_marker_color = create_object_attribute_test("project", "display_marker_color", "#FF00FF")
    test_display_marker_base = create_object_attribute_test("project", "display_marker_base", 2)
    test_display_marker_top = create_object_attribute_test("project", "display_marker_top", 1)
    test_display_marker_top_offset = create_object_attribute_test("project", "display_marker_top_offset", 0.5)
    test_display_marker_angle = create_object_attribute_test("project", "display_marker_angle", 45.6)
    test_display_marker_style = create_object_attribute_test("project", "display_marker_style", "dashed")
    test_display_calc_color = create_object_attribute_test("project", "display_calc_color", "#FF0099")
    test_display_exp_color = create_object_attribute_test("project", "display_exp_color", "#9900FF")
    test_display_calc_lw = create_object_attribute_test("project", "display_calc_lw", 5)
    test_display_exp_lw = create_object_attribute_test("project", "display_exp_lw", 1)
    test_display_plot_offset = create_object_attribute_test("project", "display_plot_offset", 1.5)
    test_display_group_by = create_object_attribute_test("project", "display_group_by", 3)
    test_display_label_pos = create_object_attribute_test("project", "display_label_pos", 0.75)
    test_axes_xscale = create_object_attribute_test("project", "axes_xscale", 1)
    test_axes_xmin = create_object_attribute_test("project", "axes_xmin", 15)
    test_axes_xmax = create_object_attribute_test("project", "axes_xmax", 52)
    test_axes_xstretch = create_object_attribute_test("project", "axes_xstretch", True)
    test_axes_yscale = create_object_attribute_test("project", "axes_yscale", 1)
    test_axes_yvisible = create_object_attribute_test("project", "axes_yvisible", True)

    # TODO
    #  - addition of phases, specimens & atom_types
    #  - loading of phases, specimens & atom_types
    #  - testing inherit properties (markers)
    #  - testing initialization deprecated keywords etc.

    pass # end of class
