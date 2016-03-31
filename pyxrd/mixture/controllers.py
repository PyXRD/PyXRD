# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import logging

logger = logging.getLogger(__name__)

from contextlib import contextmanager

from mvc import Controller
from mvc.adapters.gtk_support.dialogs.dialog_factory import DialogFactory

from pyxrd.generic.controllers import BaseController, ObjectListStoreController
from pyxrd.generic.controllers.objectliststore_controllers import wrap_list_property_to_treemodel

from pyxrd.mixture.models import Mixture
from pyxrd.mixture.views import EditMixtureView

from pyxrd.refinement.views.refinement_view import RefinementView
from pyxrd.refinement.controllers.refinement_controller import RefinementController

class EditMixtureController(BaseController):

    auto_adapt_excluded = [
        "refine_method_index",
        "refinables",
        "make_psp_plots"
    ]

    ref_view = None

    @property
    def specimens_treemodel(self):
        if self.model.project is not None:
            prop = self.model.project.Meta.get_prop_intel_by_name("specimens")
            return wrap_list_property_to_treemodel(self.model.project, prop)
        else:
            return None

    @property
    def phases_treemodel(self):
        if self.model.project is not None:
            prop = self.model.project.Meta.get_prop_intel_by_name("phases")
            return wrap_list_property_to_treemodel(self.model.project, prop)
        else:
            return None

    def register_adapters(self):
        self.create_ui()

    def create_ui(self):
        """
            Creates a complete new UI for the Mixture model
        """
        self.view.reset_view()
        for index in range(len(self.model.phases)):
            self._add_phase_view(index)
        for index in range(len(self.model.specimens)):
            self._add_specimen_view(index)

    def _add_phase_view(self, phase_slot):
        """
            Adds a new view for the given phase slot.
        """
        def on_label_changed(editable):
            self.model.phases[phase_slot] = editable.get_text()

        def on_fraction_changed(editable):
            try: self.model.fractions[phase_slot] = float(editable.get_text())
            except ValueError: return # ignore ValueErrors

        def on_phase_delete(widget):
            self.model.del_phase_slot(phase_slot)
            widget.disconnect(widget.get_data("deleventid"))

        self.view.add_phase_slot(self.phases_treemodel,
            on_phase_delete, on_label_changed, on_fraction_changed,
            self.on_combo_changed, label=self.model.phases[phase_slot],
            fraction=self.model.fractions[phase_slot], phases=self.model.phase_matrix)

    def _add_specimen_view(self, specimen_slot):
        """
            Adds a new view for the given specimen slot
        """
        def on_scale_changed(editable):
            try: self.model.scales[specimen_slot] = float(editable.get_text())
            except ValueError: return # ignore ValueErrors

        def on_bgs_changed(editable):
            try: self.model.bgshifts[specimen_slot] = float(editable.get_text())
            except ValueError: return # ignore ValueErrors

        def on_specimen_changed(combobox):
            itr = combobox.get_active_iter()
            specimen = self.specimens_treemodel.get_user_data(itr) if itr is not None else None
            self.model.set_specimen(specimen_slot, specimen)

        def on_specimen_delete(widget):
            self.model.del_specimen_slot(specimen_slot)
            widget.disconnect(widget.get_data("deleventid"))

        self.view.add_specimen_slot(self.phases_treemodel,
            self.specimens_treemodel, on_specimen_delete, on_scale_changed,
            on_bgs_changed, on_specimen_changed, self.on_combo_changed,
            scale=self.model.scales[specimen_slot], bgs=self.model.bgshifts[specimen_slot],
            specimen=self.model.specimens[specimen_slot], phases=self.model.phase_matrix)

    # ------------------------------------------------------------
    #      Notifications of observable properties
    # ------------------------------------------------------------
    @Controller.observe("data_changed", signal=True)
    def notif_has_changed(self, model, prop_name, info):
        self.view.update_all(self.model.fractions, self.model.scales, self.model.bgshifts)

    @Controller.observe("needs_reset", signal=True)
    def notif_needs_reset(self, model, prop_name, info):
        self.create_ui()

    # ------------------------------------------------------------
    #      GTK Signal handlers
    # ------------------------------------------------------------
    def on_combo_changed(self, combobox, row, col):
        itr = combobox.get_active_iter()
        phase = self.phases_treemodel.get_user_data(itr) if itr is not None else None
        self.model.set_phase(row, col, phase)

    def on_add_phase(self, widget, *args):
        with self.model.data_changed.hold():
            index = self.model.add_phase_slot("New Phase", 1.0)
            self._add_phase_view(index)

    def on_add_specimen(self, widget, *args):
        with self.model.data_changed.hold():
            index = self.model.add_specimen_slot(None, 1.0, 0.0)
            self._add_specimen_view(index)

    def on_add_both(self, widget, *args):
        with self.model.data_changed.hold():
            self.on_add_specimen(widget, *args)
            self.on_add_phase(widget, *args)

    def on_optimize_clicked(self, widget, *args):
        self.model.optimize()

    def on_refine_clicked(self, widget, *args):
        self.model.refinement.update_refinement_treestore()
        if self.ref_view is not None:
            self.ref_view.hide()
            self.ref_ctrl.cleanup()
        self.view.parent.hide()
        self.ref_view = RefinementView(parent=self.parent.view)
        self.ref_ctrl = RefinementController(model=self.model.refinement, view=self.ref_view, parent=self)
        self.ref_view.present()

    def on_composition_clicked(self, widget, *args):
        comp = "The composition of the specimens in this mixture:\n\n\n"
        comp += "<span font-family=\"monospace\">"
        # get the composition matrix (first columns contains strings with elements, others are specimen compositions)
        import re
        for row in self.model.get_composition_matrix():
            comp += "%s %s\n" % (re.sub(r'(\d+)', r'<sub>\1</sub>', row[0]), " ".join(row[1:]))
        comp += "</span>"
        DialogFactory.get_information_dialog(
            comp, parent=self.view.get_toplevel()
        ).run()

    pass # end of class

class MixturesController(ObjectListStoreController):

    treemodel_property_name = "mixtures"
    treemodel_class_type = Mixture
    columns = [ ("Mixture name", "c_name") ]
    delete_msg = "Deleting a mixture is irreverisble!\nAre You sure you want to continue?"
    obj_type_map = [
        (Mixture, EditMixtureView, EditMixtureController),
    ]

    def get_mixtures_tree_model(self, *args):
        return self.treemodel

    # ------------------------------------------------------------
    #      GTK Signal handlers
    # ------------------------------------------------------------
    def on_load_object_clicked(self, event):
        pass # cannot load mixtures
    def on_save_object_clicked(self, event):
        pass # cannot save mixtures

    def create_new_object_proxy(self):
        return Mixture(parent=self.model)

    @contextmanager
    def _multi_operation_context(self):
        with self.model.data_changed.hold():
            yield

    pass # end of class
