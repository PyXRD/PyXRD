# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import os
from pyxrd.__version import __version__
from appdirs import user_data_dir, user_cache_dir, user_log_dir

### General Information ###
VERSION = __version__

DEBUG = False
FINALIZERS = [] #A list of callables that are called before the main function is left
BGSHIFT = True

LOG_FILENAME = os.path.join(user_log_dir('PyXRD'), 'errors.log')

### The URL where PyXRD looks for updates & the online manual ###
UPDATE_URL = 'http://users.ugent.be/~madumon/pyxrd/'
MANUAL_URL = UPDATE_URL

### Factor to multiply the CSDS average with to obtain the maximum CSDS ###
LOG_NORMAL_MAX_CSDS_FACTOR = 2.5

### What type of residual error we use: ###
#   "Rp" = 'standard' pattern Rp factor
#   "Rpder" = Rp factor of first-derivatives
RESIDUAL_METHOD = "Rp"

### Default wavelength if no Goniometer is available ###
DEFAULT_LAMBDA = 0.154056

### Cache settings ###
# CAHCE: one of
#  - FILE  -  Store results on-disk (also see CACHE_DIR in the DATA_DIRS list)
#  - FILE_FETCH_ONLY (recommended) - Cache before a refinement starts, then only fetch results form disk.
#  - MEMORY (not advisable) - Cache in-memory (can cause lock-ups on low-end PC's)
#  - None - Do not cache, or try to use a cache.
CACHE = None #"FILE" # _FETCH_ONLY"
CACHE_SIZE = 500 * (1024 * 1024) # size of on-disk cache in bytes (10 Mb)
GUI_MODE = True

### Default Styles & Colors ###
DEFAULT_LAYOUT = "VIEWER" # one of the keys in DEFAULT_LAYOUTS!
DEFAULT_LAYOUTS = {
    "FULL": "Full",
    "VIEWER": "View-mode"
}

AXES_MANUAL_XMIN = 0.0
AXES_MANUAL_XMAX = 70.0
AXES_XSTRETCH = False
AXES_DSPACING = False
AXES_DEFAULT_WAVELENGTH = 0.154056

AXES_XLIMIT = 0
AXES_XLIMITS = {
    0: "Automatic",
    1: "Manual"
}

AXES_MANUAL_YMIN = 0.0
AXES_MANUAL_YMAX = 0.0
AXES_YVISIBLE = False

AXES_YNORMALIZE = 0
AXES_YNORMALIZERS = {
    0: "Multi normalised",
    1: "Single normalised",
    2: "Unchanged raw counts",
}

AXES_YLIMIT = 0
AXES_YLIMITS = {
    0: "Automatic",
    1: "Manual"
}

EXPERIMENTAL_COLOR = "#000000"
CALCULATED_COLOR = "#FF0000"

EXPERIMENTAL_LINEWIDTH = 1.0
CALCULATED_LINEWIDTH = 2.0

PATTERN_SHIFT_POSITIONS = {
    0.42574: "Quartz    0.42574   SiO2",
    0.3134:  "Silicon   0.3134    Si",
    0.2476:  "Zincite   0.2476    ZnO",
    0.2085:  "Corundum  0.2085    Al2O3"
}
PATTERN_SMOOTH_TYPES = { 0: "Moving Triangle" }
PATTERN_BG_TYPES = { 0: "Linear", 1: "Pattern" }

PLOT_OFFSET = 0.75
PATTERN_GROUP_BY = 1
LABEL_POSITION = 0.35

MARKER_VISIBLE = True
MARKER_X_OFFSET = 0.0
MARKER_Y_OFFSET = 0.05
MARKER_POSITION = 0.0

MARKER_INHERIT_COLOR = True
MARKER_COLOR = "#000000"
MARKER_INHERIT_ANGLE = True
MARKER_ANGLE = 0.0
MARKER_INHERIT_TOP_OFFSET = True
MARKER_TOP_OFFSET = 0.0
MARKER_INHERIT_BASE = True
MARKER_BASE = 1
MARKER_BASES = {
    0: "X-axis",
    1: "Experimental profile",
    2: "Calculated profile",
    3: "Lowest of both",
    4: "Highest of both"
}
MARKER_INHERIT_TOP = True
MARKER_TOP = 0
MARKER_TOPS = {
     0: "Relative to base",
     1: "Top of plot"
}
MARKER_INHERIT_STYLE = True
MARKER_STYLE = "none"
MARKER_STYLES = {
    "none": "None", "solid": "Solid",
    "dashed": "Dash", "dotted": "Dotted",
    "dashdot": "Dash-Dotted", "offset": "Display at Y-offset"
}
MARKER_INHERIT_ALIGN = True
MARKER_ALIGN = "left"
MARKER_ALIGNS = {
    "left": "Left align",
    "center": "Centered",
    "right": "Right align"
}

EXCLUSION_FOREG = "#999999"
EXCLUSION_LINES = "#333333"

### Plot Information ###
PLOT_TOP = 0.85
MAX_PLOT_RIGHT = 0.95
PLOT_BOTTOM = 0.10
PLOT_LEFT = 0.15
PLOT_HEIGHT = PLOT_TOP - PLOT_BOTTOM

OUTPUT_PRESETS = [
    ("Landscape Large print", 8000, 4800, 300.0),
    ("Landscape Medium print", 6000, 3800, 300.0),
    ("Landscape Small print", 4000, 2800, 300.0),
    ("Portrait Large print", 4800, 8000, 300.0),
    ("Portrait Medium print", 3800, 6000, 300.0),
    ("Portrait Small print", 2800, 4000, 300.0),
]

### Default Directories & Files ###
DATA_REG = None # set at run-time
DATA_DIRS = [
    ("DEFAULT_DATA", "./", None),
    ("USER_DATA", user_data_dir('PyXRD'), None),
    ("LOG_DIR", user_log_dir('PyXRD'), None),
    ("CACHE_DIR", user_cache_dir('PyXRD'), None),
    ("DEFAULT_PHASES", "default phases/", "USER_DATA"),
    ("DEFAULT_COMPONENTS", "default components/", "DEFAULT_DATA"),
    ("DEFAULT_GONIOS", "default goniometers/", "DEFAULT_DATA"),
    ("APPLICATION_ICONS", "icons/", "DEFAULT_DATA"),
]
DATA_FILES = [
    ("COMPOSITION_CONV", "composition_conversion.csv", "DEFAULT_DATA"),
    ("ATOM_SCAT_FACTORS", "atomic scattering factors.atl", "DEFAULT_DATA"),
    ("WAVELENGTHS", "wavelengths.csv", "DEFAULT_DATA"),
    ("MINERALS", "mineral_references.csv", "DEFAULT_DATA"),
]

### Parser module registration ###
# Add your custom parser modules here, these should be absolute paths!
PARSER_MODULES = [
    'pyxrd.generic.io.file_parsers',
    'pyxrd.generic.io.xrd_parsers',
    'pyxrd.specimen.parsers'
]

### Runtime Settings Retrieval ###
SETTINGS_APPLIED = False
__apply_lock__ = False
def apply_runtime_settings(no_gui=True, debug=False):
    """Apply runtime settings, can and needs to be called only once"""
    global __apply_lock__, SETTINGS_APPLIED
    if not __apply_lock__ and not SETTINGS_APPLIED:
        __apply_lock__ = True
        global GUI_MODE
        GUI_MODE = not no_gui

        global DEBUG
        global DATA_REG, DATA_DIRS, DATA_FILES

        # Set debug flag
        DEBUG = debug

        # Setup data registry:
        import sys
        from pyxrd.generic.io.data_registry import DataRegistry
        DATA_REG = DataRegistry(dirs=DATA_DIRS, files=DATA_FILES)

        # If we are running in GUI mode, setup GUI stuff:
        if not no_gui:
            import matplotlib
            import gtk

            # Setup matplotlib fonts:
            font = {
                'weight' : 'heavy', 'size': 14,
                'family' : 'sans-serif',
            }
            if sys.platform == "win32":
                font['sans-serif'] = 'Verdana, Arial, Helvetica, sans-serif'
            matplotlib.rc('font', **font)
            mathtext = {'default': 'regular', 'fontset': 'stixsans'}
            matplotlib.rc('mathtext', **mathtext)
            # matplotlib.rc('text', **{'usetex':True})

            # Load our own icons:
            iconfactory = gtk.IconFactory()
            icons_path = DATA_REG.get_directory_path("APPLICATION_ICONS")
            for root, dirnames, filenames in os.walk(icons_path):
                for filename in filenames:
                    if filename.endswith(".png"):
                        stock_id = filename[:-4] # remove extensions
                        filename = "%s/%s" % (icons_path, filename)
                        pixbuf = gtk.gdk.pixbuf_new_from_file(filename) # @UndefinedVariable
                        iconset = gtk.IconSet(pixbuf)
                        iconfactory.add(stock_id, iconset)
            iconfactory.add_default()

        # Make sure default directories exist:
        for path in DATA_REG.get_all_directories():
            try:
                os.makedirs(path)
            except OSError:
                pass

        # Register file parsers:
        for name in PARSER_MODULES:
            if not name.startswith('.'): # do not import relative paths!
                __import__(name)

        # Free some memory at this point:
        import gc
        gc.collect()

        # Log that we did all of this:
        import logging
        logger = logging.getLogger(__name__)
        logger.info("Runtime settings applied")
    __apply_lock__ = False
    SETTINGS_APPLIED = True

# ## end of settings
