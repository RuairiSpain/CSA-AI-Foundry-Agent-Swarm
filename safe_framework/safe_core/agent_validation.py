# safe_core/agent_validation.py
"""
Agent contract validation and compatibility checking.

Combines the p1-3 pattern-based validator (renamed AgentContractValidator)
and the AgentDiscovery class.  The p4 route-level ContractValidator lives
separately in safe_core/validator.py.
"""

import logging
from typing import Any, Dict, List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of agent validation."""
    valid: bool
    errors: List[str]
    warnings: List[str]
    agent_outputs: Dict[str, Any] = None
    required_outputs: List[str] = None


class AgentContractValidator:
    """Validates agent contracts against pattern requirements (p1-3 agent-YAML validator)."""

    def validate_agent_for_pattern(
        self,
        agent_contract: Dict[str, Any],
        pattern_id: str,
        placeholder_id: str
    ) -> ValidationResult:
        """
        Validate agent is compatible with pattern placeholder.

        Args:
            agent_contract: Agent YAML/dict with contract definition
            pattern_id: Pattern identifier (e.g., 'supervisor-manager')
            placeholder_id: Placeholder in pattern (e.g., 'supervisor')

        Returns:
            ValidationResult with validity and details
        """
        errors = []
        warnings = []

        # Import here to avoid circular dependency
        from safe_core.patterns import PATTERN_REGISTRY

        logger.info(f"Validating agent for pattern {pattern_id} placeholder {placeholder_id}")

        # Load pattern
        pattern = PATTERN_REGISTRY.get_pattern(pattern_id)
        if not pattern:
            errors.append(f"Pattern '{pattern_id}' not found")
            return ValidationResult(
                valid=False,
                errors=errors,
                warnings=warnings
            )

        # Find placeholder
        placeholder = next(
            (p for p in pattern.placeholders if p.id == placeholder_id),
            None
        )
        if not placeholder:
            errors.append(
                f"Pattern '{pattern_id}' has no placeholder '{placeholder_id}'"
            )
            return ValidationResult(
                valid=False,
                errors=errors,
                warnings=warnings
            )

        # Validate contract exists
        if "contract" not in agent_contract:
            errors.append("Agent has no 'contract' definition")
            return ValidationResult(
                valid=False,
                errors=errors,
                warnings=warnings
            )

        contract = agent_contract["contract"]

        # Check outputs
        agent_outputs = {}
        if "outputs" in contract:
            for output in contract["outputs"]:
                agent_outputs[output["name"]] = output

        # Validate required outputs
        required_outputs = getattr(placeholder, "required_outputs", None) or []
        for required in required_outputs:
            if required not in agent_outputs:
                errors.append(
                    f"Agent missing required output '{required}' "
                    f"for placeholder '{placeholder_id}'. "
                    f"Expected: {required_outputs}, "
                    f"Got: {list(agent_outputs.keys())}"
                )

        # Check inputs
        agent_inputs = {}
        if "inputs" in contract:
            for input_spec in contract["inputs"]:
                agent_inputs[input_spec["name"]] = input_spec

        if not agent_inputs:
            warnings.append("Agent has no inputs defined")

        if not agent_outputs:
            warnings.append("Agent has no outputs defined")

        # Check metadata
        metadata = agent_contract.get("metadata", {})

        # Check timeout
        timeout = metadata.get("timeout_seconds", 60)
        if timeout > 300:
            warnings.append(
                f"Agent timeout {timeout}s is very long (>5min), "
                f"consider optimizing"
            )

        # Check dependencies
        dependencies = metadata.get("dependencies", [])
        if len(dependencies) > 10:
            warnings.append(
                f"Agent has {len(dependencies)} dependencies, "
                f"may be fragile"
            )

        # Check requirements
        requirements = metadata.get("requirements", {})
        packages = requirements.get("packages", [])
        if len(packages) > 20:
            warnings.append(
                f"Agent requires {len(packages)} packages, "
                f"may have dependency conflicts"
            )

        # Validate skill references
        self._validate_skill_refs(agent_contract, errors, warnings)

        # Pattern-specific validations
        if pattern_id == "supervisor-manager":
            self._validate_supervisor_agent(agent_contract, placeholder_id, errors, warnings)

        elif pattern_id == "fan-out-fan-in":
            self._validate_fan_out_agent(agent_contract, placeholder_id, errors, warnings)

        logger.info(
            f"Validation complete: valid={len(errors)==0}, "
            f"errors={len(errors)}, warnings={len(warnings)}"
        )

        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            agent_outputs=agent_outputs,
            required_outputs=required_outputs
        )

    def _validate_supervisor_agent(self, agent_contract, placeholder_id, errors, warnings):
        """Supervisor-specific validation."""
        if placeholder_id == "supervisor":
            # Supervisor must output routing_decision
            contract = agent_contract.get("contract", {})
            outputs = {o["name"] for o in contract.get("outputs", [])}
            if "routing_decision" not in outputs:
                errors.append(
                    "Supervisor agent must output 'routing_decision'"
                )

    def _validate_skill_refs(self, agent_contract, errors, warnings):
        """Check that skill IDs declared in agent.yaml exist in the skills catalog."""
        skill_refs = agent_contract.get("skills", [])
        if not skill_refs:
            return
        try:
            from skills.scaffold import known_skill_ids  # type: ignore[import]
            catalog_ids = known_skill_ids()
        except Exception:
            warnings.append("Skills catalog unavailable — skill reference validation skipped")
            return
        for ref in skill_refs:
            sid = ref.get("id") if isinstance(ref, dict) else ref
            if sid and sid not in catalog_ids:
                errors.append(
                    f"Agent references unknown skill '{sid}'. "
                    f"Run 'safe skill list' to see available skills or "
                    f"'safe skill create {sid} <category> <description>' to register it."
                )

    def _validate_fan_out_agent(self, agent_contract, placeholder_id, errors, warnings):
        """Fan-out/fan-in specific validation."""
        if placeholder_id == "aggregator":
            # Aggregator should handle arrays
            description = agent_contract.get("description", "").lower()
            if "array" not in description and "parallel" not in description:
                warnings.append(
                    "Fan-in aggregator should handle arrays of results "
                    "from parallel workers"
                )


# Backwards-compat alias (the original name in p1-3 was ContractValidator)
ContractValidator = AgentContractValidator


# ============================================================================
# Agent discovery
# ============================================================================

class AgentDiscovery:
    """Find agents by keyword, use case, or pattern."""

    def __init__(self, catalog: Dict[str, Any]):
        """
        Initialize with agent catalog.

        Args:
            catalog: Loaded CATALOG.yaml as dict
        """
        self.catalog = catalog
        self.validator = AgentContractValidator()

    def search_agents(self, query: str) -> List[Dict[str, Any]]:
        """
        Search agents by keyword.

        Searches: name, description, tags, use_cases, keywords
        """
        query_lower = query.lower()
        results = []

        # Search standalone agents
        for agent in self.catalog.get("standalone", []):
            if self._agent_matches_query(agent, query_lower):
                results.append(agent)

        # Search pattern agents
        for pattern_name, agents_in_pattern in self.catalog.get("patterns", {}).items():
            for agent in agents_in_pattern:
                if self._agent_matches_query(agent, query_lower):
                    results.append(agent)

        # Sort by relevance (name match > tag match > description match)
        results.sort(
            key=lambda a: self._relevance_score(a, query_lower),
            reverse=True
        )

        logger.info(f"Search '{query}' found {len(results)} agents")
        return results

    def filter_agents(self,
                      category: Optional[str] = None,
                      pattern: Optional[str] = None,
                      complexity: Optional[str] = None,
                      min_rating: Optional[float] = None) -> List[Dict[str, Any]]:
        """Filter agents by criteria."""
        results = []

        # Collect all agents (copy to avoid mutating the catalog list)
        all_agents = list(self.catalog.get("standalone", []))
        for agents_in_pattern in self.catalog.get("patterns", {}).values():
            all_agents.extend(agents_in_pattern)

        # Apply filters
        for agent in all_agents:
            if category and agent.get("category") != category:
                continue

            if complexity and agent.get("discovery", {}).get("complexity") != complexity:
                continue

            if min_rating:
                rating = agent.get("discovery", {}).get("quality_rating", 0)
                if rating < min_rating:
                    continue

            if pattern and agent.get("id") != f"{pattern}_*":
                # Pattern agents have id like: supervisor-manager_supervisor
                if not agent.get("id", "").startswith(pattern + "_"):
                    continue

            results.append(agent)

        return results

    def suggest_agents(self, pattern_id: str,
                       placeholder_id: str) -> List[Dict[str, Any]]:
        """
        Recommend agents for pattern placeholder.

        Returns:
        1. Pattern-specific agents (highest priority)
        2. Standalone agents matching outputs (second)
        3. Popular agents (lowest priority)
        """
        suggestions = []

        # Check if pattern has specific agents for this placeholder
        pattern_agents = self.catalog.get("patterns", {}).get(pattern_id, [])
        for agent in pattern_agents:
            if agent.get("placeholder") == placeholder_id:
                agent["suggestion_reason"] = "Recommended for this pattern"
                agent["suggestion_rank"] = 1
                suggestions.append(agent)

        # If no pattern-specific agents, suggest standalone agents
        if not suggestions:
            # Find agents with matching outputs
            standalone = self.catalog.get("standalone", [])
            for agent in standalone:
                # Simple heuristic: sort by rating
                agent["suggestion_reason"] = "Compatible based on outputs"
                agent["suggestion_rank"] = 2
                suggestions.append(agent)

        # Sort by suggestion rank, then by rating
        suggestions.sort(
            key=lambda a: (
                a.get("suggestion_rank", 999),
                -(a.get("discovery", {}).get("quality_rating", 0))
            )
        )

        logger.info(f"Suggestions for {pattern_id}/{placeholder_id}: {len(suggestions)} agents")
        return suggestions

    def get_agent_stats(self) -> Dict[str, Any]:
        """Get overall catalog statistics."""
        all_agents = []
        all_agents.extend(self.catalog.get("standalone", []))
        for agents in self.catalog.get("patterns", {}).values():
            all_agents.extend(agents)

        categories = {}
        for agent in all_agents:
            cat = agent.get("category", "unknown")
            categories[cat] = categories.get(cat, 0) + 1

        return {
            "total_agents": len(all_agents),
            "standalone_agents": len(self.catalog.get("standalone", [])),
            "pattern_agents": len([
                a for pattern_agents in self.catalog.get("patterns", {}).values()
                for a in pattern_agents
            ]),
            "by_category": categories,
            "average_rating": sum(
                a.get("discovery", {}).get("quality_rating", 0)
                for a in all_agents
            ) / max(len(all_agents), 1),
            "most_used": sorted(
                all_agents,
                key=lambda a: a.get("discovery", {}).get("usage_count", 0),
                reverse=True
            )[:5]
        }

    def get_agent(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get agent by ID."""
        # Search standalone
        for agent in self.catalog.get("standalone", []):
            if agent.get("id") == agent_id:
                return agent

        # Search patterns
        for agents in self.catalog.get("patterns", {}).values():
            for agent in agents:
                if agent.get("id") == agent_id:
                    return agent

        return None

    def _agent_matches_query(self, agent: Dict, query: str) -> bool:
        """Check if agent matches search query."""
        # Name match
        if query in agent.get("name", "").lower():
            return True

        # Description match
        if query in agent.get("description", "").lower():
            return True

        # Tags match
        tags = agent.get("tags", [])
        if any(query in tag.lower() for tag in tags):
            return True

        # Keywords match
        keywords = agent.get("discovery", {}).get("keywords", [])
        if any(query in kw.lower() for kw in keywords):
            return True

        # Use cases match
        use_cases = agent.get("use_cases", [])
        if any(query in uc.lower() for uc in use_cases):
            return True

        return False

    def _relevance_score(self, agent: Dict, query: str) -> int:
        """Score agent relevance to query."""
        score = 0

        # Name match is highest priority
        if query in agent.get("name", "").lower():
            score += 10

        # Tag match is second priority
        if any(query in tag.lower() for tag in agent.get("tags", [])):
            score += 5

        # Description/keyword match is lower
        if query in agent.get("description", "").lower():
            score += 2

        # Use count as tiebreaker
        score += agent.get("discovery", {}).get("usage_count", 0) / 100

        return score
