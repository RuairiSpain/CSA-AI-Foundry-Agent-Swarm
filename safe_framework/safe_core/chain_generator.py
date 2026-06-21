"""RouteChainGenerator — renders chain.py and chain.yaml from a RouteChain."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import yaml
from jinja2 import Environment, FileSystemLoader

from .chain_models import RouteChain, RouteChainStep


_CHAINS_TEMPLATE_DIR = Path(__file__).parent.parent / "agents" / "chains"


def _class_name(s: str) -> str:
    """Convert kebab-case or snake_case to PascalCase."""
    return "".join(p.capitalize() for p in s.replace("-", "_").split("_"))


class RouteChainGenerator:

    @staticmethod
    def generate(chain: RouteChain) -> Dict[str, str]:
        """Return dict with 'chain_code' and 'chain_yaml' strings."""
        env = Environment(
            loader=FileSystemLoader(str(_CHAINS_TEMPLATE_DIR)),
            trim_blocks=True,
            lstrip_blocks=True,
            keep_trailing_newline=True,
        )
        template = env.get_template("chain.py.jinja2")

        steps_ctx: List[Dict[str, Any]] = []
        for step in chain.steps:
            steps_ctx.append({
                "route_name": step.route_name,
                "import_class": _class_name(step.route_name),
                "module_name": step.route_name.replace("-", "_"),
                "label": step.label or step.route_name,
                "field_mapping": step.field_mapping,
                "pass_through_fields": step.pass_through_fields,
                "condition": step.condition,
            })

        context: Dict[str, Any] = {
            "chain_name": chain.name,
            "class_name": _class_name(chain.name),
            "description": chain.description,
            "steps": steps_ctx,
            "total_steps": len(chain.steps),
            "timeout_seconds": chain.timeout_seconds,
            "on_step_failure": chain.on_step_failure,
            "include_chain_history": chain.include_chain_history,
            "created_at": chain.created_at.strftime("%Y-%m-%d"),
        }

        chain_code = template.render(**context)

        chain_yaml = yaml.dump(
            {
                "name": chain.name,
                "description": chain.description,
                "version": chain.version,
                "csa_email": chain.csa_email,
                "timeout_seconds": chain.timeout_seconds,
                "on_step_failure": chain.on_step_failure,
                "include_chain_history": chain.include_chain_history,
                "steps": [
                    {
                        "route_name": s.route_name,
                        "label": s.label,
                        "field_mapping": s.field_mapping,
                        "pass_through_fields": s.pass_through_fields,
                        "condition": s.condition,
                    }
                    for s in chain.steps
                ],
            },
            default_flow_style=False,
            sort_keys=False,
        )

        return {"chain_code": chain_code, "chain_yaml": chain_yaml}

    @staticmethod
    def save(chain: RouteChain, routes_dir: Path) -> Path:
        """Generate and write chain.py + chain.yaml under routes_dir/<chain.name>/."""
        result = RouteChainGenerator.generate(chain)
        chain_dir = routes_dir / chain.name
        chain_dir.mkdir(parents=True, exist_ok=True)
        (chain_dir / "chain.py").write_text(result["chain_code"], encoding="utf-8")
        (chain_dir / "chain.yaml").write_text(result["chain_yaml"], encoding="utf-8")
        return chain_dir

    @staticmethod
    def load_from_yaml(chain_yaml_path: Path) -> RouteChain:
        """Reconstruct a RouteChain from a saved chain.yaml."""
        data = yaml.safe_load(chain_yaml_path.read_text(encoding="utf-8"))
        steps = [
            RouteChainStep(
                route_name=s["route_name"],
                field_mapping=s.get("field_mapping") or {},
                pass_through_fields=s.get("pass_through_fields") or [],
                condition=s.get("condition"),
                label=s.get("label"),
            )
            for s in data["steps"]
        ]
        return RouteChain(
            name=data["name"],
            description=data.get("description", ""),
            version=data.get("version", "v1.0"),
            csa_email=data.get("csa_email", ""),
            steps=steps,
            timeout_seconds=data.get("timeout_seconds", 600),
            on_step_failure=data.get("on_step_failure", "halt"),
            include_chain_history=data.get("include_chain_history", False),
        )
