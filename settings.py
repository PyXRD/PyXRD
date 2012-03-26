VERSION = "0.3.3"

DEBUG = True
VIEW_MODE = True

LOG_FILENAME = 'errors.log'

PLOT_STATS_OFFSET = 0.15

PLOT_TOP = 0.85
MAX_PLOT_RIGHT = 0.95
PLOT_BOTTOM = 0.10
PLOT_LEFT = 0.15
MAX_PLOT_WIDTH = MAX_PLOT_RIGHT - PLOT_LEFT
PLOT_HEIGHT = PLOT_TOP - PLOT_BOTTOM

STATS_PLOT_BOTTOM = 0.10

def _get_ratio(angle):
    return min((angle / 70), 1.0) * MAX_PLOT_WIDTH

def get_plot_position(angle):
    PLOT_WIDTH = _get_ratio(angle)
    return [PLOT_LEFT, PLOT_BOTTOM, PLOT_WIDTH, PLOT_HEIGHT]

def get_plot_stats_position(angle):
    PLOT_WIDTH = _get_ratio(angle)
    return [PLOT_LEFT, PLOT_BOTTOM+PLOT_STATS_OFFSET, PLOT_WIDTH, PLOT_HEIGHT-PLOT_STATS_OFFSET]

def get_stats_plot_position(angle):
    PLOT_WIDTH = _get_ratio(angle)
    return [PLOT_LEFT, STATS_PLOT_BOTTOM, PLOT_WIDTH, PLOT_STATS_OFFSET]
    
def get_plot_right(angle):
    PLOT_WIDTH = _get_ratio(angle)
    return PLOT_LEFT + PLOT_WIDTH
    
DEFAULT_GRAPH_SIZE = "1800x1200"
