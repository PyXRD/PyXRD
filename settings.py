VERSION = "0.3.8"

DEBUG = True
VIEW_MODE = False

LOG_FILENAME = 'errors.log'

UPDATE_URL = 'http://users.ugent.be/~madumon/pyxrd/'

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

SETTINGS_APPLIED = False
def apply_runtime_settings():
    global SETTINGS_APPLIED
    if not SETTINGS_APPLIED:
        import matplotlib

        font = {'weight' : 'heavy', 'size': 14}
        matplotlib.rc('font', **font)
        mathtext = {'default': 'regular'}
        matplotlib.rc('mathtext', **mathtext)
        
        print "Runtime settings applied"
    SETTINGS_APPLIED = True
