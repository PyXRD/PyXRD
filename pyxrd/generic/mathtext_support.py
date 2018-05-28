# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import logging
logger = logging.getLogger(__name__)

import re
from fractions import Fraction

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GdkPixbuf

try:
    gi.require_foreign("cairo")
except ImportError as orig:
    try:
        import cairocffi as cairo
    except ImportError as snd:
        logger.error("No cairo integration :(")
        raise snd from orig 

from matplotlib import rcParams
import matplotlib.mathtext as mathtext

pbmt_cache = dict() # maybe use a weak ref dict or a slowly GC-ed one?
display = Gdk.Display.get_default()  # @UndefinedVariable
screen = display.get_default_screen()
dpi = screen.get_resolution() or 96

def create_pb_from_mathtext(text, align='center', weight='heavy', color='b', style='normal'):
    """
        Create a Gdk.Pixbuf from a mathtext string
    """
    
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
    """
        Create a Gtk.Image widget from a mathtext string
    """
    
    image = Gtk.Image()
    image.set_from_pixbuf(create_pb_from_mathtext(text, align=align))
    return image

###############################
# Some convenience functions: #
###############################
def _handle_customs(text):
    text = text.decode('utf-8')

    if r"\larger" in text:
        fontsize = 20
    elif r"\large" in text:
        fontsize = 15
    else:
        fontsize = 10

    replacers = [
        (r"²", r"$^{2}$"),
        (r"³", r"$^{3}$"),
        (r"α", r"$\alpha$"),
        (r"β", r"$\beta$"),
        (r"γ", r"$\gamma$"),
        (r"δ", r"$\delta$"),
        (r"γ", r"$\digamma$"),
        (r"η", r"$\eta$"),
        (r"ι", r"$\iota$"),
        (r"κ", r"$\kappa$"),
        (r"λ", r"$\lambda$"),
        (r"μ", r"$\mu$"),
        (r"ω", r"$\omega$"),
        (r"φ", r"$\phi$"),
        (r"π", r"$\pi$"),
        (r"ψ", r"$\psi$"),
        (r"ρ", r"$\rho$"),
        (r"σ", r"$\sigma$"),
        (r"τ", r"$\tau$"),
        (r"θ", r"$\theta$"),
        (r"υ", r"$\upsilon$"),
        (r"ξ", r"$\xi$"),
        (r"ζ", r"$\zeta$"),
        (r"\larger", r""),
        (r"\large", r""),
        (r"\newline", r"$\newline$"),
    ]
    for val, rep in replacers:
        text = text.replace(val, rep)

    parts = text.replace("$$", "").split(r"\newline")
    while "$$" in parts: parts.remove("$$")
    return parts, fontsize

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

def get_string_safe(expression):

    replacers = [
        (r"$", r""),
        (r"\larger", r""),
        (r"\left", r""),
        (r"\right", r""),
        (r"\leq", r"≤"),
        (r"\geq", r"≥"),
        (r"\large", r""),
        (r"\newline", "\n"),
    ]
    for val, rep in replacers:
        expression = expression.replace(val, rep)

    regex_replacers = [
        (r"\\sum_\{(\S+)\}\^\{(\S+)\}", r"Σ(\1->\2)"),
        (r"(\S+)_(?:\{(\S+)\})", r"\1\2"),
        (r"(\S+)_(\S+)", r"\1\2"),
        (r"\\frac\{([^}])\}\{([^}])\}", r"\1\\\2"), # single characters
        (r"\\frac\{(.+)\}\{(.+)\}", r"(\1)\\(\2)"), # multi charachters
        (r"\(\{([^})]+)\}\)", r"(\1)")
    ]
    for regexpr, sub in regex_replacers:
        pattern = re.compile(regexpr)
        expression = pattern.sub(sub, expression)

    return expression