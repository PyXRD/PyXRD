# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

from pkg_resources import resource_filename # @UnresolvedImport

from pyxrd.generic.views import DialogView, BaseView, HasChildView

from pyxrd.goniometer.views import InlineGoniometerView

class SpecimenView(DialogView, HasChildView):
    title = "Edit Specimen"
    subview_builder = resource_filename(__name__, "../glade/specimen.glade")
    subview_toplevel = "edit_specimen"
    resizable = False

    widget_format = "specimen_%s"

    widget_groups = {
        'full_mode_only': [
            "entry_align_absolute_scale",
            "spec_scale_lbl",
            "bg_shift_align",
            "spec_bgshift_lbl",
            "absorption_align",
            "absorption_lbl",
            "spec_length_lbl",
            "entry_sample_length_align",
            "specimen_display_calculated",
            "specimen_display_stats_in_lbl",
            "specimen_inherit_calc_color",
            "specimen_calc_color",
            "specimen_display_phases",
            "vbox_calculated_data_tv",
            "lbl_specimen_calculated",
            "vbox_exclusion_ranges_tv",
            "lbl_tabexclusions",
            "general_separator",
            "spb_calc_lw",
            "specimen_inherit_calc_lw",
            "specimen_display_residuals",
            "specimen_display_derivatives"
        ]
    }

    gonio_container = widget_format % "goniometer"
    gonio_view = None

    def __init__(self, *args, **kwargs):
        self.gonio_view = InlineGoniometerView(parent=self)
        super(SpecimenView, self).__init__(*args, **kwargs)

        top = self.gonio_view.get_top_widget()
        self._add_child_view(top, self[self.gonio_container])

    def set_layout_mode(self, state):
        super(SpecimenView, self).set_layout_mode(state)
        self.gonio_view.set_layout_mode(state)

    pass # end of class

class StatisticsView(BaseView):
    builder = resource_filename(__name__, "../specimen/glade/statistics.glade")
    top = "statistics_box"

    def __init__(self, *args, **kwargs):
        BaseView.__init__(self, *args, **kwargs)

    pass # end of class
