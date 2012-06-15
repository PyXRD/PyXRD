# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Author: Mathijs Dumon
# This work is licensed under the Creative Commons Attribution-ShareAlike 3.0 Unported License. 
# To view a copy of this license, visit http://creativecommons.org/licenses/by-sa/3.0/ or send
# a letter to Creative Commons, 444 Castro Street, Suite 900, Mountain View, California, 94041, USA.

import gtk

import matplotlib
from matplotlib.figure import Figure
from matplotlib.backends.backend_gtkcairo import FigureCanvasGTKCairo as FigureCanvasGTK

from generic.views import BaseView

class EditAtomTypeView(BaseView):
    builder = "atoms/glade/atoms.glade"
    top = "edit_atom_type"
    
    def __init__(self, *args, **kwargs):
        BaseView.__init__(self, *args, **kwargs)
        
        self.graph_parent = self["view_graph"]
        self.setup_matplotlib_widget()
        
    def setup_matplotlib_widget(self):
        style = gtk.Style()
        self.figure = Figure(dpi=72, edgecolor=str(style.bg[2]), facecolor=str(style.bg[2]))
           
        self.plot = self.figure.add_subplot(111)       
        self.figure.subplots_adjust(bottom=0.20)
        
        self.matlib_canvas = FigureCanvasGTK(self.figure)
    
        self.plot.autoscale_view()
    
        self.graph_parent.add(self.matlib_canvas)
        self.graph_parent.show_all()
        
    def update_figure(self, x, y):
        self.plot.cla()
        self.plot.plot(x, y, 'k-', aa=True)
        self.plot.set_ylabel('Scattering factor', size=14, weight="heavy")
        self.plot.set_xlabel('2θ', size=14, weight="heavy")
        self.plot.autoscale_view()
        if self.matlib_canvas != None:
            self.matlib_canvas.draw()
