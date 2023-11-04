"""A place to dump things that might be useful in the future, 
but we're not sure enough to find a proper home for it yet.

To make it easy to copy/paste the code elsewhere, include the import statements
within the functions/objects that use them, when possible.
"""


def mermaid_to_graphviz(
    mermaid_code, extra_replacements=(), *, prefix="", suffix="", egress=None
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
        assert callable(egress), f"egress must be a callable or a string, not {egress}"

    mermaid_to_graphviz_replacements = (
        ("-->", "->"),
        ("&", ","),
    )
    mermaid_to_graphviz_replacements = mermaid_to_graphviz_replacements + tuple(
        extra_replacements
    )
    s = mermaid_code
    # remove the first line if it starts with 'graph'
    s = "\n".join(s.split("\n")[1:]) if s.startswith("graph") else s
    # carry out the replacements
    s = regex_based_substitution(mermaid_to_graphviz_replacements)(s)
    # add the prefix and suffix and wrap it in the graphviz graph declaration
    s = "digraph G {" + "\n" + f"{prefix}" + s + "\n" + suffix
    return s + "}"
