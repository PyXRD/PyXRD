# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import time

# import gtk
from pyxrd.gtkmvc.model import Model, Observer

from pyxrd.data import settings

from pyxrd.generic.utils import delayed
from pyxrd.generic.models import ChildModel, DefaultSignal
from pyxrd.generic.models.mixins import ObjectListStoreParentMixin
from pyxrd.generic.models.properties import PropIntel, MultiProperty
from pyxrd.generic.models.treemodels import ObjectListStore, IndexListStore
from pyxrd.generic.io import storables, Storable

from pyxrd.specimen.models import Specimen
from pyxrd.phases.models import Phase
from pyxrd.atoms.models import AtomType
from pyxrd.mixture.models.mixture import Mixture

@storables.register()
class Project(ChildModel, Storable, ObjectListStoreParentMixin):
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
        PropIntel(name="needs_update", data_type=object, storable=False),
        PropIntel(name="needs_saving", data_type=bool, storable=False),
    ]
    __store_id__ = "Project"

    # SIGNALS:
    needs_update = None

    # PROPERTIES:
    name = ""
    date = ""
    description = None
    author = ""

    needs_saving = True

    def update_callback(self, prop_name, value):
        self.needs_update.emit()
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
        setattr(self, "_%s" % prop_name, value)
        self.needs_update.emit()

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
            self.needs_update.emit()

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
            self.needs_update.emit()


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
    def __init__(self, name="Project name", date=time.strftime("%d/%m/%Y"),
            description="Project description", author="Project author",
            atom_types=None, phases=None,
            specimens=None, mixtures=None, layout_mode=None,
            display_marker_align=None, display_marker_color=None, display_marker_base=None,
            display_marker_top=None, display_marker_top_offset=None,
            display_marker_angle=None, display_marker_style=None,
            display_plot_offset=None, display_group_by=None,
            display_calc_color=None, display_exp_color=None, display_label_pos=None,
            display_calc_lw=None, display_exp_lw=None,
            axes_xscale=None, axes_xmin=None, axes_xmax=None,
            axes_xstretch=None, axes_yscale=None, axes_yvisible=None,
            load_default_data=True, **kwargs):
        ChildModel.__init__(self, parent=kwargs.get("parent", None))
        self.parent = kwargs.get("parent") # FIXME ??? old project files seem to have an issue here?
        Storable.__init__(self)

        self.before_needs_update_lock = False
        self.needs_update = DefaultSignal(before=self.before_needs_update)

        self.layout_mode = layout_mode or self.layout_mode

        self.display_marker_align = display_marker_align or self.display_marker_align
        self.display_marker_color = display_marker_color or self.display_marker_color
        self.display_marker_base = display_marker_base or self.display_marker_base
        self.display_marker_top = display_marker_top or self.display_marker_top
        self.display_marker_top_offset = display_marker_top_offset or self.display_marker_top_offset
        self.display_marker_angle = display_marker_angle or self.display_marker_angle
        self.display_marker_style = display_marker_style or self.display_marker_style

        self.display_calc_color = display_calc_color or self.display_calc_color
        self.display_exp_color = display_exp_color or self.display_exp_color
        self.display_calc_lw = display_calc_lw or self.display_calc_lw
        self.display_exp_lw = display_exp_lw or self.display_exp_lw
        self.display_plot_offset = display_plot_offset or self.display_plot_offset
        self.display_group_by = display_group_by or self.display_group_by
        self.display_label_pos = display_label_pos or self.display_label_pos

        self.axes_xscale = axes_xscale or self.axes_xscale
        self.axes_xmin = axes_xmin or self.axes_xmin
        self.axes_xmax = axes_xmax or self.axes_xmax
        self.axes_xstretch = axes_xstretch or self.axes_xstretch
        self.axes_yscale = axes_yscale or self.axes_yscale
        self.axes_yvisible = axes_yvisible or self.axes_yvisible

        goniometer = None
        goniometer_kwargs = self.get_depr(kwargs, None, "data_goniometer", "goniometer")
        if goniometer_kwargs:
            goniometer = self.parse_init_arg(goniometer_kwargs, None, child=True)

        atom_types = atom_types or self.get_depr(kwargs, None, "data_atom_types")
        phases = phases or self.get_depr(kwargs, None, "data_phases")
        specimens = specimens or self.get_depr(kwargs, None, "data_specimens")
        mixtures = mixtures or self.get_depr(kwargs, None, "data_mixtures")
        self._atom_types = self.parse_liststore_arg(atom_types, IndexListStore, AtomType)
        self._phases = self.parse_liststore_arg(phases, ObjectListStore, Phase)
        self._specimens = self.parse_liststore_arg(specimens, ObjectListStore, Specimen)
        self._mixtures = self.parse_liststore_arg(mixtures, ObjectListStore, Mixture)

        for phase in self._phases._model_data:
            phase.resolve_json_references()
            self.observe_model(phase)
        for specimen in self._specimens.iter_objects():
            if goniometer: specimen.goniometer = goniometer
            self.observe_model(specimen)

        self._atom_types.connect("item-removed", self.on_atom_type_item_removed)
        self._phases.connect("item-removed", self.on_phase_item_removed)
        self._specimens.connect("item-removed", self.on_specimen_item_removed)
        self._mixtures.connect("item-removed", self.on_mixture_item_removed)

        self._atom_types.connect("item-inserted", self.on_atom_type_item_inserted)
        self._phases.connect("item-inserted", self.on_phase_item_inserted)
        self._specimens.connect("item-inserted", self.on_specimen_item_inserted)
        self._mixtures.connect("item-inserted", self.on_mixture_item_inserted)

        self.description = "" # gtk.TextBuffer()

        self.name = str(name or self.get_depr(kwargs, "", "data_name"))
        self.date = str(date or self.get_depr(kwargs, "", "data_date"))
        self.description = str(description or self.get_depr(kwargs, "", "data_description"))
        self.author = str(author or self.get_depr(kwargs, "", "data_author"))

        if load_default_data and self.layout_mode != 1 and \
            len(self._atom_types._model_data) == 0: self.load_default_data()

        self.needs_saving = True

    def load_default_data(self):
        AtomType.get_from_csv(
            settings.DATA_REG.get_file_path("ATOM_SCAT_FACTORS"),
            self.atom_types.append
        )

    # ------------------------------------------------------------
    #      Notifications of observable properties
    # ------------------------------------------------------------
    def on_phase_item_inserted(self, model, item, *data):
        if item.parent != self: item.parent = self
        self.observe_model(item)
    def on_atom_type_item_inserted(self, model, item, *data):
        if item.parent != self: item.parent = self
    def on_specimen_item_inserted(self, model, item, *data):
        if item.parent != self: item.parent = self
        self.observe_model(item)
    def on_mixture_item_inserted(self, model, item, *data):
        if item.parent != self: item.parent = self

    def on_phase_item_removed(self, model, item, *data):
        if item.based_on != None:
            item.based_on = None
        for phase in self._phases._model_data:
            if phase.based_on == item:
                phase.based_on = None
        for mixture in self.mixtures.iter_objects():
            mixture.unset_phase(item)
        if not self.before_needs_update_lock:
            self.needs_update.emit() # propagate signal
    def on_atom_type_item_removed(self, model, item, *data):
        if not self.before_needs_update_lock:
            self.needs_update.emit() # propagate signal
    def on_specimen_item_removed(self, model, item, *data):
        self.relieve_model(item)
        for mixture in self.mixtures.iter_objects():
            mixture.unset_specimen(item)
        if not self.before_needs_update_lock:
            self.needs_update.emit() # propagate signal
    def on_mixture_item_removed(self, model, item, *data):
        pass

    @Observer.observe("needs_update", signal=True)
    def notify_needs_update(self, model, prop_name, info):
        self.needs_saving = True
        if not self.before_needs_update_lock:
            self.needs_update.emit() # propagate signal

    @delayed("before_needs_update_lock")
    def before_needs_update(self, after):
        if not self.before_needs_update_lock and self.mixtures != None:
            self.before_needs_update_lock = True
            t1 = time.time()
            for mixture in self.mixtures.iter_objects():
                if mixture.auto_run:
                    mixture.optimize()
                else:
                    mixture.apply_current_data_object()
            t2 = time.time()
            if settings.DEBUG: print '%s took %0.3f ms' % ("before_needs_update", (t2 - t1) * 1000.0)
            after()
            self.before_needs_update_lock = False

    def freeze_updates(self):
        self.before_needs_update_lock = True

    def thaw_updates(self):
        self.before_needs_update_lock = False

    # ------------------------------------------------------------
    #      Input/Output stuff
    # ------------------------------------------------------------
    @classmethod
    def from_json(type, **kwargs):
        project = type(**kwargs)
        project.needs_saving = False # don't mark this when just loaded
        return project

    def save_object(self, filename):
        Storable.save_object(self, filename, zipped=True)
        self.needs_saving = False

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
        if self.parent != None:
            for specimen in self.parent.current_specimens:
                max_intensity = max(specimen.max_intensity, max_intensity)
        return max_intensity

    pass # end of class
