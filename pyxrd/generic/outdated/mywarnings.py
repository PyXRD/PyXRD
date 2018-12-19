from warnings import filterwarnings


class OutdatedWarningBase(Warning):
    """
    Base class for warnings in this module. Use this to filter all
    warnings from this module.
    """


class OutdatedPackageWarning(OutdatedWarningBase):
    """
    Warning emitted when a package is found to be out of date.
    """


filterwarnings("always", category=OutdatedPackageWarning)


class OutdatedCheckFailedWarning(OutdatedWarningBase):
    """
    Warning emitted when checking the version of a package fails
    with an exception.
    """


class OutdatedCacheFailedWarning(OutdatedWarningBase):
    """
    Warning emitted when writing to or reading from the cache
    fails with an exception.
    """
