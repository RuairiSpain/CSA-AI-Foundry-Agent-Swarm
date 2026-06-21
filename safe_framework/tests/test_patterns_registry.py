"""Tests for safe_core.patterns (PatternRegistry and all 12 built-in patterns)."""

import pytest
from safe_core.patterns import (
    PATTERN_REGISTRY,
    PatternCategory,
    PatternComplexity,
    PatternTemplate,
    PlaceholderNode,
    VariableParameter,
    FAN_OUT_FAN_IN,
    MAP_REDUCE,
    ROUND_ROBIN,
    MIXTURE_OF_EXPERTS,
    SEQUENTIAL_PIPELINE,
    SUPERVISOR_MANAGER,
    HIERARCHICAL_TEAMS,
    FALLBACK_CHAIN,
    RETRY_LOOP,
    DIAMOND,
    CONDITIONAL_BRANCHING,
    TREE_REDUCE,
    PatternRegistry,
)

KNOWN_PATTERN_IDS = [
    "fan-out-fan-in",
    "map-reduce",
    "round-robin",
    "mixture-of-experts",
    "sequential-pipeline",
    "supervisor-manager",
    "hierarchical-teams",
    "fallback-chain",
    "retry-loop",
    "diamond",
    "conditional-branching",
    "tree-reduce",
]


class TestPatternRegistryBuiltIns:
    def test_all_builtin_patterns_registered(self):
        for pid in KNOWN_PATTERN_IDS:
            assert PATTERN_REGISTRY.get_pattern(pid) is not None, f"{pid} not registered"

    def test_total_count(self):
        assert len(PATTERN_REGISTRY.patterns) >= 12

    def test_get_nonexistent_returns_none(self):
        assert PATTERN_REGISTRY.get_pattern("does-not-exist") is None


class TestPatternRegistryFilter:
    def test_list_all_no_filter(self):
        patterns = PATTERN_REGISTRY.list_patterns()
        assert len(patterns) >= 12

    def test_filter_by_category_parallel(self):
        patterns = PATTERN_REGISTRY.list_patterns(category=PatternCategory.PARALLEL)
        for p in patterns:
            assert p.category == PatternCategory.PARALLEL

    def test_filter_by_complexity_simple(self):
        patterns = PATTERN_REGISTRY.list_patterns(complexity=PatternComplexity.SIMPLE)
        for p in patterns:
            assert p.complexity == PatternComplexity.SIMPLE

    def test_filter_returns_sorted(self):
        patterns = PATTERN_REGISTRY.list_patterns()
        ids = [p.pattern_id for p in patterns]
        assert ids == sorted(ids)


class TestPatternRegistrySearch:
    def test_search_by_name_keyword(self):
        results = PATTERN_REGISTRY.search_patterns("fan")
        assert any(p.pattern_id == "fan-out-fan-in" for p in results)

    def test_search_by_use_case(self):
        results = PATTERN_REGISTRY.search_patterns("parallel")
        assert len(results) > 0

    def test_search_no_match_returns_empty(self):
        results = PATTERN_REGISTRY.search_patterns("zzznomatch")
        assert results == []


class TestPatternRegistryStats:
    def test_stats_keys(self):
        stats = PATTERN_REGISTRY.get_statistics()
        assert "total_patterns" in stats
        assert "by_category" in stats
        assert "by_complexity" in stats

    def test_stats_total(self):
        stats = PATTERN_REGISTRY.get_statistics()
        assert stats["total_patterns"] >= 12

    def test_stats_by_category_sums_to_total(self):
        stats = PATTERN_REGISTRY.get_statistics()
        cat_sum = sum(stats["by_category"].values())
        assert cat_sum == stats["total_patterns"]

    def test_stats_by_complexity_sums_to_total(self):
        stats = PATTERN_REGISTRY.get_statistics()
        cplx_sum = sum(stats["by_complexity"].values())
        assert cplx_sum == stats["total_patterns"]


class TestPatternRegistryRegister:
    def test_register_custom_pattern(self):
        registry = PatternRegistry()
        custom = PatternTemplate(
            pattern_id="test-custom",
            name="Test Custom",
            version="1.0",
            category=PatternCategory.SEQUENTIAL,
            complexity=PatternComplexity.SIMPLE,
            description="A test pattern",
            use_cases=["testing"],
            diagram_ascii="[A] -> [B]",
            placeholders=[
                PlaceholderNode(
                    id="a", name="A", description="A node", stage="input"
                )
            ],
            variables=[],
            code_template="",
            example_workflow={},
        )
        registry.register_pattern(custom)
        assert registry.get_pattern("test-custom") is not None
        assert registry.get_pattern("test-custom").name == "Test Custom"


class TestBuiltInPatternStructure:
    @pytest.mark.parametrize("pattern", [
        FAN_OUT_FAN_IN, MAP_REDUCE, ROUND_ROBIN, MIXTURE_OF_EXPERTS,
        SEQUENTIAL_PIPELINE, SUPERVISOR_MANAGER, HIERARCHICAL_TEAMS,
        FALLBACK_CHAIN, RETRY_LOOP, DIAMOND, CONDITIONAL_BRANCHING, TREE_REDUCE,
    ])
    def test_has_required_fields(self, pattern):
        assert pattern.pattern_id
        assert pattern.name
        assert pattern.version
        assert isinstance(pattern.category, PatternCategory)
        assert isinstance(pattern.complexity, PatternComplexity)
        assert pattern.description
        assert len(pattern.use_cases) >= 1
        assert len(pattern.placeholders) >= 1

    @pytest.mark.parametrize("pattern", [
        FAN_OUT_FAN_IN, MAP_REDUCE, ROUND_ROBIN, MIXTURE_OF_EXPERTS,
        SEQUENTIAL_PIPELINE, SUPERVISOR_MANAGER, HIERARCHICAL_TEAMS,
        FALLBACK_CHAIN, RETRY_LOOP, DIAMOND, CONDITIONAL_BRANCHING, TREE_REDUCE,
    ])
    def test_placeholders_have_required_fields(self, pattern):
        for ph in pattern.placeholders:
            assert ph.id
            assert ph.name
            assert ph.stage in ("input", "processing", "aggregation", "output")

    @pytest.mark.parametrize("pattern", [
        FAN_OUT_FAN_IN, MAP_REDUCE, ROUND_ROBIN, MIXTURE_OF_EXPERTS,
        SEQUENTIAL_PIPELINE, SUPERVISOR_MANAGER, HIERARCHICAL_TEAMS,
        FALLBACK_CHAIN, RETRY_LOOP, DIAMOND, CONDITIONAL_BRANCHING, TREE_REDUCE,
    ])
    def test_variables_have_required_fields(self, pattern):
        for var in pattern.variables:
            assert var.name
            assert var.param_type in ("integer", "string", "boolean")
            assert var.default is not None


class TestPatternCategories:
    def test_fan_out_is_parallel(self):
        assert FAN_OUT_FAN_IN.category == PatternCategory.PARALLEL

    def test_map_reduce_is_parallel(self):
        assert MAP_REDUCE.category == PatternCategory.PARALLEL

    def test_sequential_pipeline_is_sequential(self):
        assert SEQUENTIAL_PIPELINE.category == PatternCategory.SEQUENTIAL

    def test_diamond_is_conditional(self):
        assert DIAMOND.category == PatternCategory.CONDITIONAL

    def test_tree_reduce_is_reduction(self):
        assert TREE_REDUCE.category == PatternCategory.REDUCTION


class TestPatternComplexities:
    def test_round_robin_is_simple(self):
        assert ROUND_ROBIN.complexity == PatternComplexity.SIMPLE

    def test_sequential_pipeline_is_simple(self):
        assert SEQUENTIAL_PIPELINE.complexity == PatternComplexity.SIMPLE

    def test_supervisor_is_advanced(self):
        assert SUPERVISOR_MANAGER.complexity == PatternComplexity.ADVANCED

    def test_fan_out_is_intermediate(self):
        assert FAN_OUT_FAN_IN.complexity == PatternComplexity.INTERMEDIATE
