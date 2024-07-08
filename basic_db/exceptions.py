class ModelNotFoundError(Exception):
    """
    Exception raised when a model is not found in the cache.
    """

    pass


class NoPrimaryKeyError(Exception):
    """
    Exception raised when Table.get() is called on a table with no primary key.
    """

    pass


class DuplicateUniqueFieldValueError(Exception):
    """
    Exception raised when a duplicate value is found for a unique field in a table.
    """

    pass
