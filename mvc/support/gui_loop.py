__add_idle_call = None
__remove_idle_call = None
__add_timeout_call = None
__remove_timeout_call = None
__setup_event_loop = None
__start_event_loop = None
__stop_event_loop = None

__idle_call_dict = {}
__timeout_call_dict = {}

def add_idle_call(func, *args, **kwargs):
    global __add_idle_call
    global __idle_call_dict
    if __add_idle_call is not None:
        __idle_call_dict[func] = __add_idle_call(func, *args, **kwargs)
    else: # toolkit does not support this or is not loaded:
        func(*args, **kwargs)
        
def remove_idle_call(func):
    global __remove_idle_call
    global __idle_call_dict
    if __remove_idle_call is not None:
        __remove_idle_call(__idle_call_dict[func])
        
def add_timeout_call(timeout, func, *args, **kwargs):
    global __add_timeout_call
    global __timeout_call_dict
    if __add_timeout_call is not None:
        __timeout_call_dict[func] = __add_timeout_call(timeout, func, *args, **kwargs)
    else: # toolkit does not support this or is not loaded:
        func(*args, **kwargs)

def remove_timeout_call(func):
    global __remove_timeout_call
    global __timeout_call_dict
    if __remove_timeout_call is not None:
        __remove_timeout_call(__timeout_call_dict[func])

def start_event_loop():
    global __start_event_loop
    if __start_event_loop is not None:
        return __start_event_loop()

def stop_event_loop():
    global __stop_event_loop
    if __stop_event_loop is not None:
        return __stop_event_loop()    


def load_toolkit_functions(
        add_idle_call, 
        remove_idle_call,
        add_timeout_call,
        remove_timeout_call,
        start_event_loop,
        stop_event_loop):
    """
        'add_idle_call' should take a function as 1st argument, the return 
        value is passed back to 'remove_idle_call'. Internally a cache is maintained
        in which keys are functions and values are return values.
        'add_timeout_call' and 'remove_timeout_call' work analogously
        start_event_loop and stop_event_loop don't take arguments and should be self-explanatory.
    """
    global __add_idle_call
    global __remove_idle_call
    global __add_timeout_call
    global __remove_timeout_call
    global __start_event_loop
    global __stop_event_loop
    assert callable(add_idle_call)
    assert callable(remove_idle_call)
    assert callable(add_timeout_call)
    assert callable(remove_timeout_call)
    assert callable(start_event_loop)
    assert callable(stop_event_loop)
    __add_idle_call = add_idle_call
    __remove_idle_call = remove_idle_call
    __add_timeout_call = add_timeout_call
    __remove_timeout_call = remove_timeout_call
    __start_event_loop = start_event_loop
    __stop_event_loop = stop_event_loop

"""
    Decorators:
"""

def run_when_idle(func):
    def callback(*args, **kwargs):
        return add_idle_call(func, *args, **kwargs)
    return callback
    
def run_every(timeout):
    def wrapper(func):
        def callback(*args, **kwargs):
            return add_timeout_call(func, timeout, *args, **kwargs)
        return callback
    return wrapper
