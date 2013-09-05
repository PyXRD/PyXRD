# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import os, locale

import gtk

from gtkmvc import Controller

from generic.io.file_parsers import parsers
from generic.controllers import BaseController, DialogController, DialogMixin, ObjectTreeviewMixin
from generic.controllers.utils import DummyAdapter
from generic.views.treeview_tools import setup_treeview, new_text_column

from goniometer.controllers import InlineGoniometerController

from generic.controllers.line_controllers import (
    BackgroundController,
    SmoothDataController,
    AddNoiseController,
    ShiftDataController,
    StripPeakController
)

from generic.views.line_views import (
    BackgroundView,
    SmoothDataView,
    AddNoiseView,
    ShiftDataView,
    StripPeakView
)

class SpecimenController(DialogController, DialogMixin, ObjectTreeviewMixin):
    """
        Specimen controller.
        
        Attributes:
            export_filters: the file filter tuples for exporting XRD patterns
            excl_filters: the file filter tuples for exporting exclusion ranges
    """

    file_filters = [parser.file_filter for parser in parsers["xrd"]]
    export_filters = [parser.file_filter for parser in parsers["xrd"] if parser.can_write]
    excl_filters = [parser.file_filter for parser in parsers["exc"]]

    widget_handlers = {
        'custom':  'custom_handler',
    }

    # ------------------------------------------------------------
    #      Initialisation and other internals
    # ------------------------------------------------------------
    @staticmethod
    def custom_handler(self, intel, widget):
        if intel.name in ("goniometer"):
            self.gonio_ctrl = InlineGoniometerController(view=self.view.gonio_view, model=self.model.goniometer, parent=self)
            ad = DummyAdapter(intel.name)
            return ad

    def register_adapters(self):
        super(SpecimenController, self).register_adapters()
        self.update_sensitivities()

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
            edited_callback=(self.on_xy_data_cell_edited, (store, store.c_x))))
        # Y Column:
        widget.append_column(new_text_column(
            u'Intensity', text_col=store.c_y, editable=True,
            edited_callback=(self.on_xy_data_cell_edited, (store, store.c_y))))

    def setup_calculated_pattern_tree_view(self, store, widget):
        """
            Creates the calculated data TreeView layout and behavior
        """
        setup_treeview(widget, store,
            on_cursor_changed=self.on_exp_data_tv_cursor_changed,
            on_columns_changed=self.on_calc_treestore_changed,
            sel_mode=gtk.SELECTION_NONE)
        self.update_calc_treeview(widget)

    def setup_exclusion_ranges_tree_view(self, store, widget):
        """
            Creates the exclusion ranges TreeView layout and behavior
        """
        setup_treeview(widget, store,
            on_cursor_changed=self.on_exclusion_ranges_tv_cursor_changed,
            sel_mode=gtk.SELECTION_MULTIPLE)
        widget.append_column(new_text_column(
            u'From [°2θ]', text_col=store.c_x, editable=True,
            edited_callback=(self.on_xy_data_cell_edited, (store, store.c_x)),
            resizable=True, expand=True))
        widget.append_column(new_text_column(
            u'To [°2θ]', text_col=store.c_y, editable=True,
            edited_callback=(self.on_xy_data_cell_edited, (store, store.c_y)),
            resizable=True, expand=True))

    # ------------------------------------------------------------
    #      Methods & Functions
    # ------------------------------------------------------------
    def _line_store_getter(self, model, prop_name):
        """ Returns the actual XYListStore from a line model """
        return getattr(model, prop_name).xy_store
    get_experimental_pattern_tree_model = _line_store_getter
    get_calculated_pattern_tree_model = _line_store_getter

    def update_calc_treeview(self, tv):
        """
            Updates the calculated pattern TreeView layout
        """
        model = self.model.calculated_pattern.xy_store

        for column in tv.get_columns():
            tv.remove_column(column)

        def get_num(column, cell, model, itr, *data):
            cell.set_property('text', '%.3f' % model.get_value(itr, column.get_col_attr('text')))

        tv.append_column(new_text_column(u'2θ', text_col=model.c_x, data_func=get_num))
        tv.append_column(new_text_column(u'Cal', text_col=model.c_x, data_func=get_num))
        for i in range(model.get_n_columns() - 3):
            tv.append_column(new_text_column(
                model.get_y_name(i), text_col=i + 2, data_func=get_num))

    def update_sensitivities(self):
        """
            Updates the views sensitivities according to the model state.
        """
        print self, self.model, self.view
        self.view["specimen_exp_color"].set_sensitive(not self.model.inherit_exp_color)
        # if not self.model.inherit_exp_color:
        #    self.view["specimen_exp_color"].set_color(gtk.gdk.color_parse(self.model.exp_color))
        self.view["specimen_calc_color"].set_sensitive(not self.model.inherit_calc_color)
        # if not self.model.inherit_calc_color:
        #    self.view["specimen_calc_color"].set_color(gtk.gdk.color_parse(self.model.calc_color))

        self.view["spb_calc_lw"].set_sensitive(not self.model.inherit_calc_lw)
        self.view["spb_exp_lw"].set_sensitive(not self.model.inherit_exp_lw)

    def remove_background(self):
        """
            Opens the 'remove background' dialog.
        """
        bg_view = BackgroundView(parent=self.view)
        BackgroundController(self.model.experimental_pattern, bg_view, parent=self)
        bg_view.present()

    def add_noise(self):
        """
            Opens the 'add noise' dialog.
        """
        an_view = AddNoiseView(parent=self.view)
        AddNoiseController(self.model.experimental_pattern, an_view, parent=self)
        an_view.present()

    def smooth_data(self):
        """
            Opens the 'smooth data' dialog.
        """
        sd_view = SmoothDataView(parent=self.view)
        SmoothDataController(self.model.experimental_pattern, sd_view, parent=self)
        sd_view.present()

    def shift_data(self):
        """
            Opens the 'shift data' dialog.
        """
        sh_view = ShiftDataView(parent=self.view)
        ShiftDataController(self.model.experimental_pattern, sh_view, parent=self)
        sh_view.present()

    def strip_peak(self):
        """
            Opens the 'strip peak' dialog.
        """
        st_view = StripPeakView(parent=self.view)
        StripPeakController(self.model.experimental_pattern, st_view, parent=self)
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
        self.update_calc_treeview(self.view["specimen_calculated_pattern"])

    def on_btn_ok_clicked(self, event):
        self.parent.pop_status_msg('edit_specimen')
        return super(SpecimenController, self).on_btn_ok_clicked(event)

    def on_exclusion_ranges_tv_cursor_changed(self, tv):
        path, col = tv.get_cursor()
        self.view["btn_del_exclusion_ranges"].set_sensitive(path != None)
        return True

    def on_exp_data_tv_cursor_changed(self, tv):
        path, col = tv.get_cursor()
        self.view["btn_del_experimental_data"].set_sensitive(path != None)
        return True

    def on_add_experimental_data_clicked(self, widget):
        model = self.model.experimental_pattern.xy_store
        path = model.append(0, 0)
        self.set_selected_paths(self.view["specimen_experimental_pattern"], (path,))
        return True

    def on_add_exclusion_range_clicked(self, widget):
        model = self.model.exclusion_ranges
        path = model.append(0, 0)
        self.set_selected_paths(self.view["specimen_exclusion_ranges"], (path,))
        return True

    def on_del_experimental_data_clicked(self, widget):
        paths = self.get_selected_paths(self.view["specimen_experimental_pattern"])
        if paths != None:
            model = self.model.experimental_pattern.xy_store
            model.remove_from_index(*paths)
        return True

    def on_del_exclusion_ranges_clicked(self, widget):
        paths = self.get_selected_paths(self.view["specimen_exclusion_ranges"])
        if paths != None:
            model = self.model.exclusion_ranges
            model.remove_from_index(*paths)
        return True

    def on_xy_data_cell_edited(self, cell, path, new_text, model, col):
        # model, col = user_data
        itr = model.get_iter(path)
        model.set_value(itr, col, model.convert(col, locale.atof(new_text)))
        return True

    def on_import_exclusion_ranges_clicked(self, widget, data=None):
        def on_confirm(dialog):
            def on_accept(dialog):
                filename = dialog.get_filename()
                ffilter = dialog.get_filter()
                parser = ffilter.get_data("parser")
                if filename[-3:].lower() == "exc":
                    # self.model.exclusion_ranges.load_data(filename, format="DAT")
                    exclfiles = parser.parse(filename)
                    self.model.exclusion_ranges.load_data_from_generator(exclfiles[0].data, clear=True)
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
            try:
                self.model.experimental_pattern.load_data(parser, filename, clear=True)
            except Exception as msg:
                message = "An unexpected error has occured when trying to parse %s:\n\n<i>" % os.path.basename(filename)
                message += str(msg) + "</i>\n\n"
                message += "This is most likely caused by an invalid or unsupported file format."
                self.run_information_dialog(
                    message=message,
                    parent=self.view.get_top_widget()
                )
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
