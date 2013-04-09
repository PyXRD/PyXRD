# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Author: Mathijs Dumon
# This work is licensed under the Creative Commons Attribution-ShareAlike 3.0 Unported License. 
# To view a copy of this license, visit http://creativecommons.org/licenses/by-sa/3.0/ or send
# a letter to Creative Commons, 444 Castro Street, Suite 900, Mountain View, California, 94041, USA.

import locale

import gtk
import numpy as np

from gtkmvc import Controller, Observer
from gtkmvc.adapters import Adapter


from generic.plot.controllers import DraggableVLine, EyedropperCursorPlot
from generic.models.treemodels import XYListStore
from generic.controllers import DialogController, DialogMixin, BaseController, ObjectListStoreController, ObjectTreeviewMixin, ctrl_setup_combo_with_list
from generic.controllers.handlers import get_color_val
from generic.views.validators import FloatEntryValidator
from generic.views.treeview_tools import setup_treeview, new_text_column, new_toggle_column
from generic.utils import get_case_insensitive_glob

from specimen.models import Specimen, Marker, ThresholdSelector, MineralScorer
from specimen.views import (
    EditMarkerView, 
    DetectPeaksView,
    MatchMineralsView,
    BackgroundView, 
    SmoothDataView, 
    ShiftDataView
)

class SpecimenController(DialogController, DialogMixin, ObjectTreeviewMixin):

    file_filters = [("Data Files", get_case_insensitive_glob("*.DAT", "*.RD")),    
                    ("ASCII Data", get_case_insensitive_glob("*.DAT")),
                    ("Phillips Binary Data", get_case_insensitive_glob("*.RD")),
                    ("All Files", "*.*")]
                    
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
            if filename[-3:].lower() == "dat":
                self.model.experimental_pattern.load_data(filename, format="DAT", clear=True)
            if filename[-2:].lower() == "rd":
                self.model.experimental_pattern.load_data(filename, format="BIN", clear=True)
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

class BackgroundController(DialogController):


    def register_adapters(self):
        if self.model is not None:
            for name in self.model.get_properties():
                if name == "bg_type":
                    ctrl_setup_combo_with_list(self, 
                        self.view["cmb_bg_type"],
                        "bg_type", "_bg_types")
                elif name == "bg_position":
                    FloatEntryValidator(self.view["bg_offset"])
                    FloatEntryValidator(self.view["bg_position"])
                    self.adapt(name, "bg_offset")
                    self.adapt(name, "bg_position")
                elif name == "bg_scale":
                    FloatEntryValidator(self.view["bg_scale"])
                    self.adapt(name)
            return
            
    # ------------------------------------------------------------
    #      Notifications of observable properties
    # ------------------------------------------------------------
    @Controller.observe("bg_type", assign=True)
    def notif_bg_type_changed(self, model, prop_name, info):
        self.view.select_bg_view(self.model.get_bg_type_lbl().lower())
        return
            
    # ------------------------------------------------------------
    #      GTK Signal handlers
    # ------------------------------------------------------------
    def on_pattern_file_set(self, dialog):
        filename = dialog.get_filename()
        
        generator = None
        if filename[-3:].lower() == "dat":
             generator = XYListStore.parse_data(filename, format="DAT")
        if filename[-2:].lower() == "rd":
             generator = XYListStore.parse_data(filename, format="BIN")
             
        pattern = np.array([(x, y) for x, y in generator])
        bg_pattern_x = pattern[:,0].copy()
        bg_pattern_y = pattern[:,1].copy()
        del pattern
        
        if bg_pattern_x.shape != self.model.xy_store._model_data_x.shape:
            raise ValueError, "Shape mismatch: background pattern (shape = %s) and experimental data (shape = %s) need to have the same length!" % (bg_pattern_x.shape, self.model.xy_store._model_data_x.shape)
            dialog.unselect_filename(filename)
        else:
            self.model.bg_pattern = bg_pattern_y

    def on_btn_ok_clicked(self, event):
        self.model.remove_background()
        self.view.hide()
        return True
            
    def on_cancel(self):
        self.model.clear_bg_variables()
        DialogController.on_cancel(self)
            
    pass #end of class
   
class SmoothDataController(DialogController):

    def register_adapters(self):
        if self.model is not None:
            self.model.sd_degree = 5
            for name in self.model.get_properties():
                if name == "smooth_type":
                    ctrl_setup_combo_with_list(self, 
                        self.view["cmb_smooth_type"],
                        "smooth_type", "_smooth_types")
                elif name == "smooth_degree":
                    #FloatEntryValidator(self.view["smooth_degree"])
                    self.adapt(name)
            return
            
    # ------------------------------------------------------------
    #      GTK Signal handlers
    # ------------------------------------------------------------
    def on_btn_ok_clicked(self, event):
        self.model.smooth_data()
        self.view.hide()
        return True
            
    def on_cancel(self):
        self.model.sd_degree = 0
        DialogController.on_cancel(self)
            
    pass #end of class
   
class ShiftDataController(DialogController):

    def register_adapters(self):
        if self.model is not None:
            self.model.find_shift_value()
            for name in self.model.get_properties():
                if name == "shift_position":
                    ctrl_setup_combo_with_list(self, 
                        self.view["cmb_shift_position"],
                        "shift_position", "_shift_positions")
                elif name == "shift_value":
                    FloatEntryValidator(self.view["shift_value"])
                    self.adapt(name)
            return
            
    # ------------------------------------------------------------
    #      GTK Signal handlers
    # ------------------------------------------------------------
    def on_btn_ok_clicked(self, event):
        self.model.shift_data()
        self.view.hide()
        return True
            
    def on_cancel(self):
        self.model.shift_value = 0
        DialogController.on_cancel(self)
            
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
            
class EditMarkerController(BaseController):

    def register_view(self, view):
        self.update_sensitivities()

    def register_adapters(self):
        if self.model is not None:
            for name in self.model.get_properties():
                if name == "color":
                    ad = Adapter(self.model, "color")
                    ad.connect_widget(self.view["marker_color"], getter=get_color_val)
                    self.adapt(ad)
                elif name == "style":
                    ctrl_setup_combo_with_list(self, 
                        self.view["marker_style"],
                        "style", "_styles")
                elif name == "align":
                    ctrl_setup_combo_with_list(self, 
                        self.view["marker_align"],
                        "align", "_aligns")
                elif name == "base":
                    ctrl_setup_combo_with_list(self,
                        self.view["marker_base"],
                        "base", "_bases")
                elif name in ("position", "angle", "x_offset", "y_offset"):
                    FloatEntryValidator(self.view["marker_%s" % name])
                    self.adapt(name, "marker_%s" % name)
                elif not name in self.model.__have_no_widget__:
                    self.adapt(name)
                self.view["entry_nanometer"].set_text("%f" % self.model.get_nm_position())
                FloatEntryValidator(self.view["entry_nanometer"])
            return
            
    def update_sensitivities(self):
        self.view["marker_angle"].set_sensitive(not self.model.inherit_angle)
    
    # ------------------------------------------------------------
    #      Notifications of observable properties
    # ------------------------------------------------------------   
    @Controller.observe("position", assign=True, after=True)
    def notif_parameter_changed(self, model, prop_name, info):
        if prop_name=="position":
            self.view["entry_nanometer"].set_text("%f" % self.model.get_nm_position())

    @Controller.observe("inherit_angle", assign=True)
    def notif_angle_toggled(self, model, prop_name, info):
        self.update_sensitivities()

    # ------------------------------------------------------------
    #      GTK Signal handlers
    # ------------------------------------------------------------
    def on_style_changed(self, combo, user_data=None):
        pass
        itr = combo.get_active_iter()
        if itr != None:
            val = combo.get_model().get_value(itr, 0)
            self.model.style = val
            
    def on_nanometer_changed(self, widget):
        try:
            position = float(widget.get_text())
            self.model.set_nm_position(position)
        except:
            pass
        
    def on_sample_clicked(self, widget):
        self.cid = -1
        self.fig = self.parent.plot_controller.figure
        self.ret = self.view.get_toplevel()
        
        self.edc = EyedropperCursorPlot(self.parent.plot_controller.canvas, self.parent.plot_controller.canvas.get_window(), True, True)
        
        def onclick(event):
            x_pos = -1
            if event.inaxes:
                x_pos = event.xdata
            if self.cid != -1:
                self.fig.canvas.mpl_disconnect(self.cid)
            if self.edc != None:
                self.edc.enabled = False
                self.edc.disconnect()
            self.ret.present()
            if x_pos != -1:
                self.model.position = x_pos
                
        self.cid = self.fig.canvas.mpl_connect('button_press_event', onclick)
        self.view.get_toplevel().hide()
        self.parent.view.get_toplevel().present()

class MarkersController(ObjectListStoreController):

    file_filters = ("Marker file", get_case_insensitive_glob("*.MRK")),
    model_property_name = "markers"
    columns = [ ("Marker label", "c_label") ]
    delete_msg = "Deleting a marker is irreverisble!\nAre You sure you want to continue?"
    title="Edit Markers"

    def get_new_edit_view(self, obj):
        if isinstance(obj, Marker):
            return EditMarkerView(parent=self.view)
        else:
            return ObjectListStoreController.get_new_edit_view(self, obj)
        
    def get_new_edit_controller(self, obj, view, parent=None):
        if isinstance(obj, Marker):
            return EditMarkerController(obj, view, parent=parent)
        else:
            return ObjectListStoreController.get_new_edit_controller(self, obj, view, parent=parent)
    
    def set_object_sensitivities(self, value):
        self.view["cmd_match_minerals"].set_sensitive(value)
        super(MarkersController, self).set_object_sensitivities(value)
    
    # ------------------------------------------------------------
    #      GTK Signal handlers
    # ------------------------------------------------------------        
    def on_load_object_clicked(self, event):
        def on_accept(dialog):
            print "Importing markers..."
            Marker.get_from_csv(dialog.get_filename(), self.model.markers.append)
        self.run_load_dialog("Import markers", on_accept, parent=self.view.get_top_widget())


    def on_save_object_clicked(self, event):
        def on_accept(dialog):
            print "Exporting markers..."
            filename = self.extract_filename(dialog)
            Marker.save_as_csv(filename, self.get_selected_objects())
        self.run_save_dialog("Export markers", on_accept, parent=self.view.get_top_widget())
        
    def create_new_object_proxy(self):
        return Marker("New Marker", parent=self.model)
            
    def on_find_peaks_clicked(self, widget):        
        def after_cb(threshold):
            if len(self.model.markers._model_data) > 0:            
                def on_accept(dialog):
                    self.model.markers.clear()
                self.run_confirmation_dialog("Do you want to clear the current markers for this pattern?",
                                             on_accept, parent=self.view.get_top_widget())
            self.model.auto_add_peaks(threshold)
            self.parent.redraw_plot() #FIXME emit signal instead -> forwarded to containing specimen (emits a signal) -> forwarded to Application Controller -> issues a redraw

        sel_model = ThresholdSelector(parent=self.model)
        sel_view = DetectPeaksView(parent=self.view)
        sel_ctrl = ThresholdController(sel_model, sel_view, parent=self, callback = after_cb)
        
        sel_view.present()
        
    def on_match_minerals_clicked(self, widget):
        def apply_cb(matches):
            for name, abbreviation, peaks, matches, score in matches:
                for marker in self.get_selected_objects():
                    for mpos, epos in matches:
                        if marker.get_nm_position()*10. == epos:
                            marker.label += ", %s" % abbreviation
    
        def close_cb():
            self.model.mineral_preview = None
            self.model.needs_update.emit()
            self.view.show()
        
        marker_peaks = [] #position, intensity
        
        for marker in self.get_selected_objects():
            intensity = self.model.experimental_pattern.xy_store.get_y_at_x(
                marker.position)
            marker_peaks.append((marker.get_nm_position()*10., intensity))
    
        scorer_model = MineralScorer(marker_peaks=marker_peaks, parent=self.model)
        scorer_view = MatchMineralsView(parent=self.view)
        scorer_ctrl = MatchMineralController(model=scorer_model, view=scorer_view, parent=self, apply_callback = apply_cb, close_callback = close_cb)
        
        self.view.hide()
        scorer_view.present()
        
    pass #end of class
        
class MatchMineralController(DialogController):
    
    apply_callback = None
    close_callback = None
    
    # ------------------------------------------------------------
    #      Initialisation and other internals
    # ------------------------------------------------------------
    def __init__(self, model, view, spurious=False, auto_adapt=False, parent=None, apply_callback=None, close_callback=None):
        DialogController.__init__(self, model, view, spurious=spurious, auto_adapt=auto_adapt, parent=parent)
        self.apply_callback = apply_callback
        self.close_callback = close_callback
        
    def register_adapters(self):
        if self.model is not None:
            self.reload_minerals()
            self.reload_matches()

    def register_view(self, view):
        if view is not None:
            top = view.get_toplevel()
            top.set_transient_for(self.parent.view.get_toplevel())
            top.set_modal(True)
            #FIXME DO WE STILL NEED THIS?
            
            # MATCHES Treeview:
            tv = self.view['tv_matches']
            
            setup_treeview(tv, None, 
                reset=True,
                on_selection_changed=self.selection_changed,
            )

            tv.append_column(new_text_column(
                "Name", markup_col=0,
                xalign=0,
            ))

            tv.append_column(new_text_column(
                "Abbr.", markup_col=1,
                expand=False,
            ))

            def get_value(column, cell, model, itr, *args):
                value = model.get_value(itr, column.get_col_attr('markup'))
                try: value = "%.5f" % value
                except TypeError: value = ""
                cell.set_property("markup",  value)                    
                return    
            tv.append_column(new_text_column(
                "Score",
                markup_col=4,
                expand=False,
                data_func=get_value
            ))

            # ALL MINERALS Treeview:
            tv = self.view['tv_minerals']
            setup_treeview(tv, None, 
                reset=True,
                on_selection_changed=self.selection_changed,
            )

            tv.append_column(new_text_column(
                "Name", markup_col=0,
                xalign=0,
            ))
        
            tv.append_column(new_text_column(
                "Abbr.", markup_col=1,
                expand=False,
            ))
        
    # ------------------------------------------------------------
    #      Notifications of observable properties
    # ------------------------------------------------------------
    @Controller.observe("matches_changed", signal=True)
    def notif_parameter_changed(self, model, prop_name, info):
        self.reload_matches()
        
    # ------------------------------------------------------------
    #      GTK Signal handlers
    # ------------------------------------------------------------
    def selection_changed(self, selection, *args):
        if selection.count_selected_rows() >= 1:
            model, paths = selection.get_selected_rows()
            itr = model.get_iter(paths[0])
            name, abbreviation, peaks = model.get(itr, 0, 1, 2)
            self.model.specimen.mineral_preview = (name, peaks)
            self.model.specimen.needs_update.emit()
    
    def on_auto_match_clicked(self, event):
        self.model.auto_match()
        
    def on_add_match_clicked(self, event):
        selection = self.view.tv_minerals.get_selection()
        if selection.count_selected_rows() >= 1:
            model, paths = selection.get_selected_rows()
            itr = model.get_iter(paths[0])
            name, abbreviation, peaks = model.get(itr, 0, 1)
            self.model.add_match(name, abbreviation, peaks)
    
    def on_del_match_clicked(self, event):
        selection = self.view.tv_matches.get_selection()
        if selection.count_selected_rows() >= 1:
            model, paths = selection.get_selected_rows()
            self.model.del_match(*paths[0])
    
    def on_apply_clicked(self, event):
        if self.apply_callback != None and callable(self.apply_callback):
            self.apply_callback(self.model.matches)
        self.view.hide()
    
    def on_cancel(self):
        if self.close_callback != None and callable(self.close_callback):
            self.close_callback()        
        self.view.hide()
    
    # ------------------------------------------------------------
    #      Methods & Functions
    # ------------------------------------------------------------
    def reload_matches(self):
        if not hasattr(self, 'tv_matches_model'):
            self.tv_matches_model = gtk.ListStore(str, str, object, object, float)
        else:
            self.tv_matches_model.clear()
        for name, abbreviation, peaks, matches, score in self.model.matches:
            self.tv_matches_model.append([name, abbreviation, peaks, matches, score])
        
        tv = self.view.tv_matches
        tv.set_model(self.tv_matches_model)
    
    def reload_minerals(self):
        if not hasattr(self, 'tv_matches_model'):
            self.tv_minerals_model = gtk.ListStore(str, str, object)
        else:
            self.tv_minerals_model.clear()
        for name, abbreviation, peaks in self.model.minerals:
            self.tv_minerals_model.append([name, abbreviation, peaks])
        
        tv = self.view.tv_minerals
        tv.set_model(self.tv_minerals_model)
        
    pass #end of class
        
        
class ThresholdController(DialogController):
    
    callback = None
    dline = None
    
    def __init__(self, model, view, spurious=False, auto_adapt=False, parent=None, callback=None):
        DialogController.__init__(self, model, view, spurious=spurious, auto_adapt=auto_adapt, parent=parent)
        
        self.callback = callback
        self.dline = None
    
    def update_plot(self):
        self.view.plot.cla()
        if self.dline != None:
            self.dline.disconnect()
            self.dline=None
        
        def dline_cb(x):
            self.model.sel_threshold = x
            
        if self.model is not None and self.model.threshold_plot_data is not None:
            x, y = self.model.threshold_plot_data
            self.view.plot.plot(x, y, 'k-')
            self.line = self.view.plot.axvline(x=self.model.sel_threshold, color="#0000FF", linestyle="-")
            self.dline = DraggableVLine(self.line, connect=True, callback=dline_cb, window=self.view.matlib_canvas.get_window())
        self.view.plot.set_ylabel('# of peaks', labelpad=1)
        self.view.plot.set_xlabel('Threshold', labelpad=1)
        self.view.figure.subplots_adjust(left=0.15, right=0.875, top=0.875, bottom=0.15)
        self.view.plot.autoscale_view()
        self.view.matlib_canvas.draw()
    
    def register_view(self, view):
        if view is not None:
            top = view.get_toplevel()
            top.set_transient_for(self.parent.view.get_toplevel())
            top.set_modal(True)
            self.update_plot()
    
    def register_adapters(self):
        if self.model is not None:
            for name in self.model.get_properties():
                if name == "pattern":
                    ctrl_setup_combo_with_list(self, self.view["pattern"], "pattern", "_patterns")
                elif name in ("sel_threshold", "max_threshold"):
                    FloatEntryValidator(self.view[name])
                    self.adapt(name)
                elif not name in self.model.__have_no_widget__:
                    self.adapt(name)
            return
        
    # ------------------------------------------------------------
    #      Notifications of observable properties
    # ------------------------------------------------------------
    @Controller.observe("sel_threshold", assign=True)
    @Controller.observe("threshold_plot_data", assign=True)
    def notif_parameter_changed(self, model, prop_name, info):
        self.update_plot()
    
    # ------------------------------------------------------------
    #      GTK Signal handlers
    # ------------------------------------------------------------
    def on_btn_ok_clicked(self, event):
        if self.callback != None and callable(self.callback):
            self.callback(self.model)
        return DialogController.on_btn_ok_clicked(self, event)
        
    pass #end of class
