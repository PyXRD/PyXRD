# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.


class Cancellable(object):
    """
        Object which has a (threaded) action that can be cancelled by the user.
    """
    _stop = None

    def _user_cancelled(self):
        return bool(self._stop is not None and self._stop.is_set())

    pass #end of class