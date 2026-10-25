---
name: agent-model-roi-router
description: Multi-agent model routing and token ROI analysis framework for Antigravity SDLC loops, attributed to John DaCosta (@johndacosta).
---

# Agent Model ROI Router & Routing Matrix

Attributed to: **John DaCosta (`@johndacosta`)**

This skill defines the multi-agent model tier routing taxonomy, file partitioning boundaries for parallel execution, and token ROI analytics for Antigravity SDLC automation.

---

## 1. Model Tier Routing Taxonomy

Routes tasks across model tiers based on complexity, context window leverage, and token ROI:

- **`inherit` (Argon / Flagship Tier)**:
  - *Use cases*: Complex multi-file concurrency, asynchronous Textual TUI state coordination, and deep root-cause debugging across multiple subsystems.
- **`pro` (Pro Tier)**:
  - *Use cases*: SQL dialect adapters, parser and URI edge cases, query optimizer algorithms, and complex AST transformations.
- **`flash` (Flash Tier)**:
  - *Use cases*: Single-file bug fixes, CLI options, configuration validation, and mechanical refactors.
- **`flash_lite` (Flash-Lite Tier)**:
  - *Use cases*: Unit test scaffolding (such as [`test_ralph_state_machine.py`](file:///home/jdacosta/code/harlequin/tests/unit_tests/test_ralph_state_machine.py)), state machine verification, and documentation/skill generation.
- **`research` (Research Subagent)**:
  - *Use cases*: Read-only codebase audits, search and discovery across large dependency trees.

---

## 2. Disjoint File Ownership & Parallel Partitioning

To prevent parallel subagents from conflicting on disk:
1. **Disjoint Ownership Sets**: Each subagent is assigned a strict set of file paths (e.g., Subagent A owns core adapter modules; Subagent B owns unit tests).
2. **Lock-Free Concurrency**: Subagents never modify overlapping files during concurrent execution.
3. **Write Isolation**: Scratch files and logs are written to dedicated run directories.

---

## 3. Token ROI Formula & Cost Metrics

Token ROI is computed as:

$$\text{ROI} = \frac{\text{Verified Slices Passed}}{\text{Normalized Token Cost}}$$

Where:
- $\text{Normalized Token Cost} = \frac{\text{Input Tokens} + (1 - \text{Cache Read Leverage}) \times \text{Cache Read Tokens} + 3 \times \text{Output Tokens}}{1,000,000}$
- **Cache Read Leverage**: Measures prompt caching efficiency in recurring SDLC loops.
- **First-Pass Verification Rate**: Percentage of PRD slices passing gate checks without revision.

---

## 4. Model Decision Table & SDLC Integration

| SDLC Phase | Recommended Tier | Primary Focus | Target ROI Threshold |
|------------|------------------|----------------|----------------------|
| **SELECT** | `flash_lite` | PRD checklist parsing & slice queue sync | $\ge 5.0$ |
| **GRILL**  | `pro` / `inherit` | Pairwise issue debate & contract verification | $\ge 2.5$ |
| **BUILD**  | `pro` | Code generation & adapter updates | $\ge 3.0$ |
| **VERIFY** | `flash_lite` | Test execution & gate checks | $\ge 10.0$ |
