"""
Token budget analysis for SAFE agent.md files.

Counts tokens with tiktoken (cl100k_base = GPT-4o encoding).
Hard-fails CI if any single file exceeds MD_TOKEN_BUDGET (default 8000).
Writes a JSON report to test-reports/safe_token_budget.json.

Run independently:  pytest -m safe_md tests/md_analysis/test_safe_md_tokens.py
"""

import json
from pathlib import Path

import pytest

from .conftest import (
    REPORT_DIR,
    SAFE_AGENTS_ROOT,
    TOKEN_BUDGET,
    token_count,
    write_report,
)

pytestmark = pytest.mark.safe_md


@pytest.fixture(scope="module")
def all_safe_mds():
    return sorted(SAFE_AGENTS_ROOT.rglob("agent.md"))


@pytest.fixture(scope="module")
def token_report(all_safe_mds, enc):
    """Build token report once per module; write JSON artifact."""
    entries = []
    for md_file in all_safe_mds:
        content = md_file.read_text(encoding="utf-8")
        tokens = token_count(content, enc)
        entries.append(
            {
                "file": str(md_file.relative_to(SAFE_AGENTS_ROOT)),
                "tokens": tokens,
                "budget": TOKEN_BUDGET,
                "over_budget": tokens > TOKEN_BUDGET,
            }
        )

    report = {
        "suite": "safe_md",
        "budget_per_file": TOKEN_BUDGET,
        "total_files": len(entries),
        "files_over_budget": sum(1 for e in entries if e["over_budget"]),
        "max_tokens": max((e["tokens"] for e in entries), default=0),
        "avg_tokens": (
            round(sum(e["tokens"] for e in entries) / len(entries), 1) if entries else 0
        ),
        "entries": entries,
    }
    write_report(REPORT_DIR / "safe_token_budget.json", report)
    return report


class TestSafeMdTokenBudget:
    def test_report_written(self, token_report):
        report_path = REPORT_DIR / "safe_token_budget.json"
        assert report_path.exists(), "Token budget report was not written"

    def test_report_has_entries(self, token_report):
        assert token_report["total_files"] > 0, "No SAFE md files found for token analysis"

    def test_no_file_exceeds_budget(self, token_report):
        """Hard-fail: any file over MD_TOKEN_BUDGET breaks CI."""
        over = [e for e in token_report["entries"] if e["over_budget"]]
        if over:
            lines = [
                f"  {e['file']}: {e['tokens']} tokens (budget={TOKEN_BUDGET})"
                for e in over
            ]
            pytest.fail(
                f"{len(over)} file(s) exceed the {TOKEN_BUDGET}-token budget:\n"
                + "\n".join(lines)
            )

    def test_all_files_have_positive_token_count(self, token_report):
        zero = [e for e in token_report["entries"] if e["tokens"] == 0]
        assert zero == [], f"Files with 0 tokens (likely unreadable): {zero}"

    def test_summary_stats_in_report(self, token_report):
        assert "max_tokens" in token_report
        assert "avg_tokens" in token_report
        assert token_report["max_tokens"] > 0
