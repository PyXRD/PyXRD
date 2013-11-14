# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

from pkg_resources import resource_filename # @UnresolvedImport

import gtk

import matplotlib
import matplotlib.transforms as transforms
from matplotlib.figure import Figure
from matplotlib.backends.backend_gtkagg import FigureCanvasGTKAgg as FigureCanvasGTK
try:
    from matplotlib.pyparsing import ParseFatalException
except ImportError:
    from pyparsing import ParseFatalException

from mpl_toolkits.axisartist import Subplot

from pyxrd.data import settings

from pyxrd.generic.plot.plotters import plot_specimens, plot_mixtures
from pyxrd.generic.controllers import DialogMixin

class PlotController(DialogMixin):
    """
        A base class for matplotlib-canvas controllers that, sets up the 
        widgets and has image exporting functionality.
    """

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

    # ------------------------------------------------------------
    #      Initialisation and other internals
    # ------------------------------------------------------------
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

    # ------------------------------------------------------------
    #      Update subroutines
    # ------------------------------------------------------------
    def draw(self):
        try:
            self.figure.canvas.draw()
            self.fix_after_drawing()
        except ParseFatalException as e:
            print "Catching unhandled exception: %s" % e

    def fix_after_drawing(self):
        pass # nothing to fix

    # ------------------------------------------------------------
    #      Graph exporting
    # ------------------------------------------------------------
    def save(self, parent=None, suggest_name="graph", size="auto", num_specimens=1, offset=0.75):
        """
            Displays a save dialog to export an image from the current plot.
        """
        # Parse arguments:
        width, height = 0, 0
        if size == "auto":
            descr, width, height, dpi = settings.OUTPUT_PRESETS[0]
        else:
            width, height, dpi = map(float, size.replace("@", "x").split("x"))

        # Load gui:
        builder = gtk.Builder()
        builder.add_from_file(resource_filename("pyxrd.specimen", "glade/save_graph_size.glade")) # FIXME move this to this namespace!!
        size_expander = builder.get_object("size_expander")
        cmb_presets = builder.get_object("cmb_presets")

        # Setup combo with presets:
        cmb_store = gtk.ListStore(str, int, int, float)
        for row in settings.OUTPUT_PRESETS:
            cmb_store.append(row)
        cmb_presets.clear()
        cmb_presets.set_model(cmb_store)
        cell = gtk.CellRendererText()
        cmb_presets.pack_start(cell, True)
        cmb_presets.add_attribute(cell, 'text', 0)
        def on_cmb_changed(cmb, *args):
            itr = cmb_presets.get_active_iter()
            w, h, d = cmb_store.get(itr, 1, 2, 3)
            entry_w.set_text(str(w))
            entry_h.set_text(str(h))
            entry_dpi.set_text(str(d))
        cmb_presets.connect('changed', on_cmb_changed)

        # Setup input boxes:
        entry_w = builder.get_object("entry_width")
        entry_h = builder.get_object("entry_height")
        entry_dpi = builder.get_object("entry_dpi")
        entry_w.set_text(str(width))
        entry_h.set_text(str(height))
        entry_dpi.set_text(str(dpi))

        # What to do when the user wants to save this:
        def on_accept(dialog):
            # Get the selected file type and name:
            cur_fltr = dialog.get_filter()
            filename = dialog.get_filename()
            # Add the correct extension if not present yet:
            for fltr in self.file_filters:
                if cur_fltr.get_name() == fltr[0]:
                    if filename[len(filename) - 4:] != fltr[1][1:]:
                        filename = "%s%s" % (filename, fltr[1][1:])
                    break
            # Get the width, height & dpi
            width = float(entry_w.get_text())
            height = float(entry_h.get_text())
            dpi = float(entry_dpi.get_text())
            i_width, i_height = width / dpi, height / dpi
            # Save it all right!
            self.save_figure(filename, dpi, i_width, i_height)

        # Ask the user where, how and if he wants to save:
        self.run_save_dialog("Save Graph", on_accept, None, parent=parent, suggest_name=suggest_name, extra_widget=size_expander)

    def save_figure(self, filename, dpi, i_width, i_height):
        """
            Save the current plot
            
            Arguments:
             filename: the filename to save to (either .png, .pdf or .svg)
             dpi: Dots-Per-Inch resolution
             i_width: the width in inch
             i_height: the height in inch
        """
        # Get original settings:
        original_dpi = self.figure.get_dpi()
        original_width, original_height = self.figure.get_size_inches()
        # Set everything according to the user selection:
        self.figure.set_dpi(dpi)
        self.figure.set_size_inches((i_width, i_height))
        self.figure.canvas.draw() # replot
        bbox_inches = matplotlib.transforms.Bbox.from_bounds(0, 0, i_width, i_height)
        # Save the figure:
        self.figure.savefig(filename, dpi=dpi, bbox_inches=bbox_inches)
        # Put everything back the way it was:
        self.figure.set_dpi(original_dpi)
        self.figure.set_size_inches((original_width, original_height))
        self.figure.canvas.draw() # replot

class MainPlotController (PlotController):
    """
        A controller for the main plot canvas.
    """
    # ------------------------------------------------------------
    #      Initialisation and other internals
    # ------------------------------------------------------------
    def __init__(self, app_controller, *args, **kwargs):
        self.labels = list()
        self.scale = 1.0
        self.stats = False
        self.xdiff = 30.0
        self.plot_left = settings.PLOT_LEFT
        self.app_controller = app_controller
        PlotController.__init__(self, *args, **kwargs)

    def setup_content(self):
        self.title = self.figure.text(s="", va='bottom', ha='left', x=0.1, y=0.1, weight="bold")
        self.plot = Subplot(self.figure, 211, axisbg=(1.0, 1.0, 1.0, 0.0))
        self.figure.add_axes(self.plot)
        self.plot.axis["right"].set_visible(False)
        self.plot.axis["left"].set_visible(False)
        self.plot.axis["top"].set_visible(False)
        self.plot.get_xaxis().tick_bottom()
        self.plot.get_yaxis().tick_left()

        self.canvas.mpl_connect('draw_event', self.fix_after_drawing)
        self.canvas.mpl_connect('resize_event', self.fix_after_drawing)

        self.update()

    # ------------------------------------------------------------
    #      Update methods
    # ------------------------------------------------------------
    def update(self, clear=False, project=None, specimens=None):
        """
            Updates the entire plot with the given information.
        """
        if clear: self.plot.cla()

        if project and specimens:
            self.labels = plot_specimens(project, specimens, self.plot_left, self.plot)
            # get mixtures for the selected specimens:
            mixtures = []
            for mixture in project.mixtures.iter_objects():
                for specimen in specimens:
                    if specimen in mixture.specimens:
                        mixtures.append(mixture)
                        break
            plot_mixtures(project, mixtures, self.plot)
        self.update_axes(project=project)

    def update_axes(self, project=None):
        """
            Updates the view limits and displays statistics plot if needed         
        """
        self.stretch = project.axes_xstretch if project is not None else False

        self.update_lim(project=project)
        xaxis = self.plot.get_xaxis()
        # yaxis = self.plot.get_yaxis()
        xmin, xmax = xaxis.get_view_interval()
        # ymin, ymax = yaxis.get_view_interval()
        self.xdiff = xmax - xmin

        if project == None or project.axes_yvisible == False:
            self.plot.axis["left"].set_visible(False)
        else:
            self.plot.axis["left"].set_visible(True)
        self.plot.axis["bottom"].major_ticks.set_visible(True)
        self.plot.axis["right"].set_visible(False)
        self.plot.axis["top"].set_visible(False)


        def set_label_text(label, text):
            label.set_text(text)
            label.set_weight('heavy')
            label.set_size(16)

        self.plot.set_position(self.get_plot_position())

        set_label_text(self.plot.axis["bottom"].label, u'Angle (°2θ)')
        self.plot.axis["bottom"].major_ticklabels.set_visible(True)

        self.draw()

    def update_lim(self, project=None):
        """
            Updates the view limits
        """
        self.plot.relim()
        self.plot.autoscale_view()

        self.plot.set_ylim(bottom=0, auto=True)

        # xaxis = self.plot.get_xaxis()
        xmin, xmax = 0.0, 20.0
        if project == None or project.axes_xscale == 0:
            xmin, xmax = self.plot.get_xlim()
            xmin, xmax = max(xmin, 0.0), max(xmax, 20.0)
        else:
            xmin, xmax = max(project.axes_xmin, 0.0), project.axes_xmax
        self.plot.set_xlim(left=xmin, right=xmax, auto=False)

    # ------------------------------------------------------------
    #      Plot position and size calculations
    # ------------------------------------------------------------
    def fix_after_drawing(self, *args):
        """
            Fixes alignment issues due to longer labels or smaller windows
            Is executed after an initial draw event, since we can then retrieve
            the actual label dimensions and shift/resize the plot accordingly.
        """
        if len(self.labels) > 0:
            bboxes = []
            try:
                for label in self.labels:
                    bbox = label.get_window_extent()
                    # the figure transform goes from relative coords->pixels and we
                    # want the inverse of that
                    bboxi = bbox.inverse_transformed(self.figure.transFigure)
                    bboxes.append(bboxi)
            except RuntimeError as e:
                print "Catching unhandled exception: %s" % e
                return # don't continue

            # this is the bbox that bounds all the bboxes, again in relative
            # figure coords
            bbox = transforms.Bbox.union(bboxes)
            self.plot_left = 0.05 + bbox.xmax - bbox.xmin
            plot_pos = self.get_plot_position()
            self.plot.set_position(plot_pos)

            for label in self.labels:
                label.set_x(plot_pos[0] - 0.025)
        self.figure.canvas.draw()

        return False

    def _get_plot_width(self):
        MAX_PLOT_WIDTH = settings.MAX_PLOT_RIGHT - self.plot_left
        if self.stretch:
            return MAX_PLOT_WIDTH
        else:
            return min((self.xdiff / 70), 1.0) * MAX_PLOT_WIDTH

    def get_plot_position(self):
        """Get the position list of the main plot: [LEFT, BOTTOM, WIDTH, HEIGHT] """
        return [self.plot_left, settings.PLOT_BOTTOM, self._get_plot_width(), settings.PLOT_HEIGHT]

    def get_plot_right(self):
        """Get the rightmost position of the main plot: LEFT + WIDTH """
        PLOT_WIDTH = self._get_plot_width()
        return self.plot_left + PLOT_WIDTH


    def get_user_x_coordinate(self, callback):
        def onclick(x_pos, event):
            self.edc.enabled = False
            self.edc.disconnect()
            callback(x_pos)
            del self.edc
        self.edc = EyedropperCursorPlot(
            self.canvas,
            self.canvas.get_window(),
            onclick,
            True, True
        )

    pass # end of class


class EyedropperCursorPlot():
    def __init__(self, canvas, window, click_callback=None, connect=False, enabled=False):
        self.canvas = canvas
        self.window = window
        self.enabled = enabled
        self.click_callback = click_callback
        if connect: self.connect()

    def connect(self):
        self.cidmotion = self.canvas.mpl_connect(
            'motion_notify_event',
             self.on_motion
         )
        self.cidclick = self.canvas.mpl_connect(
            'button_press_event',
            self.on_click
        )

    def on_motion(self, event):
        if self.window is not None:
            if not self.enabled:
                self.window.set_cursor(None)
            else:
                self.window.set_cursor(gtk.gdk.Cursor(gtk.gdk.CROSSHAIR)) # @UndefinedVariable

    def on_click(self, event):
        x_pos = -1
        if event.inaxes:
            x_pos = event.xdata
        if self.enabled and callable(self.click_callback):
            self.click_callback(x_pos, event)

    def disconnect(self):
        if self.window is not None:
            self.window.set_cursor(None)
        self.canvas.mpl_disconnect(self.cidmotion)
        self.canvas.mpl_disconnect(self.cidclick)


class DraggableVLine():
    lock = None  # only one can be animated at a time
    def __init__(self, line, connect=False, callback=None, window=None):
        self.line = line
        self.press = None
        self.background = None
        self.callback = callback
        self.window = window
        if connect: self.connect()

    def connect(self):
        """ Connect to the canvas mouse events """
        self.cidpress = self.line.figure.canvas.mpl_connect(
            'button_press_event', self.on_press)
        self.cidrelease = self.line.figure.canvas.mpl_connect(
            'button_release_event', self.on_release)
        self.cidmotion = self.line.figure.canvas.mpl_connect(
            'motion_notify_event', self.on_motion)

    def on_press(self, event):
        """ Check if the mouse is over us and store the data """
        if event.inaxes != self.line.axes: return
        if DraggableVLine.lock is not None: return
        contains, attrd = self.line.contains(event)
        if not contains: return
        x0 = self.line.get_xdata()[0]
        self.press = x0, event.xdata
        DraggableVLine.lock = self

    def on_motion(self, event):
        """ Move the line if the mouse is over us & pressed """
        if self.window is not None and event.inaxes == self.line.axes:
            if DraggableVLine.lock is not self:
                change_cursor, attrd = self.line.contains(event)
            else:
                change_cursor = True

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
        self.line.set_xdata((x, x))

        self.line.figure.canvas.draw()

    def on_release(self, event):
        """ Reset the on_press data """
        if DraggableVLine.lock is not self:
            return

        self.press = None
        DraggableVLine.lock = None

        if self.callback is not None and callable(self.callback):
            x = self.line.get_xdata()
            self.callback(x[0])

        # redraw the full figure
        self.line.figure.canvas.draw()

    def disconnect(self):
        """ Disconnect all the stored connection ids """
        self.line.figure.canvas.mpl_disconnect(self.cidpress)
        self.line.figure.canvas.mpl_disconnect(self.cidrelease)
        self.line.figure.canvas.mpl_disconnect(self.cidmotion)
