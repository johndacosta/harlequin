# ADR 0007: No custom QuestDB lexer in v1

## Decision

v1 does **not** require a custom Pygments/QuestDB syntax highlighter. Dialect discovery for v1 is via completions, catalog hints, and docs.

Revisit highlighting only if Harlequin gains a supported adapter lexer extension point.

## Why

There is no clear first-class adapter→lexer hook today. Gating PyPI on a highlighter risks upstream core changes and fights the credible-public schedule. Completions already surface QuestDB vocabulary.
