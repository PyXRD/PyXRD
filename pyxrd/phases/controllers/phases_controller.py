# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

from contextlib import contextmanager

import logging
logger = logging.getLogger(__name__)

import gtk

from mvc import Model
from mvc.adapters.gtk_support.dialogs.dialog_factory import DialogFactory

from pyxrd.generic.gtk_tools.utils import convert_string_to_gdk_color_int
from pyxrd.generic.views.treeview_tools import new_pb_column
from pyxrd.generic.controllers import ObjectListStoreController
from pyxrd.generic.utils import not_none

from pyxrd.phases.views import (
    EditPhaseView, AddPhaseView, EditRawPatternPhaseView
)

from pyxrd.file_parsers.json_parser import JSONParser
from pyxrd.file_parsers.phase_parsers import phase_parsers

from ..models import Phase, RawPatternPhase

from .edit_phase_controller import EditPhaseController
from .raw_pattern_phase_controller import EditRawPatternPhaseController
from .add_phase_controller import AddPhaseController


class PhasesController(ObjectListStoreController):
    """ 
        Controller for the phases list
    """
    file_filters = Phase.Meta.file_filters
    treemodel_property_name = "phases"
    treemodel_class_type = Phase
    obj_type_map = [
        (Phase, EditPhaseView, EditPhaseController),
        (RawPatternPhase, EditRawPatternPhaseView, EditRawPatternPhaseController),
    ]
    multi_selection = True
    columns = [
        ("Phase name", "c_name"),
        (" ", "c_display_color"),
        ("R", "c_R"),
        ("#", "c_G"),
    ]
    delete_msg = "Deleting a phase is irreversible!\nAre You sure you want to continue?"
    title = "Edit Phases"

    def get_phases_tree_model(self, *args):
        return self.treemodel

    def load_phases(self, filename, parser=JSONParser):
        index = self.get_selected_index()
        if index is not None: index += 1
        self.model.load_phases(filename, parser=parser, insert_index=index)

    def setup_treeview_col_c_display_color(self, treeview, name, col_descr, col_index, tv_col_nr):
        def set_pb(column, cell_renderer, tree_model, iter, col_index): # @ReservedAssignment
            try:
                color = tree_model.get_value(iter, col_index)
            except TypeError:
                pass # invalid iter
            else:
                color = convert_string_to_gdk_color_int(color)
                phase = tree_model.get_user_data(iter)
                pb, old_color = getattr(phase, "__col_c_pb", (None, None))
                if old_color != color:
                    pb = gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB, True, 8, 10, 20) # @UndefinedVariable
                    pb.fill(color)
                    setattr(phase, "__col_c_pb", (color, pb))
                cell_renderer.set_property('pixbuf', pb)

        treeview.append_column(new_pb_column(
            name,
            data_func=(set_pb, (col_index,)),
            resizable=False,
            expand=False))

        return True

    def create_new_object_proxy(self):
        def on_accept(phase_type, G, R):
            index = int(not_none(self.get_selected_index(), -1)) + 1
            if phase_type == "empty":
                self.add_object(Phase(G=int(G), R=int(R)))
            elif phase_type == "raw":
                self.add_object(RawPatternPhase())
            else:
                filename = phase_type
                if filename != None:
                    self.model.load_phases(filename, parser=JSONParser, insert_index=index)

        # TODO re-use this and reset the COMBO etc.
        self.add_model = Model()
        self.add_view = AddPhaseView(parent=self.view)
        self.add_ctrl = AddPhaseController(
            model=self.add_model, view=self.add_view, parent=self.parent,
            callback=on_accept
        )

        self.add_view.present()
        return None

    @contextmanager
    def _multi_operation_context(self):
        with self.model.hold_mixtures_data_changed():
            with self.model.hold_mixtures_needs_update():
                with self.model.hold_phases_data_changed():
                    yield

    # ------------------------------------------------------------
    #      GTK Signal handlers
    # ------------------------------------------------------------
    def on_save_object_clicked(self, event):
        def on_accept(dialog):
            logger.info("Exporting phases...")
            Phase.save_phases(self.get_selected_objects(), filename=dialog.filename)
        DialogFactory.get_save_dialog(
            "Export phase", parent=self.view.get_top_widget(),
            filters=phase_parsers.get_export_file_filters()
        ).run(on_accept)
        return True


    def on_load_object_clicked(self, event):
        def on_accept(dialog):
            logger.info("Importing phases...")
            self.load_phases(dialog.filename, parser=dialog.parser)
        DialogFactory.get_load_dialog(
            "Import phase", parent=self.view.get_top_widget(),
            filters=phase_parsers.get_import_file_filters()
        ).run(on_accept)
        return True
