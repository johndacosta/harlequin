---
name: model_routing_matrix
description: Detailed decision table and SDLC state machine integration guide for agent model routing.
---

# Model Routing Matrix & SDLC Integration Guide

This reference provides the comprehensive decision framework for model tier selection across Harlequin and Antigravity SDLC loops.

## Decision Matrix

1. **Architecture & TUI Concurrency (`inherit`)**:
   - Use for state machines, Textual widget lifecycles, event bus routing, and multi-file refactoring.
2. **Adapters & Parsers (`pro`)**:
   - Use for DuckDB/SQLite/VS Code adapters, SQL statement parsing, and complex query builders.
3. **Bug Fixes & CLI (`flash`)**:
   - Use for localized bug fixes, adding CLI flags, and formatting validation.
4. **Tests & State Scaffolding (`flash_lite`)**:
   - Use for writing unit tests ([`test_ralph_state_machine.py`](file:///home/jdacosta/code/harlequin/tests/unit_tests/test_ralph_state_machine.py)), checking checklists, and updating documentation.
