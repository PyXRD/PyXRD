import os
from time import sleep
import tempfile
import functools
from contextlib import contextmanager
from datetime import datetime, timedelta
from warnings import warn

from .mywarnings import OutdatedCacheFailedWarning

def retry(num_attempts=3, exception_class=Exception, log=None, sleeptime=1):
    """
    >>> def fail():
    ...     runs[0] += 1
    ...     {}[1]
    >>> runs = [0]; retry(sleeptime=0)(fail)()
    Traceback (most recent call last):
    ...
    KeyError: 1
    >>> runs
    [3]
    >>> runs = [0]; retry(2, sleeptime=0)(fail)()
    Traceback (most recent call last):
    ...
    KeyError: 1
    >>> runs
    [2]
    >>> runs = [0]; retry(exception_class=IndexError, sleeptime=0)(fail)()
    Traceback (most recent call last):
    ...
    KeyError: 1
    >>> runs
    [1]
    >>> logger = DoctestLogger()
    >>> runs = [0]; retry(log=logger, sleeptime=0)(fail)()
    Traceback (most recent call last):
    ...
    KeyError: 1
    >>> runs
    [3]
    >>> logger.print_logs()
    Failed with error KeyError(1,), trying again
    Failed with error KeyError(1,), trying again
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for i in range(num_attempts):
                try:
                    return func(*args, **kwargs)
                except exception_class as e:
                    if i == num_attempts - 1:
                        raise
                    else:
                        if log:
                            log.warn('Failed with error %r, trying again', e)
                        sleep(sleeptime)

        return wrapper

    return decorator

def format_date(dt):
    return dt.strftime('%Y-%m-%d %H:%M:%S')


def cache_is_valid(cache_dt):
    return format_date(datetime.now() - timedelta(days=1)) < cache_dt


# noinspection PyCompatibility
@retry()
def get_url(url):
    try:
        from urllib.request import urlopen
    except ImportError:
        # noinspection PyUnresolvedReferences
        from urllib2 import urlopen

    return urlopen(url).read().decode('utf8')


@contextmanager
def cache_file(package, mode):
    """
    Yields a file-like object for the purpose of writing to or
    reading from the cache.

    The code:

        with cache_file(...) as f:
            # do stuff with f

    is guaranteed to convert any exceptions to warnings (*),
    both in the cache_file(...) call and the 'do stuff with f'
    block.

    The file is automatically closed upon exiting the with block.

    If getting an actual file fails, yields a DummyFile.

    :param package: the name of the package being checked as a string
    :param mode: the mode to open the file in, either 'r' or 'w'
    """

    f = DummyFile()

    # We have to wrap the whole function body in this block to guarantee
    # catching all exceptions. In particular the yield needs to be inside
    # to catch exceptions coming from the with block.
    with exception_to_warning('use cache while checking for outdated package',
                              OutdatedCacheFailedWarning):
        try:
            cache_path = os.path.join(tempfile.gettempdir(),
                                      get_cache_filename(package))
            if mode == 'w' or os.path.exists(cache_path):
                f = open(cache_path, mode)
        finally:
            # Putting the yield in the finally section ensures that exactly
            # one thing is yielded once, otherwise @contextmanager would
            # raise an exception.
            with f:  # closes the file afterards
                yield f


def get_cache_filename(package):
    return 'outdated_cache_' + package


@contextmanager
def exception_to_warning(description, category, always_raise=False):
    """
    Catches any exceptions that happen in the corresponding with block
    and instead emits a warning of the given category, with a message
    containing the given description and the exception message,
    unless always_raise is True or the environment variable
    OUTDATED_RAISE_EXCEPTION is set to 1, in which caise the exception
    will not be caught.
    """

    try:
        yield
    except Exception as e:
        # We check for the presence of various globals because we may be seeing the death
        # of the process if this is in a background thread, during which globals
        # get 'cleaned up' and set to None
        if always_raise or os and os.environ and os.environ.get('OUTDATED_RAISE_EXCEPTION') == '1':
            raise

        if warn:
            warn('Failed to %s:\n'
                 '%s\n'
                 'Set the environment variable OUTDATED_RAISE_EXCEPTION=1 for a full traceback.'
                 % (description, e),
                 category)


def constantly(x):
    return lambda *_, **__: x


class DummyFile(object):
    """
    File-like object that does nothing. All methods take any arguments
    and return an empty string.
    """

    write = read = close = __enter__ = __exit__ = constantly('')
