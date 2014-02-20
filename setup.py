import os
from ez_setup import use_setuptools
use_setuptools()
from setuptools import setup, find_packages

def get_version():
    from pyxrd.__version import __version__
    return __version__

def get_install_requires():
    return [
        'setuptools',
        'numpy>=1.7',
        'scipy>=0.10',
        'matplotlib>=1.2.0',
    ]

def read(fname):
    # Utility function to read the README file.
    # Used for the long_description.  It's nice, because now 1) we have a top level
    # README file and 2) it's easier to type in the README file than to put a raw
    # string in below ...
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name="PyXRD",
    version=get_version(),
    description="""\
PyXRD is a python implementation of the matrix algorithm developed for the X-ray
diffraction analysis of disordered lamellar structures""",
    long_description=read('README.md'),
    keywords="XRD disorder mixed-layers",
    author="Mathijs Dumon",
    author_email="mathijs.dumon@gmail.com",
    url="http://github.org/mathijs-dumon/PyXRD",

    license="BSD",
    setup_requires=[ "setuptools_git >= 0.3", ],
    scripts=['win32_post_install.py'],
    packages=find_packages(exclude=["test.*", "test"]),
    include_package_data=True,
    entry_points={
        'console_scripts': [ 'PyXRDScript = pyxrd.core:run_user_script' ],
        'console_scripts': [ 'PyXRDMain = pyxrd.core:run_main' ],
        'gui_scripts': [ 'PyXRD = pyxrd.core:run_main' ]
    },
    install_requires=get_install_requires(),
    zip_safe=False,

    classifiers=[
        "Development Status :: 3 - Alpha",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 2.7",
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
