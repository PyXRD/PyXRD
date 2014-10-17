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
spacings and interlayer compositions for the smectite component. 

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

If you encounter serious bugs please send me the output so we can improve!
We'll try to make a habit out of writing UnitTests for each bug we encounter.


INSTALLATION
============

As of version 0.5.0 PyXRD (finally) supports standard python packaging, meaning 
it is available from the [Python package index](https://pypi.python.org/pypi)
and has become very easy to install for most Python users.

If you're not used to (installing) Python software, see below for specific instructions.

DEPENDENCIES
------------

This is what should be present on your system.

 * Python 2.7.4 (other version may also work, or may not)
 * Setuptools 1.4.1
 * PyGTK 2.24.2 or later
 * Numpy 1.7.0 or later
 * Scipy 0.14.0 or later
 * Matplotlib 1.2.1 or later
 * PyParsing 1.5.7 or later
 * (optional) DEAP 1.0.0 or later

Windows
-------

There are numereous ways to install python 'packages' or software. If you're a 
first-time Python user and don't really care about what way it is installed,
just download and install these, in the order given:

 1. [Python 2.7.4](http://www.python.org/ftp/python/2.7.4/python-2.7.4.msi)
 2. [Setuptools 1.4.1](http://www.lfd.uci.edu/~gohlke/pythonlibs/v92jt8xn/setuptools-1.4.1.win32-py2.7.exe)
 3. [PyGTK 2.24.2](http://ftp.gnome.org/pub/GNOME/binaries/win32/pygtk/2.24/pygtk-all-in-one-2.24.2.win32-py2.7.msi)
 4. [Numpy 1.7.0](http://sourceforge.net/projects/numpy/files/NumPy/1.7.0/numpy-1.7.0-win32-superpack-python2.7.exe/download)
 5. [Scipy 0.14.0](http://sourceforge.net/projects/scipy/files/scipy/0.14.0/scipy-0.14.0-win32-superpack-python2.7.exe/download)
 6. [Matplotlib 1.2.1](https://downloads.sourceforge.net/project/matplotlib/matplotlib/matplotlib-1.2.1/matplotlib-1.2.1.win32-py2.7.exe)
 7. [PyParsing 1.5.7](http://sourceforge.net/projects/pyparsing/files/pyparsing/pyparsing-1.5.7/pyparsing-1.5.7.win32-py2.7.exe/download)
 8. [PyXRD](https://github.com/mathijs-dumon/PyXRD/releases)

At this point you should have a working version of PyXRD installed (with a desktop shortcut).

If you want to use the evolutionary algorithms for parameter refinement, you'll
need to install DEAP as well. There is currently no windows installer available
for DEAP, so you'll need to instruct Python to fetch it from the Python package index:

 * Open a command line (Start button -> Search -> enter 'cmd.exe' -> press enter)
 * Type in the following command (no quotes): 
```
C:\Python27\Scripts\easy_install.exe deap
```
 * If all went well you should have the latest version of DEAP installed now. 
   Somtimes it is neccesary to run the command line as administrator
 
Linux
-----

You'll need a working version of Python 2.7 and then install all the other 
dependencies. PyGTK is currently not easily installable from the Python package 
index, as it needs to be compiled manually (it's a binding to the GTK libs after all...).

So install these two packages from your systems package manager, terminal commands
are given below to achieve that, but you can use your systems package manager
if you like that better:

 * Debian/Ubuntu/...:
   ```sudo apt-get install python python-gtk2```
 * Fedora/Red Hat/... (not tested, gime some feedback if this works!):
    ```sudo yum install python python-gtk```
 * OpenSuSE (not tested, gime some feedback if this works!):
    ```sudo zypper install python python-gtk```

*Note: you could also add the Numpy, Scipy and Matplotlib libraries if these are
provided by your OS's package repositories. Sometimes these cause problems when
installed using pip (see below).*

Once this has been completed, keep the terminal open and issue these commands:

```
sudo easy_install pip
pip install --user 'pyxrd>=0.5.0'
```

As this will install everyting under your '~/.local' folder, you don't need admin
rights for these commands, and you will be able to run PyXRD as a regular user.

To run PyXRD type in the following:

```
~/.local/bin/PyXRD
```

If you hate typing curly braces for this purpose, edit/create a .bashrc file in
your home_directory and add a line like this:
```
export PATH=$PATH:~/.local/bin/
```

Then all installed commands under that folder will be available, and you can start
PyXRD by typing just that: PyXRD.

Mac OS X
--------

Currently no support is given for Mac's. The main problem is getting PyGTK
to work under Mac. There has been some succes using MacPorts and the like (from
what I can read & tell online), but your milage may vary, and I recommend novice
users to switch to either a Windows or Linux PC.
It should be possible to get the code running in script-mode, as it has been
modified to run on headless (GTK-less) HPC infrastructure recently. Of course
this is not a very easy way of working with PyXRD...

CREDITS
=======

- [xylib](http://github.com/wojdyr/xylib/) - Has been a great help at unravelling some common XRD formats 
