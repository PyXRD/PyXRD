# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

from pkg_resources import resource_filename # @UnresolvedImport

import gtk

from matplotlib.figure import Figure
from matplotlib.backends.backend_gtkcairo import FigureCanvasGTKCairo as FigureCanvasGTK

from pyxrd.generic.views import BaseView, HasChildView, DialogView
from mvc.adapters.gtk_support.widgets import ScaleEntry

class EditPhaseView(BaseView, HasChildView):
    title = "Edit Phases"
    builder = resource_filename(__name__, "glade/phase.glade")
    top = "edit_phase"
    widget_format = "phase_%s"

    csds_view = None
    csds_view_container = widget_format % "CSDS_distribution"

    probabilities_view = None
    probabilities_view_container = widget_format % "probabilities"

    components_view = None
    components_view_container = widget_format % "components"

    def set_csds_view(self, view):
        self.csds_view = view
        if view is not None:
            self._add_child_view(view.get_top_widget(), self[self.csds_view_container])
        return view

    def set_csds_sensitive(self, sens):
        self[self.csds_view_container].set_sensitive(sens)

    def set_probabilities_view(self, view):
        self.probabilities_view = view
        if view is not None:
            self._add_child_view(view.get_top_widget(), self[self.probabilities_view_container])
        return view

    def remove_probabilities(self):
        num = self["book_wrapper"].page_num(self[self.probabilities_view_container])
        self["book_wrapper"].remove_page(num)

    def set_components_view(self, view):
        self.components_view = view
        if view is not None:
            self._add_child_view(view.get_top_widget(), self[self.components_view_container])
        return view

class EditAtomRatioView(DialogView):
    title = "Edit Atom Ratio"
    subview_builder = resource_filename(__name__, "glade/ratio.glade")
    subview_toplevel = "edit_ratio"
    modal = True
    widget_format = "ratio_%s"

    @property
    def atom1_combo(self):
        return self["ratio_atom1"]

    @property
    def atom2_combo(self):
        return self["ratio_atom2"]

    pass # end of class

class EditAtomContentsView(DialogView, HasChildView):
    title = "Edit Atom Contents"
    subview_builder = resource_filename(__name__, "glade/contents.glade")
    subview_toplevel = "edit_contents"
    modal = True
    widget_format = "contents_%s"

    contents_list_view_container = widget_format % "atom_contents"

    def set_contents_list_view(self, view):
        self.contents_list_view = view
        return self._add_child_view(view, self[self.contents_list_view_container])

    @property
    def atom_contents_container(self):
        return self["container_atom_contents"]

    pass # end of class

class EditComponentView(BaseView, HasChildView):
    title = "Edit Component"
    builder = resource_filename(__name__, "glade/component.glade")
    top = "edit_component"
    widget_format = "component_%s"

    layer_view = None
    layer_view_container = widget_format % "layer_atoms"

    interlayer_view = None
    interlayer_view_container = widget_format % "interlayer_atoms"

    atom_relations_view = None
    atom_relations_view_container = widget_format % "atom_relations"

    ucpa_view = None
    ucpa_view_container = widget_format % "ucp_a"

    ucpb_view = None
    ucpb_view_container = widget_format % "ucp_b"


    def __init__(self, *args, **kwargs):
        BaseView.__init__(self, *args, **kwargs)

    def set_layer_view(self, view):
        self.layer_view = view
        return self._add_child_view(view, self[self.layer_view_container])

    def set_atom_relations_view(self, view):
        self.atom_relations_view = view
        return self._add_child_view(view, self[self.atom_relations_view_container])

    def set_interlayer_view(self, view):
        self.interlayer_view = view
        return self._add_child_view(view, self[self.interlayer_view_container])

    def set_ucpa_view(self, view):
        self.ucpa_view = view
        return self._add_child_view(view, self[self.ucpa_view_container])

    def set_ucpb_view(self, view):
        self.ucpb_view = view
        return self._add_child_view(view, self[self.ucpb_view_container])

class EditUnitCellPropertyView(BaseView):
    builder = resource_filename(__name__, "glade/unit_cell_prop.glade")
    top = "box_ucf"
    widget_format = "ucp_%s"

class EditCSDSDistributionView(BaseView):
    builder = resource_filename(__name__, "glade/csds.glade")
    top = "tbl_csds_distr"

    def __init__(self, *args, **kwargs):
        BaseView.__init__(self, *args, **kwargs)

        self.graph_parent = self["distr_plot_box"]
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

    def update_figure(self, distr):
        self.plot.cla()
        self.plot.hist(range(len(distr)), len(distr), weights=distr, normed=1, ec='b', histtype='stepfilled')
        self.plot.set_ylabel('')
        self.plot.set_xlabel('CSDS', size=14, weight="heavy")
        self.plot.relim()
        self.plot.autoscale_view()
        if self.matlib_canvas is not None:
            self.matlib_canvas.draw()

    def reset_params(self):
        tbl = self["tbl_params"]
        for child in tbl.get_children():
            tbl.remove(child)
        tbl.resize(1, 2)

    def add_param_widget(self, name, label, minimum, maximum):
        tbl = self["tbl_params"]
        rows = tbl.get_property("n-rows") + 1
        tbl.resize(rows, 2)

        lbl = gtk.Label(label)
        lbl.set_alignment(1.0, 0.5)
        tbl.attach(lbl, 0, 1, rows - 1, rows, gtk.FILL, gtk.FILL)

        inp = ScaleEntry(minimum, maximum, enforce_range=True)
        tbl.attach(inp, 1, 2, rows - 1, rows, gtk.FILL, gtk.FILL)

        tbl.show_all()

        self[name] = inp
        inp.set_name(name)

        return inp

class AddPhaseView(DialogView):
    title = "Add Phase"
    subview_builder = resource_filename(__name__, "glade/addphase.glade")
    subview_toplevel = "add_phase_container"

    def __init__(self, *args, **kwargs):
        DialogView.__init__(self, *args, **kwargs)

    def get_G(self):
        return int(self["G"].get_value_as_int())

    def get_R(self):
        return int(self["R"].get_value_as_int())

    def get_phase(self):
        itr = self["cmb_default_phases"].get_active_iter()
        if itr:
            val = self["cmb_default_phases"].get_model().get_value(itr, 1)
            return val if val else None
        else:
            return None

    @property
    def phase_combo_box(self):
        return self["cmb_default_phases"]

    pass # end of class
