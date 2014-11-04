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

def load(tk_reg):
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
    
    from gobject import idle_add
    tk_reg["gtk"].idle_handler = idle_add
