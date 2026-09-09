import tree_sitter_ruby
from tree_sitter import Language, Node, Parser

from slopo.indexing.parsing.base import CodeUnit, hash_body

_LANGUAGE = Language(tree_sitter_ruby.language())
_PARSER = Parser(_LANGUAGE)

_COMMENT_TYPES = {"comment"}

_UNIT_TYPES = {"method", "singleton_method", "lambda"}


def parse(source: bytes) -> list[CodeUnit]:
    tree = _PARSER.parse(source)
    units: list[CodeUnit] = []
    _collect_units(tree.root_node, source, units)
    return units


def _collect_units(node: Node, source: bytes, units: list[CodeUnit]) -> None:
    if node.type in _UNIT_TYPES or (
        node.type == "call" and node.child_by_field_name("block") is not None
    ):
        body = _body_without_comments(node, source)
        units.append(
            CodeUnit(
                name=_unit_name(node),
                body=body,
                start_line=node.start_point[0] + 1,
                end_line=node.end_point[0] + 1,
                body_node_count=_count_body_nodes(node),
                body_hash=hash_body(body),
            )
        )
    for child in node.children:
        _collect_units(child, source, units)


def _unit_name(node: Node) -> str:
    name_node = node.child_by_field_name("name")
    if name_node is None and node.type in {"lambda", "call"}:
        name_node = _binding_name_node(node)
    return name_node.text.decode() if (name_node and name_node.text) else "<unknown>"


def _binding_name_node(node: Node) -> Node | None:
    parent = node.parent
    if parent is None or parent.type != "assignment":
        return None
    target = parent.child_by_field_name("left")
    return target if target is not None and target.type == "identifier" else None


def _body_without_comments(unit: Node, source: bytes) -> str:
    comment_spans: list[tuple[int, int]] = []
    _collect_comment_spans(unit, comment_spans)

    pieces: list[bytes] = []
    cursor = unit.start_byte
    for start, end in sorted(comment_spans):
        pieces.append(source[cursor:start])
        cursor = end
    pieces.append(source[cursor : unit.end_byte])
    return b"".join(pieces).decode()


def _collect_comment_spans(node: Node, spans: list[tuple[int, int]]) -> None:
    if node.type in _COMMENT_TYPES:
        spans.append((node.start_byte, node.end_byte))
        return
    for child in node.children:
        _collect_comment_spans(child, spans)


def _count_body_nodes(unit: Node) -> int:
    body = unit.child_by_field_name("body")
    if unit.type in {"call", "lambda"}:
        block = unit.child_by_field_name("block" if unit.type == "call" else "body")
        body = block.child_by_field_name("body") if block is not None else None
    if body is None:
        return 0
    return _count_named_nodes(body)


def _count_named_nodes(node: Node) -> int:
    count = 1 if node.is_named else 0
    for child in node.children:
        count += _count_named_nodes(child)
    return count
