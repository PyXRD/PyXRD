# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import locale

import gtk

from gtkmvc import Controller
from gtkmvc.adapters import Adapter

from generic.io.file_parsers import parsers
from generic.controllers import BaseController, DialogController, DialogMixin, ObjectTreeviewMixin
from generic.controllers.handlers import get_color_val
from generic.views.validators import FloatEntryValidator
from generic.views.treeview_tools import setup_treeview, new_text_column
from generic.controllers.utils import get_case_insensitive_glob, ctrl_setup_combo_with_list

from .background_controller import BackgroundController
from .smooth_data_controller import SmoothDataController
from .shift_data_controller import ShiftDataController
from .strip_peak_controller import StripPeakController

from specimen.views import (
    BackgroundView,
    SmoothDataView,
    ShiftDataView,
    StripPeakView
)

print [parser.file_filter for parser in parsers]

class SpecimenController(DialogController, DialogMixin, ObjectTreeviewMixin):

    file_filters = [parser.file_filter for parser in parsers]
                    
    excl_filters = [("Exclusion range file", get_case_insensitive_glob("*.EXC")),
                    ("All Files", "*.*")]
    
    def update_calc_treeview(self):
        tv = self.view['calculated_data_tv']
        model = self.model.calculated_pattern.xy_store
        
        for column in tv.get_columns():
            tv.remove_column(column)
        
        def get_num(column, cell, model, itr, *data):
            cell.set_property('text', '%.3f' % model.get_value(itr, column.get_col_attr('text')))
        
        tv.append_column(new_text_column(u'2θ', text_col=model.c_x, data_func=get_num))
        tv.append_column(new_text_column(u'Cal', text_col=model.c_x, data_func=get_num))        
        for i in range(model.get_n_columns()-3):
            tv.append_column(new_text_column(
                model.get_y_name(i), text_col=i+2, data_func=get_num))
    
    def register_adapters(self):
        if self.model is not None:
            for name in self.model.get_properties():
                if name == "name":
                    ad = Adapter(self.model, "name")
                    ad.connect_widget(self.view["specimen_name"])
                    self.adapt(ad)
                elif name == "experimental_pattern":
                    #Setup treeview:
                    tv = self.view['experimental_data_tv']
                    model = self.model.experimental_pattern.xy_store
                    setup_treeview(tv, model,
                        on_cursor_changed=self.on_exp_data_tv_cursor_changed,
                        sel_mode=gtk.SELECTION_MULTIPLE)
                    #X Column:
                    tv.append_column(new_text_column(
                        u'°2θ', text_col=model.c_x, editable=True,
                        edited_callback=(self.on_xy_data_cell_edited, (model, model.c_x))))
                    #Y Column:
                    tv.append_column(new_text_column(
                        u'Intensity', text_col=model.c_y, editable=True,
                        edited_callback=(self.on_xy_data_cell_edited, (model, model.c_y))))
                elif name == "calculated_pattern":
                    tv = self.view['calculated_data_tv']
                    model = self.model.calculated_pattern.xy_store
                    setup_treeview(tv, model,
                        on_cursor_changed=self.on_exp_data_tv_cursor_changed,
                        on_columns_changed=self.on_calc_treestore_changed,
                        sel_mode=gtk.SELECTION_NONE)
                    self.update_calc_treeview()
                elif name == "exclusion_ranges":
                    tv = self.view['exclusion_ranges_tv']
                    model = self.model.exclusion_ranges
                    setup_treeview(tv, model,
                        on_cursor_changed=self.on_exclusion_ranges_tv_cursor_changed,
                        sel_mode=gtk.SELECTION_MULTIPLE)
                    tv.append_column(new_text_column(
                        u'From [°2θ]', text_col=model.c_x, editable=True,
                        edited_callback=(self.on_xy_data_cell_edited, (model, model.c_x)), 
                        resizable=True, expand=True))
                    tv.append_column(new_text_column(
                        u'To [°2θ]', text_col=model.c_y, editable=True,
                        edited_callback=(self.on_xy_data_cell_edited, (model, model.c_y)),
                        resizable=True, expand=True))
                elif name in ["calc_color", "exp_color"]:
                    ad = Adapter(self.model, name)
                    ad.connect_widget(self.view["specimen_%s" % name], getter=get_color_val)
                    self.adapt(ad)
                elif name in ["calc_lw", "exp_lw", "exp_cap_value"]:
                    self.adapt(name, "specimen_%s" % name)
                elif name in ("sample_length", "abs_scale", "bg_shift"):
                    FloatEntryValidator(self.view["specimen_%s" % name])
                    self.adapt(name)
                elif not name in self.model.__have_no_widget__:
                    self.adapt(name)
            self.update_sensitivities()
            return

    def set_exp_data_sensitivites(self, val):
        self.view["btn_del_experimental_data"].set_sensitive(val)
        
    def set_exclusion_ranges_sensitivites(self, val):
        self.view["btn_del_exclusion_ranges"].set_sensitive(val)

    def update_sensitivities(self):
        self.view["specimen_exp_color"].set_sensitive(not self.model.inherit_exp_color)
        if not self.model.inherit_exp_color:
            self.view["specimen_exp_color"].set_color(gtk.gdk.color_parse(self.model.exp_color))
        self.view["specimen_calc_color"].set_sensitive(not self.model.inherit_calc_color)
        if not self.model.inherit_calc_color:
            self.view["specimen_calc_color"].set_color(gtk.gdk.color_parse(self.model.calc_color))

        self.view["spb_calc_lw"].set_sensitive(not self.model.inherit_calc_lw)           
        self.view["spb_exp_lw"].set_sensitive(not self.model.inherit_exp_lw)

    def remove_background(self):
        bg_view = BackgroundView(parent=self.view)
        bg_ctrl = BackgroundController(self.model.experimental_pattern, bg_view, parent=self)
        bg_view.present()

    def smooth_data(self):
        sd_view = SmoothDataView(parent=self.view)
        sd_ctrl = SmoothDataController(self.model.experimental_pattern, sd_view, parent=self)
        sd_view.present()
        
    def shift_data(self):
        sh_view = ShiftDataView(parent=self.view)
        sh_ctrl = ShiftDataController(self.model.experimental_pattern, sh_view, parent=self)
        sh_view.present()
        
    def strip_peak(self):
        st_view = StripPeakView(parent=self.view)
        st_ctrl = StripPeakController(self.model.experimental_pattern, st_view, parent=self)
        st_view.present()
        
    # ------------------------------------------------------------
    #      Notifications of observable properties
    # ------------------------------------------------------------
    @Controller.observe("inherit_exp_color", assign=True)
    @Controller.observe("inherit_calc_color", assign=True)
    @Controller.observe("inherit_exp_lw", assign=True)
    @Controller.observe("inherit_calc_lw", assign=True)
    def notif_color_toggled(self, model, prop_name, info):
        self.update_sensitivities()

    # ------------------------------------------------------------
    #      GTK Signal handlers
    # ------------------------------------------------------------
    def on_calc_treestore_changed(self, *args, **kwargs):
        self.update_calc_treeview()    
    
    def on_btn_ok_clicked(self, event):
        self.parent.pop_status_msg('edit_specimen')
        return DialogController.on_btn_ok_clicked(self, event)

    def on_exclusion_ranges_tv_cursor_changed(self, tv):
        path, col = tv.get_cursor()
        self.set_exclusion_ranges_sensitivites(path != None)
        return True

    def on_exp_data_tv_cursor_changed(self, tv):
        path, col = tv.get_cursor()
        self.set_exp_data_sensitivites(path != None)
        return True

    def on_add_experimental_data_clicked(self, widget):
        model = self.model.experimental_pattern.xy_store
        path = model.append(0,0)
        self.set_selected_paths(self.view["experimental_data_tv"], (path,))
        return True
        
    def on_add_exclusion_range_clicked(self, widget):
        model = self.model.exclusion_ranges
        path = model.append(0,0)
        self.set_selected_paths(self.view["exclusion_ranges_tv"], (path,))
        return True        

    def on_del_experimental_data_clicked(self, widget):
        paths = self.get_selected_paths(self.view["experimental_data_tv"])
        if paths != None:
            model = self.model.experimental_pattern.xy_store
            model.remove_from_index(*paths)
        return True
        
    def on_del_exclusion_ranges_clicked(self, widget):
        paths = self.get_selected_paths(self.view["exclusion_ranges_tv"])
        if paths != None:
            model = self.model.exclusion_ranges
            model.remove_from_index(*paths)
        return True        

    def on_xy_data_cell_edited(self, cell, path, new_text, model, col):
        #model, col = user_data
        itr = model.get_iter(path)
        model.set_value(itr, col, model.convert(col, locale.atof(new_text)))
        return True

    def on_import_exclusion_ranges_clicked(self, widget, data=None):
        def on_confirm(dialog):
            def on_accept(dialog):
                filename = dialog.get_filename()
                if filename[-3:].lower() == "exc":
                    self.model.exclusion_ranges.load_data(filename, format="DAT")
            self.run_load_dialog(title="Import exclusion ranges",
                                 on_accept_callback=on_accept, 
                                 parent=self.view.get_top_widget(),
                                 filters=self.excl_filters)
        self.run_confirmation_dialog("Importing exclusion ranges will erase all current data.\nAre you sure you want to continue?",
                                     on_confirm, parent=self.view.get_top_widget())
        
    def on_export_exclusion_ranges_clicked(self, widget, data=None):
        def on_accept(dialog):
            filename = self.extract_filename(dialog, filters=self.excl_filters)
            if filename[-3:].lower() == "exc":
                self.model.exclusion_ranges.save_data("%s %s" % (self.model.name, self.model.sample_name), filename)
        self.run_save_dialog(title="Select file for exclusion ranges export",
                             on_accept_callback=on_accept, 
                             parent=self.view.get_top_widget(),
                             filters=self.excl_filters)

    def on_replace_experimental_data(self, *args, **kwargs):
        def on_accept(dialog):
            filename = dialog.get_filename()
            ffilter = dialog.get_filter()
            parser = ffilter.get_data("parser")
            self.model.experimental_pattern.load_data(parser, filename, clear=True)

        self.run_load_dialog(title="Open XRD file for import",
                            on_accept_callback=on_accept, 
                             parent=self.view.get_top_widget())
        return True

    def on_btn_import_experimental_data_clicked(self, widget, data=None):
        def on_confirm(dialog):
            self.on_replace_experimental_data()
        self.run_confirmation_dialog("Importing a new experimental file will erase all current data.\nAre you sure you want to continue?",
                                     on_confirm, parent=self.view.get_top_widget())
        return True
        
    def on_export_experimental_data(self, *args, **kwargs):
        def on_accept(dialog):
            filename = self.extract_filename(dialog)
            if filename[-3:].lower() == "dat":
                self.model.experimental_pattern.save_data(filename)
            if filename[-2:].lower() == "rd":
                self.run_information_dialog("RD file format not supported (yet)!", parent=self.view.get_top_widget())
        self.run_save_dialog(title="Select file for export",
                             on_accept_callback=on_accept, 
                             parent=self.view.get_top_widget())
        return True
        
    def on_btn_export_experimental_data_clicked(self, widget, data=None):
        return self.on_export_experimental_data()
        
    def on_btn_export_calculated_data_clicked(self, widget, data=None):
        def on_accept(dialog):
            filename = self.extract_filename(dialog)
            if filename[-3:].lower() == "dat":
                self.model.calculated_pattern.save_data(filename)
            if filename[-2:].lower() == "rd":
                self.run_information_dialog("RD file format not supported (yet)!", parent=self.view.get_top_widget())
        self.run_save_dialog(title="Select file for export",
                             on_accept_callback=on_accept, 
                             parent=self.view.get_top_widget())
        return True        

    pass #end of class
    
class StatisticsController(BaseController):

    def register_adapters(self):
        if self.model is not None:
            for name in self.model.get_properties():
                if name in self.model.__have_no_widget__:
                    pass
                else:
                    self.adapt(name)
            return
        
    pass #end of class
