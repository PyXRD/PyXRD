# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Author: Mathijs Dumon
# This work is licensed under the Creative Commons Attribution-ShareAlike 3.0 Unported License. 
# To view a copy of this license, visit http://creativecommons.org/licenses/by-sa/3.0/ or send
# a letter to Creative Commons, 444 Castro Street, Suite 900, Mountain View, California, 94041, USA.

from fractions import Fraction

import gtk
import cairo
from matplotlib import rcParams
import matplotlib.mathtext as mathtext
import matplotlib

pbmt_cache = dict() #maybe use a weak ref dict or a slowly GC-ed one?
display = gtk.gdk.display_get_default()
screen = display.get_default_screen()
dpi = screen.get_resolution() or 96

def _handle_customs(text):
    if r"\larger" in text:
        fontsize = 20
    elif r"\large" in text:
        fontsize = 15
    else:
        fontsize = 10
    text = text.replace(r"\larger", r"").replace(r"\large", r"").replace(r"\newline", r"$\newline$")
    parts = text.split(r"\newline")
    while "$$" in parts: parts.remove("$$")    
    return parts, fontsize

def create_pb_from_mathtext(text, align='center', weight='heavy', color='b', style='normal'):
    global pbmt_cache
    global dpi
    if not text in pbmt_cache:       
       
        parts, fontsize = _handle_customs(text)
        
        pbs = []
        width = 0
        height = 0
        heights = []
        depth = 0

        #Temporarily set font properties:
        old_params = rcParams["font.weight"], rcParams["text.color"], rcParams["font.style"]
        rcParams["font.weight"] = weight
        rcParams["text.color"] = color
        rcParams["font.style"] = style
        #Create parser and load png fragments     
        parser = mathtext.MathTextParser("Bitmap")
        for part in parts:
            png_loader = gtk.gdk.PixbufLoader('png')
            parser.to_png(png_loader, part, dpi=dpi, fontsize=fontsize)        
            png_loader.close()
            pb = png_loader.get_pixbuf()
            w, h, depth = pb.get_width(), pb.get_height(), pb.get_bits_per_sample()
            width = max(width, w)
            height += h
            pbs.append((pb, w, h))     
        #Restore font properties
        rcParams["font.weight"], rcParams["text.color"], rcParams["font.style"] = old_params
        
        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
        cr = cairo.Context(surface)
        gdkcr = gtk.gdk.CairoContext(cr)

        gdkcr.save()        
        gdkcr.set_operator(cairo.OPERATOR_CLEAR)
        gdkcr.paint()
        gdkcr.restore()
        
        offsetx = 0
        offsety = 0
        for pb, w, h in pbs:
            if align=='center':
                offsetx = int((width - w)/2)
            if align=='left':
                offsetx = 0
            if align=='right':
                offsetx = int(width - w)
            gdkcr.set_source_pixbuf(pb, offsetx, offsety)
            gdkcr.rectangle(offsetx, offsety, w, h)
            gdkcr.paint()
            offsety += h
        del pbs
        
        pbmt_cache[text] = gtk.gdk.pixbuf_new_from_data(
            surface.get_data(), 
            gtk.gdk.COLORSPACE_RGB, True, 8,
            width, height, 
            surface.get_stride()
        )
    return pbmt_cache[text]
   
def create_image_from_mathtext(text, align='center', weight='heavy', color='b', style='normal'):
    image = gtk.Image()
    image.set_from_pixbuf(create_pb_from_mathtext(text, align=align))
    return image

### Some convenience functions:

def mt_frac(val):
    val = Fraction(val).limit_denominator()
    if val.denominator > 1:
        return r"\frac{%d}{%d}" % (val.numerator, val.denominator)
    else:
        return r"%d" % val.numerator

def mt_range(lower, name, upper):
    return r"\left({ %s \leq %s \leq %s }\right)" % (mt_frac(lower), name, mt_frac(upper))
    







    

