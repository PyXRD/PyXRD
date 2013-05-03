# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import locale

import pango
import gtk
import gio

from gtkmvc import Controller
from gtkmvc.adapters import Adapter

import settings

from generic.views.treeview_tools import new_text_column, new_toggle_column, new_pb_column
from generic.views.validators import FloatEntryValidator 
from generic.controllers import BaseController, DialogController, ObjectListStoreMixin, DialogMixin, ctrl_setup_combo_with_list
from generic.controllers.handlers import get_color_val #FIXME USE HANDLERS!!
from project.models import Project
from specimen.models import Specimen
from specimen.controllers import SpecimenController

class ProjectController (DialogController, ObjectListStoreMixin, DialogMixin):

    model_property_name = "specimens"
    columns = [ ]
    delete_msg = "Deleting objects is irreverisble!\nAre You sure you want to continue?"


    file_filters = SpecimenController.file_filters

    def register_view(self, view):
        # connects the buffer and the text view
        if view is not None and self.model is not None:
            view["project_data_description"].set_buffer(self.model.description)
            if self.parent is not None:
                tv = self.parent.view["specimens_treeview"]
                tv.set_model(self.model.specimens)
                self.view.treeview = tv
        return

    def register_adapters(self):
        if self.model is not None and self.parent is not None:
            for name in self.model.get_properties():
                if name == "name":
                    self.adapt(name, "project_%s" % name)
                elif name == "description":
                    pass
                elif name in ("display_calc_color", "display_exp_color", "display_marker_color"):
                    ad = Adapter(self.model, name)
                    ad.connect_widget(self.view["project_%s" % name], getter=get_color_val)
                    self.adapt(ad)
                elif name in ("display_marker_angle", "display_plot_offset", "project_axes_xmin", "project_axes_xmax", "display_label_pos"):
                    FloatEntryValidator(self.view["project_%s" % name])
                    self.adapt(name)
                elif name in ("axes_xscale", "axes_yscale", "display_marker_align", "display_marker_style", "display_marker_base"):
                    ctrl_setup_combo_with_list(self, self.view["project_%s" % name], name, "_%ss"%name)
                elif name == "specimens":
                    # connects the treeview to the liststore
                    self.setup_treeview(self.parent.view["specimens_treeview"])
                elif not name in self.model.__have_no_widget__:
                    self.adapt(name)
            return

    def setup_treeview(self, tv):
        ObjectListStoreMixin.setup_treeview(self, tv)
        tv.connect('button-press-event', self.specimen_tv_button_press)
        tv_model = self.model.specimens
        
        #First reset & then (re)create the columns of the treeview:
        for col in tv.get_columns():
            tv.remove_column(col)
        
        #Name column:       
        col = new_text_column('Name', 
            text_col=tv_model.c_name, 
            min_width=125,
            xalign=0.0,
            ellipsize=pango.ELLIPSIZE_END)
        col.set_data("colnr", tv_model.c_name)
        tv.append_column(col)

        #Checkboxes:
        def toggle_renderer(column, cell, model, itr, data=None):
            col = column.get_col_attr("active")
            cell.set_property('active', model.get_value(itr, col))
            return  
        def setup_check_column(title, colnr):    
            col = new_toggle_column(title,
                    toggled_callback=(self.specimen_tv_toggled, (tv_model, colnr)),
                    data_func=toggle_renderer,
                    resizable=False,
                    expand=False,
                    activatable=True,
                    active_col=colnr)
            col.set_data("colnr", colnr)
            tv.append_column(col)
        
        setup_check_column('Exp', self.model.specimens.c_display_experimental)
        if not settings.VIEW_MODE:
            setup_check_column('Cal', self.model.specimens.c_display_calculated)
            setup_check_column('Sep', self.model.specimens.c_display_phases)
        
        #Up and down arrows:       
        def setup_image_button(image, colnr):
            col = new_pb_column("", resizable=False, expand=False, stock_id=image)
            col.set_data("colnr", colnr)
            tv.append_column(col)
        setup_image_button(gtk.STOCK_GO_UP, 501)
        setup_image_button(gtk.STOCK_GO_DOWN, 502)
                

    def edit_object(self, obj):
        pass

    def set_object_sensitivities(self, value):
        pass #no sensitivity stuff to do? --> TODO popup!

    @BaseController.status_message("Importing multiple specimens...", "add_specimen")
    def import_multiple_specimen(self):
        def on_accept(dialog):
            filenames = dialog.get_filenames()
            parser = dialog.get_filter().get_data("parser")
            last_iter = None
            for filename in filenames:
                specimens = Specimen.from_experimental_data(filename=filename, parent=self.model, parser=parser)                
                for specimen in specimens:
                    last_iter = self.model.specimens.append(specimen)
            if last_iter != None:
                self.parent.view["specimens_treeview"].set_cursor(last_iter)
        
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
        for widget in ("lbl_minx", "lbl_maxx", "project_axes_xmin", "project_axes_xmax"):
            self.view[widget].set_sensitive(self.model.axes_xscale==1)
        
    @Controller.observe("needs_update", signal=True)
    def notif_display_props(self, model, prop_name, info):            
        self.parent.redraw_plot()

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
            if specimen!=None:
                #clicked a specimen which is not in the current selection,
                #so clear selection and select it
                if not specimen in current_specimens:
                    self.select_object(specimen)
            else:
                #clicked an empty space, so clear selection
                self.select_object(None)
            self.view.specimens_popup(event)
            return True
        elif event.type == gtk.gdk._2BUTTON_PRESS and specimen is not None and col.get_data("colnr")==self.model.specimens.c_name:
            self.parent.on_edit_specimen_activate(event)
            return True
        elif (event.button == 1 or event.type == gtk.gdk._2BUTTON_PRESS) and specimen is not None:
            column = col.get_data("colnr")
            if column in (self.model.specimens.c_display_experimental, 
                    self.model.specimens.c_display_calculated,
                    self.model.specimens.c_display_phases):
                if column==self.model.specimens.c_display_experimental:
                    specimen.display_experimental = not specimen.display_experimental
                elif column==self.model.specimens.c_display_calculated:
                    specimen.display_calculated = not specimen.display_calculated
                elif column==self.model.specimens.c_display_phases:
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
