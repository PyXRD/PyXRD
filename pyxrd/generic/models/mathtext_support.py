# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import re
from fractions import Fraction

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





