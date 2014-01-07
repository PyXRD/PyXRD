# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import time

from pyxrd.gtkmvc.model import Observer
from pyxrd.gtkmvc.support.propintel import PropIntel, OptionPropIntel

from pyxrd.data import settings

from pyxrd.generic.models import DataModel
from pyxrd.generic.models.observers import ListObserver
from pyxrd.generic.io import storables, Storable, get_case_insensitive_glob

from pyxrd.phases.models import Phase
from pyxrd.atoms.models import AtomType
from pyxrd.mixture.models.mixture import Mixture
from pyxrd.generic.utils import not_none

prop_kwargs = dict(
    storable=True,
    has_widget=True
)

@storables.register()
class Project(DataModel, Storable):
    # MODEL INTEL:
    class Meta(DataModel.Meta):
        properties = [ # TODO add labels
            PropIntel(name="name", data_type=str, **prop_kwargs),
            PropIntel(name="date", data_type=str, **prop_kwargs),
            PropIntel(name="description", data_type=str, widget_type="text_view", **prop_kwargs),
            PropIntel(name="author", data_type=str, **prop_kwargs),
            OptionPropIntel(name="layout_mode", data_type=str, options=settings.DEFAULT_LAYOUTS, **prop_kwargs),
            OptionPropIntel(name="display_marker_align", data_type=str, options=settings.MARKER_ALIGNS, **prop_kwargs),
            PropIntel(name="display_marker_color", data_type=str, widget_type="color", **prop_kwargs),
            OptionPropIntel(name="display_marker_base", data_type=int, options=settings.MARKER_BASES, **prop_kwargs),
            OptionPropIntel(name="display_marker_top", data_type=int, options=settings.MARKER_TOPS, **prop_kwargs),
            PropIntel(name="display_marker_top_offset", data_type=float, widget_type="float_entry", **prop_kwargs),
            PropIntel(name="display_marker_angle", data_type=float, widget_type="float_entry", **prop_kwargs),
            OptionPropIntel(name="display_marker_style", data_type=str, options=settings.MARKER_STYLES, **prop_kwargs),
            PropIntel(name="display_calc_color", data_type=str, widget_type="color", **prop_kwargs),
            PropIntel(name="display_exp_color", data_type=str, widget_type="color", **prop_kwargs),
            PropIntel(name="display_calc_lw", data_type=int, widget_type="spin", **prop_kwargs),
            PropIntel(name="display_exp_lw", data_type=int, widget_type="spin", **prop_kwargs),
            PropIntel(name="display_plot_offset", data_type=float, widget_type="float_entry", **prop_kwargs),
            PropIntel(name="display_group_by", data_type=int, **prop_kwargs),
            PropIntel(name="display_label_pos", data_type=float, widget_type="float_entry", **prop_kwargs),
            OptionPropIntel(name="axes_xscale", data_type=int, options=settings.AXES_XSCALES, **prop_kwargs),
            PropIntel(name="axes_xmin", data_type=float, widget_type="float_entry", **prop_kwargs),
            PropIntel(name="axes_xmax", data_type=float, widget_type="float_entry", **prop_kwargs),
            PropIntel(name="axes_xstretch", data_type=bool, **prop_kwargs),
            OptionPropIntel(name="axes_yscale", data_type=int, options=settings.AXES_YSCALES, **prop_kwargs),
            PropIntel(name="axes_yvisible", data_type=bool, **prop_kwargs),
            PropIntel(name="specimens", data_type=object, widget_type="tree_view", **prop_kwargs),
            PropIntel(name="phases", data_type=object, has_widget=False, storable=True),
            PropIntel(name="mixtures", data_type=object, has_widget=False, storable=True),
            PropIntel(name="atom_types", data_type=object, has_widget=False, storable=True),
            PropIntel(name="needs_saving", data_type=bool, has_widget=False, storable=False),
        ]
        store_id = "Project"
        file_filters = [
            ("PyXRD Project files", get_case_insensitive_glob("*.pyxrd", "*.zpd")),
        ]
        import_filters = [
            ("Sybilla XML files", get_case_insensitive_glob("*.xml")),
        ]

    # PROPERTIES:
    name = ""
    date = ""
    description = None
    author = ""

    needs_saving = True

    _layout_mode = settings.DEFAULT_LAYOUT
    def get_layout_mode(self): return self._layout_mode
    def set_layout_mode(self, value):
        with self.visuals_changed.hold_and_emit():
            self._layout_mode = value

    _axes_xmin = settings.AXES_MANUAL_XMIN
    def get_axes_xmin(self): return self._axes_xmin
    def set_axes_xmin(self, value):
        self._axes_xmin = max(float(value), 0.0)
        self.visuals_changed.emit()

    _axes_xmax = settings.AXES_MANUAL_XMAX
    def get_axes_xmax(self): return self._axes_xmax
    def set_axes_xmax(self, value):
        self._axes_xmax = max(float(value), 0.0)
        self.visuals_changed.emit()

    _axes_xstretch = settings.AXES_XSTRETCH
    def get_axes_xstretch(self): return self._axes_xstretch
    def set_axes_xstretch(self, value):
        self._axes_xstretch = bool(value)
        self.visuals_changed.emit()

    _axes_yvisible = settings.AXES_YVISIBLE
    def get_axes_yvisible(self): return self._axes_yvisible
    def set_axes_yvisible(self, value):
        self._axes_yvisible = bool(value)
        self.visuals_changed.emit()

    _display_plot_offset = settings.PLOT_OFFSET
    def get_display_plot_offset(self): return self._display_plot_offset
    def set_display_plot_offset(self, value):
        self._display_plot_offset = max(float(value), 0.0)
        self.visuals_changed.emit()

    _display_group_by = settings.PATTERN_GROUP_BY
    def get_display_group_by(self): return self._display_group_by
    def set_display_group_by(self, value):
        self._display_group_by = max(int(value), 1)
        self.visuals_changed.emit()

    _display_marker_angle = settings.MARKER_ANGLE
    def get_display_marker_angle(self): return self._display_marker_angle
    def set_display_marker_angle(self, value):
        self._display_marker_angle = float(value)
        self.visuals_changed.emit()

    _display_marker_top_offset = settings.MARKER_TOP_OFFSET
    def get_display_marker_top_offset(self): return self._display_marker_top_offset
    def set_display_marker_top_offset(self, value):
        self._display_marker_top_offset = float(value)
        self.visuals_changed.emit()

    _display_label_pos = settings.LABEL_POSITION
    def get_display_label_pos(self): return self._display_label_pos
    def set_display_label_pos(self, value):
        self._display_label_pos = float(value)
        self.visuals_changed.emit()

    _axes_xscale = settings.AXES_XSCALE
    def get_axes_xscale(self): return self._axes_xscale
    def set_axes_xscale(self, value):
        self._axes_xscale = value
        self.visuals_changed.emit()

    _axes_yscale = settings.AXES_YSCALE
    def get_axes_yscale(self): return self._axes_yscale
    def set_axes_yscale(self, value):
        self._axes_yscale = value
        self.visuals_changed.emit()

    _display_marker_align = settings.MARKER_ALIGN
    def get_display_marker_align(self): return self._display_marker_align
    def set_display_marker_align(self, value):
        self._display_marker_align = value
        self.visuals_changed.emit()

    _display_marker_base = settings.MARKER_BASE
    def get_display_marker_base(self): return self._display_marker_base
    def set_display_marker_base(self, value):
        self._display_marker_base = value
        self.visuals_changed.emit()

    _display_marker_top = settings.MARKER_TOP
    def get_display_marker_top(self): return self._display_marker_top
    def set_display_marker_top(self, value):
        self._display_marker_top = value
        self.visuals_changed.emit()

    _display_marker_style = settings.MARKER_STYLE
    def get_display_marker_style(self): return self._display_marker_style
    def set_display_marker_style(self, value):
        self._display_marker_style = value
        self.visuals_changed.emit()

    _display_calc_color = settings.CALCULATED_COLOR
    def get_display_calc_color(self): return self._display_calc_color
    def set_display_calc_color(self, value):
        self._display_calc_color = value
        self.visuals_changed.emit()

    _display_exp_color = settings.EXPERIMENTAL_COLOR
    def get_display_exp_color(self): return self._display_exp_color
    def set_display_exp_color(self, value):
        self._display_exp_color = value
        self.visuals_changed.emit()

    _display_marker_color = settings.MARKER_COLOR
    def get_display_marker_color(self): return self._display_marker_color
    def set_display_marker_color(self, value):
        self._display_marker_color = value
        self.visuals_changed.emit()

    _display_calc_lw = settings.CALCULATED_LINEWIDTH
    def get_display_calc_lw(self): return self._display_calc_lw
    def set_display_calc_lw(self, value):
        if value != self._display_calc_lw:
            self._display_calc_lw = float(value)
            self.visuals_changed.emit()

    _display_exp_lw = settings.EXPERIMENTAL_LINEWIDTH
    def get_display_exp_lw(self): return self._display_exp_lw
    def set_display_exp_lw(self, value):
        if value != self._display_exp_lw:
            self._display_exp_lw = float(value)
            self.visuals_changed.emit()

    specimens = []
    phases = []
    atom_types = []
    mixtures = []

    # ------------------------------------------------------------
    #      Initialisation and other internals
    # ------------------------------------------------------------
    def __init__(self, *args, **kwargs):
        """
            Valid keyword arguments for a Project are:
                name: the project name
                description: the project description
                author: the project author(s)
                date: the data at which the project was created
                layout_mode: the layout mode this project should be displayed in
                display_calc_color: 'default' calculated profile color
                display_calc_lw: 'default' calculated profile line width
                display_exp_color: 'default' experimental profile color
                display_exp_lw: 'default' experimental profile line width
                display_plot_offset: the offset between patterns as a fraction of
                 the maximum intensity
                display_group_by: the number of patterns to group (having no offset)
                display_label_pos: the relative position  from the pattern offset
                 for pattern labels as a fraction of the patterns intensity
                axes_xscale: what type of scale to use for X-axis, automatic or manual
                axes_xmin: the manual lower limit for the X-axis
                axes_xmax: the manual upper limit for the X-axis
                axes_xstretch: whether or not to stretch the X-axis over the entire
                 available display
                axes_yscale: what type of y-axis to use: raw counts, single or
                 multi-normalized units
                axes_yvisible: whether or not the y-axis should be shown
                atom_types: a list of AtomTypes
                phases: a list of Phases
                specimens: a list of Specimens
                mixtures: a list of Mixtures
                load_default_data: whether or not to load default data (i.e. 
                 atom type definitions)
                
            Keyword arguments controlling the 'default' layout for markers:
                display_marker_align
                display_marker_color
                display_marker_base
                display_marker_top
                display_marker_top_offset
                display_marker_angle
                display_marker_style
            See the 'specimen.models.marker' model for an explenation on what
             these mean.
             
            Deprecated (but still supported) keyword arguments:
                goniometer: the project-level goniometer, is passed on to the
                 specimens
        """
        super(Project, self).__init__(**kwargs)

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

                self.axes_xscale = self.get_kwarg(kwargs, self.axes_xscale, "axes_xscale")
                self.axes_xmin = self.get_kwarg(kwargs, self.axes_xmin, "axes_xmin")
                self.axes_xmax = self.get_kwarg(kwargs, self.axes_xmax, "axes_xmax")
                self.axes_xstretch = self.get_kwarg(kwargs, self.axes_xstretch, "axes_xstretch")
                self.axes_yscale = self.get_kwarg(kwargs, self.axes_yscale, "axes_yscale")
                self.axes_yvisible = self.get_kwarg(kwargs, self.axes_yvisible, "axes_yvisible")

                goniometer = None
                goniometer_kwargs = self.get_kwarg(kwargs, None, "goniometer", "data_goniometer")
                if goniometer_kwargs:
                    goniometer = self.parse_init_arg(goniometer_kwargs, None, child=True)

                self.atom_types = self.get_list(kwargs, [], "atom_types", "data_atom_types", parent=self)
                self.phases = self.get_list(kwargs, [], "phases", "data_phases", parent=self)
                self.specimens = self.get_list(kwargs, [], "specimens", "data_specimens", parent=self)
                self.mixtures = self.get_list(kwargs, [], "mixtures", "data_mixtures", parent=self)

                # Resolve json references & observe phases
                for phase in self.phases:
                    phase.resolve_json_references()
                    self.observe_model(phase)
                # Set goniometer if required & observe specimens
                for specimen in self.specimens:
                    if goniometer: specimen.goniometer = goniometer
                    self.observe_model(specimen)
                # Observe mixtures:
                for mixture in self.mixtures:
                    self.observe_model(mixture)

                # Connect signals to lists and dicts:
                self._phases_observer = ListObserver(
                    self.on_phase_inserted,
                    self.on_phase_removed,
                    prop_name="phases",
                    model=self
                )
                self._specimens_observer = ListObserver(
                    self.on_specimen_inserted,
                    self.on_specimen_removed,
                    prop_name="specimens",
                    model=self
                )
                self._mixtures_observer = ListObserver(
                    self.on_mixture_inserted,
                    self.on_mixture_removed,
                    prop_name="mixtures",
                    model=self
                )
                self._atom_types_observer = ListObserver(
                    self.on_atom_type_inserted,
                    self.on_atom_type_removed,
                    prop_name="atom_types",
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
            with model.data_changed.ignore():
                model.update()
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
        self.needs_saving = False

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
    def get_scale_factor(self, specimen):
        """
        Get the factor with which to scale raw data and the scaled offset
                
        :rtype: tuple containing the scale factor and the (scaled) offset
        """
        if self.axes_yscale == 0:
            return (1.0 / (self.get_max_intensity() or 1.0), self.display_offset)
        elif self.axes_yscale == 1:
            return (1.0 / (specimen.max_intensity or 1.0), self.display_offset)
        elif self.axes_yscale == 2:
            return (1.0, self.display_offset * self.get_max_intensity())
        else:
            raise ValueError, "Wrong value for 'axes_yscale' in %s: %d; should be 0, 1 or 2" % (self, self.axes_yscale)

    def get_max_intensity(self):
        max_intensity = 0
        if self.parent is not None:
            for specimen in self.parent.current_specimens:
                max_intensity = max(specimen.max_intensity, max_intensity)
        return max_intensity

    def update_all_mixtures(self):
        for mixture in self.mixtures:
            mixture.update()

    # ------------------------------------------------------------
    #      Specimen list related
    # ------------------------------------------------------------
    def move_specimen_up(self, specimen):
        """Move the passed specimen up one slot"""
        index = self.specimens.index(specimen)
        self.specimens.insert(min(index + 1, len(self.specimens)), self.specimens.pop(index))

    def move_specimen_down(self, specimen):
        """Move the passed specimen down one slot"""
        index = self.specimens.index(specimen)
        self.specimens.insert(max(index - 1, 0), self.specimens.pop(index))
        pass

    # ------------------------------------------------------------
    #      Phases list related
    # ------------------------------------------------------------
    def load_phases(self, filename, insert_index=None):
        """
            Loads the phases from the file 'filename'. An optional index can
            be given where the phases need to be inserted at.
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
            Loads the atom types from the CSV file 'filename'.
        """
        for atom_type in AtomType.get_from_csv(filename, parent=self):
            self.atom_types.append(atom_type)

    def load_atom_types(self, filename):
        """
            Loads the atom types from the (JSON) file 'filename'.
        """
        for atom_type in AtomType.load_atom_types(filename, parent=self):
            self.atom_types.append(atom_type)

    pass # end of class
