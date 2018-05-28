# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import logging
logger = logging.getLogger(__name__)

import time
from contextlib import contextmanager

from mvc.models.properties import (
    FloatProperty, BoolProperty, StringProperty, ListProperty,
    IntegerProperty, StringChoiceProperty, IntegerChoiceProperty, SignalMixin
)

from mvc.observers import ListObserver

from pyxrd.__version import __version__

from pyxrd.data import settings

from pyxrd.generic.models import DataModel
from pyxrd.generic.models.event_context_manager import EventContextManager
from pyxrd.generic.io import storables, Storable, get_case_insensitive_glob
from pyxrd.generic.utils import not_none

from pyxrd.atoms.models import AtomType
from pyxrd.phases.models import Phase
from pyxrd.specimen.models import Specimen
from pyxrd.mixture.models.mixture import Mixture
#from pyxrd.mixture.models.insitu_behaviours import InSituBehaviour

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
        store_id = "Project"
        file_filters = [
            ("PyXRD Project files", get_case_insensitive_glob("*.pyxrd", "*.zpd")),
        ]
        import_filters = [
            ("Sybilla XML files", get_case_insensitive_glob("*.xml")),
        ]

    # PROPERTIES:

    filename = None

    #: The project name
    name = StringProperty(
        default="", text="Name",
        visible=True, persistent=True
    )

    #: The project data (string)
    date = StringProperty(
        default="", text="Date",
        visible=True, persistent=True
    )

    #: The project description
    description = StringProperty(
        default=None, text="Description",
        visible=True, persistent=True, widget_type="text_view",
    )

    #: The project author
    author = StringProperty(
        default="", text="Author",
        visible=True, persistent=True
    )

    #: Flag indicating whether this project has been changed since it was last saved.
    needs_saving = BoolProperty(
        default=True, visible=False, persistent=False
    )

    #: The layout mode this project should be displayed in
    layout_mode = StringChoiceProperty(
        default=settings.DEFAULT_LAYOUT, text="Layout mode",
        visible=True, persistent=True, choices=settings.DEFAULT_LAYOUTS,
        mix_with=(SignalMixin,), signal_name="visuals_changed"
    )

    #: The manual lower limit for the X-axis
    axes_xmin = FloatProperty(
        default=settings.AXES_MANUAL_XMIN, text="min. [°2T]",
        visible=True, persistent=True, minimum=0.0, widget_type="spin",
        mix_with=(SignalMixin,), signal_name="visuals_changed"
    )

    #: The manual upper limit for the X-axis
    axes_xmax = FloatProperty(
        default=settings.AXES_MANUAL_XMAX, text="max. [°2T]",
        visible=True, persistent=True, minimum=0.0, widget_type="spin",
        mix_with=(SignalMixin,), signal_name="visuals_changed"
    )

    #: Whether or not to stretch the X-axis over the entire available display
    axes_xstretch = BoolProperty(
        default=settings.AXES_XSTRETCH, text="Stetch x-axis to fit window",
        visible=True, persistent=True,
        mix_with=(SignalMixin,), signal_name="visuals_changed"
    )

    #: Flag toggling between d-spacing (when True) or 2-Theta axes (when False)
    axes_dspacing = BoolProperty(
        default=settings.AXES_DSPACING, text="Show d-spacing in x-axis",
        visible=True, persistent=True,
        mix_with=(SignalMixin,), signal_name="visuals_changed"
    )

    #: Whether or not the y-axis should be shown
    axes_yvisible = BoolProperty(
        default=settings.AXES_YVISIBLE, text="Y-axis visible",
        visible=True, persistent=True,
        mix_with=(SignalMixin,), signal_name="visuals_changed"
    )

    #: The manual lower limit for the Y-axis (in counts)
    axes_ymin = FloatProperty(
        default=settings.AXES_MANUAL_YMIN, text="min. [counts]",
        visible=True, persistent=True, minimum=0.0, widget_type="spin",
        mix_with=(SignalMixin,), signal_name="visuals_changed"
    )

    #: The manual upper limit for the Y-axis (in counts)
    axes_ymax = FloatProperty(
        default=settings.AXES_MANUAL_YMAX, text="max. [counts]",
        visible=True, persistent=True, minimum=0.0, widget_type="spin",
        mix_with=(SignalMixin,), signal_name="visuals_changed"
    )

    #: What type of y-axis to use: raw counts, single or multi-normalized units
    axes_ynormalize = IntegerChoiceProperty(
        default=settings.AXES_YNORMALIZE, text="Y scaling",
        visible=True, persistent=True, choices=settings.AXES_YNORMALIZERS,
        mix_with=(SignalMixin,), signal_name="visuals_changed"
    )

    #: Whether to use automatic or manual Y limits
    axes_ylimit = IntegerChoiceProperty(
        default=settings.AXES_YLIMIT, text="Y limit",
        visible=True, persistent=True, choices=settings.AXES_YLIMITS,
        mix_with=(SignalMixin,), signal_name="visuals_changed"
    )

    #: The offset between patterns as a fraction of the maximum intensity
    display_plot_offset = FloatProperty(
        default=settings.PLOT_OFFSET, text="Pattern offset",
        visible=True, persistent=True, minimum=0.0, widget_type="float_entry",
        mix_with=(SignalMixin,), signal_name="visuals_changed"
    )

    #: The number of patterns to group ( = having no offset)
    display_group_by = IntegerProperty(
        default=settings.PATTERN_GROUP_BY, text="Group patterns by",
        visible=True, persistent=True, minimum=1, widget_type="spin",
        mix_with=(SignalMixin,), signal_name="visuals_changed"
    )

    #: The relative position (from the pattern offset) for pattern labels
    #: as a fraction of the patterns intensity
    display_label_pos = FloatProperty(
        default=settings.LABEL_POSITION, text="Default label position",
        visible=True, persistent=True, widget_type="float_entry",
        mix_with=(SignalMixin,), signal_name="visuals_changed"
    )

    #: What type of scale to use for X-axis, automatic or manual
    axes_xlimit = IntegerChoiceProperty(
        default=settings.AXES_XLIMIT, text="X limit",
        visible=True, persistent=True,
        choices=settings.AXES_XLIMITS,
        mix_with=(SignalMixin,), signal_name="visuals_changed"
    )

    #: The default angle at which marker labels are displayed
    display_marker_angle = FloatProperty(
        default=settings.MARKER_ANGLE, text="Angle",
        visible=True, persistent=True, widget_type="float_entry",
        mix_with=(SignalMixin,), signal_name="visuals_changed"
    )

    #: The default offset for marker labels
    display_marker_top_offset = FloatProperty(
        default=settings.MARKER_TOP_OFFSET, text="Offset from base",
        visible=True, persistent=True, widget_type="float_entry",
        mix_with=(SignalMixin,), signal_name="visuals_changed"
    )

    #: The default marker label alignment (one of settings.MARKER_ALIGNS)
    display_marker_align = StringChoiceProperty(
        default=settings.MARKER_ALIGN, text="Label alignment",
        visible=True, persistent=True,
        choices=settings.MARKER_ALIGNS,
        mix_with=(SignalMixin,), signal_name="visuals_changed"
    )

    #: The default marker label base (one of settings.MARKER_BASES)
    display_marker_base = IntegerChoiceProperty(
        default=settings.MARKER_BASE, text="Base connection",
        visible=True, persistent=True,
        choices=settings.MARKER_BASES,
        mix_with=(SignalMixin,), signal_name="visuals_changed"
    )

    #: The default marker label top (one of settings.MARKER_TOPS)
    display_marker_top = IntegerChoiceProperty(
        default=settings.MARKER_TOP, text="Top connection",
        visible=True, persistent=True,
        choices=settings.MARKER_TOPS,
        mix_with=(SignalMixin,), signal_name="visuals_changed"
    )

    #: The default marker style (one of settings.MARKER_STYLES)
    display_marker_style = StringChoiceProperty(
        default=settings.MARKER_STYLE, text="Line style",
        visible=True, persistent=True,
        choices=settings.MARKER_STYLES,
        mix_with=(SignalMixin,), signal_name="visuals_changed"
    )

    #: The default marker color
    display_marker_color = StringProperty(
        default=settings.MARKER_COLOR, text="Color",
        visible=True, persistent=True, widget_type="color",
        mix_with=(SignalMixin,), signal_name="visuals_changed"
    )

    #: The default calculated profile color
    display_calc_color = StringProperty(
        default=settings.CALCULATED_COLOR, text="Calculated color",
        visible=True, persistent=True, widget_type="color",
        mix_with=(SignalMixin,), signal_name="visuals_changed"
    )

    #: The default experimental profile color
    display_exp_color = StringProperty(
        default=settings.EXPERIMENTAL_COLOR, text="Experimental color",
        visible=True, persistent=True, widget_type="color",
        mix_with=(SignalMixin,), signal_name="visuals_changed"
    )

    #: The default calculated profile line width
    display_calc_lw = IntegerProperty(
        default=settings.CALCULATED_LINEWIDTH, text="Calculated line width",
        visible=True, persistent=True, widget_type="spin",
        mix_with=(SignalMixin,), signal_name="visuals_changed"
    )

    #: The default experimental profile line width
    display_exp_lw = IntegerProperty(
        default=settings.EXPERIMENTAL_LINEWIDTH, text="Experimental line width",
        visible=True, persistent=True, widget_type="spin",
        mix_with=(SignalMixin,), signal_name="visuals_changed"
    )

    #: The default calculated profile line style
    display_calc_ls = StringChoiceProperty(
        default=settings.CALCULATED_LINESTYLE, text="Calculated line style",
        visible=True, persistent=True,
        choices=settings.PATTERN_LINE_STYLES,
        mix_with=(SignalMixin,), signal_name="visuals_changed"
    )

    #: The default experimental profile line style
    display_exp_ls = StringChoiceProperty(
        default=settings.EXPERIMENTAL_LINESTYLE, text="Experimental line style",
        visible=True, persistent=True,
        choices=settings.PATTERN_LINE_STYLES,
        mix_with=(SignalMixin,), signal_name="visuals_changed"
    )

    #: The default calculated profile line style
    display_calc_marker = StringChoiceProperty(
        default=settings.CALCULATED_MARKER, text="Calculated line marker",
        visible=True, persistent=True,
        choices=settings.PATTERN_MARKERS,
        mix_with=(SignalMixin,), signal_name="visuals_changed"
    )

    #: The default calculated profile line style
    display_exp_marker = StringChoiceProperty(
        default=settings.EXPERIMENTAL_MARKER, text="Experimental line marker",
        visible=True, persistent=True,
        choices=settings.PATTERN_MARKERS,
        mix_with=(SignalMixin,), signal_name="visuals_changed"
    )

    #: The list of specimens
    specimens = ListProperty(
        default=[], text="Specimens", data_type=Specimen,
        visible=True, persistent=True,
    )

    #: The list of phases
    phases = ListProperty(
        default=[], text="Phases", data_type=Phase,
        visible=False, persistent=True
    )

    #: The list of atom types
    atom_types = ListProperty(
        default=[], text="Atom types", data_type=AtomType,
        visible=False, persistent=True
    )

    #: The list of Behaviours
    #behaviours = ListProperty(
    #    default=[], text="Behaviours", data_type=InSituBehaviour,
    #    visible=False, persistent=True
    #)

    #: The list of mixtures
    mixtures = ListProperty(
        default=[], text="Mixture", data_type=Mixture,
        visible=False, persistent=True
    )

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
            "axes_yscale", "axes_xscale", "filename", "behaviours",
            *[prop.label for prop in Project.Meta.get_local_persistent_properties()]
        )
        super(Project, self).__init__(*args, **kwargs)
        kwargs = my_kwargs

        with self.data_changed.hold():
            with self.visuals_changed.hold():

                self.filename = self.get_kwarg(kwargs, self.filename, "filename")
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
                self.display_calc_ls = self.get_kwarg(kwargs, self.display_calc_ls, "display_calc_ls")
                self.display_exp_ls = self.get_kwarg(kwargs, self.display_exp_ls, "display_exp_ls")
                self.display_calc_marker = self.get_kwarg(kwargs, self.display_calc_marker, "display_calc_marker")
                self.display_exp_marker = self.get_kwarg(kwargs, self.display_exp_marker, "display_exp_marker")
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

                # Observe behaviours:
                #self.behaviours = self.get_list(kwargs, [], "behaviours", parent=self)
                #for behaviour in self.behaviours:
                #    self.observe_model(behaviour)
                #self._behaviours_observer = ListObserver(
                #    self.on_behaviour_inserted,
                #    self.on_behaviour_removed,
                #    prop_name="behaviours",
                #    model=self
                #)

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
            if getattr(item, "based_on", None) is not None:
                item.based_on = None
            for phase in self.phases:
                if getattr(phase, "based_on", None) == item:
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

    def on_behaviour_inserted(self, item):
        # Set parent and observe the new mixture:
        if item.parent != self: item.parent = self
        self.observe_model(item)

    def on_behaviour_removed(self, item):
        with self.data_changed.hold_and_emit():
            # Clear parent & stop observing:
            item.parent = None
            self.relieve_model(item)

    @DataModel.observe("data_changed", signal=True)
    def notify_data_changed(self, model, prop_name, info):
        self.needs_saving = True
        if isinstance(model, Mixture):
            self.data_changed.emit()

    @DataModel.observe("visuals_changed", signal=True)
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

    def to_json_multi_part(self):
        to_json = self.to_json()
        properties = to_json["properties"]

        for name in ("phases", "specimens", "atom_types", "mixtures"): #"behaviours"
            yield (name, properties.pop(name))
            properties[name] = "file://%s" % name

        yield ("content", to_json)
        yield ("version", __version__)

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
            return (1.0 / (self.get_max_display_y() or 1.0), 1.0)
        elif self.axes_ynormalize == 1:
            return (1.0 / (specimen.get_max_display_y or 1.0), 1.0)
        elif self.axes_ynormalize == 2:
            return (1.0, self.get_max_display_y())
        else:
            raise ValueError("Wrong value for 'axes_ysnormalize' in %s: is `%d`; should be 0, 1 or 2" % (self, self.axes_ynormalize))

    def get_max_display_y(self):
        max_display_y = 0
        if self.parent is not None:
            for specimen in self.parent.current_specimens:
                max_display_y = max(specimen.max_display_y, max_display_y)
        return max_display_y

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
        with EventContextManager(*[mixture.needs_update.hold() for mixture in self.mixtures]):
            yield

    @contextmanager
    def hold_mixtures_data_changed(self):
        logger.info("Holding back all 'data_changed' signals from Mixtures")
        with EventContextManager(*[mixture.data_changed.hold() for mixture in self.mixtures]):
            yield

    @contextmanager
    def hold_phases_data_changed(self):
        logger.info("Holding back all 'data_changed' signals from Phases")
        with EventContextManager(*[phase.data_changed.hold() for phase in self.phases]):
            yield

    @contextmanager
    def hold_atom_types_data_changed(self):
        logger.info("Holding back all 'data_changed' signals from AtomTypes")
        with EventContextManager(*[atom_type.data_changed.hold() for atom_type in self.atom_types]):
            yield

    @contextmanager
    def hold_specimens_data_changed(self):
        logger.info("Holding back all 'data_changed' signals from Specimens")
        with EventContextManager(*[specimen.data_changed.hold() for specimen in self.specimens]):
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
        return [mixture for mixture in self.mixtures if (mixture.name == mixture_name)]

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
    def load_phases(self, filename, parser, insert_index=0):
        """
        Loads all :class:`~pyxrd.phase.models.Phase` objects from the file
        'filename'. An optional index can be given where the phases need to be
        inserted at.
        """
        # make sure we have no duplicate UUID's
        insert_index = not_none(insert_index, 0)
        type(Project).object_pool.change_all_uuids()
        for phase in parser.parse(filename):
            phase.parent = self
            self.phases.insert(insert_index, phase)
            insert_index += 1

    # ------------------------------------------------------------
    #      AtomType's list related
    # ------------------------------------------------------------
    def load_atom_types(self, filename, parser):
        """
        Loads all :class:`~pyxrd.atoms.models.AtomType` objects from the
        file specified by *filename*.
        """
        # make sure we have no duplicate UUID's
        type(Project).object_pool.change_all_uuids()
        for atom_type in parser.parse(filename):
            atom_type.parent = self
            self.atom_types.append(atom_type)

    pass # end of class
