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

from generic.utils import smooth

def plot_marker_text(marker, offset, marker_scale, base_y, axes):
    """
        Plots a markers text using the given offset and scale
    """
    text = getattr(marker, "__plot_text", None)
    if marker.visible and marker.style != "offset":
        kws = dict(text=marker.label,
                   x=float(marker.position)+float(marker.x_offset), y=settings.PLOT_TOP+float(marker.y_offset),
                   clip_on=False,
                   transform=transforms.blended_transform_factory(axes.transData, axes.get_figure().transFigure),
                   horizontalalignment=marker.align, verticalalignment="center",
                   rotation=(90-marker.angle), rotation_mode="anchor",
                   color=marker.color,
                   weight="heavy")
        
        if marker.style == "none":
            y = base_y + marker.y_offset * marker_scale
            
            kws.update(dict(
                y=y,
                transform=axes.transData,
            ))
        
        if text:
            for key in kws: getattr(text, "set_%s"%key)(kws[key])
        else:
            text = Text(**kws)
        if not text in axes.get_children():
            axes.add_artist(text)
    elif text:
        try: text.remove()
        except: pass  
    marker.__plot_text = text

def plot_marker_line(marker, offset, base_y, axes):
    """
        Plots a markers connector line using the given offset
    """
    line = getattr(marker, "__plot_line", None)
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
            
        if line:
            line.set_xdata(np.array([marker.position,marker.position]))
            line.set_ydata(np.array(data))
            line.set_transform(trans)
            line.set_color(marker.color)
            line.set_linestyle(style)
        else:
            line = matplotlib.lines.Line2D([marker.position,marker.position], data , transform=trans, color=marker.color, ls=style)
            line.y_isdata = False
            
        if not line in axes.get_lines():
            axes.add_line(line)
    elif line:
        try: line.remove()
        except: pass  
    marker.__plot_line = line
    
def plot_markers(specimen, offset, scale, marker_scale, axes):
    """
        Plots a specimens markers using the given offset and scale
    """
    
    for marker in specimen.markers.iter_objects():
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
    
    #these are easier to just remove for now, not too expensive
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
    
    #Create & add new hatches:
    for i, (x0, x1) in enumerate(zip(*specimen.exclusion_ranges.get_raw_model_data())):
        leftborder = axes.axvline(x0, y0, y1, c=settings.EXCLUSION_LINES)
        hatch = axes.axvspan(
            x0, x1, y0, y1, fill=True, hatch="/", 
            facecolor=settings.EXCLUSION_FOREG, 
            edgecolor=settings.EXCLUSION_LINES, linewidth=0)
        rightborder = axes.axvline(x1, y0, y1, c=settings.EXCLUSION_LINES)    

def plot_label(specimen, labels, label_offset, axes):
    text = getattr(specimen, "__plot_label_artist", None)
    props = dict(
        text=specimen.label, 
        x=settings.PLOT_LEFT-0.05, 
        y=label_offset, 
        clip_on=False,
        horizontalalignment='right', 
        verticalalignment='center', 
        transform=transforms.blended_transform_factory(axes.get_figure().transFigure, axes.transData)
    )
    if text:
        for key in props: getattr(text, "set_%s"%key)(props[key])
    else:
        text = Text(**props)
    if not text in axes.get_children():
        axes.add_artist(text)
    labels.append(text)
    specimen.__plot_label_artist = text

def apply_transform(data, scale=1, offset=0, cap=0):
    data_x, data_y = data
    data_y = np.array(data_y) #make a copy
    if cap > 0:
        np.copyto(data_y, [cap], where=(data_y>=cap)) #copy the cap where values are larger then cap
    data_y = data_y * scale + offset #scale and offset the capped data
    return data_x, data_y

def plot_pattern(pattern, axes, scale=1, offset=0, cap=0):
    #setup or update the line       
       
    line = getattr(pattern, "__plot_line", matplotlib.lines.Line2D([],[]))
    
    line.update(dict(
        data=apply_transform(pattern.xy_store.get_raw_model_data(), scale=scale, offset=offset, cap=cap),
        color=pattern.color,
        linewidth=pattern.lw
    ))
    if not line in axes.get_lines():
        axes.add_line(line)
    pattern.__plot_line = line

def plot_specimen(project, specimen, labels, label_offset, 
        offset, scale, marker_scale, axes):
    """
        Plots a specimens patterns, markers and hatches using the given
        offset and scale
    """
    # Plot the patterns;
        
    if specimen.display_experimental:
        pattern = specimen.experimental_pattern
        
        #plot the experimental pattern:
        plot_pattern(pattern, axes, scale=scale, offset=offset, cap=pattern.cap_value)
        
        #get some common data for the next lines:        
        x_data, y_data = pattern.xy_store.get_raw_model_data()
        xmin, xmax = (np.min(x_data), np.max(x_data)) if x_data.size > 0 else (0, 0)
        ymin, ymax = (np.min(y_data), np.max(y_data)) if y_data.size > 0 else (0, 0)
        
        ########################################################################
        #plot the background pattern:
        bg_line = getattr(pattern, "__plot_bg_line", matplotlib.lines.Line2D([],[], c="#660099", lw="2"))
        if pattern.bg_type == 0 and pattern._bg_position != 0.0:
            bg_line.update(dict(
                data = apply_transform(([xmin, xmax], [pattern.bg_position, pattern.bg_position]), scale=scale, offset=offset),
                visible = True
            ))
        elif pattern.bg_type == 1 and pattern.bg_pattern != None:
            bg_line.update(dict(
                data = apply_transform((x_data, (pattern.bg_pattern * pattern.bg_scale) + pattern.bg_position), scale=scale, offset=offset),
                visible = True
            ))
        else:
            bg_line.update(dict(
                data = ([],[]),
                visible = True
            ))
            
        if bg_line.get_visible() and not bg_line in axes.get_lines():
            axes.add_line(bg_line)
        elif not bg_line.get_visible():
            try: bg_line.remove()
            except: pass
        pattern.__plot_bg_line = bg_line
        ########################################################################
        
        ########################################################################
        #plot the smooth pattern:        
        smooth_line = getattr(pattern, "__plot_smooth_line", matplotlib.lines.Line2D([],[], c="#660099", lw="2"))
        
        if int(pattern.smooth_degree) > 1:
            data = x_data, smooth(y_data, pattern.smooth_degree)
        else:
            data = [],[]
        smooth_line.update(dict(
            data = apply_transform(data, scale=scale, offset=offset),
            visible = bool(pattern.smooth_degree > 1)
        ))
        if smooth_line.get_visible() and not smooth_line in axes.get_lines():
            axes.add_line(smooth_line)
        elif not smooth_line.get_visible():
            try: smooth_line.remove()
            except: pass
        pattern.__plot_smooth_line = smooth_line
        ########################################################################
            
        ########################################################################
        #plot the shift & reference lines:       
        shifted_line = getattr(pattern, "__plot_shifted_line", matplotlib.lines.Line2D([],[], c="#660099", lw="2"))
        reference_line = getattr(pattern, "__plot_reference_line", matplotlib.lines.Line2D([],[], c="#660099", lw="2", ls="--"))
        
        if pattern.shift_value!=0.0:
            shifted_line.update(dict(
                data=apply_transform((x_data-pattern._shift_value, y_data.copy()), scale=scale, offset=offset),
                visible=True
            ))
            position = specimen.parent.goniometer.get_2t_from_nm(pattern.shift_position)
            reference_line.update(dict(
                data=apply_transform(([position, position], [0, ymax]), scale=scale, offset=offset),
                visible = True
            ))
            if not shifted_line in axes.get_lines():
                axes.add_line(shifted_line)
            if not reference_line in axes.get_lines():
                axes.add_line(reference_line)
        else:
            shifted_line.set_data([],[])
            shifted_line.set_visible(False)
            try: shifted_line.remove()
            except: pass
            reference_line.set_data([],[])
            reference_line.set_visible(False)
            try: reference_line.remove()
            except: pass
        pattern.__plot_shifted_line = shifted_line
        pattern.__plot_reference_line = reference_line
        ########################################################################
        
    if specimen.display_calculated:   
        pattern = specimen.calculated_pattern
        plot_pattern(pattern, axes, scale=scale, offset=offset)
        
        #fetch x data, y data and linewidth for the phase patterns:
        x_data = pattern.xy_store._model_data_x
        y_data_n = pattern.xy_store._model_data_y
        lw = pattern.lw
        
        #setup or update the calculated lines (phases)
        for i, phase in enumerate(pattern.phases):
            phase_line = getattr(phase, "__plot_phase_lines", dict()).get(
                specimen,
                matplotlib.lines.Line2D([],[])
            )
            phase_line.update(dict(
                data=apply_transform((x_data, y_data_n[i+1]), scale=scale, offset=offset),
                color=phase.display_color,
                linewidth=lw
            ))
            if not hasattr(phase, "__plot_phase_lines"):
                phase.__plot_phase_lines = dict() #TODO this should probably be a sort of cache (limit number of entries to 10 or so)
            if not phase_line in axes.get_lines():
                axes.add_line(phase_line)
            phase.__plot_phase_lines[specimen] = phase_line
    
    # mineral preview sticks
    if hasattr(specimen, "mineral_preview") and specimen.mineral_preview!=None:
        name, peaks = specimen.mineral_preview
        lines = getattr(specimen, "__plot_mineral_preview", [])
        for line in lines:
            try: line.remove()
            except: pass
        
        lines = []
        for position, intensity in peaks:
            position = specimen.parent.goniometer.get_2t_from_nm(position/10.)
            intensity /= 100.
            
            trans = transforms.blended_transform_factory(axes.transData, axes.transAxes)
            ymin, ymax = axes.get_ybound()
            style = "solid"
            color = "#FF00FF"
            y0 = (offset - ymin) / (ymax - ymin)
            y1 = y0 + (intensity - ymin) / (ymax - ymin)
            line = matplotlib.lines.Line2D(
                [position,position], [y0,y1],
                transform=trans, color=color, ls=style
            )
            axes.add_line(line)
            lines.append(line)
        setattr(specimen, "__plot_mineral_preview", lines)
    
    
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
    
def plot_mixtures(project, mixtures, axes):
    text = getattr(project, "__plot_mixture_text", None)
    
    str_text = u""
    for mixture in mixtures:
        str_text += u"%s:\n" % mixture.name
        str_text += u"\n".join([u"{}: {:>5.1f}".format(phase, fraction*100.0) for phase, fraction in zip(mixture.phases, mixture.fractions)])
        str_text += u"\n"
    
    props = dict(x=1.0, y=1.0,
        text=str_text,
        multialignment='right',
        horizontalalignment='right',
        verticalalignment='top',
        transform = axes.transAxes
    )
    if text:
        for key in props: getattr(text, "set_%s"%key)(props[key])
    else:
        text = Text(**props)
    if not text in axes.get_children():
        axes.add_artist(text)
    project.__plot_mixture_text = text
