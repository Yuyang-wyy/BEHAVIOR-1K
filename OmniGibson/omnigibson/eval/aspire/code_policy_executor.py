"""Minimal ASPIRE-style persistent code-block executor.

The executor deliberately knows nothing about OmniGibson.  A current-environment
harness supplies the public functions exposed to generated policy code.
"""

from __future__ import annotations

import contextlib
import io
import traceback
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping


@dataclass(frozen=True)
class CodeBlockResult:
    index: int
    ok: bool
    stdout: str
    stderr: str
    result: Any


def extract_code_blocks(source: str) -> list[str]:
    """Extract ``# Code block N`` sections, or treat source as one block."""
    lines = source.splitlines(keepends=True)
    starts = [i for i, line in enumerate(lines) if line.lstrip().startswith("# Code block")]
    if not starts:
        return [source]
    blocks = []
    for offset, start in enumerate(starts):
        end = starts[offset + 1] if offset + 1 < len(starts) else len(lines)
        block = "".join(lines[start + 1 : end]).strip()
        if offset == 0:
            preamble = "".join(lines[:start]).strip()
            if preamble:
                block = preamble + "\n" + block
        if block:
            blocks.append(block)
    return blocks


class AspireCodePolicyExecutor:
    """Run generated policy blocks against an injected public API."""

    def __init__(self, api: Mapping[str, Any]) -> None:
        self._api = dict(api)
        self.reset()

    def reset(self, inputs: Mapping[str, Any] | None = None) -> None:
        self._globals: dict[str, Any] = {
            "__name__": "__main__",
            "APIS": self._api,
            "INPUTS": dict(inputs or {}),
            "RESULT": None,
        }
        self._globals.update(self._api)

    def run_source(
        self,
        source: str,
        *,
        observation: Mapping[str, Any] | None = None,
    ) -> list[CodeBlockResult]:
        self._globals["obs"] = dict(observation or {})
        results: list[CodeBlockResult] = []
        for index, code in enumerate(extract_code_blocks(source), start=1):
            stdout = io.StringIO()
            stderr = io.StringIO()
            ok = True
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                try:
                    exec(compile(code, f"<aspire-policy-block-{index}>", "exec"), self._globals, self._globals)  # noqa: S102
                except BaseException:
                    ok = False
                    traceback.print_exc(file=stderr)
            results.append(
                CodeBlockResult(
                    index=index,
                    ok=ok,
                    stdout=stdout.getvalue(),
                    stderr=stderr.getvalue(),
                    result=self._globals.get("RESULT"),
                )
            )
            if not ok:
                break
        return results

    def run_path(
        self,
        path: str | Path,
        *,
        observation: Mapping[str, Any] | None = None,
    ) -> list[CodeBlockResult]:
        return self.run_source(Path(path).read_text(encoding="utf-8"), observation=observation)
