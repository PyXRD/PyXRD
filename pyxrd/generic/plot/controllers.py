# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

from pkg_resources import resource_filename # @UnresolvedImport

import gtk
import logging
from pyxrd.generic.plot.axes_setup import PositionSetup, update_axes
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

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
        self.figure = Figure(dpi=72, edgecolor=str(style.bg[2]), facecolor=str(style.bg[0]))
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
        except ParseFatalException:
            logger.exception("Caught unhandled exception when drawing")

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
    #      Initialization and other internals
    # ------------------------------------------------------------
    def __init__(self, app_controller, *args, **kwargs):
        self.labels = list()
        self.marker_lbls = list()
        self.scale = 1.0
        self.stats = False

        self.position_setup = PositionSetup()

        self.app_controller = app_controller
        PlotController.__init__(self, *args, **kwargs)

    def setup_content(self):
        # Create subplot and add it to the figure:
        self.plot = Subplot(self.figure, 211, axisbg=(1.0, 1.0, 1.0, 0.0))
        self.figure.add_axes(self.plot)

        # Connect events:
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
            self.labels, self.marker_lbls = plot_specimens(
                self.plot, self.position_setup,
                project, specimens
            )
            # get mixtures for the selected specimens:
            mixtures = []
            for mixture in project.mixtures:
                for specimen in specimens:
                    if specimen in mixture.specimens:
                        mixtures.append(mixture)
                        break
            plot_mixtures(self.plot, project, mixtures)

        update_axes(
            self.plot, self.position_setup,
            project, specimens
        )

        self.draw()

    # ------------------------------------------------------------
    #      Plot position and size calculations
    # ------------------------------------------------------------
    def _get_joint_bbox(self, container):
        renderer = self._find_renderer()
        bboxes = []
        try:
            for text in container:
                bbox = text.get_window_extent(renderer=renderer)
                # the figure transform goes from relative coords->pixels and we
                # want the inverse of that
                bboxi = bbox.inverse_transformed(self.figure.transFigure)
                bboxes.append(bboxi)
        except RuntimeError:
            logger.exception("Caught unhandled exception when joining boundig boxes")
            return None # don't continue
        # this is the bbox that bounds all the bboxes, again in relative
        # figure coords
        if len(bboxes) > 0:
            bbox = transforms.Bbox.union(bboxes)
            return bbox
        else:
            return None

    def _find_renderer(self):
        if hasattr(self.figure.canvas, "get_renderer"):
            #Some backends, such as TkAgg, have the get_renderer method, which
            #makes this easy.
            renderer = self.figure.canvas.get_renderer()
        else:
            #Others don't, but since this is called in the 'fix_after_drawing',
            # a renderer has been created, so we can get it like this:
            renderer = self.figure._cachedRenderer
        return renderer

    def fix_after_drawing(self, *args):
        """
            Fixes alignment issues due to longer labels or smaller windows
            Is executed after an initial draw event, since we can then retrieve
            the actual label dimensions and shift/resize the plot accordingly.
        """
        # Fix left side for wide specimen labels:
        if len(self.labels) > 0:
            bbox = self._get_joint_bbox(self.labels)
            self.position_setup.left = 0.05 + bbox.width
        # Fix top for high marker labels:
        if len(self.marker_lbls) > 0:
            bbox = self._get_joint_bbox([ label for label, flag, _ in self.marker_lbls if flag ])
            if bbox is not None: self.position_setup.top = 1.0 - (0.05 + bbox.height) #Figure top - marker margin
        # Fix bottom for x-axis label:
        bottom_label = self.plot.axis["bottom"].label
        if bottom_label is not None:
            bbox = self._get_joint_bbox([bottom_label])
            if bbox is not None: self.position_setup.bottom = 0.10 - min(bbox.ymin, 0.0)

        # Calculate new plot position & set it:
        plot_pos = self.position_setup.position
        self.plot.set_position(plot_pos)

        # Adjust specimen label position
        for label in self.labels:
            label.set_x(plot_pos[0] - 0.025)

        # Adjust marker label position
        for label, flag, y_offset in self.marker_lbls:
            if flag:
                label.set_y(plot_pos[1] + plot_pos[3] + y_offset - 0.025)

        self.figure.canvas.draw()

        return False

    pass # end of class
