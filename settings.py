# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

### General Information ###
VERSION = "0.4.4"

DEBUG = False
VIEW_MODE = False
BGSHIFT = True

LOG_FILENAME = 'errors.log'
UPDATE_URL = 'http://users.ugent.be/~madumon/pyxrd/'
MANUAL_URL = UPDATE_URL

### Factor to multiply the CSDS average with to obtain the maximum CSDS ###
LOG_NORMAL_MAX_CSDS_FACTOR = 2.5

### Default Styles & Colors ###
EXPERIMENTAL_COLOR = "#000000"
CALCULATED_COLOR = "#FF0000"

EXPERIMENTAL_LINEWIDTH = 1.0
CALCULATED_LINEWIDTH = 2.0

MARKER_COLOR = "#000000"
MARKER_BASE = 1
MARKER_STYLE = "none"
MARKER_ALIGN = "left"

EXCLUSION_FOREG = "#999999"
EXCLUSION_LINES = "#333333"

### Plot Information ###
PLOT_STATS_OFFSET = 0.15

PLOT_TOP = 0.85
MAX_PLOT_RIGHT = 0.95
PLOT_BOTTOM = 0.10
PLOT_LEFT = 0.15
PLOT_HEIGHT = PLOT_TOP - PLOT_BOTTOM

STATS_PLOT_BOTTOM = 0.10

OUTPUT_PRESETS = [
    ("Landscape Large print", 8000, 4800, 300.0),
    ("Landscape Medium print", 6000, 3800, 300.0),
    ("Landscape Small print", 4000, 2800, 300.0),
    ("Portrait Large print", 4800, 8000, 300.0),
    ("Portrait Medium print", 3800, 6000, 300.0),
    ("Portrait Small print", 2800, 4000, 300.0),
]

def _get_ratio(angle, stretch=False, plot_left=PLOT_LEFT):
    MAX_PLOT_WIDTH = MAX_PLOT_RIGHT - plot_left
    if stretch:
        return MAX_PLOT_WIDTH
    else:
        return min((angle / 70), 1.0) * MAX_PLOT_WIDTH

def get_plot_position(angle, stretch=False, plot_left=PLOT_LEFT):
    """Get the position of the main plot
    
    Arguments:
    angle     -- maximum angle of plotted data
    stretch   -- wether or not to stretch the plot to fit the available space  
                 (default False)
    plot_left -- the left side of the plot (used for label-width correction
    """
    PLOT_WIDTH = _get_ratio(angle, stretch=stretch, plot_left=plot_left)
    return [plot_left, PLOT_BOTTOM, PLOT_WIDTH, PLOT_HEIGHT]

def get_plot_stats_position(angle, stretch=False, plot_left=PLOT_LEFT):
    """Get the position of the plot when the statistics plot is also visible
    
    Arguments:
    angle     -- maximum angle of plotted data
    stretch   -- wether or not to stretch the plot to fit the available space  
                 (default False)
    plot_left -- the left side of the plot (used for label-width correction
    """
    PLOT_WIDTH = _get_ratio(angle, stretch=stretch, plot_left=plot_left)
    return [plot_left, PLOT_BOTTOM+PLOT_STATS_OFFSET, PLOT_WIDTH, PLOT_HEIGHT-PLOT_STATS_OFFSET]

def get_stats_plot_position(angle, stretch=False, plot_left=PLOT_LEFT):
    """Get the position of the statistics plot
    
    Arguments:
    angle     -- maximum angle of plotted data
    stretch   -- wether or not to stretch the plot to fit the available space  
                 (default False)
    plot_left -- the left side of the plot (used for label-width correction
    """
    PLOT_WIDTH = _get_ratio(angle, stretch=stretch, plot_left=plot_left)
    return [plot_left, STATS_PLOT_BOTTOM, PLOT_WIDTH, PLOT_STATS_OFFSET]
    
def get_plot_right(angle, stretch=False, plot_left=PLOT_LEFT):
    """Get the rightmost position of plots
    
    Arguments:
    angle     -- maximum angle of plotted data
    stretch   -- wether or not to stretch the plot to fit the available space  
                 (default False)
    plot_left -- the left side of the plot (used for label-width correction
    """
    PLOT_WIDTH = _get_ratio(angle, stretch=stretch, plot_left=plot_left)
    return plot_left + PLOT_WIDTH
    
PRINT_WIDTH = 1800
PRINT_BASE_HEIGHT = 1200
PRINT_MARGIN_HEIGHT = PRINT_BASE_HEIGHT*(1.0-PLOT_HEIGHT)
PRINT_SINGLE_HEIGHT = PRINT_BASE_HEIGHT*PLOT_HEIGHT

### Default Directories & Files ###
BASE_DIR = "" #is set runtime!
DEFAULT_DATA_DIR = 'data/'
DEFAULT_PHASES_DIR = '%sdefault phases/' % DEFAULT_DATA_DIR
DEFAULT_COMPONENTS_DIR = '%sdefault components/' % DEFAULT_DATA_DIR
DEFAULT_GONIOS_DIR = '%sdefault goniometers/' % DEFAULT_DATA_DIR
APPLICATION_ICONS_DIR = "application/icons/"

COMPOSITION_CONV_FILE = "%scomposition_conversion.csv" % DEFAULT_DATA_DIR
ATOM_SCAT_FACTORS_FILE = "%satomic scattering factors.atl" % DEFAULT_DATA_DIR
WAVELENGTHS_FILE = "%swavelengths.csv" % DEFAULT_DATA_DIR
MINERALS_FILE = "%smineral_references.csv" % DEFAULT_DATA_DIR

def get_def_dir(name):
    """Get absolute paths for default directories"""
    if name=="DEFAULT_DATA":
        global DEFAULT_DATA_DIR
        return get_abs_dir(DEFAULT_DATA_DIR)
    elif name=="DEFAULT_PHASES":
        global DEFAULT_PHASES_DIR
        return get_abs_dir(DEFAULT_PHASES_DIR)
    elif name=="DEFAULT_COMPONENTS":
        global DEFAULT_COMPONENTS_DIR
        return get_abs_dir(DEFAULT_COMPONENTS_DIR)
    elif name=="DEFAULT_GONIOS":
        global DEFAULT_GONIOS_DIR
        return get_abs_dir(DEFAULT_GONIOS_DIR)
    elif name=="APPLICATION_ICONS_DIR":
        global APPLICATION_ICONS_DIR
        return get_abs_dir(APPLICATION_ICONS_DIR)
    else:
        return get_abs_dir("")
        
def get_def_file(name):
    """Get absolute paths for default files"""
    if name=="COMPOSITION_CONV":
        global COMPOSITION_CONV_FILE    
        return get_abs_dir(COMPOSITION_CONV_FILE)
    elif name=="ATOM_SCAT_FACTORS":
        global ATOM_SCAT_FACTORS_FILE
        return get_abs_dir(ATOM_SCAT_FACTORS_FILE)
    elif name=="WAVELENGTHS":
        global WAVELENGTHS_FILE
        return get_abs_dir(WAVELENGTHS_FILE)
    elif name=="MINERALS":
        global MINERALS_FILE
        return get_abs_dir(MINERALS_FILE)
    else:
        return get_abs_dir("")
    
def get_abs_dir(rel_dir):
    global BASE_DIR
    return "%s/%s" % (BASE_DIR, rel_dir)

### Runtime Settings Retrieval ###
SETTINGS_APPLIED = False
def apply_runtime_settings(no_gui=False):
    """Apply runtime settings, can and needs to be called only once"""
    global SETTINGS_APPLIED
    global BASE_DIR
    if not SETTINGS_APPLIED:
        import sys, os
        
        BASE_DIR = os.path.abspath(os.path.dirname(sys.argv[0]))
        
        if not no_gui:
            import matplotlib
            import gtk

            font = {
                'weight' : 'heavy', 'size': 14,
                'family' : 'sans-serif',
            }
            
            if sys.platform == "win32":
               font['sans-serif'] = 'Verdana, Arial, Helvetica, sans-serif' 
            
            matplotlib.rc('font', **font)
            mathtext = {'default': 'regular', 'fontset': 'stixsans'}
            matplotlib.rc('mathtext', **mathtext)
            #matplotlib.rc('text', **{'usetex':True})
            
            # Load all additional icons
            iconfactory = gtk.IconFactory()
            for root, dirnames, filenames in os.walk(get_def_dir("APPLICATION_ICONS_DIR")):
                for filename in filenames:
                    if filename.endswith(".png"):
                        stock_id = filename[:-4] #remove extensions
                        pixbuf = gtk.gdk.pixbuf_new_from_file("%s%s" % (get_def_dir("APPLICATION_ICONS_DIR"), filename))
                        iconset = gtk.IconSet(pixbuf)
                        iconfactory.add(stock_id, iconset)
            iconfactory.add_default()
        
        #Check if the default directories exist,
        #if not create them:
        for dirname in ["DEFAULT_DATA", "DEFAULT_PHASES", "DEFAULT_COMPONENTS", "DEFAULT_GONIOS"]:
            path = get_def_dir(dirname)
            if not os.path.exists(path):
                os.makedirs(path)
        
        print "Runtime settings applied"
    SETTINGS_APPLIED = True
    
### end of settings
