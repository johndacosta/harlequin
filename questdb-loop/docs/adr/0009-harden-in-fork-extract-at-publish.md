# ADR 0009: Harden in-fork, extract at publish

## Decision

Develop and harden the QuestDB adapter **in this Harlequin fork** (`src/harlequin_questdb`) until the credible-public bar and catalog musts are met. **Extract** to a dedicated `harlequin-questdb` (or similarly named) repository as part of the PyPI publish step—not as a prerequisite for quality work.

## Why

Dual-tree development during hardening slows learning against a live QuestDB pin. Extraction is packaging/release work; quality work needs a short feedback loop in the current tree.
