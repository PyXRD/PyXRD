# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

from generic.views import DialogView

class ProjectView(DialogView):
    title = "Edit Project"
    subview_builder = "project/glade/project.glade"
    subview_toplevel = "nbk_edit_project"
    resizable = False
    
    __widgets_to_hide__ = (
        "project_display_calc_color",
        "lbl_calccolor",
        "project_display_calc_lw",
        "calc_lw_lbl")

    def __init__(self, *args, **kwargs):
        DialogView.__init__(self, *args, **kwargs)
        self["specimen_popup"].set_accel_group(self.parent["PyXRDGroup"])
        self["popup_menu_item_add_specimen"].set_related_action(self.parent["add_specimen"])
        self["popup_menu_item_edit_specimen"].set_related_action(self.parent["edit_specimen"])
        self["popup_menu_item_import_specimens"].set_related_action(self.parent["import_specimens"])
        self["popup_menu_item_replace_data"].set_related_action(self.parent["replace_specimen_data"])
        self["popup_menu_item_export_data"].set_related_action(self.parent["export_specimen_data"])
        self["popup_menu_item_del_specimen"].set_related_action(self.parent["del_specimen"])
        
    def present(self, *args, **kwargs):
        super(ProjectView, self).present(*args, **kwargs)
        self["nbk_edit_project"].set_current_page(0)    
        
    def specimens_popup(self, event):
        self["specimen_popup"].popup(None, None, None, event.button, event.time)     
        
    pass #end of class
