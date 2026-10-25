"""Error panels must show driver text literally, including brackets."""

import locale
import time
from collections.abc import Callable

import pyarrow.compute as pc
import pyarrow.lib as pl
import pytest
from rich.console import Console
from rich.panel import Panel

from harlequin.exception import (
    HarlequinConnectionError,
    HarlequinError,
    HarlequinQueryError,
    HarlequinTzDataError,
    pretty_error_message,
    pretty_print_error,
)
from harlequin.locale_manager import set_locale
from harlequin.windows_timezone import check_and_install_tzdata

# Issue #1137, plus a title that itself contains a tag and an injected link.
_LITERAL_CASES: tuple[tuple[str, str], ...] = (
    ("no column [amount] in table [orders]", "Query Error"),
    ("syntax error near [dbo].[users]", "Query Error"),
    ("column [red]count[/red] is ambiguous", "Query Error"),
    ("[Microsoft][ODBC Driver 17]Login failed.", "Query Error"),
    ("plain message", "missing [amount]"),
    ("[link=https://evil.example/]click[/link]", "Query Error"),
)


def _plain(panel: Panel, *, width: int = 200) -> str:
    """Render with Rich's own console and return its plain-text export."""
    console = Console(
        width=width,
        record=True,
        force_terminal=True,
        color_system="truecolor",
        legacy_windows=False,
    )
    console.print(panel)
    return console.export_text()


def _capture_rich_print(callback: Callable[[], None], *, width: int = 240) -> str:
    """Run ``callback`` while Rich's print console records into a buffer."""
    import rich

    console = Console(
        width=width,
        record=True,
        force_terminal=True,
        color_system="truecolor",
        legacy_windows=False,
    )
    previous = rich._console
    rich._console = console
    try:
        callback()
    finally:
        rich._console = previous
    return console.export_text()


def test_error_panel_keeps_bracketed_text_literal() -> None:
    for message, title in _LITERAL_CASES:
        error = HarlequinQueryError(msg=message, title=title)
        first = _plain(pretty_error_message(error))
        second = _plain(pretty_error_message(error))
        assert first == second
        assert message in first
        assert title in first
        # The injected anchor must stay text. Interpreted, the panel would
        # show only the word "click" and hide the URL inside a link style.
        if "evil.example" in message:
            assert "https://evil.example/" in first
            assert "[link=" in first


def test_startup_connection_failure_keeps_driver_brackets() -> None:
    """Same wrap as ``app._handle_worker_error`` for a non-Harlequin failure."""
    driver_error = RuntimeError(
        "no column [amount] in table [orders] [link=https://evil.example/]click[/link]"
    )
    title = getattr(
        driver_error,
        "title",
        "Harlequin could not connect to your database.",
    )
    error = (
        driver_error
        if isinstance(driver_error, HarlequinError)
        else HarlequinConnectionError(msg=str(driver_error), title=str(title))
    )
    assert isinstance(error, HarlequinConnectionError)
    plain = _plain(pretty_error_message(error))
    assert "[amount]" in plain
    assert "[orders]" in plain
    assert "[link=https://evil.example/]click[/link]" in plain
    assert "Harlequin could not connect to your database." in plain


def test_omitted_title_stays_default_and_literal() -> None:
    plain = _plain(pretty_error_message(HarlequinError("boom [amount]")))
    assert "Harlequin encountered an error." in plain
    assert "[amount]" in plain


def test_pretty_print_error_prints_bracketed_text() -> None:
    message = "no column [amount] in table [orders]"
    error = HarlequinQueryError(msg=message, title="Query Error")
    printed = _capture_rich_print(lambda: pretty_print_error(error))
    assert message in printed
    assert "[amount]" in printed
    assert "[orders]" in printed
    assert "Query Error" in printed


def test_long_bracketed_message_is_returned_intact() -> None:
    line = "no column [amount] in table [orders]"
    repeats = (100_000 // (len(line) + 1)) + 1
    message = "\n".join([line] * repeats)
    assert len(message) >= 100_000
    error = HarlequinQueryError(msg=message, title="Query Error")
    started = time.perf_counter()
    plain = _plain(pretty_error_message(error), width=len(line) + 20)
    elapsed = time.perf_counter() - started
    assert plain.count("[amount]") == message.count("[amount]")
    assert plain.count("[orders]") == message.count("[orders]")
    assert elapsed < 2.0, f"render took {elapsed:.3f}s"


def test_subclass_that_does_not_opt_in_stays_literal() -> None:
    class LegacyDriverError(HarlequinError):
        def __init__(self, msg: str, title: str = "") -> None:
            Exception.__init__(self, msg)
            self.msg = msg
            self.title = title

    message = "no column [amount] in table [orders]"
    title = "missing [amount]"
    error = LegacyDriverError(message, title)
    assert not hasattr(error, "markup")
    plain = _plain(pretty_error_message(error))
    assert message in plain
    assert title in plain


def test_constructor_accepts_message_and_title_without_markup() -> None:
    positional = HarlequinQueryError("hello [amount]", "Query Error")
    assert positional.msg == "hello [amount]"
    assert positional.title == "Query Error"
    assert positional.markup is False
    keyword = HarlequinError(msg="m", title="t")
    assert keyword.markup is False
    # markup is keyword-only, so existing (msg, title) calls stay valid.
    ctor: Callable[..., HarlequinError] = HarlequinError
    with pytest.raises(TypeError):
        ctor("m", "t", True)


def test_timezone_download_failure_keeps_link_and_literal_exception(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    foreign = (
        "no column [amount] in table [orders]; "
        "syntax error near [dbo].[users]; "
        "[link=https://evil.example/]click[/link]; "
        "column [red]count[/red]; unfinished [red; close [/]"
    )

    def assume_timezone(*_args: object, **_kwargs: object) -> None:
        raise pl.ArrowInvalid("no tz database")

    def urlopen(*_args: object, **_kwargs: object) -> None:
        raise OSError(foreign)

    # Patch the modules check_and_install_tzdata calls, so the failure is
    # the real raise and not a re-built copy of the message.
    monkeypatch.setattr(pc, "assume_timezone", assume_timezone)
    monkeypatch.setattr(
        "harlequin.windows_timezone.pa.set_timezone_db_path",
        lambda _path: None,
    )
    monkeypatch.setattr("harlequin.windows_timezone.urlopen", urlopen)

    with pytest.raises(HarlequinTzDataError) as exc_info:
        check_and_install_tzdata()

    error = exc_info.value
    assert isinstance(error.__cause__, OSError)
    assert foreign in str(error.__cause__)
    plain = _plain(pretty_error_message(error), width=240)
    assert "https://harlequin.sh/docs/troubleshooting/timezone-windows" in plain
    assert "[link]" not in plain
    assert "[amount]" in plain
    assert "[orders]" in plain
    assert "[dbo]" in plain
    assert "[users]" in plain
    assert "[link=https://evil.example/]click[/link]" in plain
    assert "[red]count[/red]" in plain
    assert "[/]" in plain


def test_locale_warnings_keep_authored_bold(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail_en_us(_category: int, locale_name: str = "") -> str:
        if locale_name == "en_US.UTF-8":
            raise locale.Error("unsupported")
        return "C"

    monkeypatch.setattr("harlequin.locale_manager.locale.setlocale", fail_en_us)
    failed = _capture_rich_print(lambda: set_locale(""))
    assert "--locale" in failed
    assert "--locale C" in failed
    assert "[bold]" not in failed

    def allow_en_us(_category: int, locale_name: str = "") -> str:
        if locale_name == "en_US.UTF-8":
            return "en_US.UTF-8"
        return "C"

    monkeypatch.setattr("harlequin.locale_manager.locale.setlocale", allow_en_us)
    assumed = _capture_rich_print(lambda: set_locale(""))
    assert "--locale" in assumed
    assert "--locale C" in assumed
    assert "[bold]" not in assumed
    assert failed != assumed
