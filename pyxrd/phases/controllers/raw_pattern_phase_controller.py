# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import os, locale
import logging
logger = logging.getLogger(__name__)

import gtk

from mvc.adapters.gtk_support.dialogs.dialog_factory import DialogFactory
from mvc.adapters.gtk_support.tree_view_adapters import wrap_xydata_to_treemodel, \
    wrap_list_property_to_treemodel

from pyxrd.generic.controllers import BaseController
from pyxrd.generic.controllers.objectliststore_controllers import TreeViewMixin
from pyxrd.generic.views.treeview_tools import setup_treeview, new_text_column

from ..models import RawPatternPhase

class EditRawPatternPhaseController(TreeViewMixin, BaseController):
    """ 
        Controller for the phase edit view
    """

    file_filters = RawPatternPhase.Meta.rp_filters
    rp_export_filters = RawPatternPhase.Meta.rp_export_filters

    widget_handlers = {
        'custom': 'custom_handler',
    }

    @property
    def phases_treemodel(self):
        if self.model.project is not None:
            prop = self.model.project.Meta.get_prop_intel_by_name("phases")
            return wrap_list_property_to_treemodel(self.model.project, prop)
        else:
            return None

    # ------------------------------------------------------------
    #      Initialization and other internals
    # ------------------------------------------------------------
    @staticmethod
    def custom_handler(self, intel, widget):
        pass # nothing to do

    def setup_raw_pattern_tree_view(self, store, widget):
        """
            Creates the raw pattern TreeView layout and behavior
        """

        setup_treeview(widget, store,
            on_cursor_changed=self.on_raw_pattern_tv_cursor_changed,
            sel_mode=gtk.SELECTION_MULTIPLE)
        # X Column:
        widget.append_column(new_text_column(
            u'°2θ', text_col=store.c_x, editable=True,
            edited_callback=(self.on_xy_data_cell_edited, (self.model.raw_pattern, 0)),
            resizable=True, expand=True))
        # Y Column:
        widget.append_column(new_text_column(
            u'Intensity', text_col=store.c_y, editable=True,
            edited_callback=(self.on_xy_data_cell_edited, (self.model.raw_pattern, 1)),
            resizable=True, expand=True))

    # ------------------------------------------------------------
    #      Methods & Functions
    # ------------------------------------------------------------
    def get_raw_pattern_tree_model(self):
        return wrap_xydata_to_treemodel(self.model, self.model.Meta.get_prop_intel_by_name("raw_pattern"))

    # ------------------------------------------------------------
    #      Notifications of observable properties
    # ------------------------------------------------------------
    @BaseController.observe("name", assign=True)
    def notif_name_changed(self, model, prop_name, info):
        self.phases_treemodel.on_item_changed(self.model)
        return

    # ------------------------------------------------------------
    #      GTK Signal handlers
    # ------------------------------------------------------------
    def on_raw_pattern_tv_cursor_changed(self, tv):
        path, _ = tv.get_cursor()
        self.view["btn_del_raw_data"].set_sensitive(path is not None)
        return True

    def on_add_raw_pattern_clicked(self, widget):
        self.model.raw_pattern.append(0, 0)
        return True

    def on_del_raw_pattern_clicked(self, widget):
        paths = self.get_selected_paths(self.view["phase_rp_raw_pattern"])
        if paths is not None:
            self.model.raw_pattern.remove_from_indeces(*paths)
        return True

    def on_xy_data_cell_edited(self, cell, path, new_text, model, col):
        try:
            value = float(locale.atof(new_text))
        except ValueError:
            logger.exception("ValueError: Invalid literal for float(): '%s'" % new_text)
        else:
            model.set_value(int(path), col, value)
        return True

    def on_replace_raw_pattern(self, *args, **kwargs):
        def on_accept(dialog):
            filename = dialog.filename
            parser = dialog.parser
            try:
                self.model.raw_pattern.load_data(parser, filename, clear=True)
            except Exception:
                message = "An unexpected error has occured when trying to parse '%s'.\n" % os.path.basename(filename)
                message += "This is most likely caused by an invalid or unsupported file format."
                DialogFactory.get_information_dialog(
                    message=message, parent=self.view.get_toplevel()
                ).run()
                raise
        DialogFactory.get_load_dialog(
            "Open XRD file for import", parent=self.view.get_toplevel(),
            filters=self.file_filters
        ).run(on_accept)
        return True

    def on_btn_import_raw_pattern_clicked(self, widget, data=None):
        def on_confirm(dialog):
            self.on_replace_raw_pattern()
        DialogFactory.get_confirmation_dialog(
            "Importing a new experimental file will erase all current data.\nAre you sure you want to continue?",
            parent=self.view.get_toplevel()
        ).run(on_confirm)
        return True

    def on_export_raw_pattern(self, *args, **kwargs):
        return self._export_data(self.model.raw_pattern)

    def on_btn_export_raw_pattern_clicked(self, widget, data=None):
        return self.on_export_raw_pattern()

    def _export_data(self, line):
        def on_accept(dialog):
            filename = dialog.filename
            parser = dialog.parser
            try:
                line.save_data(parser, filename, **self.model.get_export_meta_data())
            except Exception:
                message = "An unexpected error has occured when trying to save to '%s'." % os.path.basename(filename)
                DialogFactory.get_information_dialog(
                    message=message, parent=self.view.get_toplevel()
                ).run()
                raise
        ext_less_fname = os.path.splitext(self.model.name)[0]
        DialogFactory.get_save_dialog(
            "Select file for export", parent=self.view.get_toplevel(),
            filters=self.rp_export_filters,
            current_name=ext_less_fname
        ).run(on_accept)

    pass #end of class
