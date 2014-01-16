# coding=UTF-8
# ex:ts=4:sw=4:et=on
#  -------------------------------------------------------------------------
#  Copyright (C) 2014 by Mathijs Dumon <mathijs dot dumon at gmail dot com>
#
#  mvc is a framework derived from the original pygtkmvc framework
#  hosted at: <http://sourceforge.net/projects/pygtkmvc/>
#
#  mvc is free software; you can redistribute it and/or
#  modify it under the terms of the GNU Lesser General Public
#  License as published by the Free Software Foundation; either
#  version 2 of the License, or (at your option) any later version.
#
#  mvc is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#  Lesser General Public License for more details.
#
#  You should have received a copy of the GNU Lesser General Public
#  License along with this library; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor,
#  Boston, MA 02110, USA.
#  -------------------------------------------------------------------------

def load_all_adapters():
    from .adjustment_adapter import AdjustmentAdapter
    from .arrow_adapter import ArrowAdapter
    from .check_menu_item_adapter import CheckMenuItemAdapter
    from .color_button_adapter import ColorButtonAdapter
    from .color_selection_adapter import ColorSelectionAdapter
    from .combo_box_adapter import ComboBoxAdapter
    from .entry_adapter import EntryAdapter
    from .expander_adapter import ExpanderAdapter
    from .file_chooser_adapter import FileChooserAdapter
    from .float_entry_adapter import FloatEntryAdapter
    from .label_adapter import LabelAdapter
    from .link_button_adapter import LinkButtonAdapter
    from .scale_adapter import ScaleEntryAdapter
    from .text_view_adapter import TextViewAdapter
    from .toggle_button_adapter import ToggleButtonAdapter
    from .tree_view_adapters import XYListViewAdapter, ObjectListViewAdapter



# TODO: check if the logic below is transformed to the new handler logic
"""def __create_adapters__(self, prop_name, wid_name):
    ""
    Private service that looks at property and widgets types,
    and possibly creates one or more (best) fitting adapters
    that are returned as a list.
    ""
    from pyxrd.mvc.adapters.basic import Adapter, RoUserClassAdapter
    from pyxrd.mvc.adapters.containers import StaticContainerAdapter

    res = []

    wid = self.view[wid_name]
    if wid is None: raise ValueError("Widget '%s' not found" % wid_name)

    # Decides the type of adapters to be created.
    if isinstance(wid, gtk.Calendar):
        # calendar creates three adapter for year, month and day
        ad = RoUserClassAdapter(self.model, prop_name,
                                lambda d: d.year,
                                lambda d, y: d.replace(year=y),
                                spurious=self.accepts_spurious_change())
        ad.connect_widget(wid, lambda c: c.get_date()[0],
                          lambda c, y: c.select_month(c.get_date()[1], y),
                          "day-selected")
        res.append(ad) # year

        ad = RoUserClassAdapter(self.model, prop_name,
                                lambda d: d.month,
                                lambda d, m: d.replace(month=m),
                                spurious=self.accepts_spurious_change())
        ad.connect_widget(wid, lambda c: c.get_date()[1] + 1,
                          lambda c, m: c.select_month(m - 1, c.get_date()[0]),
                          "day-selected")
        res.append(ad) # month

        ad = RoUserClassAdapter(self.model, prop_name,
                                lambda d: d.day,
                                lambda d, v: d.replace(day=v),
                                spurious=self.accepts_spurious_change())
        ad.connect_widget(wid, lambda c: c.get_date()[2],
                          lambda c, d: c.select_day(d),
                          "day-selected")
        res.append(ad) # day
        return res


    try: # tries with StaticContainerAdapter
        ad = StaticContainerAdapter(self.model, prop_name,
                                    spurious=self.accepts_spurious_change())
        ad.connect_widget(wid)
        res.append(ad)

    except TypeError:
        # falls back to a simple adapter
        ad = Adapter(self.model, prop_name,
                     spurious=self.accepts_spurious_change())
        ad.connect_widget(wid)
        res.append(ad)
        pass

    return res"""
