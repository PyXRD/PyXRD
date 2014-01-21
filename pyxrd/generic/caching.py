# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

from pyxrd.generic.io import get_size, sizeof_fmt

# Apply settings
from pyxrd.data import settings
import logging
logger = logging.getLogger(__name__)

if not settings.SETTINGS_APPLIED:
    settings.apply_runtime_settings()

# Check what cache we're using and load it:
if settings.CACHE in ("FILE", "FILE_FETCH_ONLY"):
    # best choice for numpy stuff:
    logger.info("Using joblib cache (%s)" % settings.CACHE)
    from pyxrd.joblib import Memory

    cachedir = settings.DATA_REG.get_directory_path("CACHE_DIR")
    verbose = 1 if settings.DEBUG else 0

    def get_active():
        return bool(settings.CACHE == "FILE")

    memory = Memory(
        verbose=verbose,
        cachedir=cachedir,
        compress=True,
        state_getter=get_active
    )

    def cache(maxsize, cache=None, timeout=None):
        return memory.cache

    def check_cache_size(verbose=False):
        size = get_size(memory.cachedir)
        if verbose: logger.info("Cache size is:", sizeof_fmt(size))
        if size > settings.CACHE_SIZE:
            memory.clear()

elif settings.CACHE == "MEMORY":
    logger.warn("Using in-memory cache... (NOT RECOMMENDED!)")
    from pyxrd.generic.cache_collection import cache # @UnusedImport

elif settings.CACHE == None:
    logger.info("Not using cache")
    def cache(maxsize, cache=None, timeout=None):

        def dummy(func):
            func.func = func
            return func
        return dummy

else:
    raise ValueError, "Unkown value for CACHE in settings.py!"