.. PyXRD documentation master file, created by
   sphinx-quickstart on Wed Feb 12 10:27:39 2014.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

.. |pyxrd| replace:: *pyxrd*
.. |PyXRD| replace:: *PyXRD*

Welcome to the PyXRD docs!
==========================

|PyXRD| is a python implementation of the matrix algorithm for computer modeling 
of X-ray diffraction (XRD) patterns of disordered lamellar structures. It's goals are to:

   #. provide an easy user-interface for end-users
   #. provide basic tools for displaying and manipulating XRD patterns
   #. produce high-quality (publication-grade) figures
   #. make modelling of XRD patterns for mixed-layer clay minerals 'easy'
   #. be free and open-source

Motivation
==========

|PyXRD| was written with the multi-specimen full-profile fitting method in mind.
The direct result of this is the ability to 'share' parameters among similar phases.
 
This allows for instance to have an air-dry and a glycolated illite-smectite 
share their coherent scattering domain size, but still have different basal 
spacings and interlayer compositions for the smectite component.

Other features are (incomplete list):

    - Import/export several common XRD formats (.RD, .RAW, .CPI, ASCII)
    - simple background subtraction/addition (linear or custom patterns)
    - smoothing patterns and adding noise to patterns
    - peak finding and annotating (markers)
    - custom line colors, line widths, pattern positions, ...
    - goniometer settings (wavelengths, geometry settings, ...)
    - specimen settings (sample length, absorption, ...)
    - automatic parameter refinement using several algorithms, e.g.:
        - L BFGS B
        - Brute Force
        - Covariation Matrix Adapation Evolutionary Strategy (CMA-ES; using DEAP)
        - Multiple Particle Swarm Optimization (MPSO; using DEAP)
        - scripting support

Contents
========

.. toctree::
   :maxdepth: 2
   
   api/index

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

