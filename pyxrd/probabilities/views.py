# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

from pkg_resources import resource_filename # @UnresolvedImport

import gtk

from pyxrd.generic.views.widgets import ScaleEntry
from pyxrd.generic.views import BaseView, HasChildView
from pyxrd.probabilities.models import RGbounds
from pyxrd.generic.utils import rec_getattr

def get_correct_probability_views(probability, parent_view):
    """
        Convenience function that creates both an `IndependentsView` and 
        `MatrixView` based on the probability model passed.
    """
    if probability is not None:
        G = probability.G
        R = probability.R
        rank = probability.rank
        if (RGbounds[R, G - 1] > 0):
            return IndependentsView(meta=probability.Meta, parent=parent_view), MatrixView(R=R, G=G, rank=rank, parent=parent_view)
        else:
            raise ValueError, "Cannot (yet) handle R%d for %d layer structures!" % (R, G)

class EditProbabilitiesView(BaseView, HasChildView):
    """
        Container view containing one `MatrixView` and one `IndependentsView`
    """
    builder = resource_filename(__name__, "glade/probabilities.glade")
    top = "edit_probabilities"

    independents_container = "independents_box"
    independents_view = None
    dependents_container = "dependents_box"
    dependents_view = None

    widget_format = "prob_%s"

    def set_views(self, independents_view, dependents_view):
        self.independents_view = independents_view
        self._add_child_view(independents_view.get_top_widget(), self[self.independents_container])
        self.dependents_view = dependents_view
        self._add_child_view(dependents_view.get_top_widget(), self[self.dependents_container])
        self.show_all()
        return self.independents_view, self.dependents_view

class ProbabilityViewMixin():
    """
        Mixin class providing interface code for controllers
        of both `MatrixView` and `IndependentsView`
    """
    def update_matrices(self, W, P):
        raise NotImplementedError

class IndependentsView(BaseView, HasChildView, ProbabilityViewMixin):
    """
        Generic view that is able to generate an two-column list of inputs and 
        labels using the 'labels' argument passed upon creation.
        'labels' should be a list of tuples holding a PropIntel object and a
        label. This label is parsed using a mathtext parser, if this causes an 
        error the raw label is displayed. The __independent_label_map__ of the
        model this view is representing should normally be passed as 'labels'.
    """
    builder = resource_filename(__name__, "glade/R0_independents.glade")
    top = "R0independents_box"
    # generated table of weight fractions! (split in two columns)

    lbl_widget = "lbl_independents"
    sep_widget = "seperator_i"

    widget_format = "prob_%s"

    def __init__(self, meta, **kwargs):
        assert (meta is not None), "IndependentsView needs a model's Meta class!"
        BaseView.__init__(self, **kwargs)

        self.props = [ prop for prop in meta.all_properties if getattr(prop, "is_independent", False) ]

        N = len(self.props)

        def create_inputs(table):
            input_widgets = [None] * N
            check_widgets = [None] * N


            num_columns = 2
            column_width = 3

            for i, prop in enumerate(self.props):

                new_lbl = self.create_mathtext_widget(prop.math_label, prop.label)

                new_inp = ScaleEntry(lower=prop.minimum, upper=prop.maximum, enforce_range=True)
                new_inp.set_tooltip_text(prop.label)
                new_inp.set_name(self.widget_format % prop.name)
                self[self.widget_format % prop.name] = new_inp
                input_widgets[i] = new_inp

                j = (i % num_columns) * column_width
                table.attach(new_lbl, 0 + j, 1 + j, i / num_columns, (i / num_columns) + 1, xpadding=2, ypadding=2)
                table.attach(new_inp, 2 + j, 3 + j, i / num_columns, (i / num_columns) + 1, xpadding=2, ypadding=2)

                if prop.inh_name is not None:
                    inh_prop = meta.get_prop_intel_by_name(prop.inh_name)

                    new_check = gtk.CheckButton(label="")
                    new_check.set_tooltip_text(inh_prop.label)
                    new_check.set_name(self.widget_format % inh_prop.name)
                    new_check.set_sensitive(False)
                    self[self.widget_format % inh_prop.name] = new_check
                    check_widgets[i] = new_check
                    table.attach(new_check, 1 + j, 2 + j, i / num_columns, (i / num_columns) + 1, xpadding=2, ypadding=2, xoptions=gtk.FILL)


                del new_inp, new_lbl
            return input_widgets, check_widgets
        self.i_box = self['i_box']

        num_rows = (N + 1) / 2
        if not num_rows == 0:
            self.i_table = gtk.Table((N + 1) / 2, 4, False)
            self.i_inputs, self.i_checks = create_inputs(self.i_table)
        else:
            self.i_inputs, self.i_checks = [], []
        if len(self.i_inputs) == 0:
            self[self.lbl_widget].set_no_show_all(True)
            self[self.sep_widget].set_no_show_all(True)
            self[self.lbl_widget].hide()
            self[self.sep_widget].hide()
        else:
            self._add_child_view(self.i_table, self.i_box)

    def update_matrices(self, model):
        for i, (inp, check) in enumerate(zip(self.i_inputs, self.i_checks)):
            prop = self.props[i]
            inp.set_value(getattr(model, prop.name))
            if prop.inh_name is not None:
                # Set checkbox sensitivity:
                inh_from = rec_getattr(model, prop.inh_from, None)
                check.set_sensitive(not inh_from is None)
                # Set checkbox state:
                inh_value = getattr(model, prop.inh_name)
                check.set_active(inh_value)
                # Set inherit value sensitivity
                inp.set_sensitive(not inh_value)
            elif check is not None:
                check.set_senstive(False)

    pass # end of class

class MatrixView(BaseView, HasChildView, ProbabilityViewMixin):
    """
        Generic view that is able to generate and update a P and W 'matrix'
        table with labels having correct tooltips (e.g. P110). Can be used for
        any combination of R, G and rank.
    """
    builder = resource_filename(__name__, "glade/matrix.glade")
    top = "base_matrix_table"

    def __init__(self, R, G, rank, **kwargs):
        """
            Eventhough only two of R,G and rank are required theoretically, 
            they are still required by the __init__ function as a validity
            check.
        """
        BaseView.__init__(self, **kwargs)

        # make sure valid params are passed:
        assert(rank == (G ** max(R, 1)))
        self.create_matrices(R, G, rank)

    def create_matrices(self, R, G, rank):
        # calculate moduli for parameter index calculation:
        lR = max(R, 1)
        mod = [0] * lR
        for i in range(lR):
            mod[i] = rank / (G ** (i + 1))
        title_indeces = "".join([chr(105 + i) for i in range(lR + 1)])


        # Generic function for both the W and P matrix labels setup
        def create_labels(rank, table, current_lR, fmt, tooltip=lambda x, y, current_lR, fmt: ""):
            labels = [[None] * rank for _ in range(rank)]
            for x in range(rank):
                for y in range(rank):
                    new_lbl = gtk.Label("")
                    new_lbl.set_tooltip_markup(tooltip(x, y, current_lR, fmt))
                    new_lbl.set_property('justify', gtk.JUSTIFY_CENTER)
                    table.attach(new_lbl, y, y + 1, x, x + 1, xpadding=5, ypadding=5)
                    labels[x][y] = new_lbl
                    del new_lbl
            return labels

        # Generic functions for the tooltips:
        def diagonal_tooltips(x, y, current_lR, fmt):
            if x == y:
                indeces = [0] * current_lR
                for i in range(current_lR):
                    indeces[i] = (int(x / mod[i + (lR - current_lR)]) % G) + 1
                return fmt % tuple(indeces)
            else:
                return "-"

        def subdiagonal_tooltips(x, y, current_lR, fmt):
            rowsuf = [0] * current_lR # e.g. i,j,k
            colsuf = [0] * current_lR # e.g. l,m,n
            for i in range(current_lR):
                rowsuf[i] = (int(x / mod[i + (lR - current_lR)]) % G) + 1
                colsuf[i] = (int(y / mod[i + (lR - current_lR)]) % G) + 1

            # check if last n-1 and first n-1 of the suffices equal each other:
            visible = True
            for i in range(current_lR - 1):
                if rowsuf[i + 1] != colsuf[i]: visible = False
            if visible:
                return fmt % (tuple(rowsuf) + (colsuf[-1],))
            else:
                return "-"

        # Create the matrices:

        self.w_tables = []
        self.w_labels = []
        self.w_titles = []
        self.w_valids = []

        self.p_tables = []
        self.p_labels = []
        self.p_titles = []
        self.p_valids = []

        def setup_everything(tables, titles, valids, labels, title, rank, current_lR, lbl_fmt, tooltips):
            w_table = gtk.Table(rank, rank, True)
            tables.append(w_table)
            titles.append(title)
            valids.append("")
            labels.append(create_labels(
                rank, w_table,
                current_lR, lbl_fmt,
                tooltips
            ))

        for current_lR in range(1, lR + 1):
            rank = G ** current_lR

            setup_everything(
                self.w_tables, self.w_titles, self.w_valids, self.w_labels,
                "<b>W<sub>" + title_indeces[:current_lR] + "</sub></b>",
                rank, current_lR,
                "W<sub>" + "%d"*current_lR + "</sub>",
                diagonal_tooltips
            )

            setup_everything(
                self.p_tables, self.p_titles, self.p_valids, self.p_labels,
                "<b>P<sub>" + title_indeces[:current_lR + 1] + "</sub></b>",
                rank, current_lR,
                "P<sub>" + "%d"*(current_lR + 1) + "</sub>",
                subdiagonal_tooltips
            )

        # Add one extra W matrix:
        setup_everything(
            self.w_tables, self.w_titles, self.w_valids, self.w_labels,
            "<b>W<sub>" + title_indeces + "</sub></b>",
            G ** lR, lR,
            "W<sub>" + "%d"*(lR + 1) + "</sub>",
            subdiagonal_tooltips
        )

        self.show_w_matrix(len(self.w_tables) - 2)
        self.show_p_matrix(len(self.w_tables) - 1)

        return

    def update_matrices(self, model):
        lW, lP = model.get_all_matrices()
        def update_matrix(matrix, labels, mask=None, valid=False):
            shape = matrix.shape
            for i in range(shape[0]):
                for j in range(shape[1]):
                    markup = "<small><span foreground=\"%s\">%.3f</span></small>"
                    if mask is not None:
                        fgcol = "#AA0000" if mask[i, j] < 1 else "#00AA00"
                    else:
                        fgcol = "#000000"
                    labels[i][j].set_markup(markup % (fgcol, matrix[i, j]))

        for i, W in enumerate(lW):
            update_matrix(W, self.w_labels[i], model.W_valid_mask[i])
            fgcol, msg = ("#00AA00", "valid") if model.W_valid[i] else ("#AA0000", "invalid")
            self.w_valids[i] = "<small><span foreground=\"%s\">%s</span></small>" % (fgcol, msg)
            self["lbl_W_valid"].set_markup(self.w_valids[i])
        for i, P in enumerate(lP):
            update_matrix(P, self.p_labels[i], model.P_valid_mask[i])
            fgcol, msg = ("#00AA00", "valid") if model.P_valid[i] else ("#AA0000", "invalid")
            self.p_valids[i] = "<small><span foreground=\"%s\">%s</span></small>" % (fgcol, msg)
            self["lbl_P_valid"].set_markup(self.p_valids[i])

    def show_w_matrix(self, index):
        index = max(min(index, len(self.w_tables) - 1), 0)
        self._add_child_view(self.w_tables[index], self['w_box'])
        self["lbl_W_title"].set_markup(self.w_titles[index])
        self["lbl_W_valid"].set_markup(self.w_valids[index])
        self.show_all()
        return index

    def show_p_matrix(self, index):
        index = max(min(index, len(self.p_tables) - 1), 0)
        self._add_child_view(self.p_tables[index], self['p_box'])
        self["lbl_P_title"].set_markup(self.p_titles[index])
        self["lbl_P_valid"].set_markup(self.w_valids[index])
        self.show_all()
        return index

    pass # end of class

