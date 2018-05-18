# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import gi
gi.require_version('Gtk', '3.0') # @UndefinedVariable
from gi.repository import Gtk, Gdk, GdkPixbuf  # @UnresolvedImport

try:
    gi.require_foreign("cairo")
except ImportError:
    print("No pycairo integration :(")

import cairo

from matplotlib import rcParams
import matplotlib.mathtext as mathtext

pbmt_cache = dict() # maybe use a weak ref dict or a slowly GC-ed one?
display = Gdk.Display.get_default()  # @UndefinedVariable
screen = display.get_default_screen()
dpi = screen.get_resolution() or 96

def create_pb_from_mathtext(text, align='center', weight='heavy', color='b', style='normal'):
    
    from pyxrd.generic.models.mathtext_support import _handle_customs
    
    global pbmt_cache
    global dpi
    if not text in pbmt_cache:

        parts, fontsize = _handle_customs(text)

        pbs = []
        width = 0
        height = 0
        # heights = []

        # Temporarily set font properties:
        old_params = rcParams["font.weight"], rcParams["text.color"], rcParams["font.style"]
        rcParams["font.weight"] = weight
        rcParams["text.color"] = color
        rcParams["font.style"] = style
        
        # Create parser and load png fragments
        parser = mathtext.MathTextParser("Bitmap")
        for part in parts:
            png_loader = GdkPixbuf.PixbufLoader.new_with_type('png')  # @UndefinedVariable
            parser.to_png(png_loader, part, dpi=dpi, fontsize=fontsize)
            png_loader.close()
            pb = png_loader.get_pixbuf()
            w, h = pb.get_width(), pb.get_height()
            width = max(width, w)
            height += h
            pbs.append((pb, w, h))
        # Restore font properties
        rcParams["font.weight"], rcParams["text.color"], rcParams["font.style"] = old_params

        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
        cr = cairo.Context(surface)

        cr.save()
        cr.set_operator(cairo.OPERATOR_CLEAR)
        cr.paint()
        cr.restore()

        cr.save()
        offsetx = 0
        offsety = 0
        for pb, w, h in pbs:
            if align == 'center':
                offsetx = int((width - w) / 2)
            if align == 'left':
                offsetx = 0
            if align == 'right':
                offsetx = int(width - w)
            Gdk.cairo_set_source_pixbuf(cr, pb, offsetx, offsety)
            cr.rectangle(offsetx, offsety, w, h)
            cr.paint()
            offsety += h
        del pbs
        cr.restore()

        pbmt_cache[text] = Gdk.pixbuf_get_from_surface(surface, 0, 0, width, height)
        
    return pbmt_cache[text]

def create_image_from_mathtext(text, align='center', weight='heavy', color='b', style='normal'):
    image = Gtk.Image()
    image.set_from_pixbuf(create_pb_from_mathtext(text, align=align))
    return image
