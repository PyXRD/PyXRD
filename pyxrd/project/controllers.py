# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import os

import pango
import gtk

from pyxrd.mvc import Controller

from pyxrd.generic.views.treeview_tools import new_text_column, new_toggle_column, new_pb_column
from pyxrd.generic.controllers import BaseController, ObjectListStoreController
from pyxrd.specimen.models import Specimen
from contextlib import contextmanager

class ProjectController(ObjectListStoreController):

    treemodel_property_name = "specimens"
    treemodel_class_type = Specimen
    columns = [ ]
    delete_msg = "Deleting a specimen is irreversible!\nAre You sure you want to continue?"
    auto_adapt = True

    file_filters = Specimen.Meta.file_filters

    def register_view(self, view):
        if view is not None and self.model is not None:
            if self.parent is not None: # is this still needed?
                tv = self.view["project_specimens"]
                tv.set_model(self.treemodel)
                self.view.treeview = tv
                self.view.set_x_range_sensitive(self.model.axes_xlimit == 1)
                self.view.set_y_range_sensitive(self.model.axes_ylimit == 1)
        return

    def _idle_register_view(self, *args, **kwargs):
        super(ProjectController, self)._idle_register_view(*args, **kwargs)

    def adapt(self, *args, **kwargs):
        super(ProjectController, self).adapt(*args, **kwargs)

    def setup_treeview(self, widget):
        super(ProjectController, self).setup_treeview(widget)
        store = self.treemodel
        widget.connect('button-press-event', self.specimen_tv_button_press)

        # First reset & then (re)create the columns of the treeview:
        for col in widget.get_columns():
            widget.remove_column(col)

        # Name column:
        col = new_text_column('Name',
            text_col=store.c_name,
            min_width=125,
            xalign=0.0,
            ellipsize=pango.ELLIPSIZE_END)
        col.set_data("colnr", store.c_name)
        widget.append_column(col)

        # Check boxes:
        def toggle_renderer(column, cell, model, itr, data=None):
            active = False
            if model.iter_is_valid(itr):
                col = column.get_col_attr("active")
                active = model.get_value(itr, col)
            cell.set_property('active', active)
            return
        def setup_check_column(title, colnr):
            col = new_toggle_column(title,
                    toggled_callback=(self.specimen_tv_toggled, (store, colnr)),
                    data_func=toggle_renderer,
                    resizable=False,
                    expand=False,
                    activatable=True,
                    active_col=colnr)
            col.set_data("colnr", colnr)
            widget.append_column(col)

        setup_check_column('Exp', store.c_display_experimental)
        if self.model.layout_mode == "FULL":
            setup_check_column('Cal', store.c_display_calculated)
            setup_check_column('Sep', store.c_display_phases)

        # Up and down arrows:
        def setup_image_button(image, colnr):
            col = new_pb_column("", resizable=False, expand=False, stock_id=image)
            col.set_data("colnr", colnr)
            widget.append_column(col)
        setup_image_button("213-up-arrow", 501)
        setup_image_button("212-down-arrow", 502)

    def edit_object(self, obj):
        pass # clear this method, we're not having an 'edit' view pane...

    @BaseController.status_message("Importing multiple specimens...", "add_specimen")
    def import_multiple_specimen(self):
        def on_accept(dialog):
            filenames = dialog.get_filenames()
            parser = dialog.get_filter().get_data("parser")
            last_iter = None
            for filename in filenames:
                try:
                    specimens = Specimen.from_experimental_data(filename=filename, parent=self.model, parser=parser)
                except Exception as msg:
                    message = "An unexpected error has occurred when trying to parse %s:\n\n<i>" % os.path.basename(filename)
                    message += str(msg) + "</i>\n\n"
                    message += "This is most likely caused by an invalid or unsupported file format."
                    self.run_information_dialog(
                        message=message,
                        parent=self.view.get_top_widget()
                    )
                else:
                    for specimen in specimens:
                        last_iter = self.model.specimens.append(specimen)
            if last_iter is not None:
                self.view["project_specimens"].set_cursor(last_iter)

        self.run_load_dialog(title="Select XRD files for import",
                             on_accept_callback=on_accept,
                             parent=self.view.get_top_widget(),
                             multiple=True)

    @BaseController.status_message("Deleting specimen...", "del_specimen")
    def delete_selected_specimens(self):
        """
            Asks the user for confirmation and if positive deletes all the 
            selected specimens. Does nothing when no specimens are selected.
        """
        selection = self.get_selected_objects()
        if selection is not None and len(selection) >= 1:
            def delete_objects(dialog):
                for obj in selection:
                    if obj is not None:
                        self.model.specimens.remove(obj)
            self.run_confirmation_dialog(
                message='Deleting a specimen is irreversible!\nAre You sure you want to continue?',
                on_accept_callback=delete_objects,
                parent=self.view.get_top_widget())

    def edit_specimen(self):
        selection = self.get_selected_objects()
        if selection is not None and len(selection) == 1:
            # TODO move the specimen view & controller into the project level
            self.parent.view.specimen.present()

    @BaseController.status_message("Creating new specimen...", "add_specimen")
    def add_specimen(self):
        specimen = Specimen(parent=self.model, name="New Specimen")
        self.model.specimens.append(specimen)
        self.view.specimens_treeview.set_cursor(self.treemodel.on_get_path(specimen))
        self.edit_specimen()
        return True

    @contextmanager
    def _multi_operation_context(self):
        with self.model.hold_mixtures_data_changed():
            with self.model.data_changed.hold():
                yield

    # ------------------------------------------------------------
    #      Notifications of observable properties
    # ------------------------------------------------------------
    @Controller.observe("name", assign=True)
    def notif_change_name(self, model, prop_name, info):
        self.parent.update_title()
        return

    @Controller.observe("axes_xlimit", assign=True)
    def notif_xlimit_toggled(self, model, prop_name, info):
        self.view.set_x_range_sensitive(int(self.model.axes_xlimit) == 1)

    @Controller.observe("axes_ylimit", assign=True)
    def notif_ylimit_toggled(self, model, prop_name, info):
        self.view.set_y_range_sensitive(int(self.model.axes_ylimit) == 1)

    @Controller.observe("layout_mode", assign=True)
    def notif_layout_mode(self, model, prop_name, info):
        self.parent.set_layout_mode(self.model.layout_mode)
        if self.view is not None:
            self.setup_treeview(self.view.treeview)

    # ------------------------------------------------------------
    #      GTK Signal handlers
    # ------------------------------------------------------------
    def specimen_tv_toggled(self, cell, path, model, colnr):
        if model is not None:
            itr = model.get_iter(path)
            model.set_value(itr, colnr, not cell.get_active())
            return True
        return False

    def specimen_tv_button_press(self, tv, event):
        specimen = None
        current_specimens = self.parent.model.current_specimens or []
        ret = tv.get_path_at_pos(int(event.x), int(event.y))
        if ret is not None:
            path, col, x, y = ret
            specimen = self.treemodel.get_user_data_from_path(path) # FIXME
        if event.button == 3:
            if specimen is not None:
                # clicked a specimen which is not in the current selection,
                # so clear selection and select it
                if not specimen in current_specimens:
                    self.select_object(specimen)
            else:
                # clicked an empty space, so clear selection
                self.select_object(None)
            self.view.show_specimens_context_menu(event)
            return True
        elif event.type == gtk.gdk._2BUTTON_PRESS and specimen is not None and col.get_data("colnr") == self.treemodel.c_name:
            self.parent.on_edit_specimen_activate(event)
            return True
        elif (event.button == 1 or event.type == gtk.gdk._2BUTTON_PRESS) and specimen is not None:
            column = col.get_data("colnr")
            if column in (self.treemodel.c_display_experimental,
                    self.treemodel.c_display_calculated,
                    self.treemodel.c_display_phases):
                if column == self.treemodel.c_display_experimental:
                    specimen.display_experimental = not specimen.display_experimental
                elif column == self.treemodel.c_display_calculated:
                    specimen.display_calculated = not specimen.display_calculated
                elif column == self.treemodel.c_display_phases:
                    specimen.display_phases = not specimen.display_phases
                # TODO FIXME self.treemodel.on_row_changed(ret)
                return True
            elif column == 501:
                self.model.move_specimen_down(specimen)
                self.parent.model.current_specimens = self.get_selected_objects()
                return True
            elif column == 502:
                self.model.move_specimen_up(specimen)
                self.parent.model.current_specimens = self.get_selected_objects()
                return True

    def objects_tv_selection_changed(self, selection):
        ObjectListStoreController.objects_tv_selection_changed(self, selection)
        self.parent.model.current_specimens = self.get_selected_objects()
        return True

    pass # end of class
