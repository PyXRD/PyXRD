# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Author: Mathijs Dumon
# This work is licensed under the Creative Commons Attribution-ShareAlike 3.0 Unported License. 
# To view a copy of this license, visit http://creativecommons.org/licenses/by-sa/3.0/ or send
# a letter to Creative Commons, 444 Castro Street, Suite 900, Mountain View, California, 94041, USA.

from generic.views import BaseView, HasChildView

class EditPhaseView(BaseView, HasChildView):
    title = "Edit Phases"
    builder = "phases/glade/phase.glade"
    top = "edit_phase"

    layer_view = None    
    layer_view_container = "layer_atoms_container"

    interlayer_view = None
    interlayer_view_container = "interlayer_atoms_container"
        
    def set_layer_view(self, view):
        print "EditPhaseView.set_layer_view() %s" % view
        self.layer_view = view
        return self._add_child_view(view, self[self.layer_view_container])
        
    def set_interlayer_view(self, view):
        print "EditPhaseView.set_interlayer_view() %s" % view
        self.interlayer_view = view
        return self._add_child_view(view, self[self.interlayer_view_container])
        
class EditLayerView(BaseView):
    builder = "phases/glade/layer.glade"
    top = "edit_layer"
