# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import gtk

from pyxrd.gtkmvc import Controller

from pyxrd.generic.plot.controllers import DraggableVLine, EyedropperCursorPlot
from pyxrd.generic.controllers import DialogController, BaseController, ObjectListStoreController
from pyxrd.generic.views.validators import FloatEntryValidator
from pyxrd.generic.views.treeview_tools import setup_treeview, new_text_column, new_toggle_column
from pyxrd.generic.io.utils import get_case_insensitive_glob

from pyxrd.specimen.models import Marker, ThresholdSelector, MineralScorer
from pyxrd.specimen.views import (
    EditMarkerView,
    DetectPeaksView,
    MatchMineralsView
)

class EditMarkerController(BaseController):

    def register_view(self, view):
        self.update_sensitivities()

    def register_adapters(self):
        # Adapt converted position entry:
        self.view["entry_nanometer"].set_text("%f" % self.model.get_nm_position())
        FloatEntryValidator(self.view["entry_nanometer"])

    def update_sensitivities(self):
        for name in ("style", "align", "base", "top", "top_offset", "angle", "color"):
            self.view["marker_%s" % name].set_sensitive(not getattr(self.model, "inherit_%s" % name))

    # ------------------------------------------------------------
    #      Notifications of observable properties
    # ------------------------------------------------------------
    @Controller.observe("position", assign=True, after=True)
    def notif_parameter_changed(self, model, prop_name, info):
        if prop_name == "position":
            self.view["entry_nanometer"].set_text("%f" % self.model.get_nm_position())

    @Controller.observe("inherit_style", assign=True)
    @Controller.observe("inherit_align", assign=True)
    @Controller.observe("inherit_base", assign=True)
    @Controller.observe("inherit_top", assign=True)
    @Controller.observe("inherit_top_offset", assign=True)
    @Controller.observe("inherit_angle", assign=True)
    @Controller.observe("inherit_color", assign=True)
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

        def click_callback(edc, x_pos, event):
            if edc != None:
                edc.enabled = False
                edc.disconnect()
            self.view.get_toplevel().present()
            if x_pos != -1:
                self.model.position = x_pos

        self.edc = EyedropperCursorPlot(
            self.parent.plot_controller.figure,
            self.parent.plot_controller.canvas,
            self.parent.plot_controller.canvas.get_window(),
            click_callback,
            True, True
        )

        self.view.get_toplevel().hide()
        self.parent.view.get_toplevel().present()

class MarkersController(ObjectListStoreController):

    file_filters = ("Marker file", get_case_insensitive_glob("*.MRK")),
    model_property_name = "markers"
    columns = [
        (" ", "c_visible"),
        ("Marker label", "c_label")
    ]
    delete_msg = "Deleting a marker is irreversible!\nAre You sure you want to continue?"
    obj_type_map = [
        (Marker, EditMarkerView, EditMarkerController),
    ]
    title = "Edit Markers"

    def setup_treeview_col_c_visible(self, treeview, name, col_descr, col_index, tv_col_nr):
        def toggle_renderer(column, cell, model, itr, data=None):
            col = column.get_col_attr("active")
            cell.set_property('active', model.get_value(itr, col))
            return
        col = new_toggle_column(" ",
                toggled_callback=(self.on_marker_visible_toggled, (treeview.get_model(), col_index)),
                data_func=toggle_renderer,
                resizable=False,
                expand=False,
                activatable=True,
                active_col=col_index)
        col.set_data("colnr", col_index)
        treeview.append_column(col)
        return True

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

    def on_marker_visible_toggled(self, cell, path, model, colnr):
        if model != None:
            itr = model.get_iter(path)
            model.set_value(itr, colnr, not cell.get_active())
            return True
        return False

    def on_find_peaks_clicked(self, widget):
        def after_cb(threshold):
            if len(self.model.markers._model_data) > 0:
                def on_accept(dialog):
                    self.model.markers.clear()
                self.run_confirmation_dialog("Do you want to clear the current markers for this pattern?",
                                             on_accept, parent=self.view.get_top_widget())
            self.model.auto_add_peaks(threshold)

        sel_model = ThresholdSelector(parent=self.model)
        sel_view = DetectPeaksView(parent=self.view)
        sel_ctrl = ThresholdController(sel_model, sel_view, parent=self, callback=after_cb)
        sel_model.update_threshold_plot_data()

        sel_view.present()

    def on_match_minerals_clicked(self, widget):
        def apply_cb(matches):
            for name, abbreviation, peaks, matches, score in matches:
                for marker in self.get_selected_objects():
                    for mpos, epos in matches:
                        if marker.get_nm_position() * 10. == epos:
                            marker.label += ", %s" % abbreviation

        def close_cb():
            self.model.needs_update.emit()
            self.view.show()

        marker_peaks = [] # position, intensity

        for marker in self.get_selected_objects():
            intensity = self.model.experimental_pattern.xy_store.get_y_at_x(
                marker.position)
            marker_peaks.append((marker.get_nm_position() * 10., intensity))

        scorer_model = MineralScorer(marker_peaks=marker_peaks, parent=self.model)
        scorer_view = MatchMineralsView(parent=self.view)
        scorer_ctrl = MatchMineralController(model=scorer_model, view=scorer_view, parent=self, apply_callback=apply_cb, close_callback=close_cb)

        self.view.hide()
        scorer_view.present()

    pass # end of class

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
                cell.set_property("markup", value)
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
            name, abbreviation, peaks = model.get(itr, 0, 1, 2)
            self.model.add_match(name, abbreviation, peaks)

    def on_del_match_clicked(self, event):
        selection = self.view.tv_matches.get_selection()
        if selection.count_selected_rows() >= 1:
            model, paths = selection.get_selected_rows()
            self.model.del_match(*paths[0])

    def on_apply_clicked(self, event):
        if self.apply_callback != None and callable(self.apply_callback):
            self.model.specimen.mineral_preview = None
            self.apply_callback(self.model.matches)
        self.view.hide()

    def on_cancel(self):
        if self.close_callback != None and callable(self.close_callback):
            self.model.specimen.mineral_preview = None
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

    pass # end of class


class ThresholdController(DialogController):

    auto_adapt_included = [
        "pattern",
        "sel_threshold",
        "max_threshold",
        "sel_num_peaks",
        "steps"
    ]

    callback = None
    dline = None

    def __init__(self, *args, **kwargs):
        callback = kwargs.pop("callback", None)
        super(ThresholdController, self).__init__(*args, **kwargs)
        self.callback = callback
        self.dline = None

    def update_plot(self):
        if self.view != None:
            self.view.plot.cla()
            if self.dline != None:
                self.dline.disconnect()
                self.dline = None

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

    def register_adapters(self):
        self.update_plot()

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

    pass # end of class
