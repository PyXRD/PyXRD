# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Author: Mathijs Dumon
# This work is licensed under the Creative Commons Attribution-ShareAlike 3.0 Unported License. 
# To view a copy of this license, visit http://creativecommons.org/licenses/by-sa/3.0/ or send
# a letter to Creative Commons, 444 Castro Street, Suite 900, Mountain View, California, 94041, USA.

import locale

import gtk

from gtkmvc import Controller, Observer
from gtkmvc.adapters import Adapter

from generic.plot_controllers import DraggableVLine, EyedropperCursorPlot
from generic.controllers import DialogController, DialogMixin, ChildController, ObjectListStoreController, HasObjectTreeview, get_color_val, delayed, ctrl_setup_combo_with_list
from generic.validators import FloatEntryValidator
from generic.utils import get_case_insensitive_glob

from specimen.models import Specimen, Marker, ThresholdSelector
from specimen.views import EditMarkerView, DetectPeaksView

class SpecimenController(DialogController, DialogMixin, HasObjectTreeview):

    file_filters = [("Data Files", get_case_insensitive_glob("*.DAT", "*.RD")),    
                    ("ASCII Data", get_case_insensitive_glob("*.DAT")),
                    ("Phillips Binary Data", get_case_insensitive_glob("*.RD")),
                    ("All Files", "*.*")]

    xydataobserver = None
    class XYDataObserver (Observer):
        @Observer.observe('plot_update', signal=True)
        def notifications(self, model, prop_name, info):
            print "UPDATING PLOT BECAUSE OF SIGNAL IN XYDATA"
            self.callback()
            
        def __init__(self, callback, *args, **kwargs):
            Observer.__init__(self, *args, **kwargs)
            self.callback = callback

    def unregister_data_treeview(self):
        if self.view is not None and self.model is not None:
            tv = self.view['experimental_data_tv']
            tv.set_model(None)
    def register_data_treeview(self):
        if self.view is not None and self.model is not None:
            tv = self.view['experimental_data_tv']
            tv.set_model(self.model.data_experimental_pattern.xy_data)

    def register_view(self, view):
        self.register_data_treeview()
        if self.view is not None and self.model is not None:
            tv = self.view['display_phases_treeview']
            tv.set_model(self.model.parent.data_phases) #self.parent.project.model.data_phases

    def register_adapters(self):
        self.xydataobserver = self.XYDataObserver(self.parent.update_plot)
        if self.model is not None:
            for name in self.model.get_properties():
                if name == "data_name":
                    ad = Adapter(self.model, "data_name")
                    ad.connect_widget(self.view["specimen_data_name"])
                    self.adapt(ad)
                elif name in ["data_phase_removed", "data_phase_added", "del_phase", "add_phase",
                              "data_markers", "data_marker_removed", "data_marker_added", "del_marker", "add_marker" ] :
                    pass
                elif name in ["data_calculated_pattern", "data_experimental_pattern"]:
                    self.xydataobserver.observe_model(getattr(self.model, name))
                    if name == "data_experimental_pattern":
                        tv = self.view['experimental_data_tv']
                        model = self.model.data_experimental_pattern.xy_data
                        tv.set_model(model)
                        tv.connect('cursor_changed', self.on_exp_data_tv_cursor_changed)

                        #allow multiple selection:
                        sel = tv.get_selection()
                        sel.set_mode(gtk.SELECTION_MULTIPLE)

                        def add_column(title, colnr):
                            rend = gtk.CellRendererText()
                            rend.set_property("editable", True)
                            rend.connect('edited', self.on_exp_data_cell_edited, (model, colnr))
                            col = gtk.TreeViewColumn(title, rend, text=colnr)
                            col.set_resizable(True)
                            col.set_expand(True)
                            tv.append_column(col)
                        add_column('2θ', model.c_x)
                        add_column('Intensity', model.c_y)
                elif name == "data_phases":
                    # connects the treeview to the liststore
                    tv = self.view['display_phases_treeview']
                    tv_model = self.model.parent.data_phases
                    tv.set_model(tv_model)
                    
                    # creates the columns of the treeview
                    rend = gtk.CellRendererText()
                    col = gtk.TreeViewColumn('Phase name', rend, text=tv_model.c_data_name) #self.parent.project.model.data_phases.c_data_name)
                    col.set_resizable(True)
                    col.set_expand(True)
                    tv.append_column(col)

                    def check_in_use_renderer(column, cell, model, itr, data=None):
                        phase = model.get_user_data(itr)
                        cell.set_property('active', phase in self.model.data_phases)
                        return
                    rend = gtk.CellRendererToggle()
                    rend.connect('toggled', self.phase_tv_toggled, tv_model) #self.parent.project.model.data_phases)
                    col = gtk.TreeViewColumn('Used', rend, active=1)
                    col.set_cell_data_func(rend, check_in_use_renderer)
                    col.activatable = True
                    col.set_resizable(False)
                    col.set_expand(False)
                    tv.append_column(col)
                    
                    def quantity_renderer(column, cell, model, itr, data=None):
                        phase = model.get_user_data(itr)
                        try:
                            quantity = self.model.data_phases[phase]
                            cell.set_property('text', quantity)
                            column.activatable = True
                        except KeyError:
                            cell.set_property('text', "NA")
                            column.activatable = False

                        return
                    rend = gtk.CellRendererText()
                    rend.set_property("editable", True)
                    rend.connect('edited', self.phase_quantity_edited, tv_model)
                    #FIXME edit signal rend.connect('toggled', self.phase_tv_toggled, tv_model) #self.parent.project.model.data_phases)
                    col = gtk.TreeViewColumn('Quantity', rend) #, text=2)
                    col.set_cell_data_func(rend, quantity_renderer)
                    col.activatable = False
                    col.set_resizable(False)
                    col.set_expand(False)
                    tv.append_column(col)
                    
                elif name in ["calc_color", "exp_color"]:
                    ad = Adapter(self.model, name)
                    ad.connect_widget(self.view["specimen_%s" % name], getter=get_color_val)
                    self.adapt(ad)
                elif name == "data_sample_length":
                    FloatEntryValidator(self.view["specimen_%s" % name])
                    self.adapt(name)
                else:
                    print name
                    self.adapt(name)
            self.update_sensitivities()
            return

    def set_exp_data_sensitivites(self, val):
        self.view["btn_del_experimental_data"].set_sensitive(val)

    def update_sensitivities(self):
        self.view["specimen_exp_color"].set_sensitive(not self.model.inherit_exp_color)
        if not self.model.inherit_exp_color:
            self.view["specimen_exp_color"].set_color(gtk.gdk.color_parse(self.model.exp_color))
        self.view["specimen_calc_color"].set_sensitive(not self.model.inherit_calc_color)
        if not self.model.inherit_calc_color:
            self.view["specimen_calc_color"].set_color(gtk.gdk.color_parse(self.model.calc_color))

    # ------------------------------------------------------------
    #      Notifications of observable properties
    # ------------------------------------------------------------
    @Controller.observe("display_calculated", assign=True)
    @Controller.observe("display_experimental", assign=True)
    @Controller.observe("display_phases", assign=True)
    def notif_display_toggled(self, model, prop_name, info):
        self.parent.update_plot()
        
        #TODO this should be place inside the model!!
        self.model.parent.data_specimens.on_item_changed(self.model)
        return
        
    @Controller.observe("data_name", assign=True)
    @Controller.observe("data_sample", assign=True)
    def notif_data_changed(self, model, prop_name, info):
        self._update_plot_title_timeout()
    @delayed
    def _update_plot_title_timeout(self):
        self.parent.plot_controller.update_title(title=self.parent.get_plot_title())
        
    @Controller.observe("inherit_exp_color", assign=True)
    @Controller.observe("inherit_calc_color", assign=True)
    def notif_color_toggled(self, model, prop_name, info):
        self.update_sensitivities()

    # ------------------------------------------------------------
    #      GTK Signal handlers
    # ------------------------------------------------------------
    def phase_tv_toggled(self, cell, path, model=None, col=1):
        if model is not None:
            phase = model.get_user_data_from_path((int(path),))
            if not cell.get_active():
                self.model.add_phase(phase)
            else:
                self.model.del_phase(phase)
        return True

    def phase_quantity_edited(self, cell, path, new_text, tv_model):
        try:
            phase = tv_model.get_user_data_from_path((int(path),))
            self.model.data_phases[phase] = float(new_text) 
        except:    
            pass
        return True

    def on_btn_ok_clicked(self, event):
        self.parent.pop_status_msg('edit_specimen')
        return DialogController.on_btn_ok_clicked(self, event)

    def on_exp_data_tv_cursor_changed(self, tv):
        path, col = tv.get_cursor()
        self.set_exp_data_sensitivites(path != None)
        return True

    def on_add_experimental_data_clicked(self, widget):
        model = self.model.data_experimental_pattern.xy_data
        path = model.append(0,0)
        self.set_selected_paths(self.view["experimental_data_tv"], (path,))
        return True

    def on_del_experimental_data_clicked(self, widget):
        paths = self.get_selected_paths(self.view["experimental_data_tv"])
        if paths != None:
            model = self.model.data_experimental_pattern.xy_data
            model.remove_from_path(*paths)
        return True

    def on_exp_data_cell_edited(self, cell, path, new_text, user_data):
        model, col = user_data
        itr = model.get_iter(path)
        model.set_value(itr, col, model.convert(col, locale.atof(new_text)))
        return True

    def on_btn_import_experimental_data_clicked(self, widget, data=None):
        def on_confirm(dialog):
            def on_accept(dialog):
                filename = dialog.get_filename()
                if filename[-3:].lower() == "dat":
                    print "Opening file %s for import using ASCII DAT format" % filename
                    data, size, entity = dialog.get_file().load_contents()
                    self.model.data_experimental_pattern.load_data(data, format="DAT")
                if filename[-2:].lower() == "rd":
                    print "Opening file %s for import using BINARY RD format" % filename
                    self.model.data_experimental_pattern.load_data(filename, format="BIN")
            
            self.run_load_dialog(title="Open XRD file for import",
                                 on_accept_callback=on_accept, 
                                 parent=self.view.get_top_widget())
        self.run_confirmation_dialog(self,
                                     "Importing a new experimental file will erase all current data.\nAre you sure you want to continue?",
                                     on_confirm, parent=self.view.get_top_widget())
        return True

    pass # end of class
    

class EditMarkerController(ChildController):

    def register_adapters(self):
        print "EditMarkerController.register_adapters()"
        if self.model is not None:
            for name in self.model.get_properties():
                if name == "data_color":
                    ad = Adapter(self.model, "data_color")
                    ad.connect_widget(self.view["marker_data_color"], getter=get_color_val)
                    self.adapt(ad)
                elif name == "data_style":
                    ctrl_setup_combo_with_list(self, 
                        self.view["marker_data_style"],
                        "data_style", "_data_styles")
                elif name == "data_base":
                    ctrl_setup_combo_with_list(self,
                        self.view["marker_data_base"],
                        "data_base", "_data_bases")
                elif name in ("data_position", "data_angle"):
                    FloatEntryValidator(self.view["marker_%s" % name])
                    self.adapt(name)
                else:
                    self.adapt(name)
            FloatEntryValidator(self.view["entry_nanometer"])
            return
            
    def update_sensitivities(self):
        self.view["marker_data_angle"].set_sensitive(not self.model.inherit_angle)
        
    
    # ------------------------------------------------------------
    #      Notifications of observable properties
    # ------------------------------------------------------------   
    @Controller.observe("data_label", assign=True)
    def notif_name_changed(self, model, prop_name, info):
        self.model.parent.data_markers.on_item_changed(self.model)

    @Controller.observe("data_label", assign=True, after=True)
    @Controller.observe("data_position", assign=True, after=True)
    @Controller.observe("data_color", assign=True, after=True)
    @Controller.observe("data_base", assign=True, after=True)
    @Controller.observe("data_angle", assign=True, after=True)
    @Controller.observe("data_style", assign=True, after=True)
    def notif_parameter_changed(self, model, prop_name, info):
        if prop_name=="data_position":
            self.view["entry_nanometer"].set_text("%f" % self.model.get_nm_position())
        self.cparent.update_plot()

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
            self.model.data_style = val
            
    def on_nanometer_changed(self, widget):
        position = float(widget.get_text())
        self.model.set_nm_position(position)
        
    def on_sample_clicked(self, widget):
        self.cid = -1
        self.fig = self.cparent.plot_controller.figure
        self.ret = self.view.get_toplevel()
        
        self.edc = EyedropperCursorPlot(self.cparent.plot_controller.canvas, self.cparent.plot_controller.canvas.get_window(), True, True)
        
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
                self.model.data_position = x_pos
                
        self.cid = self.fig.canvas.mpl_connect('button_press_event', onclick)
        self.cparent.view.get_toplevel().present()
        
class MarkersController(ObjectListStoreController):

    file_filters = ("Marker file", "*.mrk"),
    model_property_name = "data_markers"
    columns = [ ("Marker label", 0) ]
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
    
    # ------------------------------------------------------------
    #      GTK Signal handlers
    # ------------------------------------------------------------
    def on_load_object_clicked(self, event):
        pass
        #TODO
        #def on_accept(open_dialog):
        #    print "Importing atom types..."
        #    fltr = open_dialog.get_filter()
        #    if fltr.get_name() == self.file_filters[0][0]:
        #        self.open_atom_type(open_dialog.get_filename())
        #    elif fltr.get_name() == self.file_filters[1][0]:
        #        AtomType.get_from_csv(open_dialog.get_filename(), self.model.add_atom_type, self.model)        
        #self.run_load_dialog("Import atom types", on_accept, parent=self.view.get_top_widget())


    def on_save_object_clicked(self, event):
        pass
        #TODO
        #def on_accept(save_dialog):
        #    print "Exporting atom types..."
        #    fltr = save_dialog.get_filter()
        #    filename = save_dialog.get_filename()
        #    if fltr.get_name() == self.file_filters[0][0]:
        #        if filename[len(filename)-4:] != self.file_filters[0][1][1:]:
        #            filename = "%s%s" % (filename, self.file_filters[0][1][1:])
        #        atom_type = self.get_selected_object()
        #        if atom_type is not None:
        #            atom_type.save_object(filename=filename)
        #    elif fltr.get_name() == self.file_filters[1][0]:
        #        if filename[len(filename)-4:] != self.file_filters[1][1][1:]:
        #            filename = "%s%s" % (filename, self.file_filters[1][1][1:])
        #        AtomType.save_as_csv(filename, self.get_selected_objects())
        #self.run_save_dialog("Export atom types", on_accept, parent=self.view.get_top_widget())
        
    def on_del_object_clicked(self, event):
        ObjectListStoreController.on_del_object_clicked(self, event)
        self.parent.update_plot()
        
    def on_add_object_clicked(self, event):
        new_marker = Marker("New Marker", parent=self.model)
        self.model.add_marker(new_marker)
        self.select_object(new_marker)
        self.parent.update_plot()
    
    def on_find_peaks_clicked(self, widget):
        print "ON FIND PEAKS CLICKED FOR MODEL %s!!" % self.model
        
        def after_cb(threshold):
            if len(self.model.data_markers._model_data) > 0:            
                def on_accept(dialog):
                    self.model.data_markers.clear()
                self.run_confirmation_dialog("Do you want to clear the current markers for this pattern?",
                                             on_accept, parent=self.view.get_top_widget())
            self.model.auto_add_peaks(threshold)
            self.parent.redraw_plot()

        sel_model = ThresholdSelector(parent=self.model)
        sel_view = DetectPeaksView(parent=self.view)
        sel_ctrl = ThresholdController(sel_model, sel_view, parent=self, callback = after_cb)
        
        sel_view.present()
        
class ThresholdController(DialogController):
    
    callback = None
    dline = None
    
    def __init__(self, model, view, spurious=False, auto_adapt=False, parent=None, callback=None):
        DialogController.__init__(self, model, view, spurious=spurious, auto_adapt=auto_adapt, parent=parent)
        
        self.callback = callback
        self.dline = None
    
    def update_plot(self):
        print "UPDATE PLOT"
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
        print "ThresholdController.register_adapters()"
        if view is not None:
            top = view.get_toplevel()
            top.set_transient_for(self.parent.view.get_toplevel())
            top.set_modal(True)
            self.update_plot()
    
    def register_adapters(self):
        print "ThresholdController.register_adapters()"
        if self.model is not None:
            for name in self.model.get_properties():
                if name == "pattern":
                    ctrl_setup_combo_with_list(self, self.view["pattern"], "pattern", "_patterns")
                elif name in ("sel_threshold", "max_threshold"):
                    FloatEntryValidator(self.view[name])
                    self.adapt(name)
                elif not name in ("threshold_plot_data",):
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
            self.callback(self.model.sel_threshold)
        return DialogController.on_btn_ok_clicked(self, event)
