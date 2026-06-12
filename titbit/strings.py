"""Tools for string parsing and manipulation."""

import os
from dol import written_key


def ensure_content_bytes(src, *, encoding: str = "utf-8"):
    """Resolve ``src`` to content bytes: bytes pass through; a string is read
    as a file path if one exists, fetched if it's an http(s) URL, and encoded
    otherwise.

    >>> ensure_content_bytes(b'xyz')
    b'xyz'
    >>> ensure_content_bytes('abc')
    b'abc'
    """
    if isinstance(src, bytes):
        return src
    elif isinstance(src, str):
        if os.path.isfile(src):
            return open(src, "rb").read()
        elif src.startswith("http://") or src.startswith("https://"):
            import requests

            return requests.get(src).content
        else:
            return src.encode(encoding)
    else:
        raise TypeError(f"src must be a string or bytes, not {type(src)}: {src=}")


def md_toc_string(md_src):
    """
    Generate a markdown table of contents (TOC) string from markdown.
    The markdown can be a string, a filepath, or a URL.

    >>> url = 'https://raw.githubusercontent.com/i2mint/titbit/master/README.md'
    >>> toc_string = md_toc_string(url)  # doctest: +SKIP
    >>> print(toc_string)  # doctest: +SKIP
    - [titbit](#titbit)
    - [Examples](#examples)
        - [md_toc_string](#md_toc_string)
        - [git_action_on_projects](#git_action_on_projects)
        - [mermaid_to_graphviz](#mermaid_to_graphviz)
        - [filter_code](#filter_code)
        - [bound_properties_refactor](#bound_properties_refactor)
        - [ensure_ast](#ensure_ast)

    """
    try:
        import md_toc
    except ImportError as e:
        raise ImportError(
            "md_toc_string needs the md-toc package: pip install md-toc"
        ) from e

    if not os.path.isfile(md_src):
        content_bytes = ensure_content_bytes(md_src)
        # save the bytes to a temp file and get the filepath for it
        md_src = written_key(content_bytes)
    return md_toc.api.build_toc(md_src)
