# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

from functools import partial
import numpy as np

from pyxrd.calculations.goniometer import get_2t_from_nm, get_nm_from_2t

def _get_ticks():

    def create_flat_array(*arrays):
        arr = np.array([], dtype=float)
        for new_arr in arrays:
            arr = np.append(arr, new_arr)
        return arr

    minor_ticks_nm = create_flat_array(
        np.arange(6.0, 2.0, -0.5),
        np.arange(2.0, 1.0, -0.1),
        np.arange(1.0, 0.8, -0.05),
        np.arange(0.80, 0.00, -0.01)
    )
    major_ticks_nm = create_flat_array(
        np.arange(6.0, 1.0, -1.0),
        np.arange(2.0, 1.0, -0.5),
        np.arange(1.0, 0.8, -0.1),
        np.arange(0.80, 0.00, -0.05)
    )
    label_ticks_nm = create_flat_array(
        np.arange(6.0, 1.0, -2.0),
        np.arange(2.0, 1.0, -0.5),
        np.arange(1.0, 0.8, -0.1),
        np.arange(0.80, 0.40, -0.1),
        np.arange(0.40, 0.00, -0.05)
    )

    return minor_ticks_nm, major_ticks_nm, label_ticks_nm


def update_lim(plot, project=None):
    plot.relim()
    plot.autoscale_view()

    plot.set_ylim(bottom=0, auto=True)

    # Adjust limits if needed:
    xmin, xmax = 0.0, 20.0
    if project is None or project.axes_xlimit == 0:
        xmin, xmax = plot.get_xlim()
        xmin, xmax = max(xmin, 0.0), max(xmax, 20.0)
    else:
        xmin, xmax = max(project.axes_xmin, 0.0), project.axes_xmax
    plot.set_xlim(left=xmin, right=xmax, auto=False)

    if project is not None and project.axes_ylimit != 0:
        scale, _ = project.get_scale_factor()

        ymin = max(project.axes_ymin, 0.0)
        ymax = project.axes_ymax
        if ymax <= 0:
            ymax = plot.get_ylim()[1]
        else:
            ymax = ymax * scale
        ymin = ymin * scale

        plot.set_ylim(bottom=ymin, top=ymax, auto=False)

def set_nm_ticks(plot, wavelength, xmin, xmax):
    """
        Sets the tick positions and labels for a nanomter x-axes using
        the given lower & upper limits and the wavelength
    """

    np_nm2a = np.vectorize(partial(get_2t_from_nm, wavelength=wavelength))

    def get_tick_labels(a, b):
        def in_close(value, arr):
            for val in arr:
                if np.isclose(value, val):
                    return True
            return False
        return [ "%g" % val if in_close(val, b) else "" for val in a ]

    minor_ticks_nm, major_ticks_nm, label_ticks_nm = _get_ticks()

    dmax = min(get_nm_from_2t(xmin, wavelength), 100) #limit this so we don't get an "infinite" scale
    dmin = get_nm_from_2t(xmax, wavelength)

    # Extract the part we need:
    selector = (minor_ticks_nm >= dmin) & (minor_ticks_nm <= dmax)
    minor_ticks_pos = np_nm2a(minor_ticks_nm[selector])
    selector = (major_ticks_nm >= dmin) & (major_ticks_nm <= dmax)
    major_ticks_pos = np_nm2a(major_ticks_nm[selector])

    major_ticks_labels = get_tick_labels(major_ticks_nm[selector], label_ticks_nm)

    # Set the ticks
    plot.set_xticks(minor_ticks_pos, minor=True)
    plot.set_xticks(major_ticks_pos, minor=False)

    plot.set_xticklabels(major_ticks_labels)
