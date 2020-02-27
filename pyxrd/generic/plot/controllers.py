# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

from pkg_resources import resource_filename # @UnresolvedImport

import gi
from pyxrd.generic.plot.click_catcher import ClickCatcher
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

import matplotlib
import matplotlib.transforms as transforms
from matplotlib.figure import Figure
from matplotlib.tight_layout import get_renderer
from matplotlib.backends.backend_gtk3 import NavigationToolbar2GTK3 as NavigationToolbar
from matplotlib.backends.backend_gtk3agg import FigureCanvasGTK3Agg as FigureCanvasGTK
try:
    from matplotlib.pyparsing import ParseFatalException
except ImportError:
    from pyparsing import ParseFatalException

from mpl_toolkits.axisartist import Subplot

from mvc.adapters.gtk_support.dialogs.dialog_factory import DialogFactory

from pyxrd.data import settings
from pyxrd.generic.plot.motion_tracker import MotionTracker
from pyxrd.generic.plot.axes_setup import PositionSetup, update_axes
from pyxrd.generic.plot.plotters import plot_specimens, plot_mixtures

class MainPlotController(object):
    """
        A controller for the main plot canvas.
        Sets up the widgets and has image exporting functionality.
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
    #      View integration getters
    # ------------------------------------------------------------
    def get_toolbar_widget(self, window):
        return NavigationToolbar(self.canvas, window)

    def get_canvas_widget(self):
        return self.canvas
    
    # ------------------------------------------------------------
    #      Initialization and other internals
    # ------------------------------------------------------------
    def __init__(self, status_callback, marker_callback, *args, **kwargs):
        self.setup_layout_cache()
        self.setup_figure()
        self.setup_canvas()
        self.setup_content(status_callback, marker_callback)

    def setup_layout_cache(self):
        self.position_setup = PositionSetup()
        self.labels = list()
        self.marker_lbls = list()
        self._proxies = dict()
        self.scale = 1.0
        self.stats = False
        self._last_pos = None

    def setup_figure(self):
        self.figure = Figure(dpi=72, facecolor="#FFFFFF", linewidth=0)
        self.figure.subplots_adjust(hspace=0.0, wspace=0.0)

    def setup_canvas(self):
        self._canvas = FigureCanvasGTK(self.figure)

    def setup_content(self, status_callback, marker_callback):
        # Create subplot and add it to the figure:
        self.plot = Subplot(self.figure, 211, facecolor=(1.0, 1.0, 1.0, 0.0))
        self.plot.set_autoscale_on(False)
        self.figure.add_axes(self.plot)

        # Connect events:
        self.canvas.mpl_connect('draw_event', self.fix_after_drawing)
        self.canvas.mpl_connect('resize_event', self.fix_after_drawing)

        self.mtc = MotionTracker(self, status_callback)
        self.cc = ClickCatcher(self, marker_callback)

        #self.update()

    # ------------------------------------------------------------
    #      Update methods
    # ------------------------------------------------------------
    def draw(self):
        self._last_pos = self.fix_before_drawing()
        self.figure.canvas.draw()

    def fix_after_drawing(self, *args):
        _new_pos = self.fix_before_drawing()
        
        if _new_pos != self._last_pos:
            self._last_pos = _new_pos
            self._redraw_later()

        return False

    def _redraw_later(self):
        self.timer = self.figure.canvas.new_timer(interval=10)
        self.timer.single_shot = True
        self.timer.add_callback(lambda : self.figure.canvas.draw_idle())
        self.timer.start()

    def fix_before_drawing(self, *args):
        """
            Fixes alignment issues due to longer labels or smaller windows
            Is executed after an initial draw event, since we can then retrieve
            the actual label dimensions and shift/resize the plot accordingly.
        """
        renderer = get_renderer(self.figure)        
        if not renderer or not self._canvas.get_realized():
            return False
        
        # Fix left side for wide specimen labels:
        if len(self.labels) > 0:
            bbox = self._get_joint_bbox(self.labels, renderer)
            if bbox is not None: 
                self.position_setup.left = self.position_setup.default_left + bbox.width
        # Fix top for high marker labels:
        if len(self.marker_lbls) > 0:
            bbox = self._get_joint_bbox([ label for label, flag, _ in self.marker_lbls if flag ], renderer)
            if bbox is not None: 
                self.position_setup.top = self.position_setup.default_top - bbox.height
        # Fix bottom for x-axis label:
        bottom_label = self.plot.axis["bottom"].label
        if bottom_label is not None:
            bbox = self._get_joint_bbox([bottom_label], renderer)
            if bbox is not None:
                self.position_setup.bottom = self.position_setup.default_bottom + (bbox.ymax - bbox.ymin) * 2.0 # somehow we need this?

        # Calculate new plot position & set it:
        plot_pos = self.position_setup.position
        self.plot.set_position(plot_pos)

        # Adjust specimen label position
        for label in self.labels:
            label.set_x(plot_pos[0] - 0.025)

        # Adjust marker label position
        for label, flag, y_offset in self.marker_lbls:
            if flag:
                newy = plot_pos[1] + plot_pos[3] + y_offset - 0.025
                label.set_y(newy)
        
        _new_pos = self.position_setup.to_string()
        return _new_pos
    
    def update(self, clear=False, project=None, specimens=None):
        """
            Updates the entire plot with the given information.
        """
        if clear: self.plot.cla()

        if project and specimens:
            self.labels, self.marker_lbls = plot_specimens(
                self.plot, self.position_setup, self.cc,
                project, specimens
            )
            # get mixtures for the selected specimens:
            plot_mixtures(self.plot, project, [ mixture for mixture in project.mixtures if any(specimen in mixture.specimens for specimen in specimens) ])

        update_axes(
            self.plot, self.position_setup,
            project, specimens
        )

        self.draw()

    # ------------------------------------------------------------
    #      Plot position and size calculations
    # ------------------------------------------------------------
    def _get_joint_bbox(self, container, renderer):
        bboxes = []
        try:
            for text in container:
                bbox = text.get_window_extent(renderer=renderer)
                # the figure transform goes from relative coords->pixels and we
                # want the inverse of that
                bboxi = bbox.inverse_transformed(self.figure.transFigure)
                bboxes.append(bboxi)
        except (RuntimeError, ValueError):
            logger.exception("Caught unhandled exception when joining boundig boxes")
            return None # don't continue
        # this is the bbox that bounds all the bboxes, again in relative
        # figure coords
        if len(bboxes) > 0:
            bbox = transforms.Bbox.union(bboxes)
            return bbox
        else:
            return None

    # ------------------------------------------------------------
    #      Graph exporting
    # ------------------------------------------------------------
    def save(self, parent=None, current_name="graph", size="auto", num_specimens=1, offset=0.75):
        """
            Displays a save dialog to export an image from the current plot.
        """
        # Parse arguments:
        width, height = 0, 0
        if size == "auto":
            descr, width, height, dpi = settings.OUTPUT_PRESETS[0]
        else:
            width, height, dpi = list(map(float, size.replace("@", "x").split("x")))

        # Load gui:
        builder = Gtk.Builder()
        builder.add_from_file(resource_filename("pyxrd.specimen", "glade/save_graph_size.glade")) # FIXME move this to this namespace!!
        size_expander = builder.get_object("size_expander")
        cmb_presets = builder.get_object("cmb_presets")

        # Setup combo with presets:
        cmb_store = Gtk.ListStore(str, int, int, float)
        for row in settings.OUTPUT_PRESETS:
            cmb_store.append(row)
        cmb_presets.clear()
        cmb_presets.set_model(cmb_store)
        cell = Gtk.CellRendererText()
        cmb_presets.pack_start(cell, True)
        cmb_presets.add_attribute(cell, 'text', 0)
        def on_cmb_changed(cmb, *args):
            itr = cmb.get_active_iter()
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
            # Get the width, height & dpi
            width = float(entry_w.get_text())
            height = float(entry_h.get_text())
            dpi = float(entry_dpi.get_text())
            i_width, i_height = width / dpi, height / dpi
            # Save it all right!
            self.save_figure(dialog.filename, dpi, i_width, i_height)

        # Ask the user where, how and if he wants to save:
        DialogFactory.get_save_dialog(
            "Save Graph", parent=parent,
            filters=self.file_filters, current_name=current_name,
            extra_widget=size_expander
        ).run(on_accept)

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

    pass # end of class
