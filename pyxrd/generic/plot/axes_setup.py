# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

from functools import partial

import numpy as np
from matplotlib.ticker import FixedLocator, FixedFormatter

from pyxrd.calculations.goniometer import get_2t_from_nm, get_nm_from_2t
from pyxrd.data import settings

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

def set_nm_ticks(axis, wavelength, xmin, xmax):
    """
        Sets the tick positions and labels for a nanometer x-axes using
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
    helper = axis.get_helper()

    helper.axis.minor.locator = FixedLocator(minor_ticks_pos)
    helper.axis.minor.formatter = FixedFormatter([""] * len(minor_ticks_pos))

    helper.axis.major.locator = FixedLocator(major_ticks_pos)
    helper.axis.major.formatter = FixedFormatter(major_ticks_labels)

    pass #end of func

def update_xaxis(axes, title=u'Angle (°2$\\theta$)', weight='heavy',
            rotation=0, ha="center", va="center",
            pad=0, size=16, nm_ticks=False, wavelength=None):

    axis = axes.axis["bottom"]

    axis.major_ticks.set_tick_out(True)
    axis.minor_ticks.set_tick_out(True)

    axis.label.set_text(title)
    axis.label.set_weight(weight)
    axis.label.set_size(size)
    axis.label.set_pad(pad)

    axis.major_ticklabels.set_visible(True)
    axis.major_ticklabels.set_rotation(rotation)
    axis.major_ticklabels.set_ha(ha)
    axis.major_ticklabels.set_va(va)

    if nm_ticks: set_nm_ticks(axis, wavelength, *axes.get_xlim())

def update_lim(axes, pos_setup, project):
    # Relimit and autoscale the view:
    axes.relim()
    axes.autoscale_view(tight=True)
    xmin, xmax = axes.get_xlim()

    axes.set_ylim(bottom=0, auto=True)

    # Adjust x limits if needed:
    if project is None or project.axes_xlimit == 0:
        xmin, xmax = max(xmin, 0.0), max(xmax, 20.0)
    else:
        xmin, xmax = max(project.axes_xmin, 0.0), project.axes_xmax
    axes.set_xlim(left=xmin, right=xmax, auto=False)


    # Adjust y limits if needed
    if project is not None and project.axes_ylimit != 0:
        scale, _ = project.get_scale_factor()

        ymin = max(project.axes_ymin, 0.0)
        ymax = project.axes_ymax
        if ymax <= 0:
            ymax = axes.get_ylim()[1]
        else:
            ymax = ymax * scale
        ymin = ymin * scale

        axes.set_ylim(bottom=ymin, top=ymax, auto=False)

    # Update plot position setup:
    pos_setup.xdiff = xmax - xmin
    pos_setup.xstretch = project.axes_xstretch if project is not None else False

def update_axes(axes, pos_setup, project, specimens):
    """
        Internal generic plot update method.
    """

    update_lim(axes, pos_setup, project)

    axes.axis["right"].set_visible(False)
    axes.axis["top"].set_visible(False)
    axes.get_xaxis().tick_bottom()
    axes.get_yaxis().tick_left()
    if project is None or not project.axes_yvisible:
        axes.axis["left"].set_visible(False)
    else:
        axes.axis["left"].set_visible(True)

    axes.set_position(pos_setup.position)

    if project is not None and project.axes_dspacing:
        if specimens is None or len(specimens) == 0:
            wavelength = settings.AXES_DEFAULT_WAVELENGTH
        else:
            wavelength = specimens[0].goniometer.wavelength
        update_xaxis(axes,
            title=u'd (nm)',
            rotation=-90, ha="left", pad=25,
            nm_ticks=True, wavelength=wavelength,
        )
    else:
        update_xaxis(axes)

class PositionSetup(object):
    """
        Keeps track of the positioning of a plot
    """
    left = settings.PLOT_LEFT
    top = settings.PLOT_TOP
    bottom = settings.PLOT_BOTTOM

    xdiff = 20
    xstretch = settings.AXES_XSTRETCH

    @property
    def right(self):
        return self.left + self.get_plot_width()

    @property
    def width(self):
        MAX_PLOT_WIDTH = settings.MAX_PLOT_RIGHT - self.left
        if self.xstretch:
            return MAX_PLOT_WIDTH
        else:
            return min((self.xdiff / 70), 1.0) * MAX_PLOT_WIDTH

    @property
    def height(self):
        return abs(self.top - self.bottom)

    @property
    def position(self):
        return [self.left, self.bottom, self.width, self.height]

    pass #end of class
