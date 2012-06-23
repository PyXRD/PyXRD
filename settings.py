### General Information ###
VERSION = "0.4.0"

DEBUG = True
VIEW_MODE = False

LOG_FILENAME = 'errors.log'
UPDATE_URL = 'http://users.ugent.be/~madumon/pyxrd/'

### Plot Information ###
PLOT_STATS_OFFSET = 0.15

PLOT_TOP = 0.85
MAX_PLOT_RIGHT = 0.95
PLOT_BOTTOM = 0.10
PLOT_LEFT = 0.15
MAX_PLOT_WIDTH = MAX_PLOT_RIGHT - PLOT_LEFT
PLOT_HEIGHT = PLOT_TOP - PLOT_BOTTOM

STATS_PLOT_BOTTOM = 0.10

def _get_ratio(angle, stretch=False):
    if stretch:
        return MAX_PLOT_WIDTH
    else:
        return min((angle / 70), 1.0) * MAX_PLOT_WIDTH

def get_plot_position(angle, stretch=False):
    PLOT_WIDTH = _get_ratio(angle, stretch=stretch)
    return [PLOT_LEFT, PLOT_BOTTOM, PLOT_WIDTH, PLOT_HEIGHT]

def get_plot_stats_position(angle, stretch=False):
    PLOT_WIDTH = _get_ratio(angle, stretch=stretch)
    return [PLOT_LEFT, PLOT_BOTTOM+PLOT_STATS_OFFSET, PLOT_WIDTH, PLOT_HEIGHT-PLOT_STATS_OFFSET]

def get_stats_plot_position(angle, stretch=False):
    PLOT_WIDTH = _get_ratio(angle, stretch=stretch)
    return [PLOT_LEFT, STATS_PLOT_BOTTOM, PLOT_WIDTH, PLOT_STATS_OFFSET]
    
def get_plot_right(angle, stretch=False):
    PLOT_WIDTH = _get_ratio(angle, stretch=stretch)
    return PLOT_LEFT + PLOT_WIDTH
    
PRINT_WIDTH = 1800
PRINT_BASE_HEIGHT = 1200
PRINT_MARGIN_HEIGHT = PRINT_BASE_HEIGHT*(1.0-PLOT_HEIGHT)
PRINT_SINGLE_HEIGHT = PRINT_BASE_HEIGHT*PLOT_HEIGHT

### Default Directories ###
BASE_DIR = ""
DEFAULT_PHASES_DIR = 'data/default phases/'
DEFAULT_GONIOS_DIR = 'data/default goniometers/'

def get_def_dir(name):
    global DEFAULT_PHASES_DIR
    global DEFAULT_GONIOS_DIR
    if name=="DEFAULT_PHASES":
        return get_abs_dir(DEFAULT_PHASES_DIR)
    elif name=="DEFAULT_GONIOS":
        return get_abs_dir(DEFAULT_GONIOS_DIR)
    else:
        return get_abs_dir("")
    
def get_abs_dir(rel_dir):
    global BASE_DIR
    return "%s/%s" % (BASE_DIR, rel_dir)

### Runtime Settings Retrieval ###
SETTINGS_APPLIED = False
def apply_runtime_settings():
    global SETTINGS_APPLIED
    global BASE_DIR
    if not SETTINGS_APPLIED:
        import matplotlib

        font = {'weight' : 'heavy', 'size': 14}
        matplotlib.rc('font', **font)
        mathtext = {'default': 'regular', 'fontset': 'stixsans'}
        matplotlib.rc('mathtext', **mathtext)
        #matplotlib.rc('text', **{'usetex':True})
        
        import sys, os
        BASE_DIR = os.path.abspath(os.path.dirname(sys.argv[0]))
        
        print "Runtime settings applied"
    SETTINGS_APPLIED = True
    
### end of settings
