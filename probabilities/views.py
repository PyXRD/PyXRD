# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Author: Mathijs Dumon
# This work is licensed under the Creative Commons Attribution-ShareAlike 3.0 Unported License. 
# To view a copy of this license, visit http://creativecommons.org/licenses/by-sa/3.0/ or send
# a letter to Creative Commons, 444 Castro Street, Suite 900, Mountain View, California, 94041, USA.

import gtk

from generic.views.widgets import ScaleEntry
from generic.views import BaseView, HasChildView
from probabilities.models import RGbounds

def get_correct_probability_views(probability, parent_view):
    """
        Convenience function that creates both an `IndependentsView` and 
        `MatrixView` based on the probability model passed.
    """
    if probability!=None:
        G = probability.G
        R = probability.R
        rank = probability.rank
        if (RGbounds[R,G-1] > 0):
            labels = probability.get_independent_label_map()
            return IndependentsView(labels=labels, parent=parent_view), MatrixView(R=R, G=G, rank=rank, parent=parent_view)
        else:
            raise ValueError, "Cannot (yet) handle R%d for %d layer structures!" % (R, G)        

class EditProbabilitiesView(BaseView, HasChildView):
    """
        Container view containing one `MatrixView` and one `IndependentsView`
    """
    builder = "probabilities/glade/probabilities.glade"
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
        'labels' should be a list of tuples holding the attribute name and the
        label. This label is parsed using a mathtext parser, if this causes an 
        error the raw label is displayed. The __independent_label_map__ of the
        model this view is representing should normally be passed as 'labels'.
    """
    builder = "probabilities/glade/R0_independents.glade"
    top = "R0independents_box"
    #generated table of weight fractions! (split in two columns)

    lbl_widget = "lbl_independents"
    sep_widget = "seperator_i"
    
    widget_format = "prob_%s"

    def __init__(self, labels=[], **kwargs):
        BaseView.__init__(self, **kwargs)
        
        self.labels = labels
        
        N = len(labels)
        
        def create_inputs(table):
            input_widgets = [None]*N
            for i, (prop, lbl) in enumerate(labels):
                prop, lbl = labels[i]
                
                new_lbl = self.create_mathtext_widget(lbl)
                
                #FIXME apply limits as in the model
                new_inp = ScaleEntry(lower=0.0, upper=1.0, enforce_range=True) # gtk.Entry()
                new_inp.set_tooltip_text(lbl)
                new_inp.set_name(prop)                    
                self["prob_%s" % prop] = new_inp
                input_widgets[i] = new_inp
                
                j = (i % 2)*2
                table.attach(new_lbl, 0+j, 1+j, i/2, (i/2)+1, xpadding=2, ypadding=2)
                table.attach(new_inp, 1+j, 2+j, i/2, (i/2)+1, xpadding=2, ypadding=2)
                
                del new_inp, new_lbl
            return input_widgets
        self.i_box = self['i_box']
        
        num_rows = (N+1)/2
        if not num_rows == 0:
            self.i_table = gtk.Table((N+1)/2,4, False)
            self.i_inputs = create_inputs(self.i_table)
        else:
            self.i_inputs = []
        if len(self.i_inputs)==0:
            self[self.lbl_widget].set_no_show_all(True)
            self[self.sep_widget].set_no_show_all(True)
            self[self.lbl_widget].hide()
            self[self.sep_widget].hide()
        else:
            self._add_child_view(self.i_table, self.i_box)        
                
    def update_matrices(self, model):
        for i, inp in enumerate(self.i_inputs):
            prop, lbl = self.labels[i]
            inp.set_value(getattr(model, prop))
            
    pass #end of class
            
class MatrixView(BaseView, HasChildView, ProbabilityViewMixin):
    """
        Generic view that is able to generate and update a P and W 'matrix'
        table with labels having correct tooltips (e.g. P110). Can be used for
        any combination of R, G and rank.
    """
    builder = "probabilities/glade/matrix.glade"
    top = "base_matrix_table"
         
    def __init__(self, R, G, rank, **kwargs):
        """
            Eventhough only two of R,G and rank are required theoretically, 
            they are still required by the __init__ function as a validity
            check.
        """
        BaseView.__init__(self, **kwargs)

        #make sure valid params are passed:
        assert(rank==(G**max(R,1)))
        self.create_matrices(R, G, rank)
                 
    def create_matrices(self, R, G, rank):
        #calculate moduli for parameter index calculation:
        lR = max(R,1)
        mod = [0]*lR
        for i in range(lR):
             mod[i] = rank / (G**(i+1))
        title_indeces = "".join([chr(105+i) for i in range(lR+1)])
      
      
        #Generic function for both the W and P matrix labels setup
        def create_labels(rank, table, current_lR, fmt, tooltip=lambda x,y,current_lR,fmt: ""):
            labels = [[None]*rank for _ in range(rank)]
            for x in range(rank):
                for y in range(rank):
                    new_lbl = gtk.Label("")
                    new_lbl.set_tooltip_markup(tooltip(x, y, current_lR, fmt))
                    new_lbl.set_property('justify', gtk.JUSTIFY_CENTER)
                    table.attach(new_lbl, y, y+1, x, x+1, xpadding=5, ypadding=5)
                    labels[x][y] = new_lbl
                    del new_lbl
            return labels

        #Generic functions for the tooltips:
        def diagonal_tooltips(x, y, current_lR, fmt):
            if x==y:
                indeces = [0]*current_lR
                for i in range(current_lR):
                     indeces[i] = (int(x / mod[i+(lR-current_lR)]) % G) + 1
                return fmt % tuple(indeces)
            else:
                return "-"
                
        def subdiagonal_tooltips(x, y, current_lR, fmt):
            rowsuf = [0]*current_lR # e.g. i,j,k
            colsuf = [0]*current_lR # e.g. l,m,n
            for i in range(current_lR):
                rowsuf[i] = (int(x / mod[i+(lR-current_lR)]) % G) +1
                colsuf[i] = (int(y / mod[i+(lR-current_lR)]) % G) +1
            
            #check if last n-1 and first n-1 of the suffices equal each other:
            visible = True
            for i in range(current_lR-1):
                if rowsuf[i+1] != colsuf[i]: visible = False
            if visible:
                return fmt % (tuple(rowsuf) + (colsuf[-1],))
            else:
                return "-"

        #Create the matrices:
        
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
        
        for current_lR in range(1,lR+1):
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
                "<b>P<sub>" + title_indeces[:current_lR+1] + "</sub></b>",
                rank, current_lR,
                "P<sub>" + "%d"*(current_lR+1) + "</sub>",
                subdiagonal_tooltips
            )

        #Add one extra W matrix:
        setup_everything(
            self.w_tables, self.w_titles, self.w_valids, self.w_labels,
            "<b>W<sub>" + title_indeces + "</sub></b>",
            G ** lR, lR,
            "W<sub>" + "%d"*(lR+1) + "</sub>",
            subdiagonal_tooltips
        )

        self.show_w_matrix(len(self.w_tables)-2)
        self.show_p_matrix(len(self.w_tables)-1)
                    
        return
                 
    def update_matrices(self, model):       
        lW, lP = model.get_all_matrices()
        def update_matrix(matrix, labels, mask=None, valid=False):
            shape = matrix.shape
            for i in range(shape[0]):
                for j in range(shape[1]):
                    markup = "<small><span foreground=\"%s\">%.3f</span></small>"
                    if mask!=None:
                        fgcol = "#AA0000" if mask[i,j] < 1 else "#00AA00"
                    else:
                        fgcol = "#000000"
                    labels[i][j].set_markup(markup % (fgcol, matrix[i,j]))
                    
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
        index = max(min(index, len(self.w_tables)-1),0)
        self._add_child_view(self.w_tables[index], self['w_box'])
        self["lbl_W_title"].set_markup(self.w_titles[index])
        self["lbl_W_valid"].set_markup(self.w_valids[index])
        self.show_all()
        return index
        
    def show_p_matrix(self, index):
        index = max(min(index, len(self.p_tables)-1),0)
        self._add_child_view(self.p_tables[index], self['p_box'])
        self["lbl_P_title"].set_markup(self.p_titles[index])
        self["lbl_P_valid"].set_markup(self.w_valids[index])
        self.show_all()
        return index
        
    pass #end of class
        
