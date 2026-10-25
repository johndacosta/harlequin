"""Agent backends: Cursor SDK, agent CLI, or dry-run."""

from __future__ import annotations

import os
import re
import subprocess
import textwrap
from abc import ABC, abstractmethod
from pathlib import Path


class AgentBackend(ABC):
    @abstractmethod
    def run(self, *, persona: str, system: str, prompt: str, cwd: Path) -> str:
        raise NotImplementedError


class DryRunBackend(AgentBackend):
    """
    Deterministic stub for loop testing without API spend.

    On GRILL threads, the first security turn rejects once so the pair
    rebuttal path (opposition → architect amend → resolve) is exercised.
    """

    def __init__(self) -> None:
        self._grill_security_rejects = 0

    def run(self, *, persona: str, system: str, prompt: str, cwd: Path) -> str:
        issue_ids = re.findall(r"- id:\s*([^\s]+)", prompt)
        resolved = issue_ids[0] if issue_ids else "slice_priority"
        phase_grill = "PHASE=GRILL" in prompt or "phase=GRILL" in prompt.lower()

        if (
            persona == "security"
            and phase_grill
            and "slice_validity" in prompt
            and self._grill_security_rejects == 0
        ):
            self._grill_security_rejects += 1
            return textwrap.dedent(
                f"""
                [dry-run:{persona}] REJECT once to exercise opposition routing.

                ```yaml
                ralph_phase: security
                verdict: reject
                addressed_to: architect
                opposition_to: null
                next_agent: architect
                needs_agents: []
                open_issues: []
                resolved_issues: []
                ready_to_pass: false
                blocking: true
                summary: "dry-run: demand tighter escape note before accept"
                ```
                """
            ).strip()

        special = {
            "budget_steward": "proceed",
            "tech_strategy": "hold_course",
            "horizon_scout": "recorded",
            "release_steward": "not_applicable",
        }
        verdict = special.get(persona, "accept")

        return textwrap.dedent(
            f"""
            [dry-run:{persona}] No model call.
            System chars={len(system)} prompt chars={len(prompt)} cwd={cwd}

            ```yaml
            ralph_phase: {persona}
            verdict: {verdict}
            addressed_to: null
            opposition_to: null
            next_agent: null
            needs_agents: []
            open_issues: []
            resolved_issues: [{resolved}]
            ready_to_pass: true
            ready_for_build: true
            ready_for_verify: true
            blocking: false
            summary: "dry-run accept/close {resolved}"
            slice_id: dry-run-slice
            checklist_targets: []
            checklist_can_mark: []
            p0: []
            p1: []
            files_changed: []
            tests_run: []
            ponytail_skipped: "dry-run"
            commands: []
            gaps: ["dry-run: no real work"]
            blocked_reason: null
            block_v1: false
            roi: medium
            horizon_entries_added: 0
            ```
            """
        ).strip()


class AgentCliBackend(AgentBackend):
    """
    Live runs via the Cursor `agent` CLI (uses logged-in CLI session).
    Does not require CURSOR_API_KEY when `agent status` shows logged in.
    """

    def __init__(self, model: str = "composer-2.5") -> None:
        self.model = model
        self._agent_bin = os.environ.get("RALPH_AGENT_BIN", "agent")

    def run(self, *, persona: str, system: str, prompt: str, cwd: Path) -> str:
        import tempfile

        write_phase = (
            persona in {"developer", "horizon_scout"}
            or "BUILD PHASE" in prompt
            or "PROGRESS PHASE" in prompt
            or "edit `questdb-loop/V1_SHIP_CHECKLIST.md`" in prompt
            or "Append research" in prompt
        )
        full = (
            f"{system}\n\n---\n\n"
            f"You are persona **{persona}**. Follow the routing YAML contract.\n\n"
            f"{prompt}"
        )
        # Prefer a file prompt — argv length limits are easy to hit with system+docs.
        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=f"-ralph-{persona}.md",
            delete=False,
            encoding="utf-8",
        ) as fh:
            fh.write(full)
            prompt_path = fh.name

        cmd = [
            self._agent_bin,
            "-p",
            "--output-format",
            "text",
            "--model",
            self.model,
        ]
        if write_phase:
            cmd.append("--force")
        else:
            cmd.extend(["--mode", "ask"])
        cmd.append(
            f"Read the instruction file at {prompt_path} and follow it completely. "
            "Return your full answer in the chat (include the required YAML fence). "
            "Do not ask the human questions."
        )
        try:
            proc = subprocess.run(
                cmd,
                text=True,
                capture_output=True,
                cwd=str(cwd),
                timeout=int(os.environ.get("RALPH_AGENT_TIMEOUT", "600")),
                check=False,
            )
        except FileNotFoundError as e:
            raise RuntimeError(
                "Cursor `agent` CLI not found on PATH. Install Cursor Agent CLI "
                "or use --backend cursor with CURSOR_API_KEY."
            ) from e
        except subprocess.TimeoutExpired:
            return (
                "```yaml\n"
                f"ralph_phase: {persona}\n"
                "verdict: pass_turn\n"
                "ready_to_pass: true\n"
                "summary: agent-cli timeout\n"
                "```\n"
            )
        finally:
            try:
                Path(prompt_path).unlink(missing_ok=True)
            except OSError:
                pass

        out = (proc.stdout or "").strip()
        err = (proc.stderr or "").strip()
        if proc.returncode != 0 and not out:
            return (
                f"[agent-cli exit={proc.returncode}]\n{err}\n\n"
                "```yaml\n"
                f"ralph_phase: {persona}\n"
                "verdict: pass_turn\n"
                "ready_to_pass: true\n"
                f"summary: agent-cli failed rc={proc.returncode}\n"
                "```\n"
            )
        if err and "```yaml" not in out:
            out = f"{out}\n\n[stderr]\n{err}" if out else err
        return out


class CursorSdkBackend(AgentBackend):
    def __init__(self, model: str = "composer-2.5") -> None:
        self.model = model
        key = os.environ.get("CURSOR_API_KEY")
        if not key:
            raise RuntimeError(
                "CURSOR_API_KEY is required for --backend cursor. "
                "Use --backend agent-cli if the Cursor agent CLI is logged in, "
                "or --backend dry-run."
            )
        self.api_key = key

    def run(self, *, persona: str, system: str, prompt: str, cwd: Path) -> str:
        try:
            from cursor_sdk import Agent, AgentOptions, LocalAgentOptions
        except ImportError as e:
            raise RuntimeError(
                "Install cursor-sdk: pip install cursor-sdk  "
                "(or uv pip install cursor-sdk)"
            ) from e

        full = f"SYSTEM:\n{system}\n\nUSER:\n{prompt}"
        result = Agent.prompt(
            full,
            AgentOptions(
                api_key=self.api_key,
                model=self.model,
                local=LocalAgentOptions(cwd=str(cwd)),
            ),
        )
        text = (
            getattr(result, "result", None)
            or getattr(result, "text", None)
            or str(result)
        )
        status = getattr(result, "status", None)
        if status and status not in ("finished", "success", "completed", None):
            return f"[status={status}]\n{text}"
        return str(text)


def get_backend(name: str, model: str) -> AgentBackend:
    if name == "dry-run":
        return DryRunBackend()
    if name == "agent-cli":
        return AgentCliBackend(model=model)
    if name == "cursor":
        return CursorSdkBackend(model=model)
    if name == "ollama":
        return OllamaBackend()
    if name == "hybrid":
        # Cursor orchestrates judgment/tools; Ollama does codegen + cheap YAML.
        return HybridBackend(cursor=AgentCliBackend(model=model))
    raise ValueError(f"Unknown backend: {name}")


# --- Local Ollama -----------------------------------------------------------

# Personas safe/cheap on local models (YAML + drafts). Judgment/tools stay on Cursor.
OLLAMA_PERSONAS = frozenset(
    {
        "developer",
        "horizon_scout",
        "budget_steward",
        "release_steward",
    }
)

CURSOR_PERSONAS = frozenset(
    {
        "architect",
        "product_lead",
        "security",
        "qa",
        "tech_strategy",
        "dialect_specialist",
    }
)


class OllamaBackend(AgentBackend):
    """Direct Ollama generate — good for drafts/YAML, not for shell/tool use."""

    def __init__(
        self,
        code_model: str | None = None,
        chat_model: str | None = None,
    ) -> None:
        quality = os.environ.get("RALPH_OLLAMA_QUALITY", "").lower() in {
            "1",
            "true",
            "yes",
            "high",
        }
        if quality:
            default_code = "qwen3-coder:30b"
        else:
            # Prefer 14b when installed (fits ~12GB VRAM); else 7b.
            try:
                from .ollama_client import ollama_tags

                tags = set(ollama_tags())
            except Exception:  # noqa: BLE001
                tags = set()
            if "qwen2.5-coder:14b" in tags:
                default_code = "qwen2.5-coder:14b"
            else:
                default_code = "qwen2.5-coder:7b"

        self.code_model = code_model or os.environ.get(
            "RALPH_OLLAMA_CODE", default_code
        )
        self.chat_model = chat_model or os.environ.get("RALPH_OLLAMA_CHAT", "qwen3:8b")

    def _model_for(self, persona: str) -> str:
        if persona == "developer":
            return self.code_model
        return self.chat_model

    def run(self, *, persona: str, system: str, prompt: str, cwd: Path) -> str:
        from .context_pack import pack_context
        from .ollama_client import ollama_generate

        model = self._model_for(persona)
        extra = ""
        if persona == "developer":
            extra = (
                "\n\n"
                + pack_context(
                    cwd,
                    hint_text=prompt,
                    max_chars=int(os.environ.get("RALPH_OLLAMA_CTX_CHARS", "48000")),
                )
                + "\n\n## Codegen rules\n"
                "- Propose concrete file edits as fenced blocks labeled "
                "`## FILE: path/to/file.py` then a python fence.\n"
                "- Prefer minimal diffs. Follow ponytail.\n"
                "- End with the routing YAML contract "
                "(ready_for_verify, files_changed, etc.).\n"
                "- Do NOT claim you ran tests; Cursor will apply and verify.\n"
            )
        full_prompt = prompt + extra
        sys = (
            system
            + f"\n\nYou are persona **{persona}** running on local Ollama ({model}). "
            "Always end with one ```yaml fence for the routing contract."
        )
        timeout = float(os.environ.get("RALPH_OLLAMA_TIMEOUT", "900"))
        try:
            return ollama_generate(
                model=model,
                prompt=full_prompt,
                system=sys,
                timeout=timeout,
            )
        except Exception as e:  # noqa: BLE001 — surface as YAML pass_turn
            return (
                f"[ollama error: {e}]\n\n"
                "```yaml\n"
                f"ralph_phase: {persona}\n"
                "verdict: pass_turn\n"
                "ready_to_pass: true\n"
                "ready_for_verify: false\n"
                f"summary: ollama failed: {e}\n"
                "```\n"
            )


class HybridBackend(AgentBackend):
    """
    Cursor (agent-cli) for judgment + tools; Ollama for codegen and cheap roles.

    Developer flow: Ollama drafts → Cursor applies patches with --force.
    """

    def __init__(self, cursor: AgentBackend | None = None) -> None:
        self.cursor = cursor or AgentCliBackend()
        self.ollama = OllamaBackend()
        # Allow override: RALPH_HYBRID_OLLAMA=developer,horizon_scout
        raw = os.environ.get("RALPH_HYBRID_OLLAMA", "")
        if raw.strip():
            self.ollama_personas = frozenset(
                x.strip() for x in raw.split(",") if x.strip()
            )
        else:
            self.ollama_personas = OLLAMA_PERSONAS

    def run(self, *, persona: str, system: str, prompt: str, cwd: Path) -> str:
        use_ollama = persona in self.ollama_personas
        # Force Cursor for tool-heavy prompts even if persona is listed.
        if "VERIFY PHASE" in prompt or persona == "qa":
            use_ollama = False
        if persona == "security":
            use_ollama = False

        if not use_ollama:
            return self.cursor.run(
                persona=persona, system=system, prompt=prompt, cwd=cwd
            )

        draft = self.ollama.run(persona=persona, system=system, prompt=prompt, cwd=cwd)

        if persona != "developer":
            return draft

        # Cursor applies Ollama's draft to the working tree, then returns YAML.
        apply_prompt = (
            "BUILD APPLY STEP (Cursor orchestrator).\n"
            "A local Ollama model drafted the implementation below.\n"
            "Your job: APPLY the edits to the repo with minimal changes, "
            "run targeted ruff/pytest if practical, and return the developer "
            "YAML contract (ready_for_verify, files_changed, tests_run).\n"
            "If the draft is wrong, fix it lightly (ponytail). "
            "Do not expand scope.\n\n"
            f"## Original build prompt\n{prompt}\n\n"
            f"## Ollama draft\n{draft}\n"
        )
        applied = self.cursor.run(
            persona="developer",
            system=system,
            prompt=apply_prompt,
            cwd=cwd,
        )
        return (
            "## Ollama draft (reference)\n\n"
            f"{draft}\n\n"
            "## Cursor apply result\n\n"
            f"{applied}\n"
        )
