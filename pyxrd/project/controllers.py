    # coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import os

import pango
import gtk

from pyxrd.gtkmvc import Controller

from pyxrd.generic.views.treeview_tools import new_text_column, new_toggle_column, new_pb_column
from pyxrd.generic.controllers import BaseController, DialogController, ObjectListStoreMixin, DialogMixin
from pyxrd.specimen.models import Specimen
from pyxrd.specimen.controllers import SpecimenController

class ProjectController (DialogController, ObjectListStoreMixin, DialogMixin):

    model_property_name = "specimens"
    columns = [ ]
    delete_msg = "Deleting a specimen is irreversible!\nAre You sure you want to continue?"
    file_filters = SpecimenController.file_filters

    def register_view(self, view):
        if view is not None and self.model is not None:
            if self.parent is not None:
                tv = self.view["project_specimens"]
                tv.set_model(self.model.specimens)
                self.view.treeview = tv
        return

    def setup_specimens_tree_view(self, store, widget):
        ObjectListStoreMixin.setup_treeview(self, widget)
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
            col = column.get_col_attr("active")
            cell.set_property('active', model.get_value(itr, col))
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

        setup_check_column('Exp', self.model.specimens.c_display_experimental)
        if self.model.layout_mode == "FULL":
            setup_check_column('Cal', self.model.specimens.c_display_calculated)
            setup_check_column('Sep', self.model.specimens.c_display_phases)

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
            if last_iter != None:
                self.view["project_specimens"].set_cursor(last_iter)

        self.run_load_dialog(title="Select XRD files for import",
                             on_accept_callback=on_accept,
                             parent=self.view.get_top_widget(),
                             multiple=True)

    # ------------------------------------------------------------
    #      Notifications of observable properties
    # ------------------------------------------------------------
    @Controller.observe("name", assign=True)
    def notif_change_name(self, model, prop_name, info):
        self.parent.update_title()
        return

    @Controller.observe("axes_xscale", assign=True)
    def notif_xscale_toggled(self, model, prop_name, info):
        self.view.set_x_range_sensitive(self.model.axes_xscale == 1)

    @Controller.observe("needs_update", signal=True)
    def notif_display_props(self, model, prop_name, info):
        self.parent.redraw_plot()

    @Controller.observe("layout_mode", assign=True)
    def notif_layout_mode(self, model, prop_name, info):
        self.parent.set_layout_mode(self.model.layout_mode)

    # ------------------------------------------------------------
    #      GTK Signal handlers
    # ------------------------------------------------------------
    def specimen_tv_toggled(self, cell, path, model, colnr):
        if model != None:
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
            model = tv.get_model()
            specimen = model.get_user_data_from_path(path)
        if event.button == 3:
            if specimen != None:
                # clicked a specimen which is not in the current selection,
                # so clear selection and select it
                if not specimen in current_specimens:
                    self.select_object(specimen)
            else:
                # clicked an empty space, so clear selection
                self.select_object(None)
            self.view.specimens_popup(event)
            return True
        elif event.type == gtk.gdk._2BUTTON_PRESS and specimen is not None and col.get_data("colnr") == self.model.specimens.c_name:
            self.parent.on_edit_specimen_activate(event)
            return True
        elif (event.button == 1 or event.type == gtk.gdk._2BUTTON_PRESS) and specimen is not None:
            column = col.get_data("colnr")
            if column in (self.model.specimens.c_display_experimental,
                    self.model.specimens.c_display_calculated,
                    self.model.specimens.c_display_phases):
                if column == self.model.specimens.c_display_experimental:
                    specimen.display_experimental = not specimen.display_experimental
                elif column == self.model.specimens.c_display_calculated:
                    specimen.display_calculated = not specimen.display_calculated
                elif column == self.model.specimens.c_display_phases:
                    specimen.display_phases = not specimen.display_phases
                model.on_item_changed(specimen)
                return True
            elif column == 501:
                model.move_item_up(specimen)
                self.parent.model.current_specimens = self.get_selected_objects()
                return True
            elif column == 502:
                model.move_item_down(specimen)
                self.parent.model.current_specimens = self.get_selected_objects()
                return True

    def objects_tv_selection_changed(self, selection):
        ObjectListStoreMixin.objects_tv_selection_changed(self, selection)
        self.parent.model.current_specimens = self.get_selected_objects()
        return True

    pass # end of class
