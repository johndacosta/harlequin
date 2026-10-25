from __future__ import annotations

import click
import pytest
from click.testing import CliRunner
from textual.theme import BUILTIN_THEMES

from harlequin.colors import VALID_THEMES
from harlequin.options import SelectOption, TextOption, _validate_name


def test_select_option_tuple_choices_validation() -> None:
    option = SelectOption(
        name="compression",
        description="Compression algorithm",
        choices=[("Auto", "auto"), ("Uncompressed", "uncompressed")],
        default="auto",
    )

    assert option._flat_choices() == ["auto", "uncompressed"]

    @option.to_click_option()
    @click.command()
    def cli(compression: str) -> None:
        click.echo(f"selected: {compression}")

    runner = CliRunner()

    res_auto = runner.invoke(cli, ["--compression", "auto"])
    assert res_auto.exit_code == 0
    assert "selected: auto" in res_auto.output

    res_uncompressed = runner.invoke(cli, ["--compression", "uncompressed"])
    assert res_uncompressed.exit_code == 0
    assert "selected: uncompressed" in res_uncompressed.output

    # Validating click Choice type directly does not raise BadParameter for valid values
    click_param = cli.params[0]
    assert click_param.type.convert("auto", click_param, None) == "auto"
    assert click_param.type.convert("uncompressed", click_param, None) == "uncompressed"

    # Invalid choice raises click.BadParameter
    with pytest.raises(click.BadParameter):
        click_param.type.convert("invalid", click_param, None)


@pytest.mark.parametrize(
    "invalid_name",
    [
        "bad!name",
        "foo!bar",
        "opt$1",
        "name with space",
        "1starts_with_digit",
        "-starts-with-dash",
    ],
)
def test_validate_name_rejects_invalid_trailing_chars(invalid_name: str) -> None:
    with pytest.raises(ValueError):
        _validate_name(invalid_name)

    with pytest.raises(ValueError):
        TextOption(name=invalid_name, description="Test description")


@pytest.mark.parametrize(
    "valid_name",
    [
        "valid_name",
        "valid-name",
        "validName123",
        "option",
    ],
)
def test_validate_name_accepts_valid_names(valid_name: str) -> None:
    _validate_name(valid_name)
    opt = TextOption(name=valid_name, description="Test description")
    assert opt.name == valid_name


def test_builtin_themes_not_mutated_by_colors() -> None:
    assert "textual-ansi" in BUILTIN_THEMES
    assert "textual-ansi" not in VALID_THEMES
    assert "harlequin" in VALID_THEMES
