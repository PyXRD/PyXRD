# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Author: Mathijs Dumon
# This work is licensed under the Creative Commons Attribution-ShareAlike 3.0 Unported License. 
# To view a copy of this license, visit http://creativecommons.org/licenses/by-sa/3.0/ or send
# a letter to Creative Commons, 444 Castro Street, Suite 900, Mountain View, California, 94041, USA.

from generic.views import BaseView, HasChildView, DialogView, NoneView

class EditPhaseView(BaseView, HasChildView):
    title = "Edit Phases"
    builder = "phases/glade/phase.glade"
    top = "edit_phase"

    components_view = None    
    components_view_container = "comp_container"
    
    probabilities_view = None    
    probabilities_view_container = "prob_container"
    
    def set_components_view(self, view):
        self.components_view = view
        if view != None:
            self._add_child_view(view.get_top_widget(), self[self.components_view_container])
        return view
        
    def set_probabilities_view(self, view):
        self.probabilities_view = view
        if view != None:
            self._add_child_view(view.get_top_widget(), self[self.probabilities_view_container])
        return view
    
class InlineObjectListStoreView(BaseView):
    builder = "phases/glade/inline_ols.glade"
    top = "edit_item"
    
    @property
    def treeview_widget(self):
        return self['tvw_items']
    
    @property   
    def del_item_widget(self):
        return self['btn_del_item']

    @property
    def add_item_widget(self):
        return self['btn_add_item']
        
    @property
    def export_items_widget(self):
        return self['btn_export_item']


class EditComponentView(BaseView, HasChildView):
    title = "Edit Component"
    builder = "phases/glade/component.glade"
    top = "edit_component"

    layer_view = None    
    layer_view_container = "layer_atoms_container"

    interlayer_view = None
    interlayer_view_container = "interlayer_atoms_container"
    
    atom_ratios_view = None
    atom_ratios_view_container = "atom_ratios_container"    

    ucpa_view = None    
    ucpa_view_container = "ucp_a_container"

    ucpb_view = None    
    ucpb_view_container = "ucp_b_container"

        
    def __init__(self, *args, **kwargs):
        BaseView.__init__(self, *args, **kwargs)
        
    def set_layer_view(self, view):
        self.layer_view = view
        return self._add_child_view(view, self[self.layer_view_container])
        
    def set_atom_ratios_view(self, view):
        self.atom_ratios_view = view
        return self._add_child_view(view, self[self.atom_ratios_view_container])
        
    def set_interlayer_view(self, view):
        self.interlayer_view = view
        return self._add_child_view(view, self[self.interlayer_view_container])
        
    def set_ucpa_view(self, view):
        self.ucpa_view = view
        return self._add_child_view(view, self[self.ucpa_view_container])
        
    def set_ucpb_view(self, view):
        self.ucpb_view = view
        return self._add_child_view(view, self[self.ucpb_view_container])
   
class EditUnitCellPropertyView(BaseView):
    builder = "phases/glade/unit_cell_prop.glade"
    top = "box_ucf"
    
class AddPhaseView(DialogView):
    title = "Add Phase"
    subview_builder = "phases/glade/addphase.glade"
    subview_toplevel = "add_phase_box"
       
    def __init__(self, *args, **kwargs):
        DialogView.__init__(self, *args, **kwargs)
       
    def get_G(self):
        return int(self["data_G"].get_value_as_int())
        
    def get_R(self):
        return int(self["data_R"].get_value_as_int())
