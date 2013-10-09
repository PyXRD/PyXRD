# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

from fractions import Fraction

import gtk
import cairo
from matplotlib import rcParams
import matplotlib.mathtext as mathtext

pbmt_cache = dict() # maybe use a weak ref dict or a slowly GC-ed one?
display = gtk.gdk.display_get_default()
screen = display.get_default_screen()
dpi = screen.get_resolution() or 96

def _handle_customs(text):
    text = text.decode('utf-8')

    if r"\larger" in text:
        fontsize = 20
    elif r"\large" in text:
        fontsize = 15
    else:
        fontsize = 10

    replacers = [
        (ur"²", r"$^{2}$"),
        (ur"³", r"$^{3}$"),
        (ur"α", r"$\alpha$"),
        (ur"β", r"$\beta$"),
        (ur"γ", r"$\gamma$"),
        (ur"δ", r"$\delta$"),
        (ur"γ", r"$\digamma$"),
        (ur"η", r"$\eta$"),
        (ur"ι", r"$\iota$"),
        (ur"κ", r"$\kappa$"),
        (ur"λ", r"$\lambda$"),
        (ur"μ", r"$\mu$"),
        (ur"ω", r"$\omega$"),
        (ur"φ", r"$\phi$"),
        (ur"π", r"$\pi$"),
        (ur"ψ", r"$\psi$"),
        (ur"ρ", r"$\rho$"),
        (ur"σ", r"$\sigma$"),
        (ur"τ", r"$\tau$"),
        (ur"θ", r"$\theta$"),
        (ur"υ", r"$\upsilon$"),
        (ur"ξ", r"$\xi$"),
        (ur"ζ", r"$\zeta$"),
        (r"\larger", r""),
        (r"\large", r""),
        (r"\newline", r"$\newline$"),
    ]
    for val, rep in replacers:
        text = text.replace(val, rep)

    parts = text.replace("$$", "").split(r"\newline")
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

        # Temporarily set font properties:
        old_params = rcParams["font.weight"], rcParams["text.color"], rcParams["font.style"]
        rcParams["font.weight"] = weight
        rcParams["text.color"] = color
        rcParams["font.style"] = style
        # Create parser and load png fragments
        parser = mathtext.MathTextParser("Bitmap")
        for part in parts:
            png_loader = gtk.gdk.PixbufLoader('png')
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
        gdkcr = gtk.gdk.CairoContext(cr)

        gdkcr.save()
        gdkcr.set_operator(cairo.OPERATOR_CLEAR)
        gdkcr.paint()
        gdkcr.restore()

        offsetx = 0
        offsety = 0
        for pb, w, h in pbs:
            if align == 'center':
                offsetx = int((width - w) / 2)
            if align == 'left':
                offsetx = 0
            if align == 'right':
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

# ## Some convenience functions:

def mt_frac(val):
    val = Fraction(val).limit_denominator()
    if val.denominator > 1:
        return r"\frac{%d}{%d}" % (val.numerator, val.denominator)
    else:
        return r"%d" % val.numerator

def mt_range(lower, name, upper):
    return r"\left({ %s \leq %s \leq %s }\right)" % (mt_frac(lower), name, mt_frac(upper))

def get_plot_safe(expression):
    return r"".join(_handle_customs(expression)[0])








