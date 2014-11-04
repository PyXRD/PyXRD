# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import logging
logger = logging.getLogger(__name__)

import time

from mvc import Observer, PropIntel, OptionPropIntel
from mvc.observers import ListObserver

from pyxrd.data import settings

from pyxrd.generic.models import DataModel
from pyxrd.generic.io import storables, Storable, get_case_insensitive_glob

from pyxrd.phases.models import Phase
from pyxrd.atoms.models import AtomType
from pyxrd.mixture.models.mixture import Mixture
from pyxrd.generic.utils import not_none
from pyxrd.specimen.models.base import Specimen
from pyxrd.generic.exit_stack import ExitStack
from contextlib import contextmanager

@storables.register()
class Project(DataModel, Storable):
    """
    This is the top-level object that servers the purpose of combining the
    different objects (most notably :class:`~.atoms.models.AtomType`'s,
    :class:`~.phases.models.Phase`'s, :class:`~.specimen.models.Specimen`'s and
    :class:`~.mixture.models.Mixture`'s).
    
    It also provides a large number of display-related 'default' properties 
    (e.g. for patterns and their markers, axes etc.). For more details: see the
    property descriptions.
    
    Example usage:
    
    .. code-block:: python
    
        >>> from pyxrd.project.models import Project
        >>> from pyxrd.generic.io.xrd_parsers import XRDParser
        >>> from pyxrd.specimen.models import Specimen
        >>> project = Project(name="New Project", author="Mr. X", layout_mode="FULL", axes_dspacing=True)
        >>> for specimen in Specimen.from_experimental_data("/path/to/xrd_data_file.rd", parent=project):
        ...   project.specimens.append(specimen)
        ...
        
    """

    # MODEL INTEL:
    class Meta(DataModel.Meta):
        properties = [
            PropIntel(name="name", label="Name", data_type=str, **PropIntel.ST_WID),
            PropIntel(name="date", label="Date", data_type=str, **PropIntel.ST_WID),
            PropIntel(name="description", label="Description", data_type=str, widget_type="text_view", **PropIntel.ST_WID),
            PropIntel(name="author", label="Author", data_type=str, **PropIntel.ST_WID),
            OptionPropIntel(name="layout_mode", label="Layout mode", data_type=str, options=settings.DEFAULT_LAYOUTS, **PropIntel.ST_WID),
            PropIntel(name="display_marker_color", label="Color", data_type=str, widget_type="color", **PropIntel.ST_WID),
            PropIntel(name="display_marker_top_offset", label="Offset from base", data_type=float, widget_type="float_entry", **PropIntel.ST_WID),
            PropIntel(name="display_marker_angle", label="Angle", data_type=float, widget_type="float_entry", **PropIntel.ST_WID),
            OptionPropIntel(name="display_marker_align", label="Label alignment", data_type=str, options=settings.MARKER_ALIGNS, **PropIntel.ST_WID),
            OptionPropIntel(name="display_marker_base", label="Base connection", data_type=int, options=settings.MARKER_BASES, **PropIntel.ST_WID),
            OptionPropIntel(name="display_marker_top", label="Top connection", data_type=int, options=settings.MARKER_TOPS, **PropIntel.ST_WID),
            OptionPropIntel(name="display_marker_style", label="Line style", data_type=str, options=settings.MARKER_STYLES, **PropIntel.ST_WID),
            PropIntel(name="display_calc_color", label="Calculated color", data_type=str, widget_type="color", **PropIntel.ST_WID),
            PropIntel(name="display_exp_color", label="Experimental color", data_type=str, widget_type="color", **PropIntel.ST_WID),
            PropIntel(name="display_calc_lw", label="Calculated linewidth", data_type=int, widget_type="spin", **PropIntel.ST_WID),
            PropIntel(name="display_exp_lw", label="Experimental linewidth", data_type=int, widget_type="spin", **PropIntel.ST_WID),
            PropIntel(name="display_plot_offset", label="Pattern offset", data_type=float, widget_type="float_entry", **PropIntel.ST_WID),
            PropIntel(name="display_group_by", label="Group patterns by", data_type=int, widget_type="spin", **PropIntel.ST_WID),
            PropIntel(name="display_label_pos", label="Default label position", data_type=float, widget_type="float_entry", **PropIntel.ST_WID),
            OptionPropIntel(name="axes_xlimit", label="X limit", data_type=int, options=settings.AXES_XLIMITS, **PropIntel.ST_WID),
            PropIntel(name="axes_xmin", label="min. [°2T]", data_type=float, widget_type="spin", **PropIntel.ST_WID),
            PropIntel(name="axes_xmax", label="max. [°2T]", data_type=float, widget_type="spin", **PropIntel.ST_WID),
            PropIntel(name="axes_xstretch", label="Stretch X-axis to fit window", data_type=bool, **PropIntel.ST_WID),
            PropIntel(name="axes_dspacing", label="Show d-spacing in x-axis", data_type=bool, **PropIntel.ST_WID),
            OptionPropIntel(name="axes_ynormalize", label="Y scaling", data_type=int, options=settings.AXES_YNORMALIZERS, **PropIntel.ST_WID),
            OptionPropIntel(name="axes_ylimit", label="Y limit", data_type=int, options=settings.AXES_YLIMITS, **PropIntel.ST_WID),
            PropIntel(name="axes_ymin", label="min. [counts]", data_type=float, widget_type="spin", **PropIntel.ST_WID),
            PropIntel(name="axes_ymax", label="max. [counts]", data_type=float, widget_type="spin", **PropIntel.ST_WID),
            PropIntel(name="axes_yvisible", label="Y-axis visible", data_type=bool, **PropIntel.ST_WID),
            PropIntel(name="specimens", label="Specimens", data_type=object, widget_type="object_list_view", class_type=Specimen, **PropIntel.ST_WID),
            PropIntel(name="phases", data_type=object, class_type=Phase, **PropIntel.ST),
            PropIntel(name="mixtures", data_type=object, class_type=Mixture, **PropIntel.ST),
            PropIntel(name="atom_types", data_type=object, class_type=AtomType, **PropIntel.ST),
            PropIntel(name="needs_saving", data_type=bool),
        ]
        store_id = "Project"
        file_filters = [
            ("PyXRD Project files", get_case_insensitive_glob("*.pyxrd", "*.zpd")),
        ]
        import_filters = [
            ("Sybilla XML files", get_case_insensitive_glob("*.xml")),
        ]

    # PROPERTIES:
    #: The project name
    name = ""
    #: The project data (string)
    date = ""
    #: The project description
    description = None
    #: The project author
    author = ""

    #: Flag indicating whether this project has been changed since it was last saved.
    needs_saving = True

    _layout_mode = settings.DEFAULT_LAYOUT
    @property
    def layout_mode(self):
        """The layout mode this project should be displayed in"""
        return self._layout_mode
    @layout_mode.setter
    def layout_mode(self, value):
        with self.visuals_changed.hold_and_emit():
            self._layout_mode = value

    _axes_xmin = settings.AXES_MANUAL_XMIN
    @property
    def axes_xmin(self):
        """ The manual lower limit for the X-axis"""
        return self._axes_xmin
    @axes_xmin.setter
    def axes_xmin(self, value):
        self._axes_xmin = max(float(value), 0.0)
        self.visuals_changed.emit()

    _axes_xmax = settings.AXES_MANUAL_XMAX
    @property
    def axes_xmax(self):
        """ The manual upper limit for the X-axis """
        return self._axes_xmax
    @axes_xmax.setter
    def axes_xmax(self, value):
        self._axes_xmax = max(float(value), 0.0)
        self.visuals_changed.emit()

    _axes_xstretch = settings.AXES_XSTRETCH
    @property
    def axes_xstretch(self):
        """ Whether or not to stretch the X-axis over the entire
        available display """
        return self._axes_xstretch
    @axes_xstretch.setter
    def axes_xstretch(self, value):
        self._axes_xstretch = bool(value)
        self.visuals_changed.emit()

    _axes_dspacing = settings.AXES_DSPACING
    def get_axes_dspacing(self): return self._axes_dspacing
    def set_axes_dspacing(self, value):
        self._axes_dspacing = bool(value)
        self.visuals_changed.emit()

    _axes_yvisible = settings.AXES_YVISIBLE
    @property
    def axes_yvisible(self):
        """ Whether or not the y-axis should be shown """
        return self._axes_yvisible
    @axes_yvisible.setter
    def axes_yvisible(self, value):
        self._axes_yvisible = bool(value)
        self.visuals_changed.emit()

    _axes_ymin = settings.AXES_MANUAL_YMIN
    @property
    def axes_ymin(self):
        """ The manual lower limit for the Y-axis (in counts) """
        return self._axes_ymin
    @axes_ymin.setter
    def axes_ymin(self, value):
        self._axes_ymin = max(float(value), 0.0)
        self.visuals_changed.emit()

    _axes_ymax = settings.AXES_MANUAL_YMAX
    @property
    def axes_ymax(self):
        """ The manual upper limit for the Y-axis (in counts) """
        return self._axes_ymax
    @axes_ymax.setter
    def axes_ymax(self, value):
        self._axes_ymax = max(float(value), 0.0)
        self.visuals_changed.emit()

    _display_plot_offset = settings.PLOT_OFFSET
    @property
    def display_plot_offset(self):
        """ The offset between patterns as a fraction of the maximum
         intensity """
        return self._display_plot_offset
    @display_plot_offset.setter
    def display_plot_offset(self, value):
        self._display_plot_offset = max(float(value), 0.0)
        self.visuals_changed.emit()

    _display_group_by = settings.PATTERN_GROUP_BY
    @property
    def display_group_by(self):
        """ The number of patterns to group (having no offset) """
        return self._display_group_by
    @display_group_by.setter
    def display_group_by(self, value):
        self._display_group_by = max(int(value), 1)
        self.visuals_changed.emit()

    _display_marker_angle = settings.MARKER_ANGLE
    @property
    def display_marker_angle(self):
        """ The default angle at which marker labels are displayed """
        return self._display_marker_angle
    @display_marker_angle.setter
    def display_marker_angle(self, value):
        self._display_marker_angle = float(value)
        self.visuals_changed.emit()

    _display_marker_top_offset = settings.MARKER_TOP_OFFSET
    @property
    def display_marker_top_offset(self):
        """ The default offset for marker labels """
        return self._display_marker_top_offset
    @display_marker_top_offset.setter
    def display_marker_top_offset(self, value):
        self._display_marker_top_offset = float(value)
        self.visuals_changed.emit()

    _display_label_pos = settings.LABEL_POSITION
    @property
    def display_label_pos(self):
        """ The relative position (from the pattern offset) for pattern labels
        as a fraction of the patterns intensity"""
        return self._display_label_pos
    @display_label_pos.setter
    def display_label_pos(self, value):
        self._display_label_pos = float(value)
        self.visuals_changed.emit()

    _axes_xlimit = settings.AXES_XLIMIT
    @property
    def axes_xlimit(self):
        """ What type of scale to use for X-axis, automatic or manual """
        return self._axes_xlimit
    @axes_xlimit.setter
    def axes_xlimit(self, value):
        self._axes_xlimit = int(value)
        self.visuals_changed.emit()

    _axes_ynormalize = settings.AXES_YNORMALIZE
    @property
    def axes_ynormalize(self):
        """ What type of y-axis to use: raw counts, single or 
        multi-normalized units """
        return self._axes_ynormalize
    @axes_ynormalize.setter
    def axes_ynormalize(self, value):
        self._axes_ynormalize = int(value)
        self.visuals_changed.emit()

    _axes_ylimit = settings.AXES_YLIMIT
    @property
    def axes_ylimit(self):
        """ Whether to use automatic or manual Y limits """
        return self._axes_ylimit
    @axes_ylimit.setter
    def axes_ylimit(self, value):
        self._axes_ylimit = int(value)
        self.visuals_changed.emit()

    _display_marker_align = settings.MARKER_ALIGN
    @property
    def display_marker_align(self):
        """ The default marker label alignment (one of settings.MARKER_ALIGNS) """
        return self._display_marker_align
    @display_marker_align.setter
    def display_marker_align(self, value):
        self._display_marker_align = value
        self.visuals_changed.emit()

    _display_marker_base = settings.MARKER_BASE
    @property
    def display_marker_base(self):
        """ The default marker label base (one of settings.MARKER_BASES) """
        return self._display_marker_base
    @display_marker_base.setter
    def display_marker_base(self, value):
        self._display_marker_base = int(value)
        self.visuals_changed.emit()

    _display_marker_top = settings.MARKER_TOP
    @property
    def display_marker_top(self):
        """ The default marker label top (one of settings.MARKER_TOPS) """
        return self._display_marker_top
    @display_marker_top.setter
    def display_marker_top(self, value):
        self._display_marker_top = int(value)
        self.visuals_changed.emit()

    _display_marker_style = settings.MARKER_STYLE
    @property
    def display_marker_style(self):
        """ The default marker style (one of settings.MARKER_STYLES)"""
        return self._display_marker_style
    @display_marker_style.setter
    def display_marker_style(self, value):
        self._display_marker_style = value
        self.visuals_changed.emit()

    _display_calc_color = settings.CALCULATED_COLOR
    @property
    def display_calc_color(self):
        """ The default calculated profile color """
        return self._display_calc_color
    @display_calc_color.setter
    def display_calc_color(self, value):
        self._display_calc_color = value
        self.visuals_changed.emit()

    _display_exp_color = settings.EXPERIMENTAL_COLOR
    @property
    def display_exp_color(self):
        """ The default experimental profile color """
        return self._display_exp_color
    @display_exp_color.setter
    def display_exp_color(self, value):
        self._display_exp_color = value
        self.visuals_changed.emit()

    _display_marker_color = settings.MARKER_COLOR
    @property
    def display_marker_color(self):
        """ The default marker color """
        return self._display_marker_color
    @display_marker_color.setter
    def display_marker_color(self, value):
        self._display_marker_color = value
        self.visuals_changed.emit()

    _display_calc_lw = settings.CALCULATED_LINEWIDTH
    @property
    def display_calc_lw(self):
        """ The default calculated profile line width """
        return self._display_calc_lw
    @display_calc_lw.setter
    def display_calc_lw(self, value):
        if value != self._display_calc_lw:
            self._display_calc_lw = float(value)
            self.visuals_changed.emit()

    _display_exp_lw = settings.EXPERIMENTAL_LINEWIDTH
    @property
    def display_exp_lw(self):
        """ The default experimental profile line width """
        return self._display_exp_lw
    @display_exp_lw.setter
    def display_exp_lw(self, value):
        if value != self._display_exp_lw:
            self._display_exp_lw = float(value)
            self.visuals_changed.emit()

    #: The list of specimens
    specimens = []
    #: The list of phases
    phases = []
    #: The list of atom types
    atom_types = []
    #: The list of mixtures
    mixtures = []

    # ------------------------------------------------------------
    #      Initialization and other internals
    # ------------------------------------------------------------
    def __init__(self, *args, **kwargs):
        """
            Constructor takes any of its properties as a keyword argument 
            except for:
                - needs_saving
            
            In addition to the above, the constructor still supports the 
            following deprecated keywords, mapping to a current keyword:
                - goniometer: the project-level goniometer, is passed on to the
                  specimens
                - axes_xscale: deprecated alias for axes_xlimit
                - axes_yscale: deprecated alias for axes_ynormalize
                
            Any other arguments or keywords are passed to the base class.
        """
        my_kwargs = self.pop_kwargs(kwargs,
            "goniometer", "data_goniometer", "data_atom_types", "data_phases",
            "axes_yscale", "axes_xscale",
            *[names[0] for names in type(self).Meta.get_local_storable_properties()]
        )
        super(Project, self).__init__(*args, **kwargs)
        kwargs = my_kwargs

        with self.data_changed.hold():
            with self.visuals_changed.hold():

                self.layout_mode = self.get_kwarg(kwargs, self.layout_mode, "layout_mode")

                self.display_marker_align = self.get_kwarg(kwargs, self.display_marker_align, "display_marker_align")
                self.display_marker_color = self.get_kwarg(kwargs, self.display_marker_color, "display_marker_color")
                self.display_marker_base = self.get_kwarg(kwargs, self.display_marker_base, "display_marker_base")
                self.display_marker_top = self.get_kwarg(kwargs, self.display_marker_top, "display_marker_top")
                self.display_marker_top_offset = self.get_kwarg(kwargs, self.display_marker_top_offset, "display_marker_top_offset")
                self.display_marker_angle = self.get_kwarg(kwargs, self.display_marker_angle, "display_marker_angle")
                self.display_marker_style = self.get_kwarg(kwargs, self.display_marker_style, "display_marker_style")

                self.display_calc_color = self.get_kwarg(kwargs, self.display_calc_color, "display_calc_color")
                self.display_exp_color = self.get_kwarg(kwargs, self.display_exp_color, "display_exp_color")
                self.display_calc_lw = self.get_kwarg(kwargs, self.display_calc_lw, "display_calc_lw")
                self.display_exp_lw = self.get_kwarg(kwargs, self.display_exp_lw, "display_exp_lw")
                self.display_plot_offset = self.get_kwarg(kwargs, self.display_plot_offset, "display_plot_offset")
                self.display_group_by = self.get_kwarg(kwargs, self.display_group_by, "display_group_by")
                self.display_label_pos = self.get_kwarg(kwargs, self.display_label_pos, "display_label_pos")

                self.axes_xlimit = self.get_kwarg(kwargs, self.axes_xlimit, "axes_xlimit", "axes_xscale")
                self.axes_xmin = self.get_kwarg(kwargs, self.axes_xmin, "axes_xmin")
                self.axes_xmax = self.get_kwarg(kwargs, self.axes_xmax, "axes_xmax")
                self.axes_xstretch = self.get_kwarg(kwargs, self.axes_xstretch, "axes_xstretch")
                self.axes_ylimit = self.get_kwarg(kwargs, self.axes_ylimit, "axes_ylimit")
                self.axes_ynormalize = self.get_kwarg(kwargs, self.axes_ynormalize, "axes_ynormalize", "axes_yscale")
                self.axes_yvisible = self.get_kwarg(kwargs, self.axes_yvisible, "axes_yvisible")
                self.axes_ymin = self.get_kwarg(kwargs, self.axes_ymin, "axes_ymin")
                self.axes_ymax = self.get_kwarg(kwargs, self.axes_ymax, "axes_ymax")

                goniometer = None
                goniometer_kwargs = self.get_kwarg(kwargs, None, "goniometer", "data_goniometer")
                if goniometer_kwargs:
                    goniometer = self.parse_init_arg(goniometer_kwargs, None, child=True)

                # Set up and observe atom types:
                self.atom_types = self.get_list(kwargs, [], "atom_types", "data_atom_types", parent=self)
                self._atom_types_observer = ListObserver(
                    self.on_atom_type_inserted,
                    self.on_atom_type_removed,
                    prop_name="atom_types",
                    model=self
                )

                # Resolve json references & observe phases
                self.phases = self.get_list(kwargs, [], "phases", "data_phases", parent=self)
                for phase in self.phases:
                    phase.resolve_json_references()
                    self.observe_model(phase)
                self._phases_observer = ListObserver(
                    self.on_phase_inserted,
                    self.on_phase_removed,
                    prop_name="phases",
                    model=self
                )

                # Set goniometer if required & observe specimens
                self.specimens = self.get_list(kwargs, [], "specimens", "data_specimens", parent=self)
                for specimen in self.specimens:
                    if goniometer: specimen.goniometer = goniometer
                    self.observe_model(specimen)
                self._specimens_observer = ListObserver(
                    self.on_specimen_inserted,
                    self.on_specimen_removed,
                    prop_name="specimens",
                    model=self
                )

                # Observe mixtures:
                self.mixtures = self.get_list(kwargs, [], "mixtures", "data_mixtures", parent=self)
                for mixture in self.mixtures:
                    self.observe_model(mixture)
                self._mixtures_observer = ListObserver(
                    self.on_mixture_inserted,
                    self.on_mixture_removed,
                    prop_name="mixtures",
                    model=self
                )

                self.name = str(self.get_kwarg(kwargs, "Project name", "name", "data_name"))
                self.date = str(self.get_kwarg(kwargs, time.strftime("%d/%m/%Y"), "date", "data_date"))
                self.description = str(self.get_kwarg(kwargs, "Project description", "description", "data_description"))
                self.author = str(self.get_kwarg(kwargs, "Project author", "author", "data_author"))

                load_default_data = self.get_kwarg(kwargs, True, "load_default_data")
                if load_default_data and self.layout_mode != 1 and \
                    len(self.atom_types) == 0: self.load_default_data()

                self.needs_saving = True
            pass # end with visuals_changed
        pass # end with data_changed

    def load_default_data(self):
        for atom_type in AtomType.get_from_csv(settings.DATA_REG.get_file_path("ATOM_SCAT_FACTORS")):
            self.atom_types.append(atom_type)

    # ------------------------------------------------------------
    #      Notifications of observable properties
    # ------------------------------------------------------------
    def on_phase_inserted(self, item):
        # Set parent on the new phase:
        if item.parent != self: item.parent = self
        item.resolve_json_references()

    def on_phase_removed(self, item):
        with self.data_changed.hold_and_emit():
            # Clear parent:
            item.parent = None
            # Clear links with other phases:
            if item.based_on is not None:
                item.based_on = None
            for phase in self.phases:
                if phase.based_on == item:
                    phase.based_on = None
            # Remove phase from mixtures:
            for mixture in self.mixtures:
                mixture.unset_phase(item)

    def on_atom_type_inserted(self, item, *data):
        if item.parent != self: item.parent = self
        # We do not observe AtomType's directly, if they change,
        # Atoms containing them will be notified, and that event should bubble
        # up to the project level.

    def on_atom_type_removed(self, item, *data):
        item.parent = None
        # We do not emit a signal for AtomType's, if it was part of
        # an Atom, the Atom will be notified, and the event should bubble
        # up to the project level

    def on_specimen_inserted(self, item):
        # Set parent and observe the new specimen (visuals changed signals):
        if item.parent != self: item.parent = self
        self.observe_model(item)

    def on_specimen_removed(self, item):
        with self.data_changed.hold_and_emit():
            # Clear parent & stop observing:
            item.parent = None
            self.relieve_model(item)
            # Remove specimen from mixtures:
            for mixture in self.mixtures:
                mixture.unset_specimen(item)

    def on_mixture_inserted(self, item):
        # Set parent and observe the new mixture:
        if item.parent != self: item.parent = self
        self.observe_model(item)

    def on_mixture_removed(self, item):
        with self.data_changed.hold_and_emit():
            # Clear parent & stop observing:
            item.parent = None
            self.relieve_model(item)

    @Observer.observe("data_changed", signal=True)
    def notify_data_changed(self, model, prop_name, info):
        self.needs_saving = True
        if isinstance(model, Mixture):
            self.data_changed.emit()

    @Observer.observe("visuals_changed", signal=True)
    def notify_visuals_changed(self, model, prop_name, info):
        self.needs_saving = True
        self.visuals_changed.emit() # propagate signal

    # ------------------------------------------------------------
    #      Input/Output stuff
    # ------------------------------------------------------------
    @classmethod
    def from_json(type, **kwargs): # @ReservedAssignment
        project = type(**kwargs)
        project.needs_saving = False # don't mark this when just loaded
        return project

    def save_object(self, file): # @ReservedAssignment
        Storable.save_object(self, file, zipped=True)
        type(self).object_pool.change_all_uuids()
        self.needs_saving = False

    @classmethod
    def load_object(cls, filename, data=None, parent=None):
        type(cls).object_pool.change_all_uuids()
        return Storable.load_object(filename, data=data, parent=parent)

    def to_json_multi_part(self):
        to_json = self.to_json()
        properties = to_json["properties"]

        for name in ("phases", "specimens", "atom_types", "mixtures"):
            yield (name, properties.pop(name))
            properties[name] = "file://%s" % name

        yield ("content", to_json)

    @staticmethod
    def create_from_sybilla_xml(filename, **kwargs):
        from pyxrd.project.importing import create_project_from_sybilla_xml
        return create_project_from_sybilla_xml(filename, **kwargs)

    # ------------------------------------------------------------
    #      Draggable mix-in hook:
    # ------------------------------------------------------------
    def on_label_dragged(self, delta_y, button=1):
        if button == 1:
            self.display_label_pos += delta_y
        pass

    # ------------------------------------------------------------
    #      Methods & Functions
    # ------------------------------------------------------------
    def get_scale_factor(self, specimen=None):
        """
        Get the factor with which to scale raw data and the scaled offset
                
        :rtype: tuple containing the scale factor and the (scaled) offset
        """
        if self.axes_ynormalize == 0 or (self.axes_ynormalize == 1 and specimen is None):
            return (1.0 / (self.get_max_intensity() or 1.0), 1.0)
        elif self.axes_ynormalize == 1:
            return (1.0 / (specimen.max_intensity or 1.0), 1.0)
        elif self.axes_ynormalize == 2:
            return (1.0, self.get_max_intensity())
        else:
            raise ValueError, "Wrong value for 'axes_ysnormalize' in %s: is `%d`; should be 0, 1 or 2" % (self, self.axes_ynormalize)

    def get_max_intensity(self):
        max_intensity = 0
        if self.parent is not None:
            for specimen in self.parent.current_specimens:
                max_intensity = max(specimen.max_intensity, max_intensity)
        return max_intensity

    @contextmanager
    def hold_child_signals(self):
        logger.info("Holding back all project child object signals")
        with self.hold_mixtures_needs_update():
            with self.hold_mixtures_data_changed():
                with self.hold_phases_data_changed():
                    with self.hold_specimens_data_changed():
                        with self.hold_atom_types_data_changed():
                            yield

    @contextmanager
    def hold_mixtures_needs_update(self):
        logger.info("Holding back all 'needs_update' signals from Mixtures")
        with ExitStack() as stack:
            for mixture in self.mixtures:
                stack.enter_context(mixture.needs_update.hold())
            yield

    @contextmanager
    def hold_mixtures_data_changed(self):
        logger.info("Holding back all 'data_changed' signals from Mixtures")
        with ExitStack() as stack:
            for mixture in self.mixtures:
                stack.enter_context(mixture.data_changed.hold())
            yield

    @contextmanager
    def hold_phases_data_changed(self):
        logger.info("Holding back all 'data_changed' signals from Phases")
        with ExitStack() as stack:
            for phase in self.phases:
                stack.enter_context(phase.data_changed.hold())
            yield

    @contextmanager
    def hold_atom_types_data_changed(self):
        logger.info("Holding back all 'data_changed' signals from AtomTypes")
        with ExitStack() as stack:
            for atom_type in self.atom_types:
                stack.enter_context(atom_type.data_changed.hold())
            yield

    @contextmanager
    def hold_specimens_data_changed(self):
        logger.info("Holding back all 'data_changed' signals from Specimens")
        with ExitStack() as stack:
            for specimen in self.specimens:
                stack.enter_context(specimen.data_changed.hold())
            yield

    def update_all_mixtures(self):
        """
        Forces all mixtures in this project to update. If they have auto
        optimization enabled, this will also optimize them. 
        """
        for mixture in self.mixtures:
            with self.data_changed.ignore():
                mixture.update()

    def get_mixtures_by_name(self, mixture_name):
        """
        Convenience method that returns all the mixtures who's name match the
        passed name as a list.
        """
        return filter(
            lambda mixture: (mixture.name == mixture_name),
            self.mixtures
        )

    # ------------------------------------------------------------
    #      Specimen list related
    # ------------------------------------------------------------
    def move_specimen_up(self, specimen):
        """
        Move the passed :class:`~pyxrd.specimen.models.Specimen` up one slot.
        Will raise and IndexError if the passed specimen is not in this project.
        """
        index = self.specimens.index(specimen)
        self.specimens.insert(min(index + 1, len(self.specimens)), self.specimens.pop(index))

    def move_specimen_down(self, specimen):
        """
        Move the passed :class:`~pyxrd.specimen.models.Specimen` down one slot
        Will raise and IndexError if the passed specimen is not in this project.
        """
        index = self.specimens.index(specimen)
        self.specimens.insert(max(index - 1, 0), self.specimens.pop(index))
        pass

    # ------------------------------------------------------------
    #      Phases list related
    # ------------------------------------------------------------
    def load_phases(self, filename, insert_index=None):
        """
        Loads all :class:`~pyxrd.phase.models.Phase` objects from the file
        'filename'. An optional index can be given where the phases need to be
        inserted at.
        """
        insert_index = not_none(insert_index, 0)
        for phase in Phase.load_phases(filename, parent=self):
            self.phases.insert(insert_index, phase)
            insert_index += 1

    # ------------------------------------------------------------
    #      AtomType's list related
    # ------------------------------------------------------------
    def load_atom_types_from_csv(self, filename):
        """
        Loads all :class:`~pyxrd.atoms.models.AtomType` objects from the CSV
        file specified by *filename*.
        """
        for atom_type in AtomType.get_from_csv(filename, parent=self):
            self.atom_types.append(atom_type)

    def load_atom_types(self, filename):
        """
        Loads all :class:`~pyxrd.atoms.models.AtomType` objects from the JSON
        file specified by *filename*.
        """
        for atom_type in AtomType.load_atom_types(filename, parent=self):
            self.atom_types.append(atom_type)

    pass # end of class
