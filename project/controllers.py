# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Author: Mathijs Dumon
# This work is licensed under the Creative Commons Attribution-ShareAlike 3.0 Unported License. 
# To view a copy of this license, visit http://creativecommons.org/licenses/by-sa/3.0/ or send
# a letter to Creative Commons, 444 Castro Street, Suite 900, Mountain View, California, 94041, USA.

import locale

import pango
import gtk
import gio

from gtkmvc import Controller
from gtkmvc.adapters import Adapter

import settings

from generic.validators import FloatEntryValidator 
from generic.controllers import BaseController, DialogController, HasObjectTreeview, DialogMixin, get_color_val, ctrl_setup_combo_with_list
from project.models import Project
from specimen.models import Specimen
from specimen.controllers import SpecimenController

class ProjectController (DialogController, HasObjectTreeview, DialogMixin):

    file_filters = SpecimenController.file_filters

    def register_view(self, view):
        print "ProjectController.register_view()"
        # connects the buffer and the text view
        if view is not None and self.model is not None:
            view["project_data_description"].set_buffer(self.model.description)
            if self.parent is not None:
                tv = self.parent.view["specimens_treeview"]
                tv.set_model(self.model.specimens)
        return

    def register_adapters(self):
        print "ProjectController.register_adapters()"
        if self.model is not None and self.parent is not None:
            for name in self.model.get_properties():
                if name == "name":
                    self.adapt(name, "project_%s" % name)
                elif name == "description":
                    pass
                elif name in ("display_calc_color", "display_exp_color"):
                    ad = Adapter(self.model, name)
                    ad.connect_widget(self.view["project_%s" % name], getter=get_color_val)
                    self.adapt(ad)
                elif name in ("display_marker_angle", "display_plot_offset", "project_axes_xmin", "project_axes_xmax", "display_label_pos"):
                    FloatEntryValidator(self.view["project_%s" % name])
                    self.adapt(name)
                elif name in ("axes_xscale", "axes_yscale"):
                    ctrl_setup_combo_with_list(self, self.view["cmb_%s" % name], name, "_%ss"%name)
                elif name == "specimens":
                    # connects the treeview to the liststore
                    tv = self.parent.view['specimens_treeview']
                    
                    sel = tv.get_selection()
                    sel.set_mode(gtk.SELECTION_MULTIPLE)
                    tv.connect('button-press-event', self.specimen_tv_button_press)
                    sel.connect('changed', self.specimen_tv_selection_changed)
                    
                    #reset:
                    for col in tv.get_columns():
                        tv.remove_column(col)

                    # (re)create the columns of the treeview
                    rend = gtk.CellRendererText()
                    rend.set_property('ellipsize', pango.ELLIPSIZE_END)
                    col = gtk.TreeViewColumn('Specimen name', rend, text=self.model.specimens.c_data_name)
                    col.set_resizable(True)
                    col.set_expand(True)

                    tv.append_column(col)

                    def toggle_renderer(column, cell, model, itr, data=None):
                        cell.set_property('active', getattr(model.get_user_data(itr), data))
                        return
                    def setup_check_column(name, attr_name, colnr):
                        rend = gtk.CellRendererToggle()
                        rend.connect('toggled', self.specimen_tv_toggled, self.model.specimens, attr_name)
                        col = gtk.TreeViewColumn(name, rend)
                        col.add_attribute(rend, 'active', colnr)
                        col.set_cell_data_func(rend, toggle_renderer, attr_name)
                        col.activatable = True
                        col.set_resizable(False)
                        col.set_expand(False)
                        tv.append_column(col)
                    
                    def setup_image_button(col, callback, image):
                        col = gtk.TreeViewColumn(col)
                        col.set_widget(gtk.Label())
                        col.set_resizable(False)
                        col.set_expand(False)
                        rend = gtk.CellRendererPixbuf()
                        rend.set_property("stock-id", image)
                        col.pack_end(rend)
                        tv.append_column(col)
                        
                    setup_check_column('Exp', "display_experimental", self.model.specimens.c_display_experimental)
                    if not settings.VIEW_MODE:
                        setup_check_column('Cal', "display_calculated", self.model.specimens.c_display_calculated)
                        setup_check_column('Sep', "display_phases", self.model.specimens.c_display_phases)

                    setup_image_button("UP", None, gtk.STOCK_GO_UP)
                    setup_image_button("DOWN", None, gtk.STOCK_GO_DOWN)

                elif not name in self.model.__have_no_widget__:
                    self.adapt(name)
            return

    @BaseController.status_message("Importing multiple specimens...", "add_specimen")
    def import_multiple_specimen(self):
        def on_accept(dialog):
            filenames = dialog.get_filenames()
            last_iter = None
            for filename in filenames:
                specimen = None
                if filename[-3:].lower() == "dat":
                    print "Opening file %s for import using ASCII DAT format" % filename
                    specimen = Specimen.from_experimental_data(parent=self.model, filename=filename, format="DAT")
                if filename[-2:].lower() == "rd":
                    print "Opening file %s for import using BINARY RD format" % filename
                    specimen = Specimen.from_experimental_data(parent=self.model, filename=filename, format="BIN")
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
    def specimen_tv_toggled(self, cell, path, model=None, attr_name=""):
        if model is not None:
            specimen = model.get_user_data_from_path((int(path),))
            setattr(specimen, attr_name, not getattr(specimen, attr_name)) #cell.get_active()
            return True
        return False

    def specimen_tv_button_press(self, tv, event):
        specimen = None
        ret = tv.get_path_at_pos(int(event.x), int(event.y))
        if ret is not None:
            path, col, x, y = ret
            model = tv.get_model()
            specimen = model.get_user_data_from_path(path)
        if event.button == 3:
            if specimen is not None:
                tv.set_cursor(path)
            self.parent.update_sensitivities()
            self.parent.view["popup_menu_item_del_specimen"].set_sensitive(self.model is not None and specimen is not None)
            self.parent.view["specimen_popup"].popup(None, None, None, event.button, event.time)
            return True
        elif event.type == gtk.gdk._2BUTTON_PRESS and specimen is not None and col.get_title() == "Specimen name":
            self.parent.edit_specimen(specimen)
            return True
        elif (event.button == 1 or event.type == gtk.gdk._2BUTTON_PRESS) and specimen is not None:
            title = col.get_title()
            if title in ("Exp", "Cal", "Sep"):
                if title=="Exp":
                    specimen.display_experimental = not specimen.display_experimental
                elif title=="Cal":
                    specimen.display_calculated = not specimen.display_calculated
                elif title=="Sep":
                    specimen.display_phases = not specimen.display_phases
                model.on_item_changed(specimen)
                return True
            elif title == "UP":
                model.move_item_up(specimen)
                self.parent.model.current_specimens = self.get_selected_objects()
                return True
            elif title == "DOWN":
                model.move_item_down(specimen)
                self.parent.model.current_specimens = self.get_selected_objects()
                return True


    def specimen_tv_selection_changed(self, selection):
        self.parent.model.current_specimens = self.get_selected_objects()
        return True
        
    def get_selected_object(self):
        return HasObjectTreeview.get_selected_object(self, self.parent.view['specimens_treeview'])
        
    def get_selected_objects(self):
        return HasObjectTreeview.get_selected_objects(self, self.parent.view['specimens_treeview'])
        
    def get_all_objects(self):
        return HasObjectTreeview.get_all_objects(self, self.parent.view['specimens_treeview'])

    def on_btn_ok_clicked(self, event):
        self.parent.pop_status_msg('edit_project')
        return DialogController.on_btn_ok_clicked(self, event)

    pass # end of class
