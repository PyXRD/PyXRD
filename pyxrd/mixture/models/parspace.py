# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

from traceback import format_exc
import itertools

import numpy as np
import scipy
import scipy.spatial.qhull as qhull

from mpl_toolkits.axes_grid1 import ImageGrid
import mpl_toolkits.axes_grid1.axes_size as Size
from mpl_toolkits.axes_grid1 import Divider
from pyxrd.generic.mathtext_support import get_plot_safe

from pyxrd.generic.sorted_collection import SortedCollection

class ParameterSpaceGenerator(object):

    solutions = None

    def record(self, solution, residual):
        """
            Add a new solution to the list of solutions
        """
        try:
            new_record = solution
        except TypeError: # not an iterable
            new_record = np.array([solution, ], dtype=float)
        if self.solutions == None:
            max_items = 2000
            self.solutions = SortedCollection(key=lambda s: s[0], max_items=max_items)
        self.solutions.insert((residual, new_record))

    def get_extents(self, centroid, mins, maxs, density=10):
        """
            Calculates extents for the given minimum and maximum values so
            the centroid coordinates falls on the grid. This ensures the
            minimum point can be acurately represented on the plot.
            
            This is achieved by slightly shifting the grid, or with other words,
            the minimum and maximum values
        """
        slices = []
        rmins = []
        rmaxs = []
        centroid_indexes = []
        for c, mn, mx in zip(centroid, mins, maxs):
            # Correct small offsets from the centroid.
            # This assumes the centroid to be in the min and max ranges
            normal = np.linspace(mn, mx, density)
            idx = (np.abs(normal - c)).argmin()
            centroid_indexes.append(idx)
            closest = normal[idx]
            diff = c - closest
            rmin = mn + diff
            rmax = mx + diff
            rmins.append(rmin)
            rmaxs.append(rmax)
            slices.append(slice(rmin, rmax, complex(density)))

        return np.array(centroid_indexes), np.array(rmins), np.array(rmaxs)

    def parse_solutions(self, centroid, density=100):
        """
            Returns a tuple containing:
                - point array (Nsolutions, Nparams) : contains 'coordinates'
                - value array (Nsolutions) : contains residuals
                - centroid indeces in the final grid
                - grid minimum and maximum values shifted as explained in get_extents
        """
        points = np.array([point for value, point in self.solutions]) # @UnusedVariable
        values = np.array([value for value, point in self.solutions])

        mins = points.min(axis=0)
        maxs = points.max(axis=0)

        return (points, values) + self.get_extents(
            centroid=np.array(centroid),
            mins=mins,
            maxs=maxs,
            density=density
        )

    def plot_images(self, figure, centroid, labels, density=200, smooth=0.5):
        """
            Generate the parameter space plots
        """
        try:
            # Central point:
            try:
                centroid = list(centroid)
            except TypeError: # not an iterable:
                centroid = [centroid, ]

            # Some information:
            points, values, centroid_indexes, mins, maxs = \
                self.parse_solutions(centroid, density=density)

            print "Plotting image using %d points" % len(points)

            # How many parameters?
            dims = points.shape[1]

            if dims == 1: # Only one parameter refined
                points = points.flatten()
                values = values.flatten()

                xy = np.column_stack((points, values))
                xy.view('float16,float16').sort(order=['f1'], axis=0)
                points = xy[:, 0]
                values = xy[:, 1]

                ax = figure.add_subplot(1, 1, 1)
                ax.plot(points, values)
                ax.set_ylabel("Residual error")
                ax.set_xlabel(get_plot_safe(labels[0]))
            else: # Multi-parameter space:
                """
                    An example of how grid, parameter and view numbers change
                    for dims = 4
                    
                    The numbers in the grid are:
                    
                    parameter x, parameter y
                    grid x, grid y
                
                    -----------------------------------------------------
                    |            |            |            |            |
                    |    0, 0    |    1, 0    |    2, 0    |    3, 0    |
                    |    -, -    |    -, -    |    -, -    |    -, -    |
                    |            |            |            |            |
                    ==============------------|------------|------------|
                    I            I            |            |            |
                    I    0, 1    I    1, 1    |    2, 1    |    3, 1    |
                    I    0, 0    I    1, 0    |    2, 0    |    -, -    |
                    I            I            |            |            |
                    I------------==============------------|------------|
                    I            |            I            |            |
                    I    0, 2    |    1, 2    I    2, 2    |    3, 2    |
                    I    0, 1    |    1, 1    I    2, 1    |    -, -    |
                    I            |            I            |            |
                    I------------|------------==============------------|
                    I            |            |            I            |
                    I    0, 3    |    1, 3    |    2, 3    I    3, 3    |
                    I    0, 2    |    1, 2    |    2, 2    I    -, -    |
                    I            |            |            I            |
                    I======================================I------------|
                    From the above it should be clear that:
                    
                    parameter x = grid x
                    parameter y = grid y + 1
                    grid nr = grid y + grid x * (dims - 1)
                    view nr = grid nr - (grid nr / dims) * ((grid nr / dims) +1) / 2
                    

                """

                # TODO split this into smaller bits to make it more readable...

                # save starting point somewhere and test untill we get a decent solution...
                """try:
                    import cPickle as pickle
                except:
                    import pickle as pickle
                with open("/media/mathijs/LacieDocs/Projects/PyXRD/data/tempdat.pkl", "w") as f:
                    np.savez(f, points=points, values=values)"""

                triang = qhull.Delaunay(points, qhull_options="QJ Qbb")
                interp = scipy.interpolate.LinearNDInterpolator(triang, values)

                grid = ImageGrid(
                    figure, 111,
                    nrows_ncols=(dims - 1, dims - 1),
                    cbar_location="right",
                    cbar_mode="single",
                    # add_all=False,
                    aspect=False,
                    axes_pad=0.1,
                    direction="column"
                )

                # Helper to get the axes from the image grid:
                def get_gridnr(gridx, gridy):
                    # Plot number:
                    return gridy + gridx * (dims - 1)

                rect = (0.1, 0.1, 0.8, 0.8)
                horiz = [Size.Fixed(.1)] + [Size.Scaled(1.), Size.Fixed(.1)] * max(dims - 1, 1) + [Size.Fixed(0.15)]
                vert = [Size.Fixed(.1)] + [Size.Scaled(1.), Size.Fixed(.1)] * max(dims - 1, 1)

                # divide the axes rectangle into grid whose size is specified by horiz * vert
                divider = Divider(figure, rect, horiz, vert) # , aspect=False)

                def get_locator(gridx, gridy):
                    nx = 1 + gridx * 2
                    ny = 1 + (dims - gridy - 2) * 2
                    return divider.new_locator(nx=nx, ny=ny)

                # Keep a reference to the images created,
                # se we can add a scale bar for all images (and they have the same range)
                ims = []
                tvmin, tvmax = None, None

                for parx, pary in itertools.product(range(dims), range(dims)):

                        # Calculate these, so wo don't need to worry about them:
                    gridx = parx
                    gridy = pary - 1

                    if pary > 0 and parx < (dims - 1):
                        gridnr = get_gridnr(gridx, gridy)
                        ax = grid[gridnr]
                    else:
                        ax = None

                    if pary <= parx: # only show 'bottom triangle' plots, top is just a copy, but transposed
                        if ax: ax.set_visible(False)
                        continue

                    def get_coords_grid(centroid, mn, mx, mins, maxs, density):
                        coords = []
                        lx = np.linspace(mins[mn], maxs[mn], density)
                        ly = np.linspace(mins[mx], maxs[mx], density)
                        for x, y in itertools.product(lx, ly):
                            coord = centroid[:mn]
                            coord += [x, ]
                            coord += centroid[mn + 1:mx]
                            coord += [y, ]
                            coord += centroid[mx + 1:]
                            coords.append(coord)
                        return lx, ly, coords

                    def unique_rows(a):
                        order = np.lexsort(a.T)
                        a = a[order]
                        diff = np.diff(a, axis=0)
                        ui = np.ones(len(a), 'bool')
                        ui[1:] = (diff != 0).any(axis=1)
                        return a[ui]

                    # Calculate the view:
                    mn, mx = min(parx, pary), max(parx, pary)
                    ox, oy, coords = get_coords_grid(centroid, mn, mx, mins, maxs, density)
                    coords = np.array(coords)
                    view = interp(coords).reshape(density, density).transpose()

                    if ax is not None:
                        # Setup axes:
                        ax.set_axes_locator(get_locator(gridx, gridy))
                        ax.set_visible(True)
                        extent = (mins[parx], maxs[parx], mins[pary], maxs[pary])

                        # Plot the residual parameter space cross-section:
                        aspect = 'auto' # abs((extent[1]-extent[0]) / (extent[3] - extent[2]))
                        im = ax.imshow(view, origin='lower', aspect=aspect, extent=extent, alpha=0.75)
                        # ax.set_aspect(aspect)
                        im.set_cmap('gray_r')
                        vmin, vmax = im.get_clim()
                        if tvmin == None: tvmin = vmin
                        if tvmax == None: tvmax = vmax
                        tvmin, tvmax = min(tvmin, vmin), max(tvmax, vmax)

                        ims.append(im)

                        # Add a contour & labels:
                        ct = ax.contour(view, colors='k', aspect=aspect, extent=extent, origin='lower')
                        ax.clabel(ct, colors='k', fontsize=10, format="%1.2f")

                        # Add a red cross where the 'best' solution is:
                        ax.plot((centroid[parx],), (centroid[pary],), 'r+')

                        # Rotate x labels
                        for lbl in ax.get_xticklabels():
                            lbl.set_rotation(90)

                        # Reduce number of ticks:
                        ax.locator_params(axis='both', nbins=5)

                        # Set limits:
                        ax.set_xlim(extent[0:2])
                        ax.set_ylim(extent[2:4])

                        # Add labels to the axes so the user knows which is which:
                        # TODO add some flags/color/... indicating which phase & component each parameter belongs to...
                        if parx == 0:
                            ax.set_ylabel(str("#%d " % (pary + 1)) + get_plot_safe(labels[pary]))
                        if pary == (dims - 1):
                            ax.set_xlabel(str("#%d " % (parx + 1)) + get_plot_safe(labels[parx]))

                # Set the data limits:
                for im in ims:
                    im.set_clim(tvmin, tvmax)

                # Make it look PRO:
                if im is not None:
                    cbar_ax = grid.cbar_axes[0]
                    nx = 1 + (dims - 1) * 2
                    ny1 = (dims - 1) * 2
                    cbar_ax.set_axes_locator(divider.new_locator(nx=nx, ny=1, ny1=ny1))
                    cb = cbar_ax.colorbar(im) # @UnusedVariable
        except:
            print "Unhandled exception while generating parameter space images:"
            print format_exc()
            # ignore error, tell the user via the plot and return
            for ax in figure.get_axes():
                ax.set_visible(False)
            figure.text(0.5, 0.5, "Interpolation Error", va="center", ha="center")
            return
