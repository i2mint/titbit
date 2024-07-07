"""Tools around graphs"""

from typing import Optional, Iterable


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
    """

    import re

    if not egress:
        egress = lambda s: s
    elif isinstance(egress, str):
        from lkj import import_object

        egress = import_object(egress)
    else:
        assert callable(egress), f'egress must be a callable or a string, not {egress}'

    mermaid_to_graphviz_replacements = (
        ('-->', '->'),
        ('&', ','),
    )
    mermaid_to_graphviz_replacements += tuple(extra_replacements)

    s = mermaid_code
    # Remove the first line if it starts with 'graph'
    s = '\n'.join(s.split('\n')[1:]) if s.startswith('graph') else s

    def generate_lines():
        for line in s.split('\n'):
            original_indent_len = len(line) - len(line.lstrip())
            indent = ' ' * original_indent_len

            # Extract node labels and convert to Graphviz format
            node_label_pattern = re.compile(r'(\b\w+\b)\[([^\]]+)\]')
            for match in node_label_pattern.finditer(line):
                node, label = match.groups()
                yield f'{indent}{node} [label="{label}"]'

            # Remove labels from the line
            line = node_label_pattern.sub(r'\1', line)

            # Carry out the replacements
            for old, new in mermaid_to_graphviz_replacements:
                line = line.replace(old, new)

            if '->' in line:
                yield f'{indent}{line.lstrip()}'

    # return generate_lines
    # Accumulate the generator's output and wrap it in the Graphviz graph declaration
    graphviz_code = (
        'digraph G {\n' + prefix + '\n'.join(generate_lines()) + '\n' + suffix + '}'
    )

    return graphviz_code


def attribute_dependency_graph(cls):
    """
    Return a graphviz Digraph of the attribute dependencies of a class.

    An attribute (method or property) is dependent on another attribute if it
    uses it in its definition.
    """
    from i2 import Pipe
    from i2.footprints import attribute_dependencies
    from meshed.itools import graphviz_digraph

    dependency_graph = dict(attribute_dependencies(cls))
    g = graphviz_digraph(dependency_graph)
    g.graph_dict = dependency_graph
    return g


def _merge_non_none_values(d: dict, **kwargs):
    for k, v in kwargs.items():
        if v is not None:
            d[k] = v
    return d


# TODO: When moving graph viz tools, consider injecting node attributes in signature
def update_node_attributes(
    graph,
    node_ids: Iterable,
    attributes: Optional[dict] = None,
    *,
    shape: Optional[str] = None,
    fillcolor: Optional[str] = None,
    style: Optional[str] = None,
    **extra_attributes,
):
    """
    Update attributes for specific nodes in a Graphviz Digraph.

    See list of all node attributes here: https://graphviz.org/docs/nodes/

    :param graph: The graph instance.
    :type graph: graphviz.graphs.Digraph
    :param node_ids: A list of node identifiers (labels/IDs) to update.
    :param shape: The shape attribute to update for the nodes.
    :param attributes: A dictionary of attributes to apply to the nodes.
    :param fillcolor: Color of interior of node. (Required: style='filled')
    :param style: Set style information for components of the graph.
    :param extra_attributes: Additional attributes to apply to the nodes.

    >>> import graphviz
    >>> g = graphviz.Digraph('G', filename='hello.gv')
    >>> g.node('A')
    >>> g.node('B')
    >>> g.node('C')
    >>> g.edges(['AB', 'BC', 'CA'])
    >>> g = update_node_attributes(g, ['A', 'C'], color='red', shape='box')
    >>> print(g.source)  # doctest: +NORMALIZE_WHITESPACE
    digraph G {
        A
        B
        C
        A -> B
        B -> C
        C -> A
        A [color=red shape=box]
        C [color=red shape=box]
    }

    """
    attributes = dict(attributes or {}, **extra_attributes)

    _merge_non_none_values(attributes, fillcolor=fillcolor, style=style, shape=shape)

    for node_id in node_ids:
        if any(node_id in line for line in graph.body):
            graph.node(node_id, **attributes)
        else:
            raise ValueError(f"Node {node_id} not found in the graph.")

    return graph


def graph_node_ids(graph) -> set:
    """
    Return the node identifiers (labels/IDs) of a Graphviz Digraph.

    WARNING: This is a fragile method that relies on the structure of the
    graphviz Digraph object.
    I could see no other way to do it in graphviz's API.
    See: https://graphviz.readthedocs.io/en/stable/api.html

    :param graph: The graph instance.
    :type graph: graphviz.graphs.Digraph

    >>> import graphviz
    >>> g = graphviz.Digraph('G', filename='hello.gv')
    >>> g.node('A')
    >>> g.node('B')
    >>> g.node('C')
    >>> g.edges(['AB', 'BC', 'CA'])
    >>> sorted(graph_node_ids(g))
    ['A', 'B', 'C']
    """

    def gen():
        for line in graph.body:
            if '->' not in line:
                yield line.split()[0]
            else:
                nodes_in_edge_definition = line.split('->')
                for nodes in nodes_in_edge_definition:
                    for node in nodes.split(','):
                        node = node.strip()
                        if node:
                            yield node

    return set(gen())
