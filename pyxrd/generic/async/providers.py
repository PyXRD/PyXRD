#!/usr/bin/python

# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon

import logging
logger = logging.getLogger(__name__)

from pyxrd.data.settings import ASYNC_SERER_PROVIDERS

_async_provider = None

def get_provider():
    global _async_provider
    if _async_provider is None:
        logger.info("Loading async server provider")
        for class_path in ASYNC_SERER_PROVIDERS:
            logger.info("Trying to load async server provider at %s" % class_path)
            try:
                components = class_path.split('.')
                class_name = components[-1]
                mod = __import__('.'.join(components[:-1]), fromlist=[class_name])
                klass = getattr(mod, class_name)
            except (ImportError, AttributeError):
                logger.warning("Failed to import async provider %s!" % class_path)
                continue
            _async_provider = klass
            break
        logger.info("Loaded async server provider '%s'" % _async_provider)
    return _async_provider
