# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

from pyxrd.generic.utils import not_none
from pyxrd.refinement.async_evaluatable import AsyncEvaluatable

class RefineAsyncHelper(AsyncEvaluatable):
    """
        Helper class which can help classes having a refiner object
        
    """
    def do_async_evaluation(self, iter_func, eval_func=None, data_func=None, result_func=None):
        assert self.refiner is not None, "RefineAsyncHelper can only work when a refiner is set!"
        eval_func = not_none(eval_func, self.refiner.residual_callback)
        data_func = not_none(data_func, self.refiner.get_data_object)
        result_func = not_none(result_func, self.refiner.update)
        return super(RefineAsyncHelper, self).do_async_evaluation(
            iter_func, eval_func, data_func, result_func
        )