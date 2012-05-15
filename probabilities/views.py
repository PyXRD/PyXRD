# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Author: Mathijs Dumon
# This work is licensed under the Creative Commons Attribution-ShareAlike 3.0 Unported License. 
# To view a copy of this license, visit http://creativecommons.org/licenses/by-sa/3.0/ or send
# a letter to Creative Commons, 444 Castro Street, Suite 900, Mountain View, California, 94041, USA.

import gtk

from generic.views import BaseView, HasChildView


def get_correct_probability_views(probability, parent_view):
    if probability!=None:
        G = probability.G
        R = probability.R
        labels = probability.get_independent_label_map()
        if R == 0 or G == 1:
            return R0R1R2IndependentsView(labels=labels, parent=parent_view), R0R1MatrixView(N=G, parent=parent_view)
        elif G > 1:
            if R == 1: #------------------------- R1:
                if G == 2:
                    return R0R1R2IndependentsView(labels=labels, parent=parent_view), R0R1MatrixView(N=G, parent=parent_view)
                elif G == 3:
                    return R0R1R2IndependentsView(labels=labels, parent=parent_view), R0R1MatrixView(N=G, parent=parent_view)
                elif G == 4:
                    raise ValueError, "Cannot yet handle R1 g=4" # ,R0R1MatrixView(N=G, parent=parent_view)
            elif R == 2: #----------------------- R2:
                if G == 2:
                    return R0R1R2IndependentsView(labels=labels, parent=parent_view), R2MatrixView(N=G, parent=parent_view) #raise ValueError, "Cannot yet handle R2 g=2"
                elif G == 3:
                    raise ValueError, "Cannot yet handle R2 g=3"
                elif G == 4:
                    raise ValueError, "Cannot yet handle R2 g=4"            
            elif R == 3: #----------------------- R3:
                if G == 2:
                    raise ValueError, "Cannot yet handle R3 g=2"
                elif G == 3:
                    raise ValueError, "Cannot yet handle R3 g=3"
                elif G == 4:
                    raise ValueError, "Cannot yet handle R3 g=4"
            else:
                raise ValueError, "Cannot (yet) handle Reichweite's other then 0, 1, 2 or 3"

class EditProbabilitiesView(BaseView, HasChildView):
    builder = "probabilities/glade/probabilities.glade"
    top = "edit_probabilities"
    
    independents_container = "independents_box"
    independents_view = None
    dependents_container = "dependents_box"
    dependents_view = None     
       
    def set_views(self, independents_view, dependents_view):
        self.independents_view = independents_view
        self._add_child_view(independents_view.get_top_widget(), self[self.independents_container])
        self.dependents_view = dependents_view
        self._add_child_view(dependents_view.get_top_widget(), self[self.dependents_container])
        self.show_all()
        return self.independents_view, self.dependents_view
    
class AbstractProbabilityView():
    def update_matrices(self, W, P):
        raise NotImplementedError
    
class R0R1R2IndependentsView(BaseView, HasChildView, AbstractProbabilityView):
    builder = "probabilities/glade/R0_independents.glade"
    top = "R0independents_box"
    #generated table of weight fractions! (split in two columns)

    lbl_widget = "lbl_independents"
    sep_widget = "seperator_i"

    def __init__(self, labels=[], **kwargs):
        BaseView.__init__(self, **kwargs)
        
        self.labels = labels
        
        N = len(labels)
        
        def create_inputs(table):
            label_widgets = [None]*N
            input_widgets = [None]*N
            for i, (prop, lbl) in enumerate(labels):
                prop, lbl = labels[i]
                
                new_lbl = gtk.Label(lbl % { "i": i })
                new_lbl.set_use_markup(True)
                new_lbl.set_property('justify', gtk.JUSTIFY_CENTER)
                label_widgets[i] = new_lbl
                
                new_inp = gtk.Entry()
                new_inp.set_tooltip_text(lbl % { "i": i })
                new_inp.set_name(prop)                    
                self["prob_%s" % prop] = new_inp
                input_widgets[i] = new_inp
                
                j = (i % 2)*2
                table.attach(new_lbl, 0+j, 1+j, i/2, (i/2)+1, xpadding=2, ypadding=2)
                table.attach(new_inp, 1+j, 2+j, i/2, (i/2)+1, xpadding=2, ypadding=2)
                
                del new_inp, new_lbl
            return input_widgets
        self.i_box = self['i_box']        
        self.i_table = gtk.Table((N+1)/2,4, True)
        self.i_inputs = create_inputs(self.i_table)
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
            inp.set_text("%.3f" % getattr(model, prop))
            
    pass #end of class

class R1G2IndependentsView(BaseView, AbstractProbabilityView): #TODO
    builder = "probabilities/glade/R0_independents.glade"
    top = "R0independents_box"

    def __init__(self, **kwargs):
        BaseView.__init__(self, **kwargs)
        pass
        
    pass #end of class

class R1G3IndependentsView(BaseView, AbstractProbabilityView): #TODO
    builder = "probabilities/glade/R1G3_independents.glade"
    top = ""

    def __init__(self, **kwargs):
        BaseView.__init__(self, **kwargs)
        pass
        
    pass #end of class
            
class BaseMatrixView(BaseView, HasChildView, AbstractProbabilityView):
    builder = "probabilities/glade/base_matrix.glade"
    top = "base_matrix_table"
         
    @staticmethod
    def create_labels(num, table, tooltip=lambda i,j: ""):
        labels = [[None]*num for _ in range(num)]
        for i in range(num):
            for j in range(num):
                new_lbl = gtk.Label("")
                new_lbl.set_tooltip_markup(tooltip(i,j))
                new_lbl.set_property('justify', gtk.JUSTIFY_CENTER)
                table.attach(new_lbl, j, j+1, i, i+1, xpadding=5, ypadding=5)
                labels[i][j] = new_lbl
                del new_lbl
        return labels
         
    def update_matrices(self, W, P):
        def update_matrix(matrix, labels):
            shape = matrix.shape
            for i in range(shape[0]):
                for j in range(shape[1]):
                    labels[i][j].set_text("%.3f" % matrix[i,j])
        update_matrix(W, self.w_labels)
        update_matrix(P, self.p_labels)
        
    pass #end of class        
             
class R0R1MatrixView(BaseMatrixView):   
    def __init__(self, N = 1, **kwargs):
        BaseMatrixView.__init__(self, **kwargs)

        self.w_box = self['w_box']        
        self.w_table = gtk.Table(N,N, True)
        def wtooltip(i,j):
            if i==j:return "W<sub>%(i)d</sub>" % { "i": i+1, "j": j+1 }
            else: return "-"
        self.w_labels = BaseMatrixView.create_labels(N, self.w_table, wtooltip)
        self._add_child_view(self.w_table, self.w_box)
        
        self.p_box = self['p_box']
        self.p_table = gtk.Table(N,N, True)
        self.p_labels = BaseMatrixView.create_labels(N, self.p_table, lambda i,j: "P<sub>%(i)d%(j)d</sub>" % { "i": i+1, "j": j+1 })
        self._add_child_view(self.p_table, self.p_box)
        
        self.show_all()
        
    pass #end of class
        
class R2MatrixView(BaseMatrixView):    
    def __init__(self, N = 1, **kwargs):
        BaseMatrixView.__init__(self, **kwargs)

        self.w_box = self['w_box']
        self.w_table = gtk.Table(N**2,N**2, True)
        def wtooltip(i,j):
            if i==j: return "W<sub>%(i)d%(j)d</sub>" % { "i": int(i/2)+1, "j": int(j % 2)+1 }
            else:return "-"
        self.w_labels = BaseMatrixView.create_labels(N**2, self.w_table, wtooltip)
        self._add_child_view(self.w_table, self.w_box)
        
        self.p_box = self['p_box']
        self.p_table = gtk.Table(N**2,N**2, True)
        def ptooltip(i,j):
            l = (i % N) + 1
            k = (j % N) + 1
            i = int(i/N) + 1
            j = int(j/N) + 1
            if l==j: return "P<sub>%(i)d%(j)d%(k)d</sub>" % { "i": i, "j": j, "k": k}
            else: return "-"
        self.p_labels = BaseMatrixView.create_labels(N**2, self.p_table, ptooltip)
        self._add_child_view(self.p_table, self.p_box)
        
        self.show_all()
        
    pass #end of class
        
