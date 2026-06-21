"""ChainValidator — validates RouteChain field mappings and step references."""
from __future__ import annotations

import ast
from pathlib import Path
from typing import List

from .chain_models import RouteChain
from .models import ValidationError


class ChainValidator:

    def validate(self, chain: RouteChain, routes_dir: Path) -> List[ValidationError]:
        """Return all validation errors; empty list means the chain is valid."""
        errors: List[ValidationError] = []

        if len(chain.steps) < 2:
            errors.append(ValidationError(
                error_type="min_steps",
                message="A chain must have at least 2 steps.",
                suggested_solutions=["Add more steps via 'safe chain' wizard."],
            ))
            return errors  # nothing else to check

        for i, step in enumerate(chain.steps, 1):
            # Route must exist on disk
            route_file = routes_dir / step.route_name / "route.py"
            if not route_file.exists():
                errors.append(ValidationError(
                    error_type="missing_route",
                    message=(
                        f"Step {i}: route '{step.route_name}' not found "
                        f"at {route_file}."
                    ),
                    suggested_solutions=[
                        f"Run 'safe route' and name it '{step.route_name}'.",
                        f"Or verify that '{routes_dir / step.route_name}' exists.",
                    ],
                ))

            # Condition must parse as a valid Python expression
            if step.condition:
                try:
                    ast.parse(step.condition, mode="eval")
                except SyntaxError as exc:
                    errors.append(ValidationError(
                        error_type="invalid_condition",
                        message=f"Step {i}: condition syntax error — {exc}",
                        suggested_solutions=[
                            "Fix the Python expression in condition.",
                            "Example: \"quality_score >= 0.8\"",
                        ],
                    ))

            # Field mapping keys must be non-empty strings
            for dest, src in step.field_mapping.items():
                if not dest.strip() or not src.strip():
                    errors.append(ValidationError(
                        error_type="empty_mapping_key",
                        message=(
                            f"Step {i}: field_mapping has an empty key "
                            f"('{dest}' → '{src}')."
                        ),
                        suggested_solutions=["Remove entries with blank keys from field_mapping."],
                    ))

        # Warn when the timeout budget looks too tight
        min_recommended = len(chain.steps) * 30
        if chain.timeout_seconds < min_recommended:
            errors.append(ValidationError(
                error_type="tight_timeout",
                message=(
                    f"Chain timeout {chain.timeout_seconds}s may be too short for "
                    f"{len(chain.steps)} steps (recommended ≥ {min_recommended}s)."
                ),
                suggested_solutions=[f"Set timeout_seconds to at least {min_recommended}."],
            ))

        return errors

    def validate_or_raise(self, chain: RouteChain, routes_dir: Path) -> None:
        """Raise ValueError listing all hard errors (warnings are not raised)."""
        errors = self.validate(chain, routes_dir)
        hard = [e for e in errors if e.error_type != "tight_timeout"]
        if hard:
            msgs = "\n".join(f"  • {e.message}" for e in hard)
            raise ValueError(f"Chain validation failed:\n{msgs}")
