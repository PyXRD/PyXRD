# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import time

from pyxrd.gtkmvc.model import Model, Observer

from pyxrd.data import settings

from pyxrd.generic.models import DataModel
from pyxrd.generic.models.mixins import ObjectListStoreParentMixin
from pyxrd.generic.models.properties import PropIntel, MultiProperty
from pyxrd.generic.models.treemodels import ObjectListStore, IndexListStore
from pyxrd.generic.io import storables, Storable, get_case_insensitive_glob

from pyxrd.specimen.models import Specimen
from pyxrd.phases.models import Phase
from pyxrd.atoms.models import AtomType
from pyxrd.mixture.models.mixture import Mixture

@storables.register()
class Project(DataModel, Storable, ObjectListStoreParentMixin):
    # MODEL INTEL:
    __model_intel__ = [ # TODO add labels
        PropIntel(name="name", data_type=str, storable=True, has_widget=True),
        PropIntel(name="date", data_type=str, storable=True, has_widget=True),
        PropIntel(name="description", data_type=str, storable=True, has_widget=True, widget_type="text_view"),
        PropIntel(name="author", data_type=str, storable=True, has_widget=True),
        PropIntel(name="layout_mode", data_type=str, storable=True, has_widget=True, widget_type="combo"),
        PropIntel(name="display_marker_align", data_type=str, storable=True, has_widget=True, widget_type="combo"),
        PropIntel(name="display_marker_color", data_type=str, storable=True, has_widget=True, widget_type="color"),
        PropIntel(name="display_marker_base", data_type=int, storable=True, has_widget=True, widget_type="combo"),
        PropIntel(name="display_marker_top", data_type=int, storable=True, has_widget=True, widget_type="combo"),
        PropIntel(name="display_marker_top_offset", data_type=float, storable=True, has_widget=True, widget_type="float_entry"),
        PropIntel(name="display_marker_angle", data_type=float, storable=True, has_widget=True, widget_type="float_entry"),
        PropIntel(name="display_marker_style", data_type=str, storable=True, has_widget=True, widget_type="combo"),
        PropIntel(name="display_calc_color", data_type=str, storable=True, has_widget=True, widget_type="color"),
        PropIntel(name="display_exp_color", data_type=str, storable=True, has_widget=True, widget_type="color"),
        PropIntel(name="display_calc_lw", data_type=int, storable=True, has_widget=True, widget_type="spin"),
        PropIntel(name="display_exp_lw", data_type=int, storable=True, has_widget=True, widget_type="spin"),
        PropIntel(name="display_plot_offset", data_type=float, storable=True, has_widget=True, widget_type="float_entry"),
        PropIntel(name="display_group_by", data_type=int, storable=True, has_widget=True),
        PropIntel(name="display_label_pos", data_type=float, storable=True, has_widget=True, widget_type="float_entry"),
        PropIntel(name="axes_xscale", data_type=int, storable=True, has_widget=True, widget_type="combo"),
        PropIntel(name="axes_xmin", data_type=float, storable=True, has_widget=True, widget_type="float_entry"),
        PropIntel(name="axes_xmax", data_type=float, storable=True, has_widget=True, widget_type="float_entry"),
        PropIntel(name="axes_xstretch", data_type=bool, storable=True, has_widget=True),
        PropIntel(name="axes_yscale", data_type=int, storable=True, has_widget=True, widget_type="combo"),
        PropIntel(name="axes_yvisible", data_type=bool, storable=True, has_widget=True),
        PropIntel(name="specimens", data_type=object, storable=True, has_widget=True, widget_type="tree_view"),
        PropIntel(name="phases", data_type=object, storable=True),
        PropIntel(name="mixtures", data_type=object, storable=True),
        PropIntel(name="atom_types", data_type=object, storable=True),
        PropIntel(name="needs_saving", data_type=bool, storable=False),
    ]
    __store_id__ = "Project"
    __file_filters__ = [
        ("PyXRD Project files", get_case_insensitive_glob("*.pyxrd", "*.zpd")),
    ]
    __import_filters__ = [
        ("Sybilla XML files", get_case_insensitive_glob("*.xml")),
    ]

    # PROPERTIES:
    name = ""
    date = ""
    description = None
    author = ""

    needs_saving = True

    def update_callback(self, prop_name, value):
        self.visuals_changed.emit()
    layout_mode = MultiProperty(settings.DEFAULT_LAYOUT, lambda i: i, update_callback, settings.DEFAULT_LAYOUTS)

    _axes_xmin = settings.AXES_MANUAL_XMIN
    _axes_xmax = settings.AXES_MANUAL_XMAX
    _axes_xstretch = settings.AXES_XSTRETCH
    _axes_yvisible = settings.AXES_YVISIBLE
    _display_plot_offset = 0.75
    _display_group_by = 1
    _display_marker_angle = settings.MARKER_ANGLE
    _display_marker_top_offset = settings.MARKER_TOP_OFFSET
    _display_label_pos = 0.35
    @Model.getter("axes_xmin", "axes_xmax", "axes_xstretch", "axes_yvisible",
            "display_plot_offset", "display_group_by", "display_marker_angle",
            "display_label_pos", "display_marker_top_offset")
    def get_axes_value(self, prop_name):
        return getattr(self, "_%s" % prop_name)
    @Model.setter("axes_xmin", "axes_xmax", "axes_xstretch", "axes_yvisible",
            "display_plot_offset", "display_group_by", "display_marker_angle",
            "display_label_pos", "display_marker_top_offset")
    def set_axes_value(self, prop_name, value):
        if prop_name in ("axes_xmin", "axes_xmax"): value = max(value, 0.0)
        if prop_name == "display_group_by": value = max(value, 1)
        if prop_name == "display_plot_offset": value = max(value, 0.0)
        setattr(self, "_%s" % prop_name, value)
        self.visuals_changed.emit()

    axes_xscale = MultiProperty(0, int, update_callback, { 0: "Auto", 1: "Manual" })
    axes_yscale = MultiProperty(0, int, update_callback, {
        0: "Multi normalised",
        1: "Single normalised",
        2: "Unchanged raw counts"
    })



    display_marker_align = MultiProperty(settings.MARKER_ALIGN, lambda i: i, update_callback, {
        "left": "Left align",
        "center": "Centered",
        "right": "Right align"
    })

    display_marker_base = MultiProperty(settings.MARKER_BASE, int, update_callback, {
        0: "X-axis",
        1: "Experimental profile",
        2: "Calculated profile",
        3: "Lowest of both",
        4: "Highest of both"
    })

    display_marker_top = MultiProperty(settings.MARKER_TOP, int, update_callback, {
         0: "Relative to base", 1: "Top of plot"
    })

    display_marker_style = MultiProperty(settings.MARKER_STYLE, lambda i: i, update_callback, {
        "none": "None", "solid": "Solid",
        "dashed": "Dash", "dotted": "Dotted",
        "dashdot": "Dash-Dotted", "offset": "Display at Y-offset"
    })

    _display_calc_color = settings.CALCULATED_COLOR
    _display_exp_color = settings.EXPERIMENTAL_COLOR
    _display_marker_color = settings.MARKER_COLOR
    @Model.getter("display_calc_color", "display_exp_color", "display_marker_color")
    def get_color(self, prop_name):
        return getattr(self, "_%s" % prop_name)
    @Model.setter("display_calc_color", "display_exp_color", "display_marker_color")
    def set_color(self, prop_name, value):
        if value != getattr(self, "_%s" % prop_name):
            setattr(self, "_%s" % prop_name, value)
            self.visuals_changed.emit()

    _display_calc_lw = settings.CALCULATED_LINEWIDTH
    _display_exp_lw = settings.EXPERIMENTAL_LINEWIDTH
    @Model.getter("display_calc_lw", "display_exp_lw")
    def get_lw(self, prop_name):
        return getattr(self, "_%s" % prop_name)
    @Model.setter("display_calc_lw", "display_exp_lw")
    def set_lw(self, prop_name, value):
        if value != getattr(self, "_%s" % prop_name):
            setattr(self, "_%s" % prop_name, float(value))
            calc = ("calc" in prop_name)
            if self.specimens:
                for specimen in self.specimens.iter_objects():
                    if calc and specimen.inherit_calc_lw:
                        specimen.calculated_pattern.lw = value
                    elif not calc and specimen.inherit_exp_lw:
                        specimen.experimental_pattern.lw = value
            self.visuals_changed.emit()


    _specimens = None
    def get_specimens_value(self): return self._specimens

    _phases = None
    def get_phases_value(self): return self._phases

    _atom_types = None
    def get_atom_types_value(self): return self._atom_types

    _mixtures = None
    def get_mixtures_value(self): return self._mixtures

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
                atom_types: the AtomType's ObjectListStore
                phases: the Phase's ObjectListStore
                specimens: the Specimen's ObjectListStore
                mixtures: the Mixture's ObjectListStore
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
        # self.parent = kwargs.get("parent") # FIXME ??? old project files seem to have an issue here?

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

                atom_types = self.get_kwarg(kwargs, None, "atom_types", "data_atom_types")
                phases = self.get_kwarg(kwargs, None, "phases", "data_phases")
                specimens = self.get_kwarg(kwargs, None, "specimens", "data_specimens")
                mixtures = self.get_kwarg(kwargs, None, "mixtures", "data_mixtures")
                self._atom_types = self.parse_liststore_arg(atom_types, IndexListStore, AtomType)
                self._phases = self.parse_liststore_arg(phases, ObjectListStore, Phase)
                self._specimens = self.parse_liststore_arg(specimens, ObjectListStore, Specimen)
                self._mixtures = self.parse_liststore_arg(mixtures, ObjectListStore, Mixture)

                # Resolve json references & observe phases
                for phase in self.phases.iter_objects():
                    phase.resolve_json_references()
                    self.observe_model(phase)
                # Set goniometer if required & observe specimens
                for specimen in self.specimens.iter_objects():
                    if goniometer: specimen.goniometer = goniometer
                    self.observe_model(specimen)
                # Observe mixtures:
                for mixture in self.mixtures.iter_objects():
                    self.observe_model(mixture)

                # Connect signals to ObjectListStores:
                self.atom_types.connect("item-removed", self.on_atom_type_item_removed)
                self.phases.connect("item-removed", self.on_phase_item_removed)
                self.specimens.connect("item-removed", self.on_specimen_item_removed)
                self.mixtures.connect("item-removed", self.on_mixture_item_removed)

                self.atom_types.connect("item-inserted", self.on_atom_type_item_inserted)
                self.phases.connect("item-inserted", self.on_phase_item_inserted)
                self.specimens.connect("item-inserted", self.on_specimen_item_inserted)
                self.mixtures.connect("item-inserted", self.on_mixture_item_inserted)

                self.name = str(self.get_kwarg(kwargs, "Project name", "name", "data_name"))
                self.date = str(self.get_kwarg(kwargs, time.strftime("%d/%m/%Y"), "date", "data_date"))
                self.description = str(self.get_kwarg(kwargs, "Project description", "description", "data_description"))
                self.author = str(self.get_kwarg(kwargs, "Project author", "author", "data_author"))

                load_default_data = self.get_kwarg(kwargs, False, "load_default_data")
                if load_default_data and self.layout_mode != 1 and \
                    len(self._atom_types._model_data) == 0: self.load_default_data()

                self.needs_saving = True
            pass # end with visuals_changed
        pass # end with data_changed

    def load_default_data(self):
        AtomType.get_from_csv(
            settings.DATA_REG.get_file_path("ATOM_SCAT_FACTORS"),
            self.atom_types.append
        )

    # ------------------------------------------------------------
    #      Notifications of observable properties
    # ------------------------------------------------------------
    def on_phase_item_inserted(self, model, item, *data):
        # Set parent on the new phase:
        if item.parent != self: item.parent = self
        item.resolve_json_references()

    def on_phase_item_removed(self, model, item, *data):
        with self.data_changed.hold_and_emit():
            # Clear parent:
            item.parent = None
            # Clear links with other phases:
            if item.based_on is not None:
                item.based_on = None
            for phase in self.phases.iter_objects():
                if phase.based_on == item:
                    phase.based_on = None
            # Remove phase from mixtures:
            for mixture in self.mixtures.iter_objects():
                mixture.unset_phase(item)

    def on_atom_type_item_inserted(self, model, item, *data):
        if item.parent != self: item.parent = self
        # We do not observe AtomType's directly, if they change,
        # Atoms containing them will be notified, and that event should bubble
        # up to the project level.

    def on_atom_type_item_removed(self, model, item, *data):
        item.parent = None
        # We do not emit a signal for AtomType's, if it was part of
        # an Atom, the Atom will be notified, and the event should bubble
        # up to the project level

    def on_specimen_item_inserted(self, model, item, *data):
        # Set parent and observe the new specimen (visuals changed signals):
        if item.parent != self: item.parent = self
        self.observe_model(item)

    def on_specimen_item_removed(self, model, item, *data):
        with self.data_changed.hold_and_emit():
            # Clear parent & stop observing:
            item.parent = None
            self.relieve_model(item)
            # Remove specimen from mixtures:
            for mixture in self.mixtures.iter_objects():
                mixture.unset_specimen(item)

    def on_mixture_item_inserted(self, model, item, *data):
        # Set parent and observe the new mixture:
        if item.parent != self: item.parent = self
        self.observe_model(item)

    def on_mixture_item_removed(self, model, item, *data):
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

    def update_all(self):
        for mixture in self.mixtures.iter_objects():
            mixture.update()

    def load_phases(self, filename, insert_index=None):
        """
            Loads the phases from the file 'filename'. An optional index can
            be given where the phases need to be inserted at.
        """
        for phase in Phase.load_phases(filename, parent=self):
            self.insert_phase(phase, insert_index=insert_index)
            phase.resolve_json_references()

    def insert_new_phase(self, name="New Phase", G=None, R=None, insert_index=None, **kwargs):
        """
            Adds a new phase with the given key word args
        """
        if G is not None and G > 0 and R is not None and R >= 0 and R <= 4:
            self.insert_phase(
                Phase(parent=self, name=name, G=G, R=R, **kwargs),
                insert_index=insert_index
            )

    def insert_phase(self, phase, insert_index=None):
        """
            Inserts a phase in the phases ObjectListStore. Does not take
            care of handling JSON references.
        """
        if insert_index is None:
            self.phases.append(phase)
        else:
            self.phases.insert(insert_index, phase)
            insert_index += 1

    pass # end of class
