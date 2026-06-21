"""HandoffCodeGenerator — generates ConnectedAgentTool handoff code from templates."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import yaml
from jinja2 import Environment, FileSystemLoader

from .handoff_models import HandoffDefinition, HandoffPattern, GeneratedHandoff

_HANDOFFS_TEMPLATE_DIR = Path(__file__).parent.parent / "agents" / "handoffs"

_HANDOFF_TEMPLATE_DIRS: Dict[HandoffPattern, Path] = {
    HandoffPattern.DIRECT:       _HANDOFFS_TEMPLATE_DIR / "direct-handoff",
    HandoffPattern.SELECTIVE:    _HANDOFFS_TEMPLATE_DIR / "selective-handoff",
    HandoffPattern.SEQUENTIAL:   _HANDOFFS_TEMPLATE_DIR / "sequential-handoff",
    HandoffPattern.HIERARCHICAL: _HANDOFFS_TEMPLATE_DIR / "hierarchical-handoff",
    HandoffPattern.RECURSIVE:    _HANDOFFS_TEMPLATE_DIR / "recursive-handoff",
}

_REQUIREMENTS = (
    "azure-ai-projects>=1.0.0b4\n"
    "azure-identity>=1.17.0\n"
)


def _class_name(s: str) -> str:
    return "".join(p.capitalize() for p in s.replace("-", "_").split("_"))


def _get_template(pattern: HandoffPattern):
    template_dir = _HANDOFF_TEMPLATE_DIRS[pattern]
    env = Environment(
        loader=FileSystemLoader(str(template_dir)),
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True,
    )
    return env.get_template("handoff.py.jinja2")


class HandoffCodeGenerator:

    @staticmethod
    def generate(handoff: HandoffDefinition) -> GeneratedHandoff:
        template = _get_template(handoff.pattern)
        context = HandoffCodeGenerator._build_context(handoff)
        handoff_code = template.render(**context)

        config_yaml = yaml.dump(
            {
                "name": handoff.name,
                "pattern": handoff.pattern.value,
                "description": handoff.description,
                "version": handoff.version,
                "max_depth": handoff.max_depth,
                "return_policy": handoff.return_policy,
                "timeout_seconds": handoff.timeout_seconds,
                "csa_email": handoff.csa_email,
                "tags": handoff.tags,
                "sub_agents": {
                    k: {
                        "name": v.name,
                        "description": v.description,
                        "capability_tags": v.capability_tags,
                    }
                    for k, v in handoff.sub_agents.items()
                },
            },
            default_flow_style=False,
            sort_keys=False,
        )

        return GeneratedHandoff(
            handoff_code=handoff_code,
            requirements_txt=_REQUIREMENTS,
            config_yaml=config_yaml,
            metadata={
                "pattern": handoff.pattern.value,
                "sub_agents": list(handoff.sub_agents.keys()),
                "created_at": handoff.created_at.isoformat(),
                "version": handoff.version,
            },
        )

    @staticmethod
    def _build_context(handoff: HandoffDefinition) -> Dict[str, Any]:
        ctx: Dict[str, Any] = {
            "handoff_name": handoff.name,
            "class_name": _class_name(handoff.name),
            "description": handoff.description,
            "pattern": handoff.pattern.value,
            "max_depth": handoff.max_depth,
            "return_policy": handoff.return_policy,
            "timeout_seconds": handoff.timeout_seconds,
            "sub_agents": handoff.sub_agents,
            "sub_agent_keys": list(handoff.sub_agents.keys()),
            "created_at": handoff.created_at.strftime("%Y-%m-%d"),
        }

        if handoff.pattern == HandoffPattern.DIRECT:
            ctx["delegate"] = handoff.sub_agents.get("delegate")

        elif handoff.pattern == HandoffPattern.SELECTIVE:
            ctx["coordinator"] = handoff.sub_agents.get("coordinator")
            ctx["candidates"] = {
                k: v for k, v in handoff.sub_agents.items()
                if k.startswith("candidate_")
            }

        elif handoff.pattern == HandoffPattern.SEQUENTIAL:
            ctx["stages"] = dict(
                sorted(
                    ((k, v) for k, v in handoff.sub_agents.items() if k.startswith("stage_")),
                    key=lambda item: item[0],
                )
            )

        elif handoff.pattern == HandoffPattern.HIERARCHICAL:
            ctx["manager"] = handoff.sub_agents.get("manager")
            ctx["workers"] = {
                k: v for k, v in handoff.sub_agents.items()
                if k.startswith("worker_")
            }

        elif handoff.pattern == HandoffPattern.RECURSIVE:
            ctx["recursive_agent"] = handoff.sub_agents.get("agent")

        return ctx

    @staticmethod
    def save(handoff: HandoffDefinition, handoffs_dir: Path) -> Path:
        result = HandoffCodeGenerator.generate(handoff)
        handoff_dir = handoffs_dir / handoff.name
        handoff_dir.mkdir(parents=True, exist_ok=True)
        (handoff_dir / "handoff.py").write_text(result.handoff_code, encoding="utf-8")
        (handoff_dir / "requirements.txt").write_text(result.requirements_txt, encoding="utf-8")
        (handoff_dir / "config.yaml").write_text(result.config_yaml, encoding="utf-8")
        return handoff_dir

    @staticmethod
    def load_from_yaml(config_path: Path) -> HandoffDefinition:
        """Reconstruct a HandoffDefinition from a saved config.yaml."""
        from .handoff_models import SubAgent
        data = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        sub_agents = {
            k: SubAgent(
                name=v["name"],
                description=v["description"],
                capability_tags=v.get("capability_tags", []),
            )
            for k, v in data.get("sub_agents", {}).items()
        }
        return HandoffDefinition(
            name=data["name"],
            pattern=HandoffPattern(data["pattern"]),
            sub_agents=sub_agents,
            description=data.get("description", ""),
            max_depth=data.get("max_depth", 3),
            return_policy=data.get("return_policy", "always"),
            timeout_seconds=data.get("timeout_seconds", 120),
            csa_email=data.get("csa_email", ""),
            tags=data.get("tags", []),
            version=data.get("version", "v1.0"),
        )
