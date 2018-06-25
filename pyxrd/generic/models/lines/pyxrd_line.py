# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import logging
logger = logging.getLogger(__name__)

import numpy as np
from scipy import stats
from scipy.interpolate import interp1d

from mvc.models.properties import (
    StringProperty, BoolProperty, FloatProperty,
    StringChoiceProperty, SignalMixin, ListProperty
)

from pyxrd.data import settings

from pyxrd.generic.utils import not_none
from pyxrd.generic.io.custom_io import storables
from pyxrd.generic.models.properties import InheritableMixin
from pyxrd.calculations.peak_detection import multi_peakdetect

from .storable_xy_data import StorableXYData

#from pyxrd.file_parsers.ascii_parser import ASCIIParser

@storables.register()
class PyXRDLine(StorableXYData):
    """
        A PyXRDLine is an abstract attribute holder for a real 'Line' object,
        whatever the plotting library used may be. Attributes are line width and
        color.        
    """

    # MODEL INTEL:
    class Meta(StorableXYData.Meta):
        store_id = "PyXRDLine"

    # OBSERVABLE PROPERTIES:

    #: The line label
    label = StringProperty(
        default="", text="Label", persistent=True
    )

    #: The line color
    color = StringProperty(
        default="#000000", text="Label",
        visible=True, persistent=True, widget_type="color",
        inherit_flag="inherit_color", inherit_from="parent.parent.display_exp_color",
        signal_name="visuals_changed",
        mix_with=(InheritableMixin, SignalMixin)
    )

    #: Flag indicating whether to use the grandparents color yes/no
    inherit_color = BoolProperty(
        default=True, text="Inherit color",
        visible=True, persistent=True,
        signal_name="visuals_changed", mix_with=(SignalMixin,)
    )

    #: The linewidth in points
    lw = FloatProperty(
        default=2.0, text="Linewidth",
        visible=True, persistent=True, widget_type="spin",
        inherit_flag="inherit_lw", inherit_from="parent.parent.display_exp_lw",
        signal_name="visuals_changed",
        mix_with=(InheritableMixin, SignalMixin),
    )

    #: Flag indicating whether to use the grandparents linewidth yes/no
    inherit_lw = BoolProperty(
        default=True, text="Inherit linewidth",
        visible=True, persistent=True,
        signal_name="visuals_changed", mix_with=(SignalMixin,),
    )

    #: A short string describing the (matplotlib) linestyle
    ls = StringChoiceProperty(
        default=settings.EXPERIMENTAL_LINESTYLE, text="Linestyle",
        visible=True, persistent=True, choices=settings.PATTERN_LINE_STYLES,
        mix_with=(InheritableMixin, SignalMixin,), signal_name="visuals_changed",
        inherit_flag="inherit_ls", inherit_from="parent.parent.display_exp_ls",
    )

    #: Flag indicating whether to use the grandparents linestyle yes/no
    inherit_ls = BoolProperty(
        default=True, text="Inherit linestyle",
        visible=True, persistent=True,
        mix_with=(SignalMixin,), signal_name="visuals_changed"
    )

    #: A short string describing the (matplotlib) marker
    marker = StringChoiceProperty(
        default=settings.EXPERIMENTAL_MARKER, text="Marker",
        visible=True, persistent=True, choices=settings.PATTERN_MARKERS,
        mix_with=(InheritableMixin, SignalMixin,), signal_name="visuals_changed",
        inherit_flag="inherit_marker", inherit_from="parent.parent.display_exp_marker",
    )

    #: Flag indicating whether to use the grandparents linewidth yes/no
    inherit_marker = BoolProperty(
        default=True, text="Inherit marker",
        visible=True, persistent=True,
        mix_with=(SignalMixin,), signal_name="visuals_changed",
    )
    
    #: z-data (e.g. relative humidity, temperature, for multi-column 'lines')
    z_data = ListProperty(
        default=None, text="Z data", data_type=float,
        persistent=True, visible=False
    ) 

    # REGULAR PROPERTIES:   
    @property
    def max_display_y(self):
        if self.num_columns > 2:
            # If there's several y-columns, check if we have z-data associated with them
            # if so, it is a 2D pattern, otherwise this is a multi-line pattern
            if len(self.z_data) > 2:
                return np.max(self.z_data)
            else:
                return self.max_y
        else:
            # If there's a single comumn of y-data, just get the max value
            return self.max_y

    @property
    def min_intensity(self):
        if self.num_columns > 2:
            return np.min(self.z_data)
        else:        
            return self.min_y

    @property
    def abs_max_intensity(self):
        return self.abs_max_y

    # ------------------------------------------------------------
    #      Initialisation and other internals
    # ------------------------------------------------------------
    def __init__(self, *args, **kwargs):
        """
            Valid keyword arguments for a PyXRDLine are:
                data: the actual data containing x and y values
                label: the label for this line
                color: the color of this line
                inherit_color: whether to use the parent-level color or its own
                lw: the line width of this line
                inherit_lw: whether to use the parent-level line width or its own
                ls: the line style of this line
                inherit_ls: whether to use the parent-level line style or its own
                marker: the line marker of this line
                inherit_marker: whether to use the parent-level line marker or its own
                z_data: the z-data associated with the columns in a multi-column pattern
        """
        my_kwargs = self.pop_kwargs(kwargs,
            *[prop.label for prop in PyXRDLine.Meta.get_local_persistent_properties()]
        )
        super(PyXRDLine, self).__init__(*args, **kwargs)
        kwargs = my_kwargs

        with self.visuals_changed.hold():
            self.label = self.get_kwarg(kwargs, self.label, "label")
            self.color = self.get_kwarg(kwargs, self.color, "color")
            self.inherit_color = bool(self.get_kwarg(kwargs, self.inherit_color, "inherit_color"))
            self.lw = float(self.get_kwarg(kwargs, self.lw, "lw"))
            self.inherit_lw = bool(self.get_kwarg(kwargs, self.inherit_lw, "inherit_lw"))
            self.ls = self.get_kwarg(kwargs, self.ls, "ls")
            self.inherit_ls = bool(self.get_kwarg(kwargs, self.inherit_ls, "inherit_ls"))
            self.marker = self.get_kwarg(kwargs, self.marker, "marker")
            self.inherit_marker = bool(self.get_kwarg(kwargs, self.inherit_marker, "inherit_marker"))
            self.z_data = list(self.get_kwarg(kwargs, [0], "z_data"))

    # ------------------------------------------------------------
    #      Input/Output stuff
    # ------------------------------------------------------------
    @classmethod
    def from_json(cls, **kwargs): # @ReservedAssignment
        if "xy_store" in kwargs:
            if "type" in kwargs["xy_store"]:
                kwargs["data"] = kwargs["xy_store"]["properties"]["data"]
        elif "xy_data" in kwargs:
            if "type" in kwargs["xy_data"]:
                kwargs["data"] = kwargs["xy_data"]["properties"]["data"]
            kwargs["label"] = kwargs["data_label"]
            del kwargs["data_name"]
            del kwargs["data_label"]
            del kwargs["xy_data"]
        return cls(**kwargs)

    # ------------------------------------------------------------
    #      Convenience Methods & Functions
    # ------------------------------------------------------------
    def interpolate(self, *x_vals, **kwargs):
        """
            Returns a list of (x, y) tuples for the passed x values. An optional
            column keyword argument can be passed to select a column, by default
            the first y-column is used. Returned y-values are interpolated. 
        """
        column = kwargs.get("column", 0)
        f = interp1d(self.data_x, self.data_y[:, column])
        return list(zip(x_vals, f(x_vals)))

    def get_plotted_y_at_x(self, x):
        """
            Gets the (interpolated) plotted value at the given x position.
            If this line has not been plotted (or does not have
            access to a '__plot_line' attribute set by the plotting routines)
            it will return 0.
        """
        try:
            xdata, ydata = getattr(self, "__plot_line").get_data()
        except AttributeError:
            logging.exception("Attribute error when trying to get plotter data at x position!")
        else:
            if len(xdata) > 0 and len(ydata) > 0:
                return np.interp(x, xdata, ydata)
        return 0

    def calculate_npeaks_for(self, max_threshold, steps):
        """
            Calculates the number of peaks for `steps` threshold values between
            0 and `max_threshold`. Returns a tuple containing two lists with the
            threshold values and the corresponding number of peaks. 
        """
        length = self.data_x.size

        resolution = length / (self.data_x[-1] - self.data_x[0])
        delta_angle = 0.05
        window = int(delta_angle * resolution)
        window += (window % 2) * 2

        steps = max(steps, 2) - 1
        factor = max_threshold / steps

        deltas = [i * factor for i in range(0, steps)]

        numpeaks = []

        maxtabs, mintabs = multi_peakdetect(self.data_y[:, 0], self.data_x, 5, deltas)
        for maxtab, _ in zip(maxtabs, mintabs):
            numpeak = len(maxtab)
            numpeaks.append(numpeak)
        numpeaks = list(map(float, numpeaks))

        return deltas, numpeaks

    def get_best_threshold(self, max_threshold=None, steps=None, status_dict=None):
        """
            Estimates the best threshold for peak detection using an
            iterative algorithm. Assumes there is a linear contribution from noise.
            Returns a 4-tuple containing the selected threshold, the maximum
            threshold, a list of threshold values and a list with the corresponding
            number of peaks.
        """
        length = self.data_x.size
        steps = not_none(steps, 20)
        threshold = 0.1
        max_threshold = not_none(max_threshold, threshold * 3.2)

        def get_new_threshold(threshold, deltas, num_peaks, ln):
            # Left side line:
            x = deltas[:ln]
            y = num_peaks[:ln]
            slope, intercept, R, _, _ = stats.linregress(x, y)
            return R, -intercept / slope

        if length > 2:
            # Adjust the first distribution:
            deltas, num_peaks = self.calculate_npeaks_for(max_threshold, steps)

            #  Fit several lines with increasing number of points from the
            #  generated threshold / marker count graph. Stop when the
            #  R-coefficiënt drops below 0.95 (past linear increase from noise)
            #  Then repeat this by increasing the resolution of data points
            #  and continue until the result does not change anymore

            last_threshold = None
            solution = False
            max_iters = 10
            min_iters = 3
            itercount = 0
            if status_dict is not None:
                status_dict["progress"] = 0

            while not solution:
                # Number of points to use for the lin regress:
                ln = 4
                # Maximum number of points to use:
                max_ln = len(deltas)
                # Flag indicating if we can stop searching for the linear part
                stop = False
                while not stop:
                    R, threshold = get_new_threshold(threshold, deltas, num_peaks, ln)
                    max_threshold = threshold * 3.2
                    if abs(R) < 0.98 or ln >= max_ln:
                        stop = True
                    else:
                        ln += 1
                itercount += 1 # Increase # of iterations
                if last_threshold:
                    # Check if we have run at least `min_iters`, at most `max_iters`
                    # and have not reached an equilibrium.
                    solution = bool(
                        itercount > min_iters and not
                        (
                            itercount <= max_iters and
                            last_threshold - threshold >= 0.001
                        )
                    )
                    if not solution:
                        deltas, num_peaks = self.calculate_npeaks_for(max_threshold, steps)
                last_threshold = threshold
                if status_dict is not None:
                    status_dict["progress"] = float(itercount / max_iters)

            return (deltas, num_peaks), threshold, max_threshold
        else:
            return ([], []), threshold, max_threshold


    pass # end of class