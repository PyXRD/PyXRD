#!/usr/bin/env python3

import os
from ez_setup import use_setuptools
use_setuptools()
from setuptools import setup, find_packages

def get_version():
    from pyxrd.__version import __version__
    if __version__.startswith("v"):
        __version__ = __version__.replace("v", "")
    return "%s" % __version__

def get_install_requires():
    return [
        'setuptools',
        'numpy>=1.11',
        'scipy>=1.1.0',
        'matplotlib>=2.2.2',
        'Pyro4>=4.41',
        'deap>=1.0.1',
        'cairocffi',
        'pygobject>=3.20'
    ]

def read(fname):
    with open(os.path.join(os.path.dirname(__file__), fname)) as f:
        return f.read()

setup(
    name="PyXRD",
    version=get_version(),
    description="PyXRD is a python implementation of the matrix algorithm developed for the X-ray diffraction analysis of disordered lamellar structures",
    long_description=read('README.md'),
    keywords="XRD disorder mixed-layers",
    author="Mathijs Dumon",
    author_email="mathijs.dumon@gmail.com",
    url="http://github.org/mathijs-dumon/PyXRD",

    license="BSD",
    setup_requires=[ "setuptools_git >= 1.2", ],
    packages=find_packages(exclude=["test.*", "test", "tests_mvc", "tests_mvc.*"]),
    include_package_data=True,
    install_requires=get_install_requires(),
    zip_safe=False,

    classifiers=[
        "Development Status :: 4 - Beta",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3.4",
        "Environment :: Win32 (MS Windows)",
        "Environment :: X11 Applications :: Gnome",
        "Environment :: X11 Applications :: GTK",
        "Intended Audience :: End Users/Desktop",
        "Intended Audience :: Science/Research",
        "Topic :: Utilities",
        "Topic :: Scientific/Engineering",
        "Topic :: Scientific/Engineering :: Visualization",
        "Natural Language :: English",
        "License :: OSI Approved :: BSD License",
    ],
)
