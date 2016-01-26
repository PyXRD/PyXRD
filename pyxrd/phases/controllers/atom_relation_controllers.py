# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import logging
logger = logging.getLogger(__name__)

import gtk, pango

from mvc.adapters.dummy_adapter import DummyAdapter

from pyxrd.generic.views.treeview_tools import (
    new_text_column,
    new_pb_column,
    new_combo_column,
    create_float_data_func,
    setup_treeview
)
from pyxrd.generic.views.combobox_tools import add_combo_text_column
from pyxrd.generic.views import InlineObjectListStoreView
from pyxrd.generic.controllers import (
    DialogController,
    InlineObjectListStoreController,
    BaseController,
)

from pyxrd.phases.views import EditAtomRatioView, EditAtomContentsView
from pyxrd.phases.models.atom_relations import AtomRelation, AtomRatio, AtomContents, AtomContentObject

class AtomComboMixin(object):

    extra_props = []
    custom_handler_names = []

    def reset_combo_box(self, name):
        if self.model.component is not None:
            # Get store, reset combo
            store = self.model.create_prop_store(self.extra_props)
            combo = self.view[self.view.widget_format % name]
            combo.clear()
            combo.set_model(store)

            # Add text column:
            def get_name(layout, cell, model, itr, data=None):
                obj, lbl = model.get(itr, 0, 2)
                if callable(lbl): lbl = lbl(obj)
                cell.set_property("markup", lbl)
            add_combo_text_column(combo, data_func=get_name)

            # Set the selected item to active:
            prop = getattr(self.model, name)
            if prop is not None:
                prop = tuple(prop)
                for row in store:
                    if tuple(store.get(row.iter, 0, 1)) == prop:
                        combo.set_active_iter(row.iter)
                        break

            return combo, store
        else:
            return None, None

    @staticmethod
    def custom_handler(controller, intel, prefix):
        if intel.name in controller.custom_handler_names:
            combo, store = controller.reset_combo_box(intel.name) # @UnusedVariable

            if combo is not None and store is not None:
                def on_changed(combo, user_data=None):
                    itr = combo.get_active_iter()
                    if itr is not None:
                        val = combo.get_model().get(itr, 0, 1)
                        setattr(controller.model, combo.get_data('model_prop'), val)
                combo.set_data('model_prop', intel.name)
                combo.connect('changed', on_changed)

                def on_item_changed(*args):
                    controller.reset_combo_box(intel.name)

                if controller.is_observing_method("atoms_changed", on_item_changed):
                    controller.remove_observing_method("atoms_changed", on_item_changed)
                controller.observe(on_item_changed, "atoms_changed", signal=True)

        else: return False
        return True

    pass # end of class

class EditUnitCellPropertyController(BaseController, AtomComboMixin):
    """ 
        Controller for the UnitCellProperty models (a and b cell lengths)
    """

    custom_handler_names = ["prop", ]
    widget_handlers = {
        'combo': 'custom_handler',
    }

    def __init__(self, extra_props, **kwargs):
        super(EditUnitCellPropertyController, self).__init__(**kwargs)
        self.extra_props = extra_props

    def register_adapters(self):
        BaseController.register_adapters(self)
        self.update_sensitivities()

    def update_sensitivities(self):
        self.view['ucp_value'].set_sensitive(not self.model.enabled)
        self.view['box_enabled'].set_sensitive(self.model.enabled)

    # ------------------------------------------------------------
    #      Notifications of observable properties
    # ------------------------------------------------------------
    @BaseController.observe("enabled", assign=True)
    def notif_enabled_changed(self, model, prop_name, info):
        self.update_sensitivities()

    pass # end of class

class EditAtomRatioController(DialogController, AtomComboMixin):
    """ 
        Controller for the atom ratio edit dialog
    """
    custom_handler_names = ["atom1", "atom2"]
    widget_handlers = {
        'custom': 'custom_handler',
    }

    pass # end of class

class EditAtomContentsController(DialogController):
    """ 
        Controller for the atom contents edit dialog
    """

    contents_list_view = None
    contents_list_controller = None

    widget_handlers = { 'custom': 'widget_handler' }

    def __init__(self, *args, **kwargs):
        super(EditAtomContentsController, self).__init__(*args, **kwargs)
        self.contents_list_view = InlineObjectListStoreView(parent=self.view)
        self.contents_list_controller = ContentsListController("atom_contents", model=self.model, view=self.contents_list_view, parent=self)

    @staticmethod
    def widget_handler(self, intel, widget):
        if intel.name == "atom_contents":
            self.view.set_contents_list_view(self.contents_list_view.get_top_widget())
            return DummyAdapter(controller=self, prop=intel)

    pass # end of class

class ContentsListController(InlineObjectListStoreController):
    """ 
        Controller for the atom contents ListStore
    """
    new_val = None
    auto_adapt = False # FIXME

    treemodel_class_type = AtomContentObject

    def _reset_treeview(self, tv, model):
        setup_treeview(tv, model, sel_mode=gtk.SELECTION_MULTIPLE, reset=True)
        tv.set_model(model)

        # Atom column:
        def atom_renderer(column, cell, model, itr, (obj_col, lbl_col)):
            obj = model.get_value(itr, obj_col)
            if lbl_col is not None:
                lbl = model.get_value(itr, lbl_col)
                if callable(lbl): lbl = lbl(obj)
                cell.set_property("text", lbl)
            else:
                if hasattr(obj, "name"):
                    cell.set_property('text', obj.name)
                else:
                    cell.set_property('text', '#NA#')
        def adjust_combo(cell, editable, path, data=None):
            if editable is not None:
                rend = gtk.CellRendererText()
                editable.clear()
                editable.pack_start(rend)
                editable.set_cell_data_func(rend, atom_renderer, (0, 2))
        tv.append_column(new_combo_column(
            "Atoms",
            changed_callback=self.on_atom_changed,
            edited_callback=self.on_atom_edited,
            editing_started_callback=adjust_combo,
            xalign=0.0,
            model=self.model.create_prop_store(),
            data_func=(atom_renderer, (0, None)),
            text_column=0,
            editable=True))

        # Content column:
        def on_float_edited(rend, path, new_text, col):
            itr = model.get_iter(path)
            try:
                model.set_value(itr, col, float(new_text))
            except ValueError:
                logger.exception("Invalid value entered ('%s')!" % new_text)
            return True
        tv.append_column(new_text_column('Default contents', text_col=2, xalign=0.0,
            editable=True,
            data_func=create_float_data_func(),
            edited_callback=(on_float_edited, (2,))))

    def _setup_treeview(self, tv, model):
        self._reset_treeview(tv, model)

    def __init__(self, treemodel_property_name, **kwargs):
        super(ContentsListController, self).__init__(
            treemodel_property_name=treemodel_property_name,
            enable_import=False, enable_export=False, **kwargs
        )

    def create_new_object_proxy(self):
        return AtomContentObject(None, None, 1.0)

    def on_atom_changed(self, combo, path, new_iter, user_data=None):
        self.new_val = combo.get_property("model").get(new_iter, 0, 1)
        print self.new_val

    def on_atom_edited(self, combo, path, new_text, args=None):
        if self.new_val:
            new_atom, new_prop = self.new_val
            self.model.set_atom_content_values(path, new_atom, new_prop)
            self.new_val = None
        return True

    pass # end of class

class EditAtomRelationsController(InlineObjectListStoreController):
    """ 
        Controller for the components' atom relations ObjectListStore
    """
    file_filters = AtomRelation.Meta.file_filters
    auto_adapt = False
    treemodel_class_type = AtomRelation

    add_types = [
        ("Ratio", AtomRatio, EditAtomRatioView, EditAtomRatioController),
        ("Contents", AtomContents, EditAtomContentsView, EditAtomContentsController),
    ]

    def _reset_treeview(self, tv, model):
        setup_treeview(tv, model, sel_mode=gtk.SELECTION_MULTIPLE, reset=True)
        tv.set_model(model)

        # Name column:
        def text_renderer(column, cell, model, itr, args=None):
            driven_by_other = model.get_value(itr, model.c_driven_by_other)
            cell.set_property('editable', not driven_by_other)
            cell.set_property('style', pango.STYLE_ITALIC if driven_by_other else pango.STYLE_NORMAL)
        col = new_text_column(
            'Name',
            data_func=text_renderer,
            editable=True,
            edited_callback=(self.on_item_cell_edited, (model, model.c_name)),
            resizable=False,
            text_col=model.c_name)
        col.set_data("col_descr", 'Name')
        tv.append_column(col)

        # Value of the relation:
        float_rend = create_float_data_func()
        def data_renderer(column, cell, model, itr, args=None):
            text_renderer(column, cell, model, itr, args)
            float_rend(column, cell, model, itr, args)
        col = new_text_column(
            'Value',
            data_func=data_renderer,
            editable=True,
            edited_callback=(self.on_item_cell_edited, (model, model.c_value)),
            resizable=False,
            text_col=model.c_value)
        col.set_data("col_descr", 'Value')
        tv.append_column(col)

        # Up, down and edit arrows:
        def setup_image_button(image, colnr):
            col = new_pb_column(" ", resizable=False, expand=False, stock_id=image)
            col.set_data("col_descr", colnr)
            tv.append_column(col)
        setup_image_button("213-up-arrow", "Up")
        setup_image_button("212-down-arrow", "Down")
        setup_image_button("030-pencil", "Edit")

    def _setup_treeview(self, tv, model):
        tv.connect('button-press-event', self.tv_button_press)
        self._reset_treeview(tv, model)

    def __init__(self, **kwargs):
        super(EditAtomRelationsController, self).__init__(
            enable_import=False, enable_export=False, **kwargs)

    def create_new_object_proxy(self):
        return self.add_type(parent=self.model)

    def tv_button_press(self, tv, event):
        relation = None
        ret = tv.get_path_at_pos(int(event.x), int(event.y))

        if ret is not None:
            path, col, x, y = ret
            model = tv.get_model()
            relation = model.get_user_data_from_path(path)
            column = col.get_data("col_descr")
        if event.button == 1 and relation is not None:
            column = col.get_data("col_descr")
            if column == "Edit":
                self._edit_item(relation)
                return True
            elif column == "Up":
                self.model.move_atom_relation_up(relation)
                return True
            elif column == "Down":
                self.model.move_atom_relation_down(relation)
                return True


    pass # end of class
