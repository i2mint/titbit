# titbit

A place to dump might-be-useful-again code as an alternative of leaving in a notebook where it will never be found again

To install: `pip install titbit`

# Examples

## git_action_on_projects

Take git actions all the projects in the list of projects.
A project can be a folder path or a module, or the name of a module/package.

Tip: Use `functools.partial` to set the `action`, `on_error` and `egress` and get
the function you need to perform bulk actions.

Usage:

```python
>>> from titbit import git_action_on_projects
>>> projects = [
...     some_package, "some_package_name", "some_package_dir_path"
... ]  # doctest: +SKIP
>>> # By default, the git action performed is to pull
>>> git_action_on_projects(projects)  # doctest: +SKIP
```

## mermaid_to_graphviz

Converts mermaid code to graphviz code.

```python
>>> mermaid_code = '''
... graph TD
... A --> B & C
... B & C --> D
... '''
>>> graphviz_code = mermaid_to_graphviz(mermaid_code)
>>> print(graphviz_code)  # doctest: +NORMALIZE_WHITESPACE
digraph G {
    A -> B , C
    B , C -> D
}
>>> mermaid_code = '''
... graph TD
...     A[Score] --> B[Part]
...     B --> C[Measure]
... '''
>>> print(mermaid_to_graphviz(mermaid_code))
digraph G {
    A [label="Score"]
    B [label="Part"]
    A -> B
    C [label="Measure"]
    B -> C
}
```

## filter_code

Produce a version of the code that is filtered by the filt filter function.

```python
>>> from titbit import filter_code
>>> code_str = '''
... a = b + c
... print(a)
... d[0] = a
... for i in range(1, 10):
...     d[i] = d[i-1] + b
... def f(x):
...     return x + 1
... e = [d, a, f]
... '''
>>> import ast
>>> filtered_code_str = filter_code(code_str, lambda x: isinstance(x, ast.Assign))
>>> assert filtered_code_str.strip() == ('''
... a = b + c
... d[0] = a
... e = [d, a, f]
... '''.strip())
```

## bound_properties_refactor

Generate code that refactors "flat code" into a reusable "controller" class.
Also checkout the `BoundPropertiesRefactor` class that does all the work:
With it, you'll be able to compute intermediate datas that may be of interest.

```python
>>> from titbit import bound_properties_refactor
>>> code_str = '''
... apple = banana + carrot
... date = 'banana'
... egg = apple * 2
... egg = egg + 1
... '''
>>>
>>> refactored_code = bound_properties_refactor(code_str)
>>> print(refactored_code)  # doctest: +NORMALIZE_WHITESPACE
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
```

## ensure_ast

```python
def ensure_ast(code: AST) -> AST:
    """
    Ensures that the input is an AST node, returning it as-is if already an AST.

    If input is a string, parses it as Python code and returns the resulting AST.
    If the input is a module object, it will get the code, parse it, and return an AST.
    """
```
