# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import os, locale
import logging
logger = logging.getLogger(__name__)

import gtk

from mvc.adapters import DummyAdapter
from mvc.adapters.gtk_support.tree_view_adapters import wrap_xydata_to_treemodel
from pyxrd.generic.controllers import BaseController, DialogController, TreeViewMixin
from pyxrd.generic.views.treeview_tools import setup_treeview, new_text_column

from pyxrd.goniometer.controllers import InlineGoniometerController
from pyxrd.specimen.models.base import Specimen

from pyxrd.generic.controllers.line_controllers import (
    LinePropertiesController,
    BackgroundController,
    SmoothDataController,
    AddNoiseController,
    ShiftDataController,
    StripPeakController,
    CalculatePeakAreaController,
)

from pyxrd.generic.views.line_views import (
    BackgroundView,
    SmoothDataView,
    AddNoiseView,
    ShiftDataView,
    StripPeakView,
    CalculatePeakAreaView
)
from pyxrd.data import settings

class SpecimenController(DialogController, TreeViewMixin):
    """
        Specimen controller.
        
        Attributes:
            export_filters: the file filter tuples for exporting XRD patterns
            excl_filters: the file filter tuples for exporting exclusion ranges
    """

    file_filters = Specimen.Meta.file_filters
    export_filters = Specimen.Meta.export_filters
    excl_filters = Specimen.Meta.excl_filters

    widget_handlers = {
        'custom':  'custom_handler',
    }

    # ------------------------------------------------------------
    #      Initialization and other internals
    # ------------------------------------------------------------
    @staticmethod
    def custom_handler(self, intel, widget):
        if intel.name in ("goniometer"):
            self.gonio_ctrl = InlineGoniometerController(view=self.view.gonio_view, model=self.model.goniometer, parent=self)
            ad = DummyAdapter(controller=self, prop=intel) # TODO FIXME
            return ad

    def setup_experimental_pattern_tree_view(self, store, widget):
        """
            Creates the experimental data TreeView layout and behavior
        """
        setup_treeview(widget, store,
            on_cursor_changed=self.on_exp_data_tv_cursor_changed,
            sel_mode=gtk.SELECTION_MULTIPLE)
        # X Column:
        widget.append_column(new_text_column(
            u'°2θ', text_col=store.c_x, editable=True,
            edited_callback=(self.on_xy_data_cell_edited, (self.model.experimental_pattern, 0))))
        # Y Column:
        widget.append_column(new_text_column(
            u'Intensity', text_col=store.c_y, editable=True,
            edited_callback=(self.on_xy_data_cell_edited, (self.model.experimental_pattern, 1))))
        # Other properties:
        self.exp_line_ctrl = LinePropertiesController(model=self.model.experimental_pattern, view=self.view.exp_line_view, parent=self)

    def setup_calculated_pattern_tree_view(self, store, widget):
        """
            Creates the calculated data TreeView layout and behavior
        """
        setup_treeview(widget, store,
            on_cursor_changed=self.on_exp_data_tv_cursor_changed,
            sel_mode=gtk.SELECTION_NONE)
        store.connect('columns_changed', self.on_calc_columns_changed),
        self.update_calc_treeview(widget)
        # Other properties:
        self.calc_line_ctrl = LinePropertiesController(model=self.model.calculated_pattern, view=self.view.calc_line_view, parent=self)

    def setup_exclusion_ranges_tree_view(self, store, widget):
        """
            Creates the exclusion ranges TreeView layout and behavior
        """
        setup_treeview(widget, store,
            on_cursor_changed=self.on_exclusion_ranges_tv_cursor_changed,
            sel_mode=gtk.SELECTION_MULTIPLE)
        widget.append_column(new_text_column(
            u'From [°2θ]', text_col=store.c_x, editable=True,
            edited_callback=(self.on_xy_data_cell_edited, (self.model.exclusion_ranges, 0)),
            resizable=True, expand=True))
        widget.append_column(new_text_column(
            u'To [°2θ]', text_col=store.c_y, editable=True,
            edited_callback=(self.on_xy_data_cell_edited, (self.model.exclusion_ranges, 1)),
            resizable=True, expand=True))

    # ------------------------------------------------------------
    #      Methods & Functions
    # ------------------------------------------------------------
    def get_experimental_pattern_tree_model(self):
        return wrap_xydata_to_treemodel(self.model, self.model.Meta.get_prop_intel_by_name("experimental_pattern"))
    def get_calculated_pattern_tree_model(self):
        return wrap_xydata_to_treemodel(self.model, self.model.Meta.get_prop_intel_by_name("calculated_pattern"))
    def get_exclusion_ranges_tree_model(self):
        return wrap_xydata_to_treemodel(self.model, self.model.Meta.get_prop_intel_by_name("exclusion_ranges"))

    def update_calc_treeview(self, tv):
        """
            Updates the calculated pattern TreeView layout
        """
        model = self.get_calculated_pattern_tree_model()

        for column in tv.get_columns():
            tv.remove_column(column)

        def get_num(column, cell, model, itr, *data):
            cell.set_property('text', '%.3f' % model.get_value(itr, column.get_col_attr('text')))

        tv.append_column(new_text_column(u'2θ', text_col=model.c_x, data_func=get_num))
        tv.append_column(new_text_column(u'Cal', text_col=model.c_y, data_func=get_num))
        for i in range(model.get_n_columns() - 2):
            tv.append_column(new_text_column(
                self.model.calculated_pattern.get_y_name(i), text_col=i + 2, data_func=get_num))

    def remove_background(self):
        """
            Opens the 'remove background' dialog.
        """
        bg_view = BackgroundView(parent=self.view)
        BackgroundController(model=self.model.experimental_pattern, view=bg_view, parent=self)
        bg_view.present()

    def add_noise(self):
        """
            Opens the 'add noise' dialog.
        """
        an_view = AddNoiseView(parent=self.view)
        AddNoiseController(model=self.model.experimental_pattern, view=an_view, parent=self)
        an_view.present()

    def smooth_data(self):
        """
            Opens the 'smooth data' dialog.
        """
        sd_view = SmoothDataView(parent=self.view)
        SmoothDataController(model=self.model.experimental_pattern, view=sd_view, parent=self)
        sd_view.present()

    def shift_data(self):
        """
            Opens the 'shift data' dialog.
        """
        sh_view = ShiftDataView(parent=self.view)
        ShiftDataController(model=self.model.experimental_pattern, view=sh_view, parent=self)
        sh_view.present()

    def strip_peak(self):
        """
            Opens the 'strip peak' dialog.
        """
        st_view = StripPeakView(parent=self.view)
        StripPeakController(model=self.model.experimental_pattern, view=st_view, parent=self)
        st_view.present()

    def peak_area(self):
        """
            Opens the 'peak area' dialog.
        """
        pa_view = CalculatePeakAreaView(parent=self.view)
        CalculatePeakAreaController(model=self.model.experimental_pattern, view=pa_view, parent=self)
        pa_view.present()

    # ------------------------------------------------------------
    #      GTK Signal handlers
    # ------------------------------------------------------------
    def on_calc_columns_changed(self, *args, **kwargs):
        self.update_calc_treeview(self.view["specimen_calculated_pattern"])

    def on_btn_ok_clicked(self, event):
        self.parent.pop_status_msg('edit_specimen')
        return super(SpecimenController, self).on_btn_ok_clicked(event)

    def on_exclusion_ranges_tv_cursor_changed(self, tv):
        path, col = tv.get_cursor()
        self.view["btn_del_exclusion_ranges"].set_sensitive(path is not None)
        return True

    def on_exp_data_tv_cursor_changed(self, tv):
        path, col = tv.get_cursor()
        self.view["btn_del_experimental_data"].set_sensitive(path is not None)
        return True

    def on_add_experimental_data_clicked(self, widget):
        self.model.experimental_pattern.append(0, 0)
        return True

    def on_add_exclusion_range_clicked(self, widget):
        self.model.exclusion_ranges.append(0, 0)
        return True

    def on_del_experimental_data_clicked(self, widget):
        paths = self.get_selected_paths(self.view["specimen_experimental_pattern"])
        if paths is not None:
            self.model.experimental_pattern.remove_from_indeces(*paths)
        return True

    def on_del_exclusion_ranges_clicked(self, widget):
        paths = self.get_selected_paths(self.view["specimen_exclusion_ranges"])
        if paths is not None:
            self.model.exclusion_ranges.remove_from_indeces(*paths)
        return True

    def on_xy_data_cell_edited(self, cell, path, new_text, model, col):
        try:
            value = float(locale.atof(new_text))
        except ValueError:
            logger.exception("ValueError: Invalid literal for float(): '%s'" % new_text)
        else:
            model.set_value(int(path), col, value)
        return True

    def on_import_exclusion_ranges_clicked(self, widget, data=None):
        def on_confirm(dialog):
            def on_accept(dialog):
                filename = dialog.get_filename()
                ffilter = dialog.get_filter()
                parser = ffilter.get_data("parser")
                try:
                    self.model.exclusion_ranges.load_data(parser, filename, clear=True)
                except Exception as msg:
                    message = "An unexpected error has occured when trying to parse %s:\n\n<i>" % os.path.basename(filename)
                    message += str(msg) + "</i>\n\n"
                    message += "This is most likely caused by an invalid or unsupported file format."
                    self.run_information_dialog(
                        message=message,
                        parent=self.view.get_top_widget()
                    )
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
                header = "%s %s" % (self.model.name, self.model.sample_name)
                self.model.exclusion_ranges.save_data(filename, header=header)
        self.run_save_dialog(title="Select file for exclusion ranges export",
                             on_accept_callback=on_accept,
                             parent=self.view.get_top_widget(),
                             filters=self.excl_filters)

    def on_replace_experimental_data(self, *args, **kwargs):
        def on_accept(dialog):
            filename = dialog.get_filename()
            ffilter = dialog.get_filter()
            parser = ffilter.get_data("parser")
            try:
                self.model.experimental_pattern.load_data(parser, filename, clear=True)
            except Exception:
                message = "An unexpected error has occured when trying to parse '%s'.\n" % os.path.basename(filename)
                message += "This is most likely caused by an invalid or unsupported file format."
                self.run_information_dialog(
                    message=message,
                    parent=self.view.get_top_widget()
                )
                raise
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
            elif filename[-2:].lower() == "rd":
                self.run_information_dialog("RD file format not supported (yet)!", parent=self.view.get_top_widget())

        self.run_save_dialog(title="Select file for export",
                             on_accept_callback=on_accept,
                             parent=self.view.get_top_widget(),
                             filters=self.export_filters,
                             suggest_name=self.model.name)
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

    pass # end of class

class StatisticsController(BaseController):

    def register_adapters(self):
        if self.model is not None:
            for name in self.model.get_properties():
                if name in self.model.__have_no_widget__:
                    pass
                else:
                    self.adapt(name)
            return

    pass # end of class
