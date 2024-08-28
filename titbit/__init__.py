"""A place to dump things that might be useful in the future, 
but we're not sure enough to find a proper home for it yet.

To make it easy to copy/paste the code elsewhere, include the import statements
within the functions/objects that use them, when possible.
"""

from titbit.ast_utils import (
    rename_variables,
    bound_properties_refactor,
    BoundPropertiesRefactor,
    ensure_ast,
    filter_code,
)

from titbit.graphs import (
    mermaid_to_graphviz,
    attribute_dependency_graph,
    update_node_attributes,
)

from titbit.strings import md_toc_string


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
    >>> # By default, the git action performed is to pull
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
