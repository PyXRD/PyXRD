from pyxrd.refinement.refine_method_meta import RefineMethodMeta

from methods import *  # @UnusedWildImport

class RefineMethodManager(object):
    
    @classmethod
    def initialize_methods(cls, refine_options):
        """
            Returns a dict of refine methods as values and their index as key
            with the passed refine_options dict applied.
        """
        # 1. Create a list of refinement instances:
        refine_methods = {}
        for index, method in cls.get_all_methods().iteritems():
            refine_methods[index] = method()

        # 2. Create dict of default options
        default_options = {}
        for method in refine_methods.values():
            default_options[method.index] = {
                name: getattr(type(method), name).default for name in method.options
            }

        # 3. Apply the refine options to the methods
        if not refine_options == None:
            for index, options in zip(refine_options.keys(), refine_options.values()):
                index = int(index)
                if index in refine_methods:
                    method = refine_methods[index]
                    for arg, value in zip(options.keys(), options.values()):
                        if hasattr(method, arg):
                            setattr(method, arg, value)

        return refine_methods
    
    @classmethod
    def get_all_methods(cls):
        """ Returns all the registered refinement methods """
        return RefineMethodMeta.registered_methods
    
    @classmethod
    def get_method_from_index(cls, index):
        """ Returns the actual refinement method defined by the index """
        return cls.get_all_methods()[index]
    
    pass # end of class