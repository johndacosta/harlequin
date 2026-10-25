from __future__ import annotations

import pytest
from textual.app import App, ComposeResult
from textual.widgets.text_area import Selection

from harlequin.components.code_editor import CodeEditor


class EditorTestApp(App[None]):
    def compose(self) -> ComposeResult:
        yield CodeEditor(language="sql", id="editor")


@pytest.mark.asyncio
async def test_selected_queries_semicolon_boundary() -> None:
    app = EditorTestApp()
    async with app.run_test() as pilot:
        editor = app.query_one("#editor", CodeEditor)
        editor.text = "select 1;select 2;"
        await pilot.pause()

        # Selection ends right after the first semicolon: (0, 9)
        editor.selection = Selection(start=(0, 0), end=(0, 9))
        queries = editor.selected_queries()
        assert queries == ["select 1;"]

        # Cursor collapsed right after the first semicolon: (0, 9)
        editor.selection = Selection(start=(0, 9), end=(0, 9))
        queries_cursor = editor.selected_queries()
        assert queries_cursor == ["select 1;"]
