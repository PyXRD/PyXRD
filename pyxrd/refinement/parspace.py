# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

from traceback import format_exc
import itertools
from math import sqrt

import logging
from pyxrd.data import settings
logger = logging.getLogger(__name__)

import numpy as np
from scipy.interpolate.ndgriddata import griddata

from mpl_toolkits.axes_grid1 import ImageGrid
import mpl_toolkits.axes_grid1.axes_size as Size
from mpl_toolkits.axes_grid1 import Divider
from pyxrd.generic.mathtext_support import get_plot_safe

class ParameterSpaceGenerator(object):

    num_cross_sections = 0
    grid = None

    def initialize(self, ranges, density):
        """
            Create a new generator with the given minimum and maximum values
            and the given grid density (expressed as # of data points for that 
            parameter axis).
        """

        self.num_params = len(ranges)
        assert self.num_params >= 1, "Need to have at least one refinable parameter!"

        ranges = np.asarray(ranges, dtype=float)

        self.minima = np.asarray(ranges[:, 0])
        self.maxima = np.asarray(ranges[:, 1])
        self.center_point = 0.5 * (self.minima + self.maxima)

        self.num_cross_sections = int(self.num_params * (self.num_params + 1) / 2)
        self.grid_dtype = np.dtype([("point", object), ("value", float), ("distance", float)])
        self.density = self._calculate_density(density)

        if self.num_params == 1:
            self.grid = np.empty(shape=(self.density,), dtype=self.grid_dtype)
        else:
            self.grid = np.empty(shape=(self.num_cross_sections, self.density, self.density), dtype=self.grid_dtype)

    def _calculate_density(self, density, memory_limit=settings.PAR_SPACE_MEMORY_LIMIT):
        block_size = self.grid_dtype.itemsize
        limited = sqrt(memory_limit / (block_size * self.num_cross_sections))
        return max(min(density, limited), 3)

    def _find_closest_grid_index(self, solution):
        """ Returns the closest grid point's indexes """

        # Transform solution so center of grid is zero point and min-max goes from -1 to +1
        transf = (np.asarray(solution) - self.center_point) / (self.maxima - self.minima)

        if self.num_params > 1:
            # Calculate distance to each cross section and find closest
            smallest_distance = None
            closest_cross_section = None

            for index, (par1, par2) in enumerate(itertools.combinations(range(self.num_params), 2)):
                # Project on to the normal of the A/B plan at the center point:
                projected = transf.copy()
                projected[par1] = 0
                projected[par2] = 0
                distance = np.linalg.norm(projected)
                if smallest_distance is None or smallest_distance > distance:
                    smallest_distance = distance
                    closest_cross_section = index, (par1, par2), distance

            index, (par1, par2), distance = closest_cross_section

            # Move back to 0->density space (was in -1 -> 1 space)
            gridded_location = np.array(np.round(0.5 * (transf + 1) * (self.density - 1)), dtype=int)
            closest_index = (index, int(gridded_location[par1]), int(gridded_location[par2]))
        else:
            # Only a single parameter, so only a single index:
            gridded_location = 0.5 * (transf + 1.0) * (self.density - 1.0)
            distance = np.abs(np.round(gridded_location) - gridded_location)
            closest_index = (int(np.round(gridded_location)[0]),)

        return closest_index, distance

    total_record_calls = 0
    total_actual_records = 0

    def record(self, new_solution, new_residual):
        """
            Add a new solution to the list of solutions
        """
        self.total_record_calls += 1
        # Get the best spot to store this one:
        closest_index, new_distance = self._find_closest_grid_index(new_solution)

        old_item = self.grid[closest_index]
        old_solution = old_item["point"]
        #old_residual = old_item["value"]
        old_distance = old_item["distance"]

        # If we have a previous point, check which one is closer:
        if (old_solution is not None and old_solution[0] is not None) and new_distance > old_distance:
            return
        else:
            self.total_actual_records += 1
            # If we got here, we can store the result:
            self.grid[closest_index] = (new_solution, new_residual, new_distance)

    def clear(self):
        del self.grid

    def clear_image(self, figure, message="Interpolation Error"):
        figure.clear()
        figure.text(0.5, 0.5, message, va="center", ha="center")

    def _setup_image_grid(self, figure, dims):
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
        image_grid = ImageGrid(
            figure, 111,
            nrows_ncols=(dims - 1, dims - 1),
            cbar_location="right",
            cbar_mode="single",
            # add_all=False,
            aspect=False,
            axes_pad=0.1,
            direction="column"
        )

        rect = (0.1, 0.1, 0.8, 0.8)
        horiz = [Size.Fixed(.1)] + [Size.Scaled(1.), Size.Fixed(.1)] * max(dims - 1, 1) + [Size.Fixed(0.15)]
        vert = [Size.Fixed(.1)] + [Size.Scaled(1.), Size.Fixed(.1)] * max(dims - 1, 1)

        # divide the axes rectangle into grid whose size is specified by horiz * vert
        divider = Divider(figure, rect, horiz, vert) # , aspect=False)

        # Helper to get the axis for par x and y:
        def get_grid(parx, pary):
            gridx = parx
            gridy = pary - 1
            return image_grid[gridy + gridx * (dims - 1)]

        # Helper to get the grid locator for par x and par y
        def get_locator(parx, pary):
            gridx = parx
            gridy = pary - 1
            nx = 1 + gridx * 2
            ny = 1 + (dims - gridy - 2) * 2
            return divider.new_locator(nx=nx, ny=ny)

        # Hide the unused plots & setup the used ones:
        for parx, pary in itertools.product(range(self.num_params - 1), range(1, self.num_params)):

            # Calculate the grid position:
            ax = get_grid(parx, pary)

            # Setup axes:
            if pary <= parx:
                ax.set_visible(False)
            else:
                ax.set_axes_locator(get_locator(parx, pary))
                ax.set_visible(True)

        return image_grid, divider, get_grid

    def plot_images(self, figure, centroid, labels, density=200, smooth=0.5):
        """
            Generate the parameter space plots
        """

        try:

            def extraxt_points_from_grid(grid2D, parx=None, pary=None):
                """ Helper function that extract x,y(,z) points from all the data """
                grid2D = grid2D.flatten()
                if parx is not None and pary is not None:
                    points_x = np.array([item["point"][parx] for item in grid2D if item["point"] is not None])
                    points_y = np.array([item["point"][pary] for item in grid2D if item["point"] is not None])
                    points_z = np.array([item["value"] for item in grid2D if item["point"] is not None])
                    return points_x, points_y, points_z
                else:
                    points_x = np.array([item["point"] for item in grid2D if item["point"] is not None])
                    points_y = np.array([item["value"] for item in grid2D if item["point"] is not None])
                    points_x = points_x.flatten()
                    points_y = points_y.flatten()
                    xy = np.array(zip(points_x, points_y), dtype=[('x', float), ('y', float)])
                    xy.sort(order=['x'], axis=0)
                    points_x = xy['x']
                    points_y = xy['y']
                    return points_x, points_y

            if self.num_params == 1:
                # Only one parameter refined:
                points_x, points_y = extraxt_points_from_grid(self.grid)
                ax = figure.add_subplot(1, 1, 1)
                ax.plot(points_x, points_y)
                ax.set_ylabel("Residual error")
                ax.set_xlabel(get_plot_safe(labels[0]))

            else:
                # Multi-parameter space:
                image_grid, divider, get_grid = self._setup_image_grid(figure, self.num_params)

                # Keep a reference to the images created,
                # so we can add a scale bar for all images (and they have the same range)
                ims = []
                tvmin, tvmax = None, None

                for index, (parx, pary) in enumerate(itertools.combinations(range(self.num_params), 2)):
                    # Get the data for this cross section:
                    grid2D = self.grid[index, ...]
                    points_x, points_y, points_z = extraxt_points_from_grid(grid2D, parx, pary)

                    # Setup axis:
                    ax = get_grid(parx, pary)
                    extent = (
                        self.minima[parx], self.maxima[parx],
                        self.minima[pary], self.maxima[pary]
                    )
                    aspect = 'auto'

                    # Try to interpolate the data:
                    xi = np.linspace(self.minima[parx], self.maxima[parx], density)
                    yi = np.linspace(self.minima[pary], self.maxima[pary], density)
                    zi = griddata((points_x, points_y), points_z, (xi[None, :], yi[:, None]), method='cubic')

                    # Plot it:
                    im = ax.imshow(zi, origin='lower', aspect=aspect, extent=extent, alpha=0.75)
                    ims.append(im)
                    im.set_cmap('gray_r')

                    # Get visual limits:
                    vmin, vmax = im.get_clim()
                    if index == 0:
                        tvmin, tvmax = vmin, vmax
                    else:
                        tvmin, tvmax = min(tvmin, vmin), max(tvmax, vmax)

                    # Try to add a contour & labels:
                    try:
                        ct = ax.contour(xi, yi, zi, colors='k', aspect=aspect, extent=extent, origin='lower')
                        ax.clabel(ct, colors='k', fontsize=10, format="%1.2f")
                    except ValueError:
                        pass #ignore the "zero-size array" error for now.

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
                    if pary == (self.num_params - 1):
                        ax.set_xlabel(str("#%d " % (parx + 1)) + get_plot_safe(labels[parx]))

                # Set the data limits:
                for im in ims:
                    im.set_clim(tvmin, tvmax)

                # Make it look PRO:
                if im is not None:
                    cbar_ax = image_grid.cbar_axes[0]
                    nx = 1 + (self.num_params - 1) * 2
                    ny1 = (self.num_params - 1) * 2
                    cbar_ax.set_axes_locator(divider.new_locator(nx=nx, ny=1, ny1=ny1))
                    cb = cbar_ax.colorbar(im) # @UnusedVariable

        except:
            print "Unhandled exception while generating parameter space images:"
            print format_exc()
            # ignore error, tell the user via the plot and return
            self.clear_image(figure)
            return

    pass #end of class
