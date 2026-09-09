from pathlib import Path

import pytest

from slopo.indexing.parsing.base import CodeUnit
from slopo.indexing.parsing.lang.ruby import parse

FIXTURES = Path(__file__).parent / "fixtures" / "ruby"


@pytest.fixture
def example() -> list[CodeUnit]:
    return parse((FIXTURES / "Example.rb").read_bytes())


@pytest.fixture
def nested_in_body() -> list[CodeUnit]:
    return parse((FIXTURES / "NestedInBody.rb").read_bytes())


@pytest.fixture
def comments() -> list[CodeUnit]:
    return parse((FIXTURES / "Comments.rb").read_bytes())


@pytest.fixture
def heredocs() -> list[CodeUnit]:
    return parse((FIXTURES / "Heredocs.rb").read_bytes())


@pytest.fixture
def modern() -> list[CodeUnit]:
    return parse((FIXTURES / "Modern.rb").read_bytes())


@pytest.fixture
def body_sizes() -> list[CodeUnit]:
    return parse((FIXTURES / "BodySizes.rb").read_bytes())


def test_extracts_methods_closures_and_blocks(example):
    assert [u.name for u in example] == [
        "inc",
        "increment",
        "adder",
        "callback",
        "<unknown>",
        "<unknown>",
        "<unknown>",
    ]


def test_method_bodies_exact(example):
    inc = next(u for u in example if u.name == "inc")
    increment = next(u for u in example if u.name == "increment")
    assert inc.body == "def inc(x) = x + 1"
    assert increment.body == "def self.increment(x) = x + 1"


def test_line_numbers_are_one_based_and_correct(example):
    inc = next(u for u in example if u.name == "inc")
    assert inc.start_line == 2
    assert inc.end_line == 2


def test_bound_closure_bodies_exact(example):
    adder = next(u for u in example if u.name == "adder")
    callback = next(u for u in example if u.name == "callback")
    assert adder.body == "->(x) { x + 1 }"
    assert callback.body == "proc { |x| x + 1 }"


def test_body_node_count_excludes_parameters(example):
    inc = next(u for u in example if u.name == "inc")
    adder = next(u for u in example if u.name == "adder")
    callback = next(u for u in example if u.name == "callback")
    assert inc.body_node_count == 3
    assert adder.body_node_count == 4
    assert callback.body_node_count == 4


def test_nested_call_bodies_exact(example):
    calls = [u for u in example if u.name == "<unknown>"]
    assert calls[0].body == 'describe "X" do\n  it("works") { check }\nend'
    assert calls[1].body == 'it("works") { check }'


def test_nested_block_is_emitted_alongside_method(nested_in_body):
    assert [u.name for u in nested_in_body] == ["f", "<unknown>"]
    assert nested_in_body[0].body == "def f; xs.map { |x| x + 1 }; end"
    assert nested_in_body[1].body == "xs.map { |x| x + 1 }"


def test_strips_comments_but_preserves_string_content(comments):
    assert comments[0].body == 'def f\n  1 \n  "# literal"\nend'


def test_method_contained_heredoc_is_preserved(heredocs):
    assert heredocs[0].body == "def f\n  <<~TXT\n  # literal\n  TXT\nend"
    assert heredocs[0].start_line == 1
    assert heredocs[0].end_line == 5


def test_endless_heredoc_uses_native_method_span(heredocs):
    # Tree-sitter puts the payload outside the method node.
    assert heredocs[1].body == "def text = <<~TEXT"
    assert heredocs[1].start_line == 7
    assert heredocs[1].end_line == 7


def test_modern_method_bodies_exact(modern):
    assert [u.body for u in modern if u.name != "<unknown>"] == [
        "def forward(...) = g(...)",
        "def anonymous(*, **, &); g(*, **, &); end",
        "def pattern(x); case x; in {name:}; name; end; end",
        "def implicit; xs.map { it.to_s }; end",
    ]


def test_data_section_is_not_code(modern):
    assert [u.name for u in modern] == [
        "forward",
        "anonymous",
        "pattern",
        "implicit",
        "<unknown>",
    ]


def test_empty_bodies_have_zero_nodes(body_sizes):
    assert [u.name for u in body_sizes] == ["empty", "empty_lambda", "empty_block"]
    assert [u.body_node_count for u in body_sizes] == [0, 0, 0]
