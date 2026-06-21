"""
Validates that every SAFE agent.md has the required documentation sections.

Run independently:  pytest -m safe_md tests/md_analysis/test_safe_md_sections.py
"""

import pytest
from .conftest import SAFE_AGENTS_ROOT, REQUIRED_SAFE_SECTIONS

pytestmark = pytest.mark.safe_md


def _md_ids(files):
    return [str(f.relative_to(SAFE_AGENTS_ROOT)) for f in files]


@pytest.fixture(scope="module")
def all_safe_mds():
    return sorted(SAFE_AGENTS_ROOT.rglob("agent.md"))


class TestSafeMdSections:
    def test_at_least_one_safe_md_exists(self, all_safe_mds):
        assert len(all_safe_mds) > 0, "No agent.md files found under safe_framework/agents"

    @pytest.mark.parametrize("section", REQUIRED_SAFE_SECTIONS)
    def test_all_files_have_section(self, all_safe_mds, section):
        """Every agent.md must contain each required section header."""
        missing = []
        for md_file in all_safe_mds:
            content = md_file.read_text(encoding="utf-8")
            if section not in content:
                missing.append(str(md_file.relative_to(SAFE_AGENTS_ROOT)))

        assert missing == [], (
            f"Section '{section}' missing in {len(missing)} files:\n"
            + "\n".join(f"  - {p}" for p in missing[:10])
            + ("\n  ... (truncated)" if len(missing) > 10 else "")
        )

    def test_files_have_title_heading(self, all_safe_mds):
        """Each file must start with a level-1 heading."""
        missing = []
        for md_file in all_safe_mds:
            first_line = md_file.read_text(encoding="utf-8").split("\n")[0]
            if not first_line.startswith("# "):
                missing.append(str(md_file.relative_to(SAFE_AGENTS_ROOT)))

        assert missing == [], (
            f"Missing # title in {len(missing)} files:\n"
            + "\n".join(f"  - {p}" for p in missing[:10])
        )

    def test_files_have_mermaid_diagram(self, all_safe_mds):
        """Each file must contain a Mermaid flowchart block."""
        missing = []
        for md_file in all_safe_mds:
            content = md_file.read_text(encoding="utf-8")
            if "```mermaid" not in content:
                missing.append(str(md_file.relative_to(SAFE_AGENTS_ROOT)))

        assert missing == [], (
            f"Missing mermaid diagram in {len(missing)} files:\n"
            + "\n".join(f"  - {p}" for p in missing[:10])
        )

    def test_files_are_non_empty(self, all_safe_mds):
        """No file should be a stub (< 100 chars)."""
        stubs = [
            str(f.relative_to(SAFE_AGENTS_ROOT))
            for f in all_safe_mds
            if len(f.read_text(encoding="utf-8").strip()) < 100
        ]
        assert stubs == [], f"Stub MD files detected: {stubs}"
