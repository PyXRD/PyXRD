# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

from pkg_resources import resource_filename # @UnresolvedImport

import gtk
import gobject
from time import time, sleep
from pyxrd.application.icons import get_icon_list

def scale_ratio(src_width, src_height, dest_width, dest_height):
    """Return a size fitting into dest preserving src's aspect ratio."""
    if src_height > dest_height:
        if src_width > dest_width:
            ratio = min(float(dest_width) / src_width,
                        float(dest_height) / src_height)
        else:
            ratio = float(dest_height) / src_height
    elif src_width > dest_width:
        ratio = float(dest_width) / src_width
    else:
        ratio = 1
    return int(ratio * src_width), int(ratio * src_height)

class ScalableImage(gtk.Image):
    """A gtk.Image that rescales to fit whatever size is available.

    Only Pixbuf data is supported; it can be loaded from a file or
    passed directly.
    """
    def __init__(self, pixbuf=None):
        super(ScalableImage, self).__init__()
        self._pixbuf = None
        self.connect('size-allocate', self._on_size_allocate)
        self.set_size_request(1, 1)
        self._hyper_id = None
        if pixbuf is not None:
            self.set_from_pixbuf(pixbuf)

    def _on_timeout_hyper(self):
        """Perform a delayed high-quality scale."""
        self._hyper_id = None
        allocation = self.get_allocation()
        target_width, target_height = scale_ratio(
            self._pixbuf.get_width(), self._pixbuf.get_height(),
            allocation.width, allocation.height)
        if target_width > 0 and target_height > 0:
            pixbuf = self._pixbuf.scale_simple(
                target_width, target_height, gtk.gdk.INTERP_HYPER) # @UndefinedVariable
            super(ScalableImage, self).set_from_pixbuf(pixbuf)

    def _on_size_allocate(self, image, allocation, force=False):
        """Scale the internal pixbuf copy to a new size."""
        if self._pixbuf is None:
            return
        pix_width = self._pixbuf.get_width()
        pix_height = self._pixbuf.get_height()
        target_width, target_height = scale_ratio(
            pix_width, pix_height, allocation.width, allocation.height)
        old_pix = self.get_pixbuf()
        if target_width < pix_width or target_height < pix_height:
            if (force or not old_pix
                or old_pix.get_width() != target_width
                or old_pix.get_height() != target_height):
                # If we're forcing an update we have a new image,
                # since that's a "big" event we can afford to
                # hyper-scale right away. On the other hand if it's
                # not a forced update the window just resized, that
                # needs responsiveness immediately, so delay the hyper
                # scale until the window is stationary for at least
                # 1/10 of a second.
                if self._hyper_id:
                    gobject.source_remove(self._hyper_id)
                    self._hyper_id = None
                if target_width > 0 and target_height > 0:
                    pixbuf = self._pixbuf.scale_simple(
                        target_width, target_height,
                        gtk.gdk.INTERP_HYPER if force else gtk.gdk.INTERP_NEAREST) # @UndefinedVariable
                    if not force:
                        self._hyper_id = gobject.timeout_add(100, self._on_timeout_hyper)
                    super(ScalableImage, self).set_from_pixbuf(pixbuf)
        elif old_pix != self._pixbuf:
            if self._hyper_id:
                gobject.source_remove(self._hyper_id)
                self._hyper_id = None
            super(ScalableImage, self).set_from_pixbuf(self._pixbuf)

    def set_from_file(self, filename):
        """Set the image by loading a file."""
        pixbuf = gtk.gdk.pixbuf_new_from_file(filename) # @UndefinedVariable
        self.set_from_pixbuf(pixbuf)

    def set_from_pixbuf(self, pixbuf):
        """Set the image from a gtk.gdk.Pixbuf."""
        self._pixbuf = pixbuf
        self._on_size_allocate(None, self.get_allocation(), force=True)

    def __not_implemented(self, *args):
        """This gtk.Image storage type is not supported."""
        raise NotImplementedError("only pixbuf images are currently supported")

    set_from_animation = __not_implemented
    set_from_gicon = __not_implemented
    set_from_icon_name = __not_implemented
    set_from_icon_set = __not_implemented
    set_from_image = __not_implemented
    set_from_pixmap = __not_implemented
    set_from_stock = __not_implemented

class SplashScreen(object):
    def __init__(self, filename, version=""):
        # DONT connect 'destroy' event here!
        gtk.window_set_auto_startup_notification(False)
        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window.set_icon_list(*get_icon_list())
        self.window.set_title('PyXRD')
        self.window.set_position(gtk.WIN_POS_CENTER)
        self.window.set_decorated(False)
        self.window.set_resizable(False)
        self.window.set_border_width(1)
        self.window.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse('black')) # @UndefinedVariable

        ebox = gtk.EventBox() # prevent the black color from showing through...
        self.window.add(ebox)

        main_vbox = gtk.VBox(False, 1)
        main_vbox.set_border_width(10)
        ebox.add(main_vbox)

        self.img = ScalableImage()
        self.img.set_from_file(filename)
        self.img.set_size_request(500, 300)
        main_vbox.pack_start(self.img, True, True)

        self.lbl = gtk.Label()
        self.lbl.set_markup("<span size=\"larger\"><b>Loading ...</b></span>")
        self.lbl.set_alignment(0.5, 0.5)
        main_vbox.pack_end(self.lbl, True, True)

        self.version_lbl = gtk.Label()
        self.version_lbl.set_markup("<i>Version %s</i>" % version)
        self.version_lbl.set_alignment(0.5, 0.5)
        main_vbox.pack_end(self.version_lbl, True, True)

        self.window.show_all()
        while gtk.events_pending():
            gtk.main_iteration()
        self.start_time = time()

    def set_message(self, message):
        self.lbl.set_markup("<span size=\"larger\"><b>%s</b></span>" % message)
        while gtk.events_pending():
            gtk.main_iteration()

    def close(self):
        gtk.window_set_auto_startup_notification(True)
        while (max(1.5 - (time() - self.start_time), 0) != 0):
            sleep(0.1)
            if gtk.events_pending():
                gtk.main_iteration()
        self.window.destroy()


    pass # end of class
