"""A place to dump things that might be useful in the future, 
but we're not sure enough to find a proper home for it yet.

To make it easy to copy/paste the code elsewhere, include the import statements
within the functions/objects that use them, when possible.
"""


def git_action_on_projects(
    projects,
    action='pull',
    *,
    on_error=lambda project, e: print(f'Error with {project=}: {e}'),
    egress=lambda result: result.stdout,
):
    """Take git actions all the projects in the list of projects.
    A project can be a folder path or a module, or the name of a module/package.

    :param folders: list of projects

    Usage:

    >>> projects = [
    ...     some_package, "some_package_name", "some_package_dir_path"
    ... ]  # doctest: +SKIP
    >>> git_action_on_projects(projects)  # doctest: +SKIP

    """
    import os
    import subprocess

    def _pkg_folder_of_module(module):
        if hasattr(module, '__path__'):
            return os.path.dirname(module.__path__[0])
        elif isinstance(module, str):
            return _pkg_folder_of_module(__import__(module))
        else:
            raise ValueError(f"Can't resolve this module to a folder: {module}")

    def _resolve_folder(project):
        if os.path.isdir(project):
            return project
        else:
            return _pkg_folder_of_module(project)

    def _git_action(project):
        folder = _resolve_folder(project)
        try:
            # Execute git pull in the specified folder
            result = subprocess.run(
                ['git', '-C', folder, action],
                check=True,
                text=True,
                capture_output=True,
            )
            return egress(result)
        except subprocess.CalledProcessError as e:
            print(f'Failed {action=} on {folder}: {e}')
        except Exception as e:
            print(f'An error occurred with {folder}: {e}')

    for project in projects:
        try:
            yield _git_action(project)
        except Exception as e:
            if on_error:
                on_error(project, e)


def mermaid_to_graphviz(
    mermaid_code, extra_replacements=(), *, prefix='', suffix='', egress=None
):
    """Converts mermaid code to graphviz code.
    
    >>> mermaid_code = '''
    ... graph TD
    ... A --> B & C
    ... B & C --> D
    ... '''
    >>> graphviz_code = mermaid_to_graphviz(mermaid_code)
    >>> print(graphviz_code)  # doctest: +NORMALIZE_WHITESPACE
    digraph G {
    <BLANKLINE>
    graph TD
        A -> B , C
        B , C -> D
    <BLANKLINE>
    }
    """

    from lkj import regex_based_substitution, import_object

    if not egress:
        egress = lambda s: s
    elif isinstance(egress, str):
        egress = import_object(egress)
    else:
        assert callable(egress), f'egress must be a callable or a string, not {egress}'

    mermaid_to_graphviz_replacements = (
        ('-->', '->'),
        ('&', ','),
    )
    mermaid_to_graphviz_replacements = mermaid_to_graphviz_replacements + tuple(
        extra_replacements
    )
    s = mermaid_code
    # remove the first line if it starts with 'graph'
    s = '\n'.join(s.split('\n')[1:]) if s.startswith('graph') else s
    # carry out the replacements
    s = regex_based_substitution(mermaid_to_graphviz_replacements)(s)
    # add the prefix and suffix and wrap it in the graphviz graph declaration
    s = 'digraph G {' + '\n' + f'{prefix}' + s + '\n' + suffix
    return s + '}'
