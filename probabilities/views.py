# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Author: Mathijs Dumon
# This work is licensed under the Creative Commons Attribution-ShareAlike 3.0 Unported License. 
# To view a copy of this license, visit http://creativecommons.org/licenses/by-sa/3.0/ or send
# a letter to Creative Commons, 444 Castro Street, Suite 900, Mountain View, California, 94041, USA.

from generic.views import BaseView, HasChildView


def get_correct_probability_views(phase, parent_view):
    if phase!=None:
        G = phase.data_G
        R = phase.data_R
        if R == 0 or G == 1:
            return R0IndependentsView(N=G, parent=parent_view), R0R1MatrixView(N=G, parent=parent_view)
        elif G > 1:
            if R == 1: #------------------------- R1:
                if G == 2:
                    return R1G2IndependentsView(parent=parent_view), R0R1MatrixView(N=G, parent=parent_view)
                elif G == 3:
                    return R1G3IndependentsView(parent=parent_view), R0R1MatrixView(N=G, parent=parent_view)
                elif G == 4:
                    raise ValueError, "Cannot yet handle R1 g=4" # ,R0R1MatrixView(N=G, parent=parent_view)
            elif R == 2: #----------------------- R2:
                if G == 2:
                    raise ValueError, "Cannot yet handle R2 g=2"
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

class EditProbabilitiesView(HasChildView):
    builder = "probabilities/glade/probabilities.glade"
    top = "edit_probabilities"
    
    independents_container = "independents_box"
    independents_widget = None
    dependents_container = "matrix_view"
    dependents_view = None     
    
    
    b_independents_set = False
    def set_independents_builder(self, builder, toplevel):
        if not self.b_independents_set:
            self.b_independents_set = True
            self._builder.add_from_file(self.subview_builder)
            self.independents_widget = toplevel
            self._add_child_view(self[self.independents_widget], self[self.independents_container])

        
    def set_dependents_view(self, view):
        self.dependents_view = view
        self._add_child_view(view.get_top_widget(), self[self.dependents_container])
        return self.dependents_view
    
    
    
class R0IndependentsView(HasChildView): #TODO
    #generated table of weight fractions! (split in two columns)

     def __init__(self, N = 1, **kwargs):
        HasChildView.__init__(self, **kwargs)
        pass

class R1G2IndependentsView(BaseView): #TODO
    builder = "probabilities/glade/R1G2_independents.glade"
    top = ""

    def __init__(self, **kwargs):
        BaseView.__init__(self, **kwargs)
        pass

class R1G3IndependentsView(BaseView): #TODO
    builder = "probabilities/glade/R1G3_independents.glade"
    top = ""

    def __init__(self, **kwargs):
        BaseView.__init__(self, **kwargs)
        pass
             
class R0R1MatrixView(HasChildView):
    builder = "probabilities/glade/base_matrix.glade"
    top = "base_matrix_table"
    
    def __init__(self, N = 1, **kwargs):
        HasChildView.__init__(self, **kwargs)
        
        def create_labels(num, table, tooltip=""):
            labels = [[None]*N]*N
            for i in range(N):
                for j in range(N):
                    new_lbl = gtk.Label("")
                    new_lbl.set_tooltip_text(tooltip % { "i": i, "j": j })
                    table.attach(new_lbl, j, j+1, i, i+1, xpadding=2, ypadding=2)
                    labels[i][j] = new_lbl

        self.w_box = self['w_box']        
        self.w_table = gtk.table(N,N, True)
        self.w_labels = create_labels(N, self.w_table, "W%(i)d")
        self._add_child_view(self.w_table, self.w_box)
        
        self.p_box = self['p_box']
        self.p_table = gtk.table(N,N, True)
        self.p_labels = create_labels(N, self.p_table, "P%(i)d%(j)d")
        self._add_child_view(self.p_table, self.p_box)
                
    def update_matrices(self, W, P):
        def update_matrix(matrix, labels):        
            shape = matrix.shape
            for i in range(shape[0]):
                for j in range(shape[1]):
                    labels[i][j].set_text("%.3f" % matrix[i,j])
        update_matrix(W, self.w_labels)
        update_matrix(P, self.p_labels)
        
        
        
