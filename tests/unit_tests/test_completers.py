import json
from pathlib import Path

import pytest

from harlequin.autocomplete.completers import MemberCompleter, WordCompleter
from harlequin.autocomplete.completion import HarlequinCompletion
from harlequin.catalog import Catalog, CatalogItem


@pytest.fixture
def iris_completer(data_dir: Path) -> WordCompleter:
    source = data_dir / "unit_tests" / "completions" / "iris_db.json"
    with open(source, "r") as f:
        data = f.read()
    completions = [HarlequinCompletion(**x) for x in json.loads(data)]
    completer = WordCompleter([], [], [], [])
    completer.completions = completions
    return completer


def test_completer_fixed_first(iris_completer: WordCompleter) -> None:
    completions = iris_completer("se")
    assert completions[0][1] == "select", completions[0][1]


def test_completer_fuzzy_match(iris_completer: WordCompleter) -> None:
    completions = iris_completer("width")
    labels = {x[1] for x in completions}

    assert "petal_width" in labels
    assert "sepal_width" in labels
    assert len(labels) == 2


def test_member_completer_case_insensitive_context() -> None:
    col = HarlequinCompletion(
        label="my_col",
        type_label="col",
        value="my_col",
        priority=1000,
        context="MY_TABLE",
    )
    completer = MemberCompleter([], [], [col], [])
    res_upper = completer("MY_TABLE.")
    assert len(res_upper) == 1
    assert res_upper[0][1] == "MY_TABLE.my_col"

    res_lower = completer("my_table.")
    assert len(res_lower) == 1
    assert res_lower[0][1] == "my_table.my_col"


def test_completers_merge_deduplication() -> None:
    c1 = HarlequinCompletion(
        label="id",
        type_label="col",
        value="id",
        priority=1000,
        context="users",
    )
    c2 = HarlequinCompletion(
        label="id",
        type_label="col",
        value="id",
        priority=1000,
        context="users",
    )
    merged = MemberCompleter._merge_completions([c1], [c2])
    assert len(merged) == 1


def test_completion_rich_comparisons() -> None:
    c_high = HarlequinCompletion(
        label="zebra",
        type_label="col",
        value="zebra",
        priority=100,
    )
    c_low = HarlequinCompletion(
        label="aardvark",
        type_label="col",
        value="aardvark",
        priority=500,
    )
    assert c_high < c_low
    assert c_high <= c_low
    assert c_low > c_high
    assert c_low >= c_high
