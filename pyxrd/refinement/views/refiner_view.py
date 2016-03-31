# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

from pkg_resources import resource_filename  # @UnresolvedImport

import gtk

import matplotlib
from matplotlib.figure import Figure
from matplotlib.backends.backend_gtkagg import FigureCanvasGTKAgg as FigureCanvasGTK, NavigationToolbar2GTKAgg as NavigationToolbar

from pyxrd.generic.views import BaseView

class RefinerView(BaseView):
    """
        A view for the Refiner object
    """
    
    builder = resource_filename(__name__, "glade/refine_results.glade")
    top = "window_refine_results"
    modal = True

    graph_parent = "plot_box"

    def __init__(self, *args, **kwargs):
        BaseView.__init__(self, *args, **kwargs)

        self.graph_parent = self[self.graph_parent]

        self.get_toplevel().set_transient_for(self.parent.get_toplevel())

        self.setup_matplotlib_widget()

    def update_labels(self, initial, best, last):
        self["initial_residual"].set_text("%f" % initial)
        self["best_residual"].set_text("%f" % best)
        self["last_residual"].set_text("%f" % last)

    def setup_matplotlib_widget(self):
        # TODO Create a mixin for this kind of thing!!
        style = gtk.Style()
        self.figure = Figure(dpi=72, edgecolor=str(style.bg[2]), facecolor=str(style.bg[2]))

        self.figure.subplots_adjust(bottom=0.20)

        self.canvas = FigureCanvasGTK(self.figure)

        box = gtk.VBox()
        box.pack_start(NavigationToolbar(self.canvas, self.get_top_widget()), expand=False)
        box.pack_start(self.canvas)
        self.graph_parent.add(box)
        self.graph_parent.show_all()

        cdict = {'red': ((0.0, 0.0, 0.0),
                         (0.5, 1.0, 1.0),
                         (1.0, 0.0, 0.0)),
                'green': ((0.0, 0.0, 0.0),
                         (0.5, 1.0, 1.0),
                         (1.0, 0.0, 0.0)),
                'blue': ((0.0, 0.0, 0.0),
                         (0.5, 1.0, 1.0),
                         (1.0, 0.0, 0.0))}
        self.wbw_cmap = matplotlib.colors.LinearSegmentedColormap('WBW', cdict, 256)

    pass # end of class