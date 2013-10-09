__all__ = ("add_adapter", "remove_adapter", "search_adapter_info",
           "SIGNAL", "GETTER", "SETTER", "WIDTYPE")

# ----------------------------------------------------------------------
# This list defines a default behavior for widgets.
# If no particular behaviour has been specified, adapters will
# use information contained into this list to create themself.
# This list is ordered: the earlier a widget occurs, the better it
# will be matched by the search function.
# ----------------------------------------------------------------------
__def_adapter = []

# constants to access values:
WIDGET, SIGNAL, GETTER, SETTER, WIDTYPE = range(5)
# ----------------------------------------------------------------------

def add_adapter(widget_class, signal_name, getter, setter, value_type):
    """This function can be used to extend at runtime the set of
    default adapters. If given widget class which is being added is
    already in the default set, it will be substituted by the new one
    until the next removal (see remove_adapter)."""

    new_tu = (widget_class, signal_name, getter, setter, value_type)
    for it, tu in enumerate(__def_adapter):
        if issubclass(tu[WIDGET], widget_class):
            # found an insertion point, iteration is over after inserting
            __def_adapter.insert(it, new_tu)
            return
        pass

    # simply append it
    __def_adapter.append(new_tu)
    return


def remove_adapter(widget_class):
    """Removes the given widget class information from the default set
    of adapters.

    If widget_class had been previously added by using add_adapter,
    the added adapter will be removed, restoring possibly previusly
    existing adapter(s). Notice that this function will remove only
    *one* adapter about given wiget_class (the first found in order),
    even if many are currently stored.

    Returns True if one adapter was removed, False if no adapter was
    removed."""
    for it, tu in enumerate(__def_adapter):
        if widget_class == tu[WIDGET]:
            del __def_adapter[it]
            return True
        pass
    return False # no adapter was found


# To optimize the search
__memoize__ = {}
def search_adapter_info(wid):
    """Given a widget returns the default tuple found in __def_adapter"""
    t = type(wid)
    if __memoize__.has_key(t): return __memoize__[t]

    for w in __def_adapter:
        if isinstance(wid, w[0]):
            __memoize__[t] = w
            return w
        pass

    raise TypeError("Adapter type " + str(t) + " not found among supported adapters")

