#  Author: Roberto Cavada <roboogle@gmail.com>
#
#  Copyright (c) 2007 by Roberto Cavada
#
#  pygtkmvc is free software; you can redistribute it and/or
#  modify it under the terms of the GNU Lesser General Public
#  License as published by the Free Software Foundation; either
#  version 2 of the License, or (at your option) any later version.
#
#  pygtkmvc is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#  Lesser General Public License for more details.
#
#  You should have received a copy of the GNU Lesser General Public
#  License along with this library; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor,
#  Boston, MA 02110, USA.
#
#  For more information on pygtkmvc see <http://pygtkmvc.sourceforge.net>
#  or email to the author Roberto Cavada <roboogle@gmail.com>.
#  Please report bugs to <roboogle@gmail.com>.

from gtkmvc import Controller
from gtkmvc.adapters import Adapter

import os
import gtk


class ProgenCtrl (Controller):

    def register_view(self, view):
        self.view['window_appl'].connect('delete-event',
                                         self.on_window_delete)
        self.__enable_generate()
        return

    def register_adapters(self):
        self.adapt("name")
        self.adapt("author")
        self.adapt("email")
        self.adapt("complex")
        self.adapt("dist_gtkmvc", "cb_gtkmvc")
        self.adapt("copyright")
        self.adapt("glade")
        

        a = Adapter(self.model, "destdir")
        a.connect_widget(self.view['filechooserbutton'],
                         gtk.FileChooser.get_current_folder,
                         lambda w,p: w.set_current_folder(os.path.abspath(p)), 
                         "current-folder-changed")
        self.adapt(a)
        return

    # signals
    def on_window_delete(self, w, e): gtk.main_quit(); return True

    def on_button_next_clicked(self, b):
        self.view.next_page()
        return

    def on_button_prev_clicked(self, b):
        self.view.prev_page()
        return

    def on_button_generate_clicked(self, b):
        # sets some more properties:
        if not self.view['cb_std_header'].get_active():
            buf = self.view['tv_header'].get_buffer()
            self.model.src_header = buf.get_text(*buf.get_bounds())
            pass
        
        buf = self.view['tv_comment'].get_buffer()
        self.model.other_comment = buf.get_text(*buf.get_bounds())

        try: res = self.model.generate_project()
        except Exception, e:
            msg = "An error occured dring project generation"
            self.log(str(e))
            pass
        else:
            if res: msg = "Project generation was successful"
            else: msg = "Project already exists, no actions were taken"
            pass

        self.view['label_res'].set_markup("<big><b>%s</b></big>" % msg)
        self.view['notebook_appl'].set_current_page(1)
        return

    def log(self, msg):
        buf = self.view['tv_res'].get_buffer()
        buf.insert(buf.get_end_iter(), msg+"\n")
        return

    def on_cb_std_header_toggled(self, cb):
        self.view['tv_header'].set_sensitive(not cb.get_active())
        return

    # Properties
    @Controller.observe("name", assign=True)
    @Controller.observe("author", assign=True)
    def name_change(self, m, pname, info):
        self.__enable_generate()
        return

    # private
    def __enable_generate(self):
        enable = self.model.name not in ("",None) and \
                 self.model.author not in ("",None)
        self.view['button_generate'].set_sensitive(enable)
        self.view['button_next'].set_sensitive(enable)
        return
    
    pass # end of class
