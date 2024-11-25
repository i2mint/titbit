"""Titbits on mappings (key-value interfaces)"""

from typing import Iterable, Callable, KT, VT, T, Iterator, TypeVar, Tuple

KeyValueAggregate = TypeVar("KeyValueAggregate")


def identity(x):
    return x


# TODO: Could go further and convert non-callables to callables with itemgetter
def generate_key_values(
    iterable: Iterable[T],
    *,
    key_func: Callable[[T], KT] = identity,
    value_func: Callable[[T], VT] = identity,
    egress: Callable[[Iterator[Tuple[KT, VT]]], KeyValueAggregate] = identity
) -> KeyValueAggregate:
    return egress((key_func(item), value_func(item)) for item in iterable)


from functools import partial
from operator import itemgetter

iterable_to_dict = partial(generate_key_values, egress=dict)
iterable_to_dict.__doc__ = """
    Convert an iterable of key-value pairs to a dictionary.

    >>> iterable_to_dict([('a', 1), ('b', 2)])
    {'a': 1, 'b': 2}

    >>> iterable_to_dict([('key1', 'value1'), ('key2', 'value2')])
    {'key1': 'value1', 'key2': 'value2'}
"""

fields_as_keys = lambda key_fields: partial(
    iterable_to_dict, key_func=itemgetter(*key_fields)
)
fields_as_keys.__doc__ = """
    Create a dictionary where the keys are derived from specific fields in the items of the iterable.

    Args:
        key_fields (int or tuple of int): The index or indices of the fields to use as keys.

    Returns:
        Callable: A function that takes an iterable and returns a dictionary.

    >>> data = [{'id': 1, 'value': 'A'}, {'id': 2, 'value': 'B'}]
    >>> fields_as_keys(['id'])(data)
    {1: {'id': 1, 'value': 'A'}, 2: {'id': 2, 'value': 'B'}}
"""

fields_as_values = lambda val_fields: partial(
    iterable_to_dict, value_func=itemgetter(*val_fields)
)
fields_as_values.__doc__ = """
    Create a dictionary where the values are derived from specific fields in the items of the iterable.

    Args:
        val_fields (int or tuple of int): The index or indices of the fields to use as values.

    Returns:
        Callable: A function that takes an iterable and returns a dictionary.

    >>> data = [{'id': 1, 'value': 'A'}, {'id': 2, 'value': 'B'}]
    >>> fields_as_values(['value'])(data)
    {'id': 'A', 'id': 'B'}
"""

fields_popped = lambda key_fields: partial(
    iterable_to_dict, key_func=lambda x: x.pop(key_fields)
)
fields_popped.__doc__ = """
    Create a dictionary where the keys are derived from specific fields in the items of the iterable,
    and those fields are removed (popped) from the items.

    Args:
        key_fields (str): The key to pop from each item to use as the dictionary key.

    Returns:
        Callable: A function that takes an iterable and returns a dictionary.

    >>> data = [{'id': 1, 'value': 'A'}, {'id': 2, 'value': 'B'}]
    >>> fields_popped('id')(data)
    {1: {'value': 'A'}, 2: {'value': 'B'}}
"""

key_and_value_fields = lambda key_fields, value_fields: partial(
    iterable_to_dict,
    key_func=itemgetter(*key_fields),
    value_func=itemgetter(*value_fields),
)
key_and_value_fields.__doc__ = """
    Create a dictionary where the keys and values are derived from separate fields in the items of the iterable.

    Args:
        key_fields (int or tuple of int): The index or indices of the fields to use as keys.
        value_fields (int or tuple of int): The index or indices of the fields to use as values.

    Returns:
        Callable: A function that takes an iterable and returns a dictionary.

    >>> data = [{'id': 1, 'value': 'A'}, {'id': 2, 'value': 'B'}]
    >>> key_and_value_fields(['id'], ['value'])(data)
    {1: 'A', 2: 'B'}
"""
