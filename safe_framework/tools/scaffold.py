"""
safe tool scaffold — fork an existing tool MCP for project-level customisation.

Usage (via CLI):
    safe tool fork <tool-id> <project-name>
    safe tool list
    safe tool info <tool-id>

For custom MCPs (safe-*):   copies the source file and patches the server name.
For native tools (iq-*, azure-*): generates a delegation wrapper stub that calls
through to the native endpoint so the engineer adds logic without reimplementing.

Forked files land in safe_framework/tools/mcp/ with the name:
    project_<project>_<tool_slug>.py   (underscores — valid Python module name)

The catalog entry ID uses kebab-case to match the convention:
    project-<project>-<tool-id>
"""

from __future__ import annotations

import re
import textwrap
from datetime import date
from pathlib import Path
from typing import Any

import yaml

_TOOLS_DIR = Path(__file__).parent
_MCP_DIR = _TOOLS_DIR / "mcp"
_CATALOG_PATH = _TOOLS_DIR / "catalog.yaml"

# Source Python files for our custom safe-* MCPs
_SAFE_MCP_FILES: dict[str, str] = {
    "safe-durable-task":  "durable_task_mcp.py",
    "safe-model-router":  "model_router_mcp.py",
    "safe-token-metrics": "token_metrics_mcp.py",
}

# Wrapper stub templates for native (non-Python) tools
# Each entry: tool_id → dict of function stubs
_NATIVE_STUBS: dict[str, list[dict[str, str]]] = {
    "iq-foundry": [
        {
            "name": "search",
            "args": 'query: str, top_k: int = 5, index: str = ""',
            "doc": "Semantic search over the Foundry IQ knowledge index.",
            "body": textwrap.dedent("""\
                # TODO: add org-specific filtering, result caching, or metadata injection
                # before delegating to the native Foundry IQ MCP endpoint.
                # Native endpoint is configured in Azure AI Foundry portal → Tools → Foundry IQ.
                raise NotImplementedError(
                    "Replace this stub with your customised Foundry IQ search logic."
                )"""),
        },
        {
            "name": "retrieve",
            "args": "document_id: str",
            "doc": "Retrieve a specific document or chunk by ID from Foundry IQ.",
            "body": textwrap.dedent("""\
                raise NotImplementedError(
                    "Replace this stub with your customised Foundry IQ retrieve logic."
                )"""),
        },
    ],
    "iq-work": [
        {
            "name": "search",
            "args": 'query: str, content_type: str = "all"',
            "doc": "Search M365 content (emails, meetings, documents, chats).",
            "body": textwrap.dedent("""\
                # content_type: 'email' | 'meeting' | 'document' | 'chat' | 'all'
                raise NotImplementedError(
                    "Replace this stub with your customised Work IQ search logic."
                )"""),
        },
        {
            "name": "get_meeting_context",
            "args": "meeting_id: str",
            "doc": "Retrieve meeting transcript and action items.",
            "body": textwrap.dedent("""\
                raise NotImplementedError(
                    "Replace this stub with your customised Work IQ meeting context logic."
                )"""),
        },
    ],
    "iq-fabric": [
        {
            "name": "query",
            "args": "nl_query: str, dataset: str",
            "doc": "Natural-language query over a Power BI semantic model or OneLake dataset.",
            "body": textwrap.dedent("""\
                raise NotImplementedError(
                    "Replace this stub with your customised Fabric IQ query logic."
                )"""),
        },
    ],
    "iq-web": [
        {
            "name": "web_search",
            "args": "query: str, freshness: str = \"Week\"",
            "doc": "Search the live public web and news via Bing grounding.",
            "body": textwrap.dedent("""\
                # freshness: 'Day' | 'Week' | 'Month' | 'Year'
                raise NotImplementedError(
                    "Replace this stub with your customised Web IQ search logic."
                )"""),
        },
    ],
    "azure-cosmos-db": [
        {
            "name": "vector_search",
            "args": "query: str, container: str, top_k: int = 5",
            "doc": "Hybrid vector + keyword search over a Cosmos DB container.",
            "body": textwrap.dedent("""\
                raise NotImplementedError(
                    "Replace this stub with your customised Cosmos DB vector search logic."
                )"""),
        },
        {
            "name": "upsert",
            "args": "container: str, document: dict",
            "doc": "Insert or update a document in Cosmos DB.",
            "body": textwrap.dedent("""\
                raise NotImplementedError(
                    "Replace this stub with your customised Cosmos DB upsert logic."
                )"""),
        },
    ],
}


def _slug(s: str) -> str:
    """Convert kebab/hyphen string to Python identifier (underscores)."""
    return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")


def _load_catalog() -> dict[str, Any]:
    with _CATALOG_PATH.open() as f:
        return yaml.safe_load(f)


def _save_catalog(catalog: dict[str, Any]) -> None:
    with _CATALOG_PATH.open("w") as f:
        yaml.dump(catalog, f, allow_unicode=True, sort_keys=False, default_flow_style=False)


def _find_tool(catalog: dict[str, Any], tool_id: str) -> dict[str, Any] | None:
    return next((t for t in catalog.get("tools", []) if t["id"] == tool_id), None)


def _forked_id(project: str, tool_id: str) -> str:
    return f"project-{project}-{tool_id}"


def _forked_filename(project: str, tool_id: str) -> str:
    return f"project_{_slug(project)}_{_slug(tool_id)}.py"


def _generate_wrapper_stub(project: str, tool_id: str, original: dict[str, Any]) -> str:
    server_id = _forked_id(project, tool_id)
    stubs = _NATIVE_STUBS.get(tool_id, [])
    today = date.today().isoformat()
    display_name = original.get("display_name", tool_id)
    category = original.get("category", "Unknown")
    endpoint_notes = (original.get("endpoint") or {}).get("notes", "see tools/catalog.yaml")
    env_prefix = _slug(tool_id).upper()

    tool_blocks: list[str] = []
    for fn in stubs:
        indented_body = textwrap.indent(fn["body"], "    ")
        tool_blocks.append(
            f'@mcp.tool()\n'
            f'async def {fn["name"]}({fn["args"]}) -> dict:\n'
            f'    """{fn["doc"]}"""\n'
            f'{indented_body}\n'
        )

    tools_section = "\n\n".join(tool_blocks) or (
        "@mcp.tool()\nasync def placeholder() -> dict:\n    \"\"\"TODO: add tool functions.\"\"\"\n    raise NotImplementedError\n"
    )

    # Build at column 0 so textwrap.dedent doesn't fight with tools_section
    lines = [
        '"""',
        f'{server_id}',
        f'Forked from: {tool_id}',
        f'Date: {today}',
        f'Project: {project}',
        '',
        f'This is a delegation wrapper — the functions below mirror the native {tool_id} API.',
        'Customise each function to add org-specific logic:',
        '  - caching / rate-limit handling',
        '  - request filtering or enrichment (e.g. inject tenant/org scope)',
        '  - response post-processing (e.g. strip PII, reformat results)',
        '  - auth token exchange or header injection',
        '',
        'Native tool details:',
        f'  display_name : {display_name}',
        f'  category     : {category}',
        f'  endpoint     : {endpoint_notes}',
        '',
        f'Mount via tools/catalog.yaml → id: {server_id}',
        '"""',
        '',
        'from __future__ import annotations',
        '',
        'from mcp.server.fastmcp import FastMCP',
        '',
        f'mcp = FastMCP("{server_id}")',
        '',
        '# ── Add environment variables / config here ───────────────────────────',
        '# import os',
        f'# _ENDPOINT = os.environ.get("{env_prefix}_ENDPOINT", "")',
        f'# _API_KEY   = os.environ.get("{env_prefix}_KEY", "")',
        '',
        '',
        tools_section,
        '',
        'if __name__ == "__main__":',
        '    mcp.run()',
    ]
    return "\n".join(lines) + "\n"


def _fork_safe_mcp(project: str, tool_id: str, original: dict[str, Any]) -> tuple[Path, str]:
    """Copy a safe-* MCP source file and patch the server name."""
    src_filename = _SAFE_MCP_FILES[tool_id]
    src_path = _MCP_DIR / src_filename
    dest_filename = _forked_filename(project, tool_id)
    dest_path = _MCP_DIR / dest_filename
    server_id = _forked_id(project, tool_id)
    today = date.today().isoformat()

    source = src_path.read_text()

    # Patch the module docstring header
    fork_header = (
        f'"""\n'
        f'{server_id}\n'
        f'Forked from: {tool_id} ({src_filename})\n'
        f'Date: {today}\n'
        f'Project: {project}\n'
        f'\n'
        f'Customise freely — this is your project\'s copy. The original remains at\n'
        f'safe_framework/tools/mcp/{src_filename} and will not be affected.\n'
        f'"""\n'
    )

    # Replace the existing top-level docstring (first triple-quoted block)
    patched = re.sub(r'^""".*?"""\n', fork_header, source, count=1, flags=re.DOTALL)

    # Patch FastMCP server name
    patched = re.sub(
        r'FastMCP\(["\'][^"\']+["\']\)',
        f'FastMCP("{server_id}")',
        patched,
        count=1,
    )

    dest_path.write_text(patched)
    return dest_path, dest_filename


def fork_tool(tool_id: str, project: str) -> dict[str, Any]:
    """Fork a tool for project-level customisation.

    Returns a dict with 'file', 'catalog_id', 'is_copy' keys.
    Raises ValueError if tool_id is not found or already forked.
    """
    project = project.lower().strip()
    if not re.match(r"^[a-z0-9][a-z0-9-]*[a-z0-9]$", project):
        raise ValueError(
            f"project name '{project}' must be lowercase alphanumeric with optional hyphens"
        )

    catalog = _load_catalog()
    original = _find_tool(catalog, tool_id)
    if original is None:
        available = [t["id"] for t in catalog.get("tools", [])]
        raise ValueError(
            f"Tool '{tool_id}' not found in catalog.\nAvailable: {', '.join(available)}"
        )

    new_id = _forked_id(project, tool_id)
    if _find_tool(catalog, new_id):
        raise ValueError(
            f"Tool '{new_id}' already exists in catalog. Delete it first to re-fork."
        )

    # Generate or copy the MCP file
    if tool_id in _SAFE_MCP_FILES:
        dest_path, dest_filename = _fork_safe_mcp(project, tool_id, original)
        is_copy = True
    else:
        dest_filename = _forked_filename(project, tool_id)
        dest_path = _MCP_DIR / dest_filename
        dest_path.write_text(_generate_wrapper_stub(project, tool_id, original))
        is_copy = False

    # Build new catalog entry
    module_path = f"safe_framework.tools.mcp.{dest_filename[:-3]}"
    new_entry: dict[str, Any] = {
        "id": new_id,
        "display_name": f"{project.title()} — {original['display_name']}",
        "description": (
            f"Project fork of {original['display_name']} for {project}.\n"
            f"Customise {dest_filename} to add org-specific logic.\n"
            f"Original: {tool_id}"
        ),
        "category": original.get("category", "Custom"),
        "tags": [new_id, f"project-{project}", tool_id, "forked"]
                + [t for t in original.get("tags", []) if t != tool_id],
        "tool_type": "local_mcp",
        "endpoint": {
            "type": "local_python",
            "module": module_path,
            "notes": f"Forked from {tool_id}. Edit {dest_filename} to customise.",
        },
        "authentication": original.get("authentication", {"type": "managed_identity"}),
        "functions": original.get("functions", []),
    }
    catalog["tools"].append(new_entry)
    _save_catalog(catalog)

    return {
        "file": str(dest_path),
        "catalog_id": new_id,
        "module": module_path,
        "is_copy": is_copy,
    }


def list_tools() -> list[dict[str, Any]]:
    """Return all tools from the catalog."""
    catalog = _load_catalog()
    return catalog.get("tools", [])


def tool_info(tool_id: str) -> dict[str, Any]:
    """Return full catalog entry for a tool."""
    catalog = _load_catalog()
    tool = _find_tool(catalog, tool_id)
    if tool is None:
        raise ValueError(f"Tool '{tool_id}' not found in catalog.")
    return tool
