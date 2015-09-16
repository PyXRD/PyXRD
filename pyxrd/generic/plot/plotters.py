# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import logging
logger = logging.getLogger(__name__)

from itertools import izip

from pyxrd.data import settings

import numpy as np

import matplotlib
import matplotlib.transforms as transforms
from matplotlib.patches import FancyBboxPatch, Rectangle
from matplotlib.offsetbox import VPacker, HPacker, AnchoredOffsetbox, TextArea, AuxTransformBox
from matplotlib.text import Text

from pyxrd.generic.custom_math import smooth, add_noise

from draggables import DraggableMixin

def getattr_or_create(obj, attr, create):
    value = getattr(obj, attr, None)
    if value == None:
        class_type, args, kwargs = create
        value = class_type(*args, **kwargs)
    return value

def plot_marker_text(project, marker, offset, marker_scale, base_y, axes):
    """
        Plots a markers text using the given offset and scale
    """
    text = getattr(marker, "__plot_text", None)
    within_range = bool(
        project.axes_xlimit == 0 or
        (marker.position >= project.axes_xmin and
        marker.position <= project.axes_xmax)
    )
    if marker.visible and marker.style != "offset" and within_range:
        # prevent empty $$ from causing an error:
        save_label = marker.label.replace("$$", "")

        # Calculate position and set transform:
        x = float(marker.position) + float(marker.x_offset)
        if marker.top == 0: # relative to base
            y = base_y + (marker.top_offset + marker.y_offset) * marker_scale
            transform = axes.transData
        elif marker.top == 1: # top of plot
            y = settings.PLOT_TOP + float(marker.y_offset)
            transform = transforms.blended_transform_factory(axes.transData, axes.get_figure().transFigure)

        kws = dict(text=save_label,
                   x=x, y=y,
                   clip_on=False,
                   transform=transform,
                   horizontalalignment=marker.align, verticalalignment="center",
                   rotation=(90 - marker.angle), rotation_mode="anchor",
                   color=marker.color,
                   weight="heavy")

        if text:
            for key in kws: getattr(text, "set_%s" % key)(kws[key])
        else:
            text = Text(**kws)
        if not text in axes.get_children():
            axes.add_artist(text)
    elif text:
        try: text.remove()
        except: pass
    marker.__plot_text = text
    return text

def plot_marker_line(project, marker, offset, base_y, axes):
    """
        Plots a markers connector line using the given offset
    """
    line = getattr(marker, "__plot_line", None)
    within_range = bool(
        project.axes_xlimit == 0 or
        (marker.position >= project.axes_xmin and
        marker.position <= project.axes_xmax)
    )
    if marker.visible and within_range:
        # We need to strip away the units for comparison with
        # non-unitized bounds
        trans = transforms.blended_transform_factory(axes.transData, axes.transAxes)

        # Calculate top and bottom positions:
        ymin, ymax = axes.get_ybound()
        y = base_y
        y0 = (y - ymin) / (ymax - ymin)
        if marker.top == 0: # relative to base
            y1 = y0 + (marker.top_offset - ymin) / (ymax - ymin)
        elif marker.top == 1: # top of plot
            y1 = 1.0

        # If style is 'offset', re-calculate positions accordingly
        style = marker.style
        if style == "offset":
            style = "solid"
            y0 = (offset - ymin) / (ymax - ymin)
            y1 = y0 + (marker.y_offset - ymin) / (ymax - ymin)

        data = [y0, y1]

        if line:
            line.set_xdata(np.array([marker.position, marker.position]))
            line.set_ydata(np.array(data))
            line.set_transform(trans)
            line.set_color(marker.color)
            line.set_linestyle(style)
        else:
            line = matplotlib.lines.Line2D([marker.position, marker.position], data , transform=trans, color=marker.color, ls=style)
            line.y_isdata = False

        if not line in axes.get_lines():
            axes.add_line(line)
    elif line:
        try: line.remove()
        except: pass
    marker.__plot_line = line

def plot_markers(project, specimen, marker_lbls, offset, scale, marker_scale, axes):
    """
        Plots a specimens markers using the given offset and scale
    """

    for marker in specimen.markers:
        base_y = 0
        if marker.base == 1:
            base_y = specimen.experimental_pattern.get_plotted_y_at_x(marker.position)
        elif marker.base == 2:
            base_y = specimen.calculated_pattern.get_plotted_y_at_x(marker.position)
        elif marker.base == 3:
            base_y = min(
                specimen.experimental_pattern.get_plotted_y_at_x(marker.position),
                specimen.calculated_pattern.get_plotted_y_at_x(marker.position)
            )
        elif marker.base == 4:
            base_y = max(
                specimen.experimental_pattern.get_plotted_y_at_x(marker.position),
                specimen.calculated_pattern.get_plotted_y_at_x(marker.position)
            )

        plot_marker_line(project, marker, offset, base_y, axes)
        text = plot_marker_text(project, marker, offset, marker_scale, base_y, axes)
        if text is not None:
            marker_lbls.append((text, marker.base == 0, marker.y_offset))

def plot_hatches(project, specimen, offset, scale, axes):
    """
        Plots a specimens exclusion 'hatched' areas using the given offset and
        scale
    """
    # calculate the Y limits
    y0 = offset
    y1 = offset + max(specimen.max_intensity * scale, 1.0)

    # these are easier to just remove for now, not too expensive
    leftborder, hatch, rightborder = getattr(specimen, "__plot_hatches_artists", (None, None, None))
    if leftborder:
        try: leftborder.remove()
        except: pass
    if hatch:
        try: hatch.remove()
        except: pass
    if rightborder:
        try: rightborder.remove()
        except: pass

    # Create & add new hatches:
    for x0, x1 in izip(*specimen.exclusion_ranges.get_xy_data()):
        leftborder = axes.plot([x0, x0], [y0, y1], c=settings.EXCLUSION_LINES)
        axes.add_patch(Rectangle(
            (x0, y0), x1 - x0, y1 - y0,
            fill=True, hatch="/", linewidth=0,
            facecolor=settings.EXCLUSION_FOREG,
            edgecolor=settings.EXCLUSION_LINES)
        )
        rightborder = axes.plot([x1, x1], [y0, y1], c=settings.EXCLUSION_LINES)

def plot_label(specimen, labels, label_offset, plot_left, axes):
    text = getattr(specimen, "__plot_label_artist", None)

    # prevent empty $$ from causing an error:
    save_label = specimen.label.replace("$$", "")

    props = dict(
        text=save_label,
        x=plot_left - 0.05,
        y=label_offset,
        clip_on=False,
        horizontalalignment='right',
        verticalalignment='center',
        transform=transforms.blended_transform_factory(axes.get_figure().transFigure, axes.transData)
    )
    if text:
        for key in props: getattr(text, "set_%s" % key)(props[key])
    else:
        text = Text(**props)
    if not text in axes.get_children():
        axes.add_artist(text)
    labels.append(text)
    specimen.__plot_label_artist = text

def apply_transform(data, scale=1, offset=0, cap=0):
    data_x, data_y = data
    data_y = np.array(data_y) # make a copy
    if cap > 0:
        np.copyto(data_y, [cap], where=(data_y >= cap)) # copy the cap where values are larger then cap
    data_y = data_y * scale + offset # scale and offset the capped data
    return data_x, data_y

def plot_pattern(pattern, axes, scale=1, offset=0, cap=0, **kwargs):
    # setup or update the line

    line = getattr_or_create(pattern, "__plot_line", (matplotlib.lines.Line2D, ([], []), {}))

    if kwargs:
        line.update(kwargs)
    line.update(dict(
        data=apply_transform(pattern.get_xy_data(), scale=scale, offset=offset, cap=cap),
        color=pattern.color,
        linewidth=pattern.lw,
        ls=getattr(pattern, "ls", "-"),
        marker=getattr(pattern, "marker", "")
    ))
    if not line in axes.get_lines():
        axes.add_line(line)
    pattern.__plot_line = line

def make_draggable(artist, drag_x_handler=None, drag_y_handler=None):
    if artist != None:
        draggable = getattr(artist, "__draggable", None)
        if draggable == None:
            draggable = DraggableMixin(artist, drag_x_handler, drag_y_handler)
        else:
            draggable.update(artist, drag_x_handler, drag_y_handler)
        artist.__draggable = draggable

def plot_specimen(project, specimen, labels, marker_lbls, label_offset, plot_left,
        offset, scale, marker_scale, axes):
    """
        Plots a specimens patterns, markers and hatches using the given
        offset and scale
    """
    # Plot the patterns;

    if specimen.display_experimental:
        pattern = specimen.experimental_pattern

        # plot the experimental pattern:
        plot_pattern(pattern, axes, scale=scale, offset=offset, cap=pattern.cap_value)
        #make_draggable(getattr(pattern, "__plot_line", None), drag_y_handler=specimen.on_pattern_dragged)

        # get some common data for the next lines:
        x_data, y_data = pattern.get_xy_data()
        xmin, xmax = (np.min(x_data), np.max(x_data)) if x_data.size > 0 else (0, 0)
        ymin, ymax = (np.min(y_data), np.max(y_data)) if y_data.size > 0 else (0, 0)

        ########################################################################
        # plot the background pattern:
        bg_line = getattr_or_create(pattern, "__plot_bg_line", (matplotlib.lines.Line2D, ([], []), dict(c="#660099", lw="2", zorder=10)))
        if pattern.bg_type == 0 and pattern._bg_position != 0.0:
            bg_line.update(dict(
                data=apply_transform(([xmin, xmax], [pattern.bg_position, pattern.bg_position]), scale=scale, offset=offset),
                visible=True
            ))
        elif pattern.bg_type == 1 and pattern.bg_pattern is not None:
            bg_line.update(dict(
                data=apply_transform((x_data, (pattern.bg_pattern * pattern.bg_scale) + pattern.bg_position), scale=scale, offset=offset),
                visible=True
            ))
        else:
            bg_line.update(dict(
                data=([], []),
                visible=True
            ))

        if bg_line.get_visible() and not bg_line in axes.get_lines():
            axes.add_line(bg_line)
        elif not bg_line.get_visible():
            try: bg_line.remove()
            except: pass
        pattern.__plot_bg_line = bg_line
        ########################################################################

        ########################################################################
        # plot the smooth pattern:
        smooth_line = getattr_or_create(pattern, "__plot_smooth_line", (matplotlib.lines.Line2D, ([], []), dict(c="#660099", lw="2", zorder=10)))

        if int(pattern.smooth_degree) > 1:
            data = x_data, smooth(y_data, pattern.smooth_degree)
        else:
            data = [], []
        smooth_line.update(dict(
            data=apply_transform(data, scale=scale, offset=offset),
            visible=bool(pattern.smooth_degree > 1)
        ))
        if smooth_line.get_visible() and not smooth_line in axes.get_lines():
            axes.add_line(smooth_line)
        elif not smooth_line.get_visible():
            try: smooth_line.remove()
            except: pass
        pattern.__plot_smooth_line = smooth_line
        ########################################################################

        ########################################################################
        # plot the noisified pattern:
        noise_line = getattr_or_create(pattern, "__plot_noise_line", (matplotlib.lines.Line2D, ([], []), dict(c="#660099", lw="2", zorder=10)))


        if pattern.noise_fraction > 0.0:
            data = x_data, add_noise(y_data, pattern.noise_fraction)
        else:
            data = [], []
        noise_line.update(dict(
            data=apply_transform(data, scale=scale, offset=offset),
            visible=bool(pattern.noise_fraction > 0.0)
        ))
        if noise_line.get_visible() and not noise_line in axes.get_lines():
            axes.add_line(noise_line)
        elif not noise_line.get_visible():
            try: noise_line.remove()
            except: pass
        pattern.__plot_noise_line = noise_line
        ########################################################################

        ########################################################################
        # plot the shift & reference lines:
        shifted_line = getattr_or_create(pattern, "__plot_shifted_line", (matplotlib.lines.Line2D, ([], []), dict(c="#660099", lw="2", zorder=10)))
        reference_line = getattr_or_create(pattern, "__plot_reference_line", (matplotlib.lines.Line2D, ([], []), dict(c="#660099", lw="2", ls="--", zorder=10)))

        if pattern.shift_value != 0.0:
            shifted_line.update(dict(
                data=apply_transform((x_data - pattern._shift_value, y_data.copy()), scale=scale, offset=offset),
                visible=True
            ))
            position = specimen.goniometer.get_2t_from_nm(pattern.shift_position)
            reference_line.update(dict(
                data=apply_transform(([position, position], [0, ymax]), scale=scale, offset=offset),
                visible=True
            ))
            if not shifted_line in axes.get_lines():
                axes.add_line(shifted_line)
            if not reference_line in axes.get_lines():
                axes.add_line(reference_line)
        else:
            shifted_line.set_data([], [])
            shifted_line.set_visible(False)
            try: shifted_line.remove()
            except: pass
            reference_line.set_data([], [])
            reference_line.set_visible(False)
            try: reference_line.remove()
            except: pass
        pattern.__plot_shifted_line = shifted_line
        pattern.__plot_reference_line = reference_line
        ########################################################################

        ########################################################################
        # plot the pattern after peak stripping:
        stripped_line = getattr_or_create(pattern, "__plot_stripped_line", (matplotlib.lines.Line2D, ([], []), dict(c="#660099", lw="1", zorder=10)))


        if pattern.strip_startx != 0.0 and pattern.strip_endx != 0.0:
            strip_xdata, strip_ydata = pattern.stripped_pattern
            stripped_line.update(dict(
                data=apply_transform((strip_xdata.copy(), strip_ydata.copy()), scale=scale, offset=offset),
                visible=True
            ))
            if not stripped_line in axes.get_lines():
                axes.add_line(stripped_line)
        else:
            stripped_line.set_data([], [])
            stripped_line.set_visible(False)
            try: stripped_line.remove()
            except: pass

        pattern.__plot_stripped_line = stripped_line
        ########################################################################

        ########################################################################
        # plot the pattern after peak stripping:
        peak_area = getattr(specimen, "__plot_peak_area", None)
        if peak_area is not None and peak_area in axes.get_children():
            peak_area.remove()
        if pattern.area_startx != 0.0 and pattern.area_endx != 0.0 and pattern.area_pattern is not None:
            area_xdata, area_bg, area_ydata = pattern.area_pattern
            _, area_bg = apply_transform((area_xdata.copy(), area_bg.copy()), scale=scale, offset=offset)
            area_xdata, area_ydata = apply_transform((area_xdata.copy(), area_ydata.copy()), scale=scale, offset=offset)
            peak_area = axes.fill_between(area_xdata, area_bg, area_ydata, interpolate=True, facecolor="#660099", zorder=10)
        setattr(specimen, "__plot_peak_area", peak_area)

    if specimen.display_calculated:
        pattern = specimen.calculated_pattern
        plot_pattern(pattern, axes, scale=scale, offset=offset)
        #if not specimen.display_experimental:
        #    make_draggable(getattr(pattern, "__plot_line", None), drag_y_handler=specimen.on_pattern_dragged)

        # setup or update the calculated lines (phases)
        if specimen.display_phases:
            phase_lines = getattr(specimen, "__plot_phase_lines", [])

            # Clear previous phase lines:
            for phase_line in phase_lines:
                if phase_line in axes.get_lines():
                    axes.remove_line(phase_line)

            # Update & add phase lines:
            for i in xrange(2, pattern.num_columns):
                phase_data = pattern.get_xy_data(i)
                # Get the line object or create it:
                try:
                    phase_line = phase_lines[i - 2]
                except IndexError:
                    phase_line = matplotlib.lines.Line2D(*phase_data)
                    phase_lines.append(phase_line)
                # Get the phase color or use a default color:
                try:
                    phase_color = pattern.phase_colors[i - 2]
                except IndexError:
                    phase_color = pattern.color
                # Update the line object properties:
                phase_line.update(dict(
                    data=apply_transform(phase_data, scale=scale, offset=offset),
                    color=phase_color,
                    linewidth=pattern.lw
                ))

                # Add to axes:
                axes.add_line(phase_line)

            specimen.__plot_phase_lines = phase_lines

    # mineral preview sticks
    if hasattr(specimen, "mineral_preview") and specimen.mineral_preview is not None:
        name, peaks = specimen.mineral_preview
        lines = getattr(specimen, "__plot_mineral_preview", [])
        for line in lines:
            try: line.remove()
            except: pass

        lines = []
        for position, intensity in peaks:
            position = specimen.goniometer.get_2t_from_nm(position / 10.)
            intensity /= 100.

            trans = transforms.blended_transform_factory(axes.transData, axes.transAxes)
            ymin, ymax = axes.get_ybound()
            style = "solid"
            color = "#FF00FF"
            y0 = (offset - ymin) / (ymax - ymin)
            y1 = y0 + (intensity - ymin) / (ymax - ymin)
            line = matplotlib.lines.Line2D(
                [position, position], [y0, y1],
                transform=trans, color=color, ls=style
            )
            axes.add_line(line)
            lines.append(line)
        setattr(specimen, "__plot_mineral_preview", lines)


    # exclusion ranges;
    plot_hatches(project, specimen, offset, scale, axes)
    # markers;
    plot_markers(project, specimen, marker_lbls, offset, scale, marker_scale, axes)
    # & label:
    plot_label(specimen, labels, label_offset, plot_left, axes)
    #make_draggable(getattr(specimen, "__plot_label_artist", None), drag_y_handler=project.on_label_dragged)

def plot_statistics(project, specimen, spec_scale, stats_y_pos, stats_height, axes):

    # Scales & shifts the pattern so the zero line plots in the middle.
    def plot_pattern_middle(pattern, axes, height, vscale, offset, **kwargs):
        """
            Height is the fraction of the plot reserved for the residual pattern
            vscale is a user scaling factor applied to the residual pattern
            offset is the offset of the residual pattern position from the x-axis of the plot
        """
        # Offset to the middle of the available space:
        offset = offset + 0.5 * height
        # If the intensity difference is smaller then the space available, don't scale
        scale = spec_scale * 0.5 * vscale
        plot_pattern(pattern, axes, scale=scale, offset=offset, **kwargs)

    if specimen.display_residuals and specimen.statistics.residual_pattern is not None:
        plot_pattern_middle(
            specimen.statistics.residual_pattern,
            axes, height=stats_height,
            vscale=specimen.display_residual_scale,
            offset=stats_y_pos, alpha=0.75
        )
    if specimen.display_derivatives:
        for pattern in (
                specimen.statistics.der_residual_pattern,
                specimen.statistics.der_exp_pattern,
                specimen.statistics.der_calc_pattern):
            if pattern is not None:
                plot_pattern_middle(
                    pattern, axes, height=stats_height,
                    vscale=specimen.display_residual_scale,
                    offset=stats_y_pos, alpha=0.65
                )

def plot_specimens(axes, pos_setup, project, specimens):
    """
        Plots multiple specimens within the context of a project
    """

    base_offset = project.display_plot_offset
    base_height = 1.0
    label_offset = project.display_label_pos

    scale, scale_unit = project.get_scale_factor()

    labels, marker_lbls = list(), list()
    current_y_pos = 0
    lbl_y_offset = 0
    group_counter = 0 # 'group by' specimen counter

    ylim = 0 # used to keep track of maximum y-value, for a tight y-axis

    for _, specimen in enumerate(specimens):

        spec_max_intensity = float(specimen.max_intensity)

        # single specimen normalization:
        if project.axes_ynormalize == 1:
            scale = (1.0 / spec_max_intensity) if spec_max_intensity != 0.0 else 1.0

        spec_y_offset = specimen.display_vshift * scale_unit
        spec_y_pos = current_y_pos * scale_unit + spec_y_offset
        spec_alloc_height = base_height * scale_unit
        spec_reqst_height = spec_alloc_height * specimen.display_vscale

        lbl_y_offset = (label_offset + specimen.display_vshift) * scale_unit
        lbl_y_pos = current_y_pos * scale_unit + lbl_y_offset

        # For the y-limit we do not add the specimens vscale or vshift:
        ylim = current_y_pos * scale_unit + spec_alloc_height

        # Specimen scale = global scale, adjusted by specimen vscale
        spec_scale = scale * specimen.display_vscale

        # when statistics are plotted,
        # 65% of the height goes to the actual specimen plots
        # 35% goes to the statistics plot:
        if project.layout_mode == "FULL" and (specimen.display_residuals or specimen.display_derivatives):
            stats_y_pos = spec_y_pos
            stats_height = 0.35 * spec_reqst_height

            spec_y_pos = spec_y_pos + stats_height
            spec_scale = spec_scale * 0.65

            plot_statistics(
                project, specimen, spec_scale,
                stats_y_pos, stats_height,
                axes
            )

        plot_specimen(
            project, specimen, labels, marker_lbls,
            lbl_y_pos, pos_setup.left, spec_y_pos, spec_scale, scale_unit,
            axes
        )

        # increase offsets:
        group_counter += 1
        if group_counter >= project.display_group_by:
            group_counter = 0
            current_y_pos += base_offset

    axes.set_ylim(top=ylim)

    return labels, marker_lbls

def plot_mixtures(axes, project, mixtures):
    legend = getattr(project, "__plot_mixture_legend", None)
    if legend:
        try: legend.remove()
        except ValueError: pass

    figure = axes.get_figure()
    trans = figure.transFigure

    def create_rect_patch(ec="#000000", fc=None):
        _box = AuxTransformBox(transforms.IdentityTransform())
        rect = FancyBboxPatch(
            xy=(0, 0),
            width=0.02,
            height=0.02,
            boxstyle='square',
            ec=ec,
            fc=fc,
            mutation_scale=14, # font size
            transform=trans,
            alpha=1.0 if (ec is not None or fc is not None) else 0.0
        )
        _box.add_artist(rect)
        return _box

    legends = []
    for mixture in mixtures:
        legend_items = []

        # Add title:
        title = TextArea(mixture.name)
        title_children = [create_rect_patch(ec=None) for spec in mixture.specimens]
        title_children.insert(0, title)
        title_box = HPacker(children=title_children, align="center", pad=5, sep=3)
        legend_items.append(title_box)

        # Add phase labels & boxes
        for i, (phase, fraction) in enumerate(izip(mixture.phases, mixture.fractions)):
            label_text = u"{}: {:>5.1f}".format(phase, fraction * 100.0)
            label = TextArea(label_text)
            phase_children = [
                create_rect_patch(fc=phase.display_color)
                for phase in mixture.phase_matrix[:, i].flat if phase is not None
            ]
            phase_children.insert(0, label)
            legend_items.append(
                HPacker(children=phase_children, align="center", pad=0, sep=3)
            )

        # Add created legend to the list:
        legends.append(
            VPacker(children=legend_items, align="right", pad=0, sep=3)
        )

    # Only add this if there's something to add!
    if legends:
        # Pack legends & plot:
        legend = AnchoredOffsetbox(
            loc=1,
            pad=0.1,
            borderpad=0.1,
            frameon=False,
            child=VPacker(children=legends, align="right", pad=0, sep=5)
        )

        axes.add_artist(legend)
        setattr(project, "__plot_mixture_legend", legend)


