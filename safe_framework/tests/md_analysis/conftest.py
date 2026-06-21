"""Shared fixtures for MD analysis test suites."""

import json
import os
from pathlib import Path

import pytest


FRAMEWORK_ROOT = Path(__file__).parents[3]  # repo root
SAFE_AGENTS_ROOT = FRAMEWORK_ROOT / "safe_framework" / "agents"
PROJECT_MD_ROOT = FRAMEWORK_ROOT / "routes"  # engineer project files
REPORT_DIR = FRAMEWORK_ROOT / "test-reports"

# Default token budget per file — override with MD_TOKEN_BUDGET env var
_DEFAULT_BUDGET = 8000
TOKEN_BUDGET = int(os.environ.get("MD_TOKEN_BUDGET", _DEFAULT_BUDGET))

REQUIRED_SAFE_SECTIONS = [
    "## Overview",
    "## Pattern Diagram",
    "## Contract Specification",
    "## Azure Tools",
    "## Usage",
]

REQUIRED_PROJECT_SECTIONS = [
    "# ",
    "## ",
]


class _CharEncoder:
    """Fallback token counter: 1 token ≈ 4 characters (GPT-4o rule of thumb)."""

    def encode(self, text: str) -> list:
        return ["x"] * max(1, len(text) // 4)


def _make_encoder():
    """Try tiktoken (requires cached BPE data), fall back to char-based approx."""
    try:
        import tiktoken  # noqa: PLC0415

        enc = tiktoken.get_encoding("cl100k_base")
        enc.encode("ping")  # trigger any lazy download — fail fast if not cached
        return enc
    except Exception:
        return _CharEncoder()


@pytest.fixture(scope="session")
def enc():
    return _make_encoder()


@pytest.fixture(scope="session")
def safe_md_files():
    """All agent.md files under safe_framework/agents."""
    return sorted(SAFE_AGENTS_ROOT.rglob("agent.md"))


@pytest.fixture(scope="session")
def project_md_files():
    """All .md files under routes/ (engineer project files)."""
    if not PROJECT_MD_ROOT.exists():
        return []
    return sorted(PROJECT_MD_ROOT.rglob("*.md"))


def token_count(text: str, encoding) -> int:
    return len(encoding.encode(text))


def write_report(report_path: Path, data: dict) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
