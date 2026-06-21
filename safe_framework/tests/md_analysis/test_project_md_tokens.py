"""
Token budget analysis for engineer project MD files under routes/.

Independent of SAFE scaffolding tests — uses separate marker (project_md)
and writes to test-reports/project_token_budget.json.

Run independently:  pytest -m project_md tests/md_analysis/test_project_md_tokens.py
"""

import pytest

from .conftest import (
    PROJECT_MD_ROOT,
    REPORT_DIR,
    TOKEN_BUDGET,
    token_count,
    write_report,
)

pytestmark = pytest.mark.project_md


@pytest.fixture(scope="module")
def project_mds():
    if not PROJECT_MD_ROOT.exists():
        return []
    return sorted(PROJECT_MD_ROOT.rglob("*.md"))


@pytest.fixture(scope="module")
def project_token_report(project_mds, enc):
    """Build token report for all project MD files."""
    entries = []
    for md_file in project_mds:
        content = md_file.read_text(encoding="utf-8")
        tokens = token_count(content, enc)
        entries.append(
            {
                "file": str(md_file.relative_to(PROJECT_MD_ROOT)),
                "tokens": tokens,
                "budget": TOKEN_BUDGET,
                "over_budget": tokens > TOKEN_BUDGET,
            }
        )

    report = {
        "suite": "project_md",
        "budget_per_file": TOKEN_BUDGET,
        "total_files": len(entries),
        "files_over_budget": sum(1 for e in entries if e["over_budget"]),
        "max_tokens": max((e["tokens"] for e in entries), default=0),
        "avg_tokens": (
            round(sum(e["tokens"] for e in entries) / len(entries), 1) if entries else 0
        ),
        "entries": entries,
    }
    write_report(REPORT_DIR / "project_token_budget.json", report)
    return report


class TestProjectMdTokenBudget:
    def test_report_written(self, project_token_report):
        report_path = REPORT_DIR / "project_token_budget.json"
        assert report_path.exists()

    def test_no_file_exceeds_budget(self, project_token_report):
        over = [e for e in project_token_report["entries"] if e["over_budget"]]
        if over:
            lines = [
                f"  {e['file']}: {e['tokens']} tokens (budget={TOKEN_BUDGET})"
                for e in over
            ]
            pytest.fail(
                f"{len(over)} project MD file(s) exceed the {TOKEN_BUDGET}-token budget:\n"
                + "\n".join(lines)
            )

    def test_routes_dir_accessible(self, project_token_report):
        """Informational: routes/ either has files or is empty — both are valid."""
        assert project_token_report["total_files"] >= 0
