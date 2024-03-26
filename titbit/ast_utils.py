"""AST Utils"""

import ast
from ast import AST
from functools import lru_cache, partial
from typing import Iterable, Tuple, List, KT, VT, Sequence, Callable, Dict
from collections.abc import Mapping  # not from typing because need for singledispatch
from collections import defaultdict
import inspect
from itertools import chain


# -------------------------------------------------------------------------------
# General utils


def yield_class_hierarchy(
    module, base_class: type, path: Sequence[str] = ()
) -> Iterable[Tuple[Sequence[str], str]]:
    """
    Prints out the hierarchy of AST types defined in the ast module.

    Args:
    - module: The module to visit
    - base_class: The current base class to print subclasses for
    """
    # Iterate through all classes defined in the module.
    for _, obj in inspect.getmembers(module, inspect.isclass):
        # Check if the class is a direct subclass of the current base_class.
        if issubclass(obj, base_class) and obj is not base_class:
            # yield the class name
            yield path, obj.__name__
            # Recursively print subclasses of the current class.
            yield from yield_class_hierarchy(module, obj, path + (obj.__name__,))


def group_values_by_key(kv_pairs: Iterable[Tuple[KT, VT]]) -> Dict[KT, List[VT]]:
    """
    Groups values by key in a list.

    :param kv_pairs: Iterable of key-value pairs
    :return: A dictionary with keys and list of values grouped by key

    >>> group_values_by_key([('a', 1), ('b', 2), ('a', 3)])
    {'a': [1, 3], 'b': [2]}

    """
    cumul = defaultdict(list)

    for path, name in kv_pairs:
        cumul[path].append(name)

    return dict(cumul)


# -------------------------------------------------------------------------------
# ast utils

from functools import singledispatch
from typing import Union
from types import ModuleType

Code = Union[AST, str]


@singledispatch
def ensure_ast(code: AST) -> AST:
    """Ensures that the input is an AST node, returning it as-is if already an AST.
    If input is a string, parses it as Python code and returns the resulting AST.
    """
    assert isinstance(code, AST), "Input must be an AST node or a string."
    return code


@ensure_ast.register(str)
def _(code: str) -> AST:
    """Parses a string containing Python code and returns its AST."""
    return ast.parse(code)


@ensure_ast.register(ModuleType)
def _(code: ModuleType) -> AST:
    """Parses a module and returns its AST."""
    return ensure_ast(inspect.getsource(code))


def ast_flat_hierarchy():
    """
    Returns a dictionary with the AST classes grouped by their module path.

    >>> t = ast_flat_hierarchy()
    >>> sorted(t)  # doctest: +NORMALIZE_WHITESPACE
    ['ast', 'ast.Constant', 'ast.boolop', 'ast.cmpop', 'ast.excepthandler',
    'ast.expr', 'ast.expr.Constant', 'ast.expr_context', 'ast.mod', 'ast.operator',
    'ast.pattern', 'ast.slice', 'ast.stmt', 'ast.type_ignore', 'ast.unaryop']
    >>> sorted(t['ast.expr.Constant'])
    ['Bytes', 'Ellipsis', 'NameConstant', 'Num', 'Str']

    """
    kv_pairs = yield_class_hierarchy(ast, path=('ast',), base_class=ast.AST)
    kv_pairs = (('.'.join(k), v) for k, v in kv_pairs)  # mk dot-paths from tuple paths
    return group_values_by_key(kv_pairs)


@lru_cache
def ast_class_names():
    """The set of names of ast classes"""
    return set(chain.from_iterable(ast_flat_hierarchy().values()))


# TODO: The idea here, left for later to explore, was to make it easier to
# do ast visitors using routing and namespacing.
# from i2 import Namespace
# from titbit.ast_utils import ast_class_names
# ast_types = Namespace(**{name: getattr(ast, name) for name in ast_class_names})
## etc.


CallableMapping = Callable[[KT], VT]
OldToNew = Union[CallableMapping, Mapping[KT, VT]]


@singledispatch
def ensure_callable_mapping(mapping: CallableMapping) -> CallableMapping:
    assert callable(mapping), "mapping must be callable."
    return mapping


def _default_to_key(mapping, k=None):
    if k is None:
        return partial(_default_to_key, mapping)
    return mapping.get(k, k)


@ensure_callable_mapping.register
def _ensure_callable_mapping_mapping(mapping: Mapping) -> CallableMapping:
    """Returns a callable getter that is based on a mapping.
    If the key exists, the mapping will be used to return the value.
    If not, the key itself will be returned.

    >>> func = _ensure_callable_mapping_mapping({'a': 1})
    >>> func('a')
    1
    >>> func('b')
    'b'

    """
    return _default_to_key(mapping)


def rename_variables(code: Code, old_to_new: OldToNew) -> ast.AST:
    """
    Yields a new ast.AST with all variables renamed according to new_names.

    :param code: The code string or ast.AST object to rename variables in
    :param old_to_new: A mapping from old variable names to new variable names

    >>> import ast
    >>> test_code_str = '''
    ... apple = banana + carrot
    ... date = 'banana'
    ... egg = apple * self.apple
    ... '''
    >>> transformed_test_code = rename_variables(test_code_str, {'apple': 'APPLE', 'banana': 'BANANA'})
    >>> transformed_test_code_str = ast.unparse(transformed_test_code)
    >>>
    >>> assert transformed_test_code_str.strip() == ('''
    ... APPLE = BANANA + carrot
    ... date = 'banana'
    ... egg = APPLE * self.apple
    ... '''.strip())

    """
    code = ensure_ast(code)
    old_to_new = ensure_callable_mapping(old_to_new)

    def _rename(node):
        if isinstance(node, ast.Name):
            node.id = old_to_new(node.id)
        for field, value in ast.iter_fields(node):
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, ast.AST):
                        _rename(item)
            elif isinstance(value, ast.AST):
                _rename(value)

    _rename(code)
    return code


# -------------------------------------------------------------------------------
# Refactoring flat code (e.g. notebook cells) to Controller classes


def assignments_nodes(code: Code):
    """
    Yield the `(varname, var_expression)` pairs for all assignment nodes of `code_str`.
    """
    code = ensure_ast(code)

    for node in ast.walk(code):
        if isinstance(node, ast.Assign):
            target = node.targets[0]
            if isinstance(target, ast.Name):
                yield target.id, node.value


def assignments_code(code: Code) -> Iterable[Tuple[str, str]]:
    """Yield (name, code_definition) variable assignments pairs."""
    code = ensure_ast(code)
    for name, ast_node in assignments_nodes(code):
        yield name, ast.unparse(ast_node)


def property_method_lines(varname: str, nodes):
    """
    Generate lines that would correspond to property methods for assignments
    made by the code specified by nodes, for an assignment to a variable named varname.
    """

    if len(nodes) == 1:
        yield f"return {ast.unparse(nodes[0]).strip()}"
    else:
        for node in nodes:
            yield f"{varname} = {ast.unparse(node).strip()}"
        yield f"return {varname}"


def generate_property_refactor_line(
    varname,
    nodes,
    *,
    indent='',
    decorator='@property',
    instance_name='self',
    exclude_types=(ast.Constant,),
):
    if len(nodes) == 1 and isinstance(nodes[0], exclude_types):
        yield f"{indent}{varname} = {ast.unparse(nodes[0]).strip()}" + f'\n{indent}'
    else:
        if decorator:
            yield f'{indent}{decorator}'
        yield f'{indent}def {varname}({instance_name}):'
        yield (
            '\n'.join(f"{indent}\t{x}" for x in property_method_lines(varname, nodes))
            + f'\n{indent}'
        )


def generate_lines(
    code_str, *, sep: str = '\n', decorator='@property', instance_name='self'
):
    kwargs = dict(decorator=decorator, instance_name=instance_name)
    for varname, nodes in group_values_by_key(assignments_nodes(code_str)).items():
        yield from generate_property_refactor_line(varname, nodes, **kwargs)
        if sep:
            yield sep


from dataclasses import dataclass


@dataclass
class BoundPropertiesRefactor:
    """
    Generate code that refactors "flat code" into a reusable "controller" class.

    >>> code_str = '''
    ... apple = banana + carrot
    ... date = 'banana'
    ... egg = apple * 2
    ... egg = egg + 1
    ... '''
    >>>
    >>> b = BoundPropertiesRefactor(code_str)
    >>> print(b())  # doctest: +NORMALIZE_WHITESPACE
    @property
    def apple(self):
        return banana + carrot
    <BLANKLINE>
    date = 'banana'
    <BLANKLINE>
    @property
    def egg(self):
        egg = self.apple * 2
        egg = egg + 1
        return egg
    <BLANKLINE>

    """

    code: Code

    prefix: str = ''
    indent: str = ''
    decorator: str = '@property'
    instance_name: str = 'self'
    exclude_types = (ast.Constant,)

    def __post_init__(self):
        self._refactored_lines_gen = partial(
            generate_property_refactor_line,
            indent=self.indent,
            decorator=self.decorator,
            instance_name=self.instance_name,
            exclude_types=self.exclude_types,
        )

    @property
    def assignments_to_bind(self):
        return group_values_by_key(assignments_nodes(self.code))

    @property
    def refactored_items(self):
        for varname, nodes in self.assignments_to_bind.items():
            bound_names = set(self.assignments_to_bind) - {varname}
            _rename_to_bound_var = partial(
                rename_variables,
                old_to_new={name: f'self.{name}' for name in bound_names},
            )
            yield varname, list(map(_rename_to_bound_var, nodes))

    @property
    def refactored_nodes(self):
        return dict(self.refactored_items)

    @property
    def _refactored_lines(self):
        for varname, nodes in self.refactored_nodes.items():
            yield from self._refactored_lines_gen(varname, nodes)

    @property
    def refactored_code(self):
        s = ''
        if self.prefix:
            s += self.prefix
        s += '\n'.join(self._refactored_lines)
        return s

    def __call__(self):
        return self.refactored_code
