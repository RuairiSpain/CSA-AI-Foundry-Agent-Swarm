"""HandoffValidator — validates HandoffDefinition against pattern-specific rules."""

from __future__ import annotations

from typing import List

from .handoff_models import HandoffDefinition, HandoffPattern
from .models import ValidationError

_VALID_RETURN_POLICIES = frozenset({"always", "on_partial", "on_failure"})


class HandoffValidator:
    """Validates a HandoffDefinition.

    Deliberately lighter than ContractValidator: handoffs are dynamic, so we
    cannot verify which sub-agent will be chosen at runtime. We only check
    structural rules (required role keys, depth bounds, pool size).
    """

    def validate(self, handoff: HandoffDefinition) -> List[ValidationError]:
        """Return all validation errors; empty list means valid."""
        errors: List[ValidationError] = []
        errors.extend(self._validate_common(handoff))
        errors.extend(self._validate_pattern(handoff))
        return errors

    def validate_or_raise(self, handoff: HandoffDefinition) -> None:
        errors = self.validate(handoff)
        if errors:
            msgs = "\n".join(f"  • {e.message}" for e in errors)
            raise ValueError(f"Handoff validation failed:\n{msgs}")

    # ── common ────────────────────────────────────────────────────────────────

    def _validate_common(self, handoff: HandoffDefinition) -> List[ValidationError]:
        errors: List[ValidationError] = []

        if not handoff.sub_agents:
            errors.append(ValidationError(
                error_type="empty_pool",
                message="HandoffDefinition must declare at least one sub-agent.",
                suggested_solutions=["Add sub-agents under sub_agents."],
            ))

        errors.extend(self._validate_restrictions(handoff))

        if handoff.return_policy not in _VALID_RETURN_POLICIES:
            errors.append(ValidationError(
                error_type="invalid_return_policy",
                message=(
                    f"return_policy '{handoff.return_policy}' is invalid. "
                    f"Must be one of: {sorted(_VALID_RETURN_POLICIES)}"
                ),
                suggested_solutions=[
                    "Set return_policy to 'always', 'on_partial', or 'on_failure'."
                ],
            ))

        if handoff.max_depth < 1:
            errors.append(ValidationError(
                error_type="invalid_max_depth",
                message=f"max_depth must be ≥ 1, got {handoff.max_depth}.",
                suggested_solutions=["Set max_depth to at least 1."],
            ))

        if handoff.timeout_seconds < 10:
            errors.append(ValidationError(
                error_type="timeout_too_low",
                message=f"Handoff timeout too low: {handoff.timeout_seconds}s.",
                suggested_solutions=["Set timeout_seconds to at least 30."],
            ))

        return errors

    def _validate_restrictions(self, handoff: HandoffDefinition) -> List[ValidationError]:
        """Validate allowed_callers and max_calls fields on each sub-agent."""
        errors: List[ValidationError] = []
        known_keys = set(handoff.sub_agents.keys())

        for role_key, sub in handoff.sub_agents.items():
            # allowed_callers must reference existing role keys in the same pool
            for caller in sub.allowed_callers:
                if caller not in known_keys:
                    errors.append(ValidationError(
                        error_type="unknown_caller",
                        message=(
                            f"sub_agent '{role_key}' lists unknown caller '{caller}' "
                            f"in allowed_callers. Must be a role key in the same HandoffDefinition."
                        ),
                        suggested_solutions=[
                            f"Remove '{caller}' from allowed_callers.",
                            f"Or add a sub-agent with key '{caller}' to sub_agents.",
                        ],
                    ))
                if caller == role_key:
                    errors.append(ValidationError(
                        error_type="self_caller",
                        message=(
                            f"sub_agent '{role_key}' lists itself in allowed_callers. "
                            "A sub-agent cannot be its own caller."
                        ),
                        suggested_solutions=[f"Remove '{role_key}' from its own allowed_callers."],
                    ))

            # max_calls must be non-negative
            if sub.max_calls < 0:
                errors.append(ValidationError(
                    error_type="invalid_max_calls",
                    message=(
                        f"sub_agent '{role_key}' has max_calls={sub.max_calls}. "
                        "Must be ≥ 0 (0 = unlimited)."
                    ),
                    suggested_solutions=["Set max_calls to 0 (unlimited) or a positive integer."],
                ))

        # Warn when a sub-agent's allowed_callers would prevent it from ever being called
        for role_key, sub in handoff.sub_agents.items():
            if sub.allowed_callers:
                # Find callers that exist but whose own allowed_callers doesn't include role_key
                # (i.e. potential dead sub-agents — only a warning, not a hard error)
                reachable = any(
                    c in known_keys for c in sub.allowed_callers
                )
                if not reachable:
                    errors.append(ValidationError(
                        error_type="unreachable_sub_agent",
                        message=(
                            f"sub_agent '{role_key}' has allowed_callers "
                            f"{sub.allowed_callers!r} but none of those keys exist in sub_agents."
                        ),
                        suggested_solutions=[
                            f"Add a sub-agent with one of {sub.allowed_callers!r} as its key.",
                            "Or clear allowed_callers to make it unrestricted.",
                        ],
                    ))

        return errors

    # ── pattern-specific ──────────────────────────────────────────────────────

    def _validate_pattern(self, handoff: HandoffDefinition) -> List[ValidationError]:
        dispatch = {
            HandoffPattern.DIRECT:       self._validate_direct,
            HandoffPattern.SELECTIVE:    self._validate_selective,
            HandoffPattern.SEQUENTIAL:   self._validate_sequential,
            HandoffPattern.HIERARCHICAL: self._validate_hierarchical,
            HandoffPattern.RECURSIVE:    self._validate_recursive,
        }
        validator = dispatch.get(handoff.pattern)
        return validator(handoff) if validator else []

    def _validate_direct(self, handoff: HandoffDefinition) -> List[ValidationError]:
        errors: List[ValidationError] = []
        if "delegate" not in handoff.sub_agents:
            errors.append(ValidationError(
                error_type="missing_sub_agent",
                message="direct-handoff requires a sub-agent with role key 'delegate'.",
                suggested_solutions=["Add a sub-agent with key 'delegate' to sub_agents."],
            ))
        if len(handoff.sub_agents) > 1:
            errors.append(ValidationError(
                error_type="too_many_sub_agents",
                message=(
                    f"direct-handoff delegates to exactly one sub-agent; "
                    f"found {len(handoff.sub_agents)}. "
                    "Use selective-handoff for multiple candidates."
                ),
                suggested_solutions=[
                    "Remove extra sub-agents.",
                    "Switch pattern to selective-handoff.",
                ],
            ))
        return errors

    def _validate_selective(self, handoff: HandoffDefinition) -> List[ValidationError]:
        errors: List[ValidationError] = []
        if "coordinator" not in handoff.sub_agents:
            errors.append(ValidationError(
                error_type="missing_sub_agent",
                message="selective-handoff requires a 'coordinator' sub-agent.",
                suggested_solutions=["Add a sub-agent with key 'coordinator'."],
            ))
        candidates = [k for k in handoff.sub_agents if k.startswith("candidate_")]
        if len(candidates) < 2:
            errors.append(ValidationError(
                error_type="insufficient_candidates",
                message=(
                    "selective-handoff requires at least 2 candidate_* sub-agents; "
                    f"found {len(candidates)}."
                ),
                suggested_solutions=["Add sub-agents with keys candidate_0, candidate_1, …"],
            ))
        return errors

    def _validate_sequential(self, handoff: HandoffDefinition) -> List[ValidationError]:
        errors: List[ValidationError] = []
        stage_keys = [k for k in handoff.sub_agents if k.startswith("stage_")]
        if len(stage_keys) < 2:
            errors.append(ValidationError(
                error_type="insufficient_stages",
                message=(
                    "sequential-handoff requires at least 2 stage_* sub-agents; "
                    f"found {len(stage_keys)}."
                ),
                suggested_solutions=["Add sub-agents with keys stage_0, stage_1, …"],
            ))
        return errors

    def _validate_hierarchical(self, handoff: HandoffDefinition) -> List[ValidationError]:
        errors: List[ValidationError] = []
        if "manager" not in handoff.sub_agents:
            errors.append(ValidationError(
                error_type="missing_sub_agent",
                message="hierarchical-handoff requires a 'manager' sub-agent.",
                suggested_solutions=["Add a sub-agent with key 'manager'."],
            ))
        workers = [k for k in handoff.sub_agents if k.startswith("worker_")]
        if not workers:
            errors.append(ValidationError(
                error_type="missing_sub_agent",
                message="hierarchical-handoff requires at least one worker_* sub-agent.",
                suggested_solutions=["Add sub-agents with keys worker_0, worker_1, …"],
            ))
        if handoff.max_depth < 2:
            errors.append(ValidationError(
                error_type="shallow_hierarchy",
                message=(
                    "hierarchical-handoff max_depth should be ≥ 2 for meaningful hierarchies; "
                    f"got {handoff.max_depth}."
                ),
                suggested_solutions=["Set max_depth to 2 or higher."],
            ))
        return errors

    def _validate_recursive(self, handoff: HandoffDefinition) -> List[ValidationError]:
        errors: List[ValidationError] = []
        if "agent" not in handoff.sub_agents:
            errors.append(ValidationError(
                error_type="missing_sub_agent",
                message="recursive-handoff requires a sub-agent with role key 'agent'.",
                suggested_solutions=["Add a sub-agent with key 'agent'."],
            ))
        if handoff.max_depth > 10:
            errors.append(ValidationError(
                error_type="depth_too_high",
                message=(
                    f"recursive-handoff max_depth {handoff.max_depth} may cause unbounded "
                    "delegation chains. Recommend ≤ 5."
                ),
                suggested_solutions=["Set max_depth to 5 or lower."],
            ))
        return errors
