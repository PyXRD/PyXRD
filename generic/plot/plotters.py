# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Author: Mathijs Dumon
# This work is licensed under the Creative Commons Attribution-ShareAlike 3.0 Unported License. 
# To view a copy of this license, visit http://creativecommons.org/licenses/by-sa/3.0/ or send
# a letter to Creative Commons, 444 Castro Street, Suite 900, Mountain View, California, 94041, USA.

import settings

import numpy as np

import matplotlib
import matplotlib.transforms as transforms
from matplotlib.text import Text

def plot_marker_text(marker, offset, marker_scale, base_y, axes):
    """
        Plots a markers text using the given offset and scale
    """
    if marker.visible and marker.style != "offset":
        kws = dict(text=marker.label,
                   x=float(marker.position)+float(marker.x_offset), y=settings.PLOT_TOP+float(marker.y_offset),
                   clip_on=False,
                   transform=transforms.blended_transform_factory(axes.transData, axes.get_figure().transFigure),
                   horizontalalignment="left", verticalalignment="center",
                   rotation=(90-marker.angle), rotation_mode="anchor",
                   color=marker.color,
                   weight="heavy")
        
        if marker.style == "none":
            y = base_y + marker.y_offset * marker_scale
            
            kws.update(dict(
                y=y,
                transform=axes.transData,
            ))
        
        if not hasattr(marker, "_plt_text") or marker._plt_text == None:
            marker._plt_text = Text(**kws)
        else:
            for key in kws:
                getattr(marker._plt_text, "set_%s"%key)(kws[key])
        if not marker._plt_text in axes.get_children():
            axes.add_artist(marker._plt_text)

def plot_marker_line(marker, offset, base_y, axes):
    """
        Plots a markers connector line using the given offset
    """
    if marker.visible:
        # We need to strip away the units for comparison with
        # non-unitized bounds
        trans = transforms.blended_transform_factory(axes.transData, axes.transAxes)
        
        ymin, ymax = axes.get_ybound()
        y = base_y
        y0, y1 = (y - ymin) / (ymax - ymin), 1.0
        
        style = marker.style
        if style == "offset":
            style = "solid"
            y0 = (offset - ymin) / (ymax - ymin)
            y1 = y0 + (marker.y_offset - ymin) / (ymax - ymin)
            
        data = [y0,y1]
            
        if not hasattr(marker, "_plt_vline") or marker._plt_vline == None:
            marker._plt_vline = matplotlib.lines.Line2D([marker.position,marker.position], data , transform=trans, color=marker.color, ls=style)
            marker._plt_vline.y_isdata = False
        else:
            marker._plt_vline.set_xdata(np.array([marker.position,marker.position]))
            marker._plt_vline.set_ydata(np.array(data))
            marker._plt_vline.set_transform(trans)
            marker._plt_vline.set_color(marker.color)
            marker._plt_vline.set_linestyle(style)
            
        if not marker._plt_vline in axes.get_lines():
            axes.add_line(marker._plt_vline)

def plot_markers(specimen, offset, scale, marker_scale, axes):
    """
        Plots a specimens markers using the given offset and scale
    """     
    for marker in specimen.markers.iter_objects():
        base_y = 0
        if marker.base == 1:
            base_y = specimen.experimental_pattern.get_y_at_x(marker.position)
        elif marker.base == 2:
            base_y = specimen.calculated_pattern.get_y_at_x(marker.position)
        elif marker.base == 3:   
            base_y = specimen.get_y_min_at_x(marker.position)
        elif marker.base == 4:
            base_y = specimen.get_y_max_at_x(marker.position)
            
        plot_marker_line(marker, offset, base_y, axes)
        plot_marker_text(marker, offset, marker_scale, base_y, axes)


def plot_hatches(specimen, offset, scale, axes):
    """
        Plots a specimens exclusion 'hatched' areas using the given offset and
        scale
    """          
    # calculate the Y limits
    y0 = offset
    y1 = offset + max(specimen.max_intensity * scale, 1.0)
    
    #Create & add new hatches:
    for i, (x0, x1) in enumerate(zip(*specimen.exclusion_ranges.get_raw_model_data())):
        leftborder = axes.axvline(x0, y0, y1, c=settings.EXCLUSION_LINES)
        hatch = axes.axvspan(
            x0, x1, y0, y1, fill=True, hatch="/", 
            facecolor=settings.EXCLUSION_FOREG, 
            edgecolor=settings.EXCLUSION_LINES, linewidth=0)
        rightborder = axes.axvline(x1, y0, y1, c=settings.EXCLUSION_LINES)

def plot_label(specimen, labels, label_offset, axes):
    text = Text(
        text=specimen.label, x=settings.PLOT_LEFT-0.05, y=label_offset, 
        clip_on=False,
        horizontalalignment='right', verticalalignment='center', 
        transform=transforms.blended_transform_factory(axes.get_figure().transFigure, axes.transData)
    )
    axes.add_artist(text)
    labels.append(text)

def plot_specimen(project, specimen, labels, label_offset, 
        offset, scale, marker_scale, axes):
    """
        Plots a specimens patterns, markers and hatches using the given
        offset and scale
    """
    # Plot the patterns;
    specimen.set_transform_factors(scale, offset)
    axes.add_line(specimen.calculated_pattern)    
    axes.add_line(specimen.experimental_pattern)
    # exclusion ranges;
    plot_hatches(specimen, offset, scale, axes)
    # markers;
    plot_markers(specimen, offset, scale, marker_scale, axes)
    # & label:
    plot_label(specimen, labels, label_offset, axes)
    
def plot_specimens(project, specimens, axes):
    """
        Plots multiple specimens within the context of a project
    """
    max_intensity = project.get_max_intensity()
    
    scale = 1.0
    marker_scale = 1.0
    if project.axes_yscale == 0:
        scale = (1.0 / max_intensity) if max_intensity!=0 else 1.0

    base_offset = project.display_plot_offset
    label_offset = project.display_label_pos
    if project.axes_yscale == 2:
        base_offset *= max_intensity
        label_offset *= max_intensity
    
    labels = list()
    offset = 0   
    group_counter = 0 
    for specimen in specimens:
        #adjust actual offsets using the specimen vertical shifts:
        spec_offset = offset + base_offset * specimen.display_vshift
        spec_lbl_offset = label_offset + base_offset * specimen.display_vshift * specimen.display_vscale
        spec_scale = scale
        
        #single specimen normalisation:
        if project.axes_yscale == 1:
            max_intensity = specimen.max_intensity
            spec_scale = (1.0 / max_intensity) if max_intensity!=0 else 1.0
        if project.axes_yscale == 2:
            marker_scale = specimen.max_intensity
        #plot it

        spec_scale *= specimen.display_vscale
        #marker_scale *= specimen.display_vscale
    
        plot_specimen(
            project, specimen, labels,
            spec_lbl_offset, spec_offset, spec_scale, marker_scale, 
            axes)
        #increase offsets:
        group_counter += 1
        if group_counter >= project.display_group_by:
            group_counter = 0
            offset += base_offset
            label_offset += base_offset
        
    return labels
    
def plot_mixture(mixture, axes):
    axes.text(1.0, 1.0,
        "\n".join(["{}: {:>5.1f}".format(phase, fraction*100.0) for phase, fraction in zip(mixture.phases, mixture.fractions)]),
        multialignment='right',
        horizontalalignment='right',
        verticalalignment='top',
        transform = axes.transAxes)
        
    
