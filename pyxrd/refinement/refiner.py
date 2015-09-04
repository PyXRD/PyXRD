# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import logging
logger = logging.getLogger(__name__)

import random
import time

from functools import partial

from mvc import PropIntel, OptionPropIntel
from mvc.models import TreeNode

from pyxrd.data import settings
from pyxrd.generic.models import ChildModel
from pyxrd.generic.threads import CancellableThread

from .refinables.mixins import RefinementValue, RefinementGroup
from .refinables.wrapper import RefinableWrapper

from .methods import get_all_refine_methods
from .refine_context import RefineContext

class Refiner(ChildModel):
    """
        A simple model that plugs onto the Mixture model. It provides
        the functionality related to refinement of parameters.
    """

    # MODEL INTEL:
    class Meta(ChildModel.Meta):
        properties = [ # TODO add labels
            PropIntel(name="refinables", label="", has_widget=True, data_type=object, is_column=True, widget_type="object_tree_view", class_type=RefinableWrapper),
            PropIntel(name="refine_options", label="", data_type=dict, is_column=False),
            OptionPropIntel(name="refine_method", label="Refinement method", has_widget=True, data_type=int, options={ key: method.name for key, method in get_all_refine_methods().iteritems() }),
            PropIntel(name="make_psp_plots", label="", data_type=bool, is_colum=False, has_widget=True, storable=False),
        ]
        store_id = "Refiner"

    mixture = property(ChildModel.parent.fget, ChildModel.parent.fset)

    #: Refinement context
    context = None

    #: Refinement thread (or None if not running)
    thread = None

    #: Flag, True if after refinement plots should be generated of the parameter space
    make_psp_plots = False

    #: TreeNode containing the refinable properties
    refinables = None

    #: A dict containing an instance of each refinement method
    refine_methods = None

    _refine_method = 0
    @property
    def refine_method(self):
        """ An integer describing which method to use for the refinement (see 
        refinement.methods.get_all_refine_methods) """
        return self._refine_method
    @refine_method.setter
    def refine_method(self, value): self._refine_method = int(value)

    #: A dict containing the current refinement options
    @property
    def refine_options(self):
        method = self.get_refinement_method()
        return { name: getattr(method, name) for name in method.options }

    #: A dict containing all refinement options
    @property
    def all_refine_options(self):
        return {
            method.index : { name: getattr(method, name) for name in method.options }
            for method in self.refine_methods.values()
        }

    def __init__(self, *args, **kwargs):
        my_kwargs = self.pop_kwargs(kwargs,
            "refine_method", "refine_options"
        )
        super(Refiner, self).__init__(*args, **kwargs)
        kwargs = my_kwargs

        # Setup the refinables treestore
        self.refinables = TreeNode()

        # Setup the refine methods
        try:
            self.refine_method = int(self.get_kwarg(kwargs, None, "refine_method"))
        except ValueError:
            self.refine_method = self.refine_method
            pass # ignore faulty values, these indices change from time to time.

        self.refine_methods = self.create_refine_methods(self.get_kwarg(kwargs, None, "refine_options"))

        self.update_refinement_treestore()

    # ------------------------------------------------------------
    #      Methods & Functions
    # ------------------------------------------------------------
    def setup_context(self, store=False):
        """
            Creates a RefineContext object filled with parameters based on the
            current state of the Mixture object.
        """
        self.context = RefineContext(
            parent=self.parent,
            options=self.parent.refine_options,
            store=store
        )

    def delete_context(self):
        """
            Clears the RefineContext from this model
        """
        self.context = None

    def _inner_refine(self, refine_method, context, stop=None, **kwargs):
        # Suppress updates:
        with self.mixture.needs_update.hold():
            with self.mixture.data_changed.hold():
                # If something has been selected: continue...
                if len(context.ref_props) > 0:
                    # Make sure the stop signal is not set from a previous run:
                    if stop is not None:
                        stop.clear()

                    # Log some information:
                    logger.info("-"*80)
                    logger.info("Starting refinement with this setup:")
                    msg_frm = "%22s: %s"
                    logger.info(msg_frm % ("refinement method", refine_method))
                    logger.info(msg_frm % ("number of parameters", len(context.ref_props)))
                    logger.info(msg_frm % ("GUI mode", settings.GUI_MODE))

                    # Record start time
                    t1 = time.time()

                    try: # Run until it ends or it raises an exception:
                        refine_method(context, stop=stop)
                    except any as error:
                        logger.exception("Unhandled run-time error when refining: %s" % error)
                        context.status = "error"
                        context.status_message = "Error occurred..."
                    else: # No errors occurred:
                        if stop is not None and stop.is_set():
                            context.status = "stopped"
                            context.status_message = "Stopped ..."
                            logger.info("Refinement was stopped prematurely")
                        else:
                            context.status = "finished"
                            context.status_message = "Finished"
                            logger.info("Refinement ended successfully")

                    # Record end time
                    t2 = time.time()

                    # Log some more information:
                    logger.info('%s took %0.3f ms' % ("Total refinement", (t2 - t1) * 1000.0))
                    logger.info('Best solution found was:')
                    for line in context.best_solution_to_string().split('\n'):
                        logger.info(line)
                    logger.info("-"*80)
                else: # nothing selected for refinement
                    context.status = "error"
                    context.status_message = "No parameters selected!"
                # Return the context to whatever called this
                return context

    def refine(self, threaded=False, on_complete=None, **kwargs):
        """
            This refines the selected properties using the selected algorithm.
            This can be run asynchronously when threaded is set to True.
        """

        refine_method = partial(self._inner_refine,
            self.get_refinement_method(), self.context, **kwargs)

        if not threaded:
            context = refine_method()
            if callable(on_complete):
                on_complete(context)
        else:
            def thread_completed(context):
                #Assuming this is GTK-thread safe (i.e. wrapped in @run_when_idle)
                on_complete(context)
                self.thread = None
            self.thread = CancellableThread(refine_method, thread_completed)
            self.thread.start()

    def cancel(self):
        """
            Cancels a threaded refinement, 
            and will call the on_complete callback passed to `refine`
        """
        if self.thread is not None:
            logger.info("Refinement cancelled")
            self.thread.cancel()
        else:
            logger.info("Cannot cancel, no refinement running")
        self.thread = None

    def stop(self):
        """ Stops a threaded refinement, not returning any result """
        if self.thread is not None:
            logger.info("Refinement stopped")
            self.thread.stop()
        else:
            logger.info("Cannot stop, no refinement running")
        self.thread = None

    # ------------------------------------------------------------
    #      Refinement Methods Management
    # ------------------------------------------------------------
    @staticmethod
    def get_all_refine_methods():
        return get_all_refine_methods()

    @staticmethod
    def create_refine_methods(refine_options):
        """
            Returns a dict of refine methods as values and their index as key
            with the passed refine_options dict applied.
        """

        # 1. Create a list of refinement instances:
        refine_methods = {}
        for index, method in get_all_refine_methods().iteritems():
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

    def get_refinement_method(self):
        """
            Returns the actual refinement method by translating the 
            `refine_method` attribute
        """
        return self.refine_methods[self.refine_method]

    def get_refinement_option(self, option):
        return getattr(type(self.get_refinement_method()), option)

    def get_refinement_option_value(self, option):
        return getattr(self.get_refinement_method(), option)

    def set_refinement_option_value(self, option, value):
        return setattr(self.get_refinement_method(), option, value)

    # ------------------------------------------------------------
    #      Refinables Management
    # ------------------------------------------------------------


    # TODO set a restrict range attribute on the PropIntels, so we can use custom ranges for each property
    def auto_restrict(self):
        """
            Convenience function that restricts the selected properties 
            automatically by setting their minimum and maximum values.
        """
        with self.mixture.needs_update.hold():
            for node in self.refinables.iter_children():
                ref_prop = node.object
                if ref_prop.refine and ref_prop.refinable:
                    ref_prop.value_min = ref_prop.value * 0.8
                    ref_prop.value_max = ref_prop.value * 1.2

    def randomize(self):
        """
            Convenience function that randomize the selected properties.
            Respects the current minimum and maximum values.
            Executes an optimization after the randomization.
        """
        with self.mixture.data_changed.hold_and_emit():
            with self.mixture.needs_update.hold_and_emit():
                for node in self.refinables.iter_children():
                    ref_prop = node.object
                    if ref_prop.refine and ref_prop.refinable:
                        ref_prop.value = random.uniform(ref_prop.value_min, ref_prop.value_max)

    def update_refinement_treestore(self):
        """
            This creates a tree store with all refinable properties and their
            minimum, maximum and current value.
        """
        if self.parent is not None: # not linked so no valid phases!
            self.refinables.clear()

            def add_property(parent_node, obj, prop, is_grouper):
                rp = RefinableWrapper(obj=obj, prop=prop, parent=self.mixture, is_grouper=is_grouper)
                return parent_node.append(TreeNode(rp))

            def parse_attribute(obj, prop, root_node):
                """
                    obj: the object
                    attr: the attribute of obj or None if obj contains attributes
                    root_node: the root TreeNode new iters should be put under
                """
                if prop is not None:
                    if hasattr(obj, "get_uninherited_property_value"):
                        value = obj.get_uninherited_property_value(prop)
                    else:
                        value = getattr(obj, prop.name)
                else:
                    value = obj

                if isinstance(value, RefinementValue): # AtomRelation and UnitCellProperty
                    new_node = add_property(root_node, value, prop, False)
                elif hasattr(value, "__iter__"): # List or similar
                    for new_obj in value:
                        parse_attribute(new_obj, None, root_node)
                elif isinstance(value, RefinementGroup): # Phase, Component, Probability
                    if len(value.refinables) > 0:
                        new_node = add_property(root_node, value, prop, True)
                        for prop in value.refinables:
                            parse_attribute(value, prop, new_node)
                else: # regular values
                    new_node = add_property(root_node, obj, prop, False)

            for phase in self.mixture.project.phases:
                if phase in self.mixture.phase_matrix:
                    parse_attribute(phase, None, self.refinables)


    pass # end of class
