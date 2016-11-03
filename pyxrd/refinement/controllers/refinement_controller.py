# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import logging
logger = logging.getLogger(__name__)

import gtk, gobject
import sys

from mvc.adapters.gtk_support.dialogs.dialog_factory import DialogFactory

from pyxrd.generic.async.providers import get_status
from pyxrd.generic.threads import CancellableThread
from pyxrd.generic.gtk_tools.utils import run_when_idle
from pyxrd.generic.views.treeview_tools import new_text_column, new_pb_column, new_toggle_column
from pyxrd.generic.mathtext_support import create_pb_from_mathtext
from pyxrd.generic.controllers import DialogController

from pyxrd.refinement.views.refiner_view import RefinerView
from pyxrd.refinement.controllers.refiner_controller import RefinerController

class RefinementController(DialogController):

    auto_adapt_included = [
        "refine_method_index",
        "refinables",
        "make_psp_plots",
    ]

    @property
    def treemodel(self):
        return self.model.refinables

    def setup_refinables_tree_view(self, store, widget):
        """
            Setup refinables TreeView layout
        """
        widget.set_show_expanders(True)

        if sys.platform == "win32":
            def get_label(column, cell, model, itr, user_data=None):
                ref_prop = model.get_user_data(itr)
                cell.set_property("text", ref_prop.get_text_title())
                return
            widget.append_column(new_text_column('Name/Prop', xalign=0.0, data_func=get_label))
        else:
            # Labels are parsed for mathtext markup into pb's:
            def get_pb(column, cell, model, itr, user_data=None):
                ref_prop = model.get_user_data(itr)
                try:
                    if not hasattr(ref_prop, "pb") or not ref_prop.pb:
                        ref_prop.pb = create_pb_from_mathtext(
                            ref_prop.title,
                            align='left',
                            weight='medium'
                        )
                    cell.set_property("pixbuf", ref_prop.pb)
                except RuntimeError:
                    logger.warning("An error occured when trying to convert a property title to a PixBuf")
                    raise
                return
            widget.append_column(new_pb_column('Name/Prop', xalign=0.0, data_func=get_pb))

        # Editable floats:
        def get_value(column, cell, model, itr, *args):
            col = column.get_col_attr('markup')
            try:
                value = model.get_value(itr, col)
                value = "%.5f" % value
            except TypeError: value = ""
            cell.set_property("markup", value)
            return
        def on_float_edited(rend, path, new_text, model, col):
            itr = model.get_iter(path)
            try:
                model.set_value(itr, col, float(new_text))
            except ValueError:
                return False
            return True

        def_float_args = {
            "sensitive_col": store.c_refinable,
            "editable_col": store.c_refinable,
            "visible_col": store.c_refinable,
            "data_func": get_value
        }

        widget.append_column(new_text_column(
            "Value", markup_col=store.c_value,
            edited_callback=(
                on_float_edited,
                (store, store.c_value,)
            ), **def_float_args
        ))
        widget.append_column(new_text_column(
            "Min", markup_col=store.c_value_min,
            edited_callback=(
                on_float_edited,
                (store, store.c_value_min,)
            ), **def_float_args
        ))
        widget.append_column(new_text_column(
            "Max", markup_col=store.c_value_max,
            edited_callback=(
                on_float_edited,
                (store, store.c_value_max,)
            ), **def_float_args
        ))

        # The 'refine' checkbox:
        widget.append_column(new_toggle_column(
            "Refine",
            toggled_callback=(self.refine_toggled, (store,)),
            resizable=False,
            expand=False,
            active_col=store.c_refine,
            sensitive_col=store.c_refinable,
            activatable_col=store.c_refinable,
            visible_col=store.c_refinable
        ))

    def _update_method_options_store(self):
        """
            Update the method options tree store (when a new method is selected)
        """
        tv = self.view['tv_method_options']
        store = gtk.ListStore(str, str)
        method = self.model.get_refinement_method()
        for arg in method.options:
            description = getattr(type(method), arg).description
            store.append([arg, description])
        tv.set_model(store)
        return tv

    def _setup_method_options_treeview(self):
        """
            Initial method options tree view layout & behavior setup
        """
        # Update the method options store to match the currently selected
        # refinement method
        tv = self._update_method_options_store()

        # The name of the option:
        tv.append_column(new_text_column("Name", text_col=1))

        # The value of the option:
        def get_value(column, cell, model, itr, *args):
            option_name, = tv.get_model().get(itr, 0)
            method = self.model.get_refinement_method()
            cell.set_property("sensitive", True)
            cell.set_property("editable", True)
            cell.set_property("markup", getattr(method, option_name))
            return
        
        def on_value_edited(rend, path, new_text, col):
            store = tv.get_model()
            itr = store.get_iter(path)
            option_name, = store.get(itr, 0)
            method = self.model.get_refinement_method()
            try:
                setattr(method, option_name, new_text)
            except ValueError:
                pass
            return True
        tv.append_column(new_text_column(
            "Value", text_col=0,
            data_func=get_value,
            edited_callback=(on_value_edited, (0,)),
        ))

    def register_view(self, view):
        # Create the method treeview:
        self._setup_method_options_treeview()
        # Update the server status:
        self.view.update_server_status(get_status())

    def cleanup(self):
        if hasattr(self, "view"):
            del self.view
        if hasattr(self, "results_view"):
            del self.results_view
        if hasattr(self, "results_controller"):
            del self.results_controller
        if hasattr(self, "model"):
            self.relieve_model(self.model)

    # ------------------------------------------------------------
    #      Notifications of observable properties
    # ------------------------------------------------------------
    @DialogController.observe("refine_method_index", assign=True)
    def on_prop_changed(self, model, prop_name, info):
        self._update_method_options_store()

    # ------------------------------------------------------------
    #      GTK Signal handlers
    # ------------------------------------------------------------
    def on_cancel(self):
        if self.view is not None:
            self.view.hide()
            self.parent.view.parent.show()

    def refine_toggled(self, cell, path, model):
        if model is not None:
            itr = model.get_iter(path)
            model.set_value(itr, model.c_refine, not cell.get_active())
        return True

    def on_btn_randomize_clicked(self, event):
        self.model.randomize()

    def on_auto_restrict_clicked(self, event):
        self.model.auto_restrict()

    def _launch_gui_updater(self, refiner):
        def _on_update_gui():
            if self.view is not None and refiner is not None:
                self.view.update_refinement_info(
                    refiner.history.last_residual,
                    refiner.status.message,
                    get_status()
                )
                return True
            else:
                return False
        return gobject.timeout_add(250, _on_update_gui)

    def _launch_refine_thread(self, refiner, gui_timeout_id):
        @run_when_idle
        def thread_completed(*args, **kwargs):
            """ Called when the refinement is completed """
            self.thread = None
            
            gobject.source_remove(gui_timeout_id)
            self.view.stop_spinner()
            
            # Make some plots:
            if self.model.make_psp_plots:
                self.view.update_refinement_status("Processing...")
                self.results_controller.generate_images()
            
            # Set the labels:
            self.results_controller.update_labels()
                
            # Hide our shit:
            self.view.hide_refinement_info()
            self.view.hide()
            
            # Show results:
            self.results_view.present()

        thread = CancellableThread(refiner.refine, thread_completed)
        thread.start()
        return thread

    def _connect_cancel_button(self, refiner, gui_timeout_id, thread):
        # Connect the cancel button (custom widget):
        def thread_cancelled(*args, **kwargs):
            """ Called when the refinement is cancelled by the user """
            gobject.source_remove(gui_timeout_id)
            self.view.stop_spinner()
            
            self.view.update_refinement_status("Cancelling...")
            thread.cancel()
            
            self.view.hide_refinement_info()
        self.view.connect_cancel_request(thread_cancelled)

    @DialogController.status_message("Refining mixture...", "refine_mixture")
    def on_refine_clicked(self, event):
        with self.model.mixture.needs_update.hold():
            with self.model.mixture.data_changed.hold():
                if len(self.model.mixture.specimens) > 0:
                    # Create the refiner object
                    with DialogFactory.error_dialog_handler(
                            "There was an error when creating the refinement setup:\n{}", 
                            parent=self.view.get_toplevel(), reraise=False):
                        refiner = self.model.get_refiner()

                        # Setup results controller
                        self.results_view = RefinerView(parent=self.view.parent)
                        self.results_controller = RefinerController(
                            refiner=refiner,
                            model=self.model,
                            view=self.results_view,
                            parent=self
                        )
    
                        # Gtk timeout loop for our GUI updating:
                        gui_timeout_id = self._launch_gui_updater(refiner)
                        
                        # This creates a thread that will run the refiner.refine method:
                        thread = self._launch_refine_thread(refiner, gui_timeout_id)
                        
                        # Connect the cancel button:
                        self._connect_cancel_button(refiner, gui_timeout_id, thread)
    
                        # Show the context updates in the gui:
                        self.view.show_refinement_info()
                        self.view.start_spinner()

                else:
                    DialogFactory.get_information_dialog(
                        "Cannot refine an empty mixture!", parent=self.view.get_toplevel()
                    ).run()

    pass # end of class