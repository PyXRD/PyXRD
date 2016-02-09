# coding=UTF-8
# ex:ts=4:sw=4:et=on
from functools import wraps

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.


class StatusBarMixin(object):
    @property
    def statusbar(self):
        if self.parent is not None:
            return self.parent.statusbar
        elif self.view is not None:
            return self.view['statusbar']
        else:
            return None

    @property
    def status_cid(self):
        if self.statusbar is not None:
            return self.statusbar.get_context_id(self.__class__.__name__)
        else:
            return None

    @staticmethod
    def status_message(message, cid=None):
        def decorator(func):
            @wraps(func)
            def wrapper(self, *args, **kwargs):
                self.push_status_msg(message, cid)
                res = func(self, *args, **kwargs)
                self.pop_status_msg(cid)
                return res
            return wrapper
        return decorator

    def push_status_msg(self, msg, cid=None):
        if cid is not None:
            cid = self.statusbar.get_context_id(cid)
        else:
            cid = self.status_cid
        if cid is not None:
            self.statusbar.push(cid, msg)

    def pop_status_msg(self, cid=None):
        if cid is not None:
            cid = self.statusbar.get_context_id(cid)
        else:
            cid = self.status_cid
        if cid is not None:
            self.statusbar.pop(cid)

    pass # end of class
