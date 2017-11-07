#!/usr/bin/python

# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import unittest

import numpy as np

from pyxrd.calculations.data_objects import GonioData
from pyxrd.calculations.goniometer import (
    get_2t_from_nm,
    get_nm_from_2t, 
    get_nm_from_t,
    get_t_from_nm,
    get_S, 
    get_fixed_to_ads_correction_range,
    get_lorentz_polarisation_factor
)

__all__ = [
    'TestGoniometerCalcs',
]

class TestGoniometerCalcs(unittest.TestCase):

    def setUp(self):
        self.goniometer_data_kwargs = dict(
            min_2theta = 3.0,
            max_2theta = 45,
            mcr_2theta = 0,
            steps = 2500,
            soller1 = 2.3,
            soller2 = 2.3,
            divergence = 0.5,
            has_ads = False,
            ads_fact = 1.0,
            ads_phase_fact = 1.0,
            ads_phase_shift = 0.0,
            ads_const = 0.0,
            radius = 24.0,
            wavelength_distribution = [
                [0.1544426,0.955148885],
                [0.153475,0.044851115],
            ]  
        )
        self.goniometer_data = GonioData(**self.goniometer_data_kwargs)

    def tearDown(self):
        del self.goniometer_data

    def test_not_none(self):
        self.assertIsNotNone(self.goniometer_data)
        
    def test_attributes(self):
        for key, value in self.goniometer_data_kwargs.iteritems():
            self.assertEquals(getattr(self.goniometer_data, key), value)

    def test_fixed_to_ads_correction_range(self):
        result = get_fixed_to_ads_correction_range(
            np.asanyarray([2.2551711385, 2.478038901, 2.7001518288, 2.9214422642, 3.1418428, 3.3612863, 3.5797059197, 3.7970351263]),
            self.goniometer_data
        )
        self.assertIsNotNone(result)
        self.assertEquals(np.allclose(
            result, 
            [7.74814435e-01, 6.15920411e-01, 4.27242611e-01, 2.18376385e-01, -2.50146408e-04, -2.17930643e-01, -4.24231682e-01, -6.09510086e-01]
        ), True)

    def test_lorentz_polarisation_factor(self):
        result = get_lorentz_polarisation_factor(
            np.asanyarray([2.2551711385, 2.478038901, 2.7001518288, 2.9214422642, 3.1418428, 3.3612863, 3.5797059197, 3.7970351263]),
            12,
            self.goniometer_data.soller1, self.goniometer_data.soller2, self.goniometer_data.mcr_2theta
        )
        self.assertIsNotNone(result)
        self.assertEquals(np.allclose(
            result, 
            [3.00643375e-03, 4.83799816e-03, 1.33173586e-02, 6.56714627e-02, 5.11941694e+02, 6.59637604e-02, 1.35695934e-02, 4.97673826e-03]
        ), True)
        pass

    def test_S(self):
        # 
        result = get_S(2.5, 2.5);
        self.assertIsNotNone(result)
        self.assertEquals(len(result), 2)
        S, S1S2 = result
        self.assertAlmostEquals(S, 1.7677669529663689)
        self.assertAlmostEquals(S1S2, 6.25)

    def test_2t_from_nm_positive(self):
        # boundary condition: positive
        result = get_2t_from_nm(0.716)
        self.assertIsNotNone(result)
        self.assertAlmostEquals(result, 12.351779659)
    def test_2t_from_nm_zero(self):
        # boundary condition: 0
        result = get_2t_from_nm(0)
        self.assertIsNotNone(result)
        self.assertAlmostEquals(result, 0)
    def test_2t_from_nm_negative(self):
        # boundary condition: negative
        result = get_2t_from_nm(-0.716)
        self.assertIsNotNone(result)
        self.assertAlmostEquals(result, -12.351779659)
     
    def test_nm_from_2t_positive(self):
        # boundary condition: positive
        result = get_nm_from_2t(12.351779659)
        self.assertIsNotNone(result)
        self.assertAlmostEquals(result, 0.716)
    def test_nm_from_2t_zero(self):
        # boundary condition: 0
        result = get_nm_from_2t(0)
        self.assertIsNotNone(result)
        self.assertAlmostEquals(result, 1e+16)
        result = get_nm_from_2t(0, zero_for_inf=True)
        self.assertIsNotNone(result)
        self.assertAlmostEquals(result, 0)
    def test_nm_from_2t_negative(self):
        # boundary condition: negative
        result = get_nm_from_2t(-12.351779659)
        self.assertIsNotNone(result)
        self.assertAlmostEquals(result, -0.716)
        
    def test_nm_from_t_positive(self):
        # boundary condition: positive
        result = get_nm_from_t(6.17588983)
        self.assertIsNotNone(result)
        self.assertAlmostEquals(result, 0.716)        
    def test_nm_from_t_zero(self):
        # boundary condition: 0
        result = get_nm_from_t(0)
        self.assertIsNotNone(result)
        self.assertAlmostEquals(result, 1e+16)
        result = get_nm_from_t(0, zero_for_inf=True)
        self.assertIsNotNone(result)
        self.assertAlmostEquals(result, 0)
    def test_nm_from_t_negative(self):
        # boundary condition: negative
        result = get_nm_from_t(-6.17588983)
        self.assertIsNotNone(result)
        self.assertAlmostEquals(result, -0.716)
       
    def test_t_from_nm_positive(self):
        # boundary condition: positive
        result = get_t_from_nm(0.716)
        self.assertIsNotNone(result)
        self.assertAlmostEquals(result, 6.17588983)
    def test_t_from_nm_zero(self):
        # boundary condition: 0
        result = get_t_from_nm(0)
        self.assertIsNotNone(result)
        self.assertAlmostEquals(result, 0)
    def test_t_from_nm_negative(self):
        # boundary condition: negative
        result = get_t_from_nm(-0.716)
        self.assertIsNotNone(result)
        self.assertAlmostEquals(result, -6.17588983)

    pass # end of class
