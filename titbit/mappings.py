"""Titbits on mappings (key-value interfaces)"""

from typing import KT, VT, T, TypeVar, Tuple
from collections.abc import Iterable, Callable, Iterator

KeyValueAggregate = TypeVar("KeyValueAggregate")


def identity(x):
    """Return ``x`` unchanged (the default key/value/egress function)."""
    return x


# TODO: Could go further and convert non-callables to callables with itemgetter
def generate_key_values(
    iterable: Iterable[T],
    *,
    key_func: Callable[[T], KT] = identity,
    value_func: Callable[[T], VT] = identity,
    egress: Callable[[Iterator[tuple[KT, VT]]], KeyValueAggregate] = identity,
) -> KeyValueAggregate:
    """Make ``(key_func(item), value_func(item))`` pairs from an iterable,
    aggregated by ``egress`` (e.g. ``dict``; default: the pairs generator).

    >>> generate_key_values([1, 2], key_func=str, egress=dict)
    {'1': 1, '2': 2}
    """
    return egress((key_func(item), value_func(item)) for item in iterable)


from functools import partial
from operator import itemgetter


def iterable_to_dict(iterable, *, key_func=identity, value_func=identity):
    """Aggregate an iterable into a ``dict`` (``generate_key_values`` with
    ``egress=dict``). By default each item maps to itself; pass ``key_func``
    and/or ``value_func`` to shape the keys and values.

    >>> from operator import itemgetter
    >>> pairs = [('a', 1), ('b', 2)]
    >>> iterable_to_dict(pairs, key_func=itemgetter(0), value_func=itemgetter(1))
    {'a': 1, 'b': 2}
    """
    return generate_key_values(
        iterable, key_func=key_func, value_func=value_func, egress=dict
    )


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
