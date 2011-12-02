# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Author: Mathijs Dumon
# This work is licensed under the Creative Commons Attribution-ShareAlike 3.0 Unported License. 
# To view a copy of this license, visit http://creativecommons.org/licenses/by-sa/3.0/ or send
# a letter to Creative Commons, 444 Castro Street, Suite 900, Mountain View, California, 94041, USA.

import gtk
from generic.views import DialogView

class GoniometerView (DialogView):
    title = "Edit Goniometer"
    subview_builder = "goniometer/glade/goniometer.glade"
    subview_toplevel = "edit_goniometer"
