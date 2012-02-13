# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Author: Mathijs Dumon
# This work is licensed under the Creative Commons Attribution-ShareAlike 3.0 Unported License. 
# To view a copy of this license, visit http://creativecommons.org/licenses/by-sa/3.0/ or send
# a letter to Creative Commons, 444 Castro Street, Suite 900, Mountain View, California, 94041, USA.

import gtk

from math import sin, radians

import matplotlib
#matplotlib.use('GTKCairo')
from matplotlib.figure import Figure
from matplotlib.backends.backend_gtkcairo import FigureCanvasGTKCairo as FigureCanvasGTK
from matplotlib.ticker import FuncFormatter, IndexLocator

from mpl_toolkits.axes_grid1.axes_divider import make_axes_area_auto_adjustable

from generic.controllers import DialogMixin

class PlotController (DialogMixin):
    file_filters = ("Portable Network Graphics (PNG)", "*.png"), \
                   ("Scalable Vector Graphics (SVG)", "*.svg"), \
                   ("Portable Document Format (PDF)", "*.pdf")

    _canvas = None
    @property
    def canvas(self):
        if not self._canvas:
            self.setup_figure()
            self.setup_canvas()
            self.setup_content()
        return self._canvas

    def __init__(self):
        self._proxies = dict()
        self.setup_figure()
        self.setup_canvas()
        self.setup_content()

    def setup_figure(self):
        style = gtk.Style()
        self.figure = Figure(dpi=72, edgecolor=str(style.bg[2]), facecolor=str(style.bg[2]))
        self.figure.subplots_adjust(hspace=0.0, wspace=0.0)

    def setup_canvas(self):
        self._canvas = FigureCanvasGTK(self.figure)
       
    def setup_content(self):
        raise NotImplementedError
        
    _proxies = None
    def register(self, proxy, callback, last=True):
        if not (proxy, callback) in self._proxies:
            if last:
                self._proxies.append((proxy, callback))
            else:
                self._proxies = [(proxy, callback),] + self._proxies
            setattr(proxy, "__pctrl__", self)
    
    def unregister(self, proxy, callback):
        if (proxy, callback) in self._proxies:
            self._proxies.remove((proxy, callback))
            setattr(proxy, "__pctrl__", None)
            
    def unregister_all(self):
        for (proxy, callback) in self._proxies:
            setattr(proxy, "__pctrl__", None)
        self._proxies = list()
        
    def draw(self):
        self.figure.canvas.draw()
        
    def save(self, parent=None, suggest_name="graph", dpi=175, size="2000x1400"):
        dpi = dpi or self.figure.get_dpi()
        width, height = map(float, size.split("x"))
        builder = gtk.Builder()
        builder.add_from_file("specimen/glade/save_graph_size.glade")    
        size_expander = builder.get_object("size_expander")
        entry_w = builder.get_object("entry_width")
        entry_h = builder.get_object("entry_height")
        entry_d = builder.get_object("entry_dpi")
        entry_w.set_text(str(width))
        entry_h.set_text(str(height))
        entry_d.set_text(str(dpi))
        
        def on_accept(dialog):
            cur_fltr = dialog.get_filter()
            filename = dialog.get_filename()
            for fltr in self.file_filters:
                if cur_fltr.get_name() == fltr[0]:
                    if filename[len(filename)-4:] != fltr[1][1:]:
                        filename = "%s%s" % (filename, fltr[1][1:])
                    break
            width = float(entry_w.get_text())
            height = float(entry_h.get_text())
            dpi = float(entry_d.get_text())
            i_width, i_height = width / dpi, height / dpi
            original_size = self.figure.get_size_inches()      
            self.figure.set_size_inches((i_width, i_height))
            self.figure.savefig(filename, dpi=dpi)
            self.figure.set_size_inches(original_size)
        
        self.run_save_dialog("Save Graph", on_accept, None, parent=parent, suggest_name=suggest_name, extra_widget=size_expander)
        
class MainPlotController (PlotController):

    def __init__(self, app_controller, *args, **kwargs):
        self.app_controller = app_controller
        PlotController.__init__(self, *args, **kwargs)
        
    def setup_content(self):
        gtkcol = gtk.Style().bg[2]
        bg_color = (gtkcol.red_float, gtkcol.green_float, gtkcol.blue_float)
    
        self.title = self.figure.text(s="", va='bottom', ha='left', x=0.1, y=0.1, weight="bold")
        self.plot = self.figure.add_subplot(211, axisbg=(1.0,1.0,1.0,0.0))
        self.plot.set_frame_on(False)
        self.plot.get_xaxis().tick_bottom()
        self.plot.get_yaxis().set_ticks_position('none')
        make_axes_area_auto_adjustable(self.plot, adjust_dirs=["left"], pad=0)
        
        xmin, xmax = self.plot.get_xaxis().get_view_interval()
        ymin, ymax = self.plot.get_yaxis().get_view_interval()
        self.xaxis_line = matplotlib.lines.Line2D((xmin, xmax), (ymin, ymin), color='black', linewidth=2)
        
        
        self.stats_plot = self.figure.add_subplot(212, sharex=self.plot, axisbg=(1.0,1.0,1.0,0.0))
        self.stats_plot.get_xaxis().tick_bottom()
        yaxis = self.stats_plot.get_yaxis()
        yaxis.tick_left()
        #yaxis.get_major_locator().set_params(symmetric=True, nbins=2)
        self.figure.delaxes(self.stats_plot) #remove for now until we need it
        #self.stats_plot.autoscale(axis='y')
        make_axes_area_auto_adjustable(self.stats_plot, adjust_dirs=["left"], pad=0.0, use_axes=self.plot)

        self.update()
        
    ###
    ### UPDATE SUBROUTINES
    ###
    def update(self, new_title="", clear=False, single=True, labels=None, stats=(False,None)):
        if clear: self.plot.cla()
        
        self.update_proxies(draw=False)
        self.update_axes(draw=False, single=single, labels=labels, stats=stats)
        self.update_title(draw=False, title=new_title)
        
        self.draw()

    def update_proxies(self, draw=True):
        for obj, callback in self._proxies:
            ret = getattr(obj, callback)(self.figure, self.plot, self)
        if draw: self.draw()
    
    def update_lim(self):
        self.plot.relim()
        self.plot.autoscale_view()
        self.plot.set_ylim(bottom=0, auto=True)

    def update_axes(self, draw=True, single=True, labels=None, stats=(False,None)):
        self.update_lim()
        
        stats, res_pattern = stats
        
        xmin, xmax = self.plot.get_xaxis().get_view_interval()
        ymin, ymax = self.plot.get_yaxis().get_view_interval()
        xaxis = self.plot.get_xaxis()
        yaxis = self.plot.get_yaxis()
        box = self.plot.get_position()
        
        stats_offset = 0.15 if stats else 0.0
        
        if single:
            self.plot.set_position([0.10, 0.25+stats_offset, 0.80, 0.55-stats_offset]) #l, b, w, h
            self.plot.legend(loc="lower right", bbox_to_anchor=(0.02, 0.02, 0.94, 0.94), bbox_transform=self.figure.transFigure, borderaxespad=0.0, fancybox=False ) #-0.4-stats_offset*2
            #self.plot.set_ylabel('Intensity')
            yaxis.set_ticks_position('none')
            yaxis.set_ticklabels([])
            matplotlib.artist.setp(self.plot.get_yticklabels(), visible=False)

        else:
            self.plot.set_position([0.10, 0.10, 0.80, 0.70]) #l, b, w, h
            if labels != None and labels != []:
                labels, ticks = zip(*labels)
                yaxis.set_ticks(ticks)
                yaxis.set_ticklabels(labels)
                yaxis.set_ticks_position('none')
            self.xaxis_line.set_data((xmin, xmax), (ymin, ymin))
            
        if single and stats:          
            self.figure.add_axes(self.stats_plot)
            self.stats_plot.cla()
            self.stats_plot.add_line(res_pattern)
            self.stats_plot.set_ylim(auto=True)
            self.stats_plot.relim()
            self.stats_plot.get_yaxis().get_major_locator().set_params(symmetric=True, nbins=2, integer=False)            
            self.stats_plot.axhline(ls=":", c="k")
            
            self.stats_plot.autoscale_view()
            self.stats_plot.set_position([0.10, 0.22, 0.80, stats_offset]) #l, b, w, h                
            self.stats_plot.set_ylabel('Residual',  weight="heavy", size=14)
        
            matplotlib.artist.setp(self.plot.get_xticklabels(), visible=False)
            matplotlib.artist.setp(self.plot.get_xlabel(), visible=False)
            
            self.stats_plot.set_xlabel('Angle (°2θ)', weight="heavy", size=14)
        else:
            if self.stats_plot in self.figure.axes:
                self.figure.delaxes(self.stats_plot)
        
            matplotlib.artist.setp(self.plot.get_xticklabels(), visible=True)
            matplotlib.artist.setp(self.plot.get_xlabel(), visible=True)
            xaxis.tick_bottom()            
            self.plot.set_xlabel('Angle (°2θ)', weight="heavy", size=14)

        self.xaxis_line.set_data((xmin, xmax), (ymin, ymin))
        self.plot.add_artist(self.xaxis_line)
            
        if draw: self.draw()

    def update_title(self, title="", draw=True):
        self.title.set_text(title)
        if draw: self.draw()
    
    def update_labels(self, draw=True, single=True):
        if draw: self.draw()

    def plot_lines(self, lines, draw=True, clear=True):
        if clear: self.plot.cla()
        if lines != None:
            for line in lines:
                self.plot.add_line(line)
        if draw: self.draw()

    def plot_markers(self, markers, draw=True, clear=True):
        if clear: self.plot.cla()
        if markers != None:
            if hasattr(markers, "_model_data"):
                markers = markers._model_data
            for marker in markers:
               marker.plot(self.plot)
        if draw: self.draw()

    
class SmallPlotController (PlotController):
    pass
    
class EyedropperCursorPlot():
    def __init__(self, canvas, window, connect = False, enabled = False):
        self.canvas = canvas
        self.window = window
        self.enabled = enabled
        if connect: self.connect()

    def connect(self):
        self.cidmotion = self.canvas.mpl_connect(
            'motion_notify_event', self.on_motion)

    def on_motion(self, event):
        if self.window != None:           
            if not self.enabled:
                self.window.set_cursor(None)
            else:
                self.window.set_cursor(gtk.gdk.Cursor(gtk.gdk.CROSSHAIR))

    def disconnect(self):
        if self.window != None:           
            self.window.set_cursor(None)
        self.canvas.mpl_disconnect(self.cidmotion)
    
class DraggableVLine():
    lock = None  # only one can be animated at a time
    def __init__(self, line, connect = False, callback = None, window = None):
        self.line = line
        self.press = None
        self.background = None
        self.callback = callback
        self.window = window
        if connect: self.connect()

    def connect(self):
        'connect to all the events we need'
        self.cidpress = self.line.figure.canvas.mpl_connect(
            'button_press_event', self.on_press)
        self.cidrelease = self.line.figure.canvas.mpl_connect(
            'button_release_event', self.on_release)
        self.cidmotion = self.line.figure.canvas.mpl_connect(
            'motion_notify_event', self.on_motion)

    def on_press(self, event):
        'on button press we will see if the mouse is over us and store some data'
        if event.inaxes != self.line.axes: return
        if DraggableVLine.lock is not None: return
        contains, attrd = self.line.contains(event)
        if not contains: return
        x0 = self.line.get_xdata()[0]
        print 'event contains', x0
        self.press = x0, event.xdata
        DraggableVLine.lock = self

    def on_motion(self, event):
        'on motion we will move the line if the mouse is over us'
        if self.window != None and event.inaxes == self.line.axes:
            if DraggableVLine.lock is not self:
                change_cursor, attrd = self.line.contains(event)
            else:
                change_cursor=True
            
            if not change_cursor: 
                self.window.set_cursor(None)
            else:
                arrows = gtk.gdk.Cursor(gtk.gdk.SB_H_DOUBLE_ARROW)
                self.window.set_cursor(arrows)
        
        if DraggableVLine.lock is not self:
            return
        if event.inaxes != self.line.axes: return
        x0, xpress = self.press
        x = max(x0 + (event.xdata - xpress), 0)
        self.line.set_xdata((x,x))
        
        self.line.figure.canvas.draw()

    def on_release(self, event):
        'on release we reset the press data'
        if DraggableVLine.lock is not self:
            return

        self.press = None
        DraggableVLine.lock = None

        if self.callback!=None and callable(self.callback):
            x = self.line.get_xdata()
            self.callback(x[0])

        # redraw the full figure
        self.line.figure.canvas.draw()

    def disconnect(self):
        'disconnect all the stored connection ids'
        self.line.figure.canvas.mpl_disconnect(self.cidpress)
        self.line.figure.canvas.mpl_disconnect(self.cidrelease)
        self.line.figure.canvas.mpl_disconnect(self.cidmotion)
