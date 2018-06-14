PyXRD
=====

PyXRD is a python implementation of the matrix algorithm for computer modeling
of X-ray diffraction (XRD) patterns of disordered lamellar structures.
It's goals are to:

 - provide an easy user-interface for end-users
 - provide basic tools for displaying and manipulating XRD patterns
 - produce high-quality (publication-grade) figures
 - make modelling of XRD patterns for mixed-layer clay minerals 'easy'
 - be free and open-source (open box instead of closed box model)
 
PyXRD was written with the multi-specimen full-profile fitting method in mind. 
A direct result is the ability to 'share' parameters among similar phases.
This allows for instance to have an air-dry and a glycolated illite-smectite 
share their coherent scattering domain size, but still have different basal 
spacings and interlayer compositions for the smectite component. Or play with
the di/tri-octahedral composition of a chlorite with ease.

Other features are (incomplete list):

 - Import/export several common XRD formats (.RD, .RAW, .CPI, ASCII)
 - Simple background subtraction/addition (linear or custom patterns)
 - Smoothing patterns and adding noise to patterns
 - Peak finding and annotating (markers)
 - Peak stripping and peak area calculation tools
 - Custom line colors, line widths, pattern positions, ...
 - Goniometer settings (wavelengths, geometry settings, ...)
 - Specimen settings (sample length, absorption, ...)
 - Automatic parameter refinement using several algorithms, e.g.:
    - L BFGS B
    - Brute Force
    - Covariation Matrix Adapation Evolutionary Strategy (CMA-ES; using DEAP 1.0)
    - Multiple Particle Swarm Optimization (MPSO; using DEAP 1.0)
    - Particle-swarm CMA-ES (PS-CMA-ES; using DEAP 1.0)
 - Scripting support

DISCLAIMER
==========
PyXRD is still very much work in progress. Currently there is no strict 
development cycle as it is still a one-man project. This also means little
time is going into testing and adding new tests for new features. Most of the
codebase therefore remains untested at this point and Things May Break as a 
result.

If you encounter bugs please:

 * create a new [issue](https://github.com/PyXRD/PyXRD/issues/new) or;
 * send me an e-mail


INSTALLATION
============

As of version 0.5.0 PyXRD (finally) supports standard python packaging, meaning 
it is available from the [Python package index](https://pypi.python.org/pypi)
and has become very easy to install for most Python users once the dependencies
are installed.

If you're not used to (installing) Python software, see below for specific
instructions.


Dependencies
------------

This is what should be present on your system.

 * Python 3.4 or later
 * Setuptools
 * GTK3 and pygobject 3.2 or later
 * cairocffi
 * Numpy 1.11 or later
 * Scipy 1.1 or later
 * Matplotlib 2.2 or later
 * Pyro4 4.41 or later
 * DEAP 1.0 or later
 
Additionally, to be able to run the unit tests, you'll need to install 
pyton-mock (>= 1.3.0). To just run PyXRD, you won't need it though.

Windows
-------

PyXRD is developed on Ubuntu Linux, and thus has a number of dependencies which
are not native to windows. Because of the difficulties in installing these
correctly, from version 0.8 onwards an all-in-one stand alone installer is
provided for windows users. Previous installations should not interfere, but
it's better to remove them (including python, numpy, scipy and 
pygtk installed along with pre-v0.8 versions).


You can choose for a local installation or a portable (single-folder) 
installation. The latter is just a zip-file which can be extracted e.g. onto an
usb-drive. The downside is you don't get start menu entries.


The installers are made available here:

https://github.com/mathijs-dumon/PyXRD/releases


After installation there should be a start menu entry available.


If PyXRD does not launch, run cmd.exe (the command prompt), enter the 
following and send me the output (right-click to copy after selecting):

```"C:\Program Files (x86)\PyXRD\bin\python3.exe" -m pyxrd```

 
Linux
-----

It should be as easy as:

```
python3 -m ensurepip --upgrade
python3 -m pip install pyxrd
```

To run PyXRD:

```
python3 -m pyxrd
```

Mac OS X
--------

Currently no support is given for iOS. If anyone is interested in getting this
to work feel free to contact me.

CREDITS
=======

- [xylib](http://github.com/wojdyr/xylib/) - Has been a great help at 
unravelling some common XRD formats 
