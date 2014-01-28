# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import logging
logger = logging.getLogger(__name__)

from pyxrd.mvc import Controller
from pyxrd.mvc.adapters.dummy_adapter import DummyAdapter

from pyxrd.generic.views import InlineObjectListStoreView
from pyxrd.generic.views.combobox_tools import add_combo_text_column
from pyxrd.generic.controllers import BaseController, ChildObjectListStoreController
from pyxrd.generic.io.utils import get_case_insensitive_glob

from pyxrd.phases.controllers import EditLayerController, EditAtomRelationsController, EditUnitCellPropertyController
from pyxrd.phases.views import EditComponentView, EditUnitCellPropertyView
from pyxrd.phases.models import Phase, Component
from pyxrd.generic.controllers.objectliststore_controllers import wrap_list_property_to_treemodel

class EditComponentController(BaseController):
    """ 
        Controller for the component edit view
    """
    layer_view = None
    layer_controller = None

    interlayer_view = None
    interlayer_controller = None

    atom_relations_view = None
    atom_relations_controller = None

    ucpa_view = None
    ucpa_controller = None

    ucpb_view = None
    ucpb_controller = None

    widget_handlers = {
        'custom': 'custom_handler',
    }

    @property
    def components_treemodel(self):
        if self.model.phase.based_on:
            prop = Phase.Meta.get_prop_intel_by_name("components")
            return wrap_list_property_to_treemodel(self.model.phase.based_on, prop)
        else:
            return None

    def reset_combo_box(self):
        """
            Reset the `linked_with` combo box.
        """
        if self.model is not None and self.model.parent is not None:
            combo = self.view["component_linked_with"]
            combo.clear()
            combo.set_model(self.components_treemodel)
            if self.components_treemodel is not None:
                add_combo_text_column(combo, text_col=self.components_treemodel.c_name)
                for row in self.components_treemodel:
                    comp = self.components_treemodel.get_user_data(row.iter)
                    if comp == self.model.linked_with:
                        combo.set_active_iter (row.iter)
                        break

    @staticmethod
    def custom_handler(self, intel, widget):
        if intel.name == "layer_atoms":
            self.view.set_layer_view(self.layer_view.get_top_widget())
        elif intel.name == "interlayer_atoms":
            self.view.set_interlayer_view(self.interlayer_view.get_top_widget())
        elif intel.name == "atom_relations":
            self.view.set_atom_relations_view(self.atom_relations_view.get_top_widget())
        elif intel.name in ("ucp_a", "ucp_b"):
            self.view.set_ucpa_view(self.ucpa_view.get_top_widget())
            self.view.set_ucpb_view(self.ucpb_view.get_top_widget())
        elif intel.name == "linked_with":
            self.reset_combo_box()
        return DummyAdapter(controller=self, prop=intel)

    def register_view(self, view):
        super(EditComponentController, self).register_view(view)

        self.layer_view = InlineObjectListStoreView(parent=view)
        self.layer_controller = EditLayerController(treemodel_property_name="layer_atoms", model=self.model, view=self.layer_view, parent=self)

        self.interlayer_view = InlineObjectListStoreView(parent=view)
        self.interlayer_controller = EditLayerController(treemodel_property_name="interlayer_atoms", model=self.model, view=self.interlayer_view, parent=self)

        self.atom_relations_view = InlineObjectListStoreView(parent=view)
        self.atom_relations_controller = EditAtomRelationsController(treemodel_property_name="atom_relations", model=self.model, view=self.atom_relations_view, parent=self)

        self.ucpa_view = EditUnitCellPropertyView(parent=view)
        self.ucpa_controller = EditUnitCellPropertyController(extra_props=[(self.model, "cell_b", "B cell length"), ], model=self.model._ucp_a, view=self.ucpa_view, parent=self)

        self.ucpb_view = EditUnitCellPropertyView(parent=view)
        self.ucpb_controller = EditUnitCellPropertyController(extra_props=[(self.model, "cell_a", "A cell length"), ], model=self.model._ucp_b, view=self.ucpb_view, parent=self)

    def register_adapters(self):
        self.update_sensitivities()

    def update_sensitivities(self):
        can_inherit = (self.model.linked_with is not None)

        def update(widget, name):
            self.view[widget].set_sensitive(not (can_inherit and getattr(self.model, "inherit_%s" % name)))
            self.view[widget].set_visible(not (can_inherit and getattr(self.model, "inherit_%s" % name)))
            self.view["component_inherit_%s" % name].set_sensitive(can_inherit)
        for name in ("default_c", "delta_c", "d001"):
            update("container_%s" % name, name)
        for name in ("interlayer_atoms", "layer_atoms", "atom_relations", "ucp_a", "ucp_b"):
            update(self.view.widget_format % name, name)


    # ------------------------------------------------------------
    #      Notifications of observable properties
    # ------------------------------------------------------------
    @Controller.observe("inherit_layer_atoms", assign=True)
    @Controller.observe("inherit_interlayer_atoms", assign=True)
    @Controller.observe("inherit_atom_relations", assign=True)
    @Controller.observe("inherit_ucp_a", assign=True)
    @Controller.observe("inherit_ucp_b", assign=True)
    @Controller.observe("inherit_d001", assign=True)
    @Controller.observe("inherit_default_c", assign=True)
    @Controller.observe("inherit_delta_c", assign=True)
    def notif_change_inherit(self, model, prop_name, info):
        self.update_sensitivities()

    @Controller.observe("linked_with", assign=True)
    def notif_linked_with_changed(self, model, prop_name, info):
        self.reset_combo_box()


    # ------------------------------------------------------------
    #      GTK Signal handlers
    # ------------------------------------------------------------
    def on_linked_with_changed(self, combo, user_data=None):
        itr = combo.get_active_iter()
        if itr is not None:
            val = combo.get_model().get_user_data(itr)
            self.model.linked_with = val
            self.update_sensitivities()
            return
        combo.set_active(-1)
        self.update_sensitivities()
        self.model.linked_with = None

class ComponentsController(ChildObjectListStoreController):
    """ 
        Controller for the components ObjectListStore
    """
    treemodel_property_name = "components"
    treemodel_class_type = Component
    columns = [ ("Component name", "c_name") ]
    delete_msg = "Deleting a component is irreversible!\nAre You sure you want to continue?"
    file_filters = [("Component file", get_case_insensitive_glob("*.CMP")), ]
    obj_type_map = [
        (Component, EditComponentView, EditComponentController),
    ]

    def load_components(self, filename):
        old_comps = self.get_selected_objects()
        if old_comps:
            num_oc = len(old_comps)
            new_comps = list()
            for comp in Component.load_components(filename, parent=self.model):
                comp.resolve_json_references()
                new_comps.append(comp)
            num_nc = len(new_comps)
            if num_oc != num_nc:
                self.run_information_dialog("The number of components to import must equal the number of selected components!")
                return
            else:
                self.select_object(None)
                logger.info("Importing components...")
                # replace component(s):
                for old_comp, new_comp in zip(old_comps, new_comps):
                    i = self.model.components.index(old_comp)
                    self.model.components[i] = new_comp
        else:
            self.run_information_dialog("No components selected to replace!")

    # ------------------------------------------------------------
    #      GTK Signal handlers
    # ------------------------------------------------------------
    def on_save_object_clicked(self, event):
        def on_accept(dialog):
            logger.info("Exporting components...")
            filename = self.extract_filename(dialog)
            Component.save_components(self.get_selected_objects(), filename=filename)
        self.run_save_dialog("Export components", on_accept, parent=self.view.get_toplevel())
        return True

    def on_load_object_clicked(self, event):
        def on_accept(dialog):
            self.load_components(dialog.get_filename())
        self.run_load_dialog("Import components", on_accept, parent=self.view.get_toplevel())
        return True
