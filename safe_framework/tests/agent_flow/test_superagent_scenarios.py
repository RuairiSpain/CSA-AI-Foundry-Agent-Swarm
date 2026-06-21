"""
Superagent dry-run scenario tests.

Each scenario simulates a multi-pattern workflow by chaining MockAgents:
  - Policy Q&A (RAG pattern)
  - Contract Review (RAG → EvaluatorOptimizer → GateGuard)
  - Employee Onboarding excerpt (Planning → Reflection → HITL)

All tests run without LLM calls; MockAgent validates contract shape and
returns schema-compliant synthetic outputs.
"""

import pytest
from safe_core.models import Agent, RouteDefinition, RoutePattern

from .conftest import MockAgent


def make_agent(name, inputs=None, outputs=None):
    return Agent(
        name=name,
        category="test",
        version="1.0",
        input_schema={"properties": {k: {} for k in (inputs or [])}, "required": list(inputs or [])},
        output_schema={"properties": {k: {} for k in (outputs or [])}, "required": list(outputs or [])},
    )


# ---------------------------------------------------------------------------
# Scenario 1: Policy Q&A (RAG)
# ---------------------------------------------------------------------------

class TestPolicyQaScenario:
    """Simulate: question → retriever → reranker → generator → answer"""

    @pytest.mark.asyncio
    async def test_rag_chain_executes_in_order(self):
        retriever = MockAgent(
            make_agent("Retriever", inputs=["query"], outputs=["chunks"]),
            {"chunks": ["chunk1", "chunk2"]},
        )
        reranker = MockAgent(
            make_agent("Reranker", inputs=["chunks"], outputs=["ranked_chunks"]),
            {"ranked_chunks": ["chunk1"]},
        )
        generator = MockAgent(
            make_agent("Generator", inputs=["ranked_chunks", "query"], outputs=["answer"]),
            {"answer": "Policy answer"},
        )

        # Simulate the RAG chain
        user_query = {"query": "What is the remote work policy?"}
        retrieved = await retriever.invoke(user_query)
        reranked = await reranker.invoke(retrieved)
        final = await generator.invoke({**reranked, **user_query})

        assert retriever.calls == 1
        assert reranker.calls == 1
        assert generator.calls == 1
        assert "answer" in final

    @pytest.mark.asyncio
    async def test_rag_retriever_receives_query(self):
        retriever = MockAgent(
            make_agent("Retriever", inputs=["query"], outputs=["chunks"]),
        )
        await retriever.invoke({"query": "test question"})
        assert retriever.last_input == {"query": "test question"}

    @pytest.mark.asyncio
    async def test_rag_output_has_answer_field(self):
        retriever = MockAgent(make_agent("R", outputs=["chunks"]), {"chunks": ["c"]})
        reranker = MockAgent(make_agent("RR", outputs=["ranked_chunks"]), {"ranked_chunks": ["c"]})
        generator = MockAgent(make_agent("G", outputs=["answer"]), {"answer": "yes"})

        r1 = await retriever.invoke({"query": "q"})
        r2 = await reranker.invoke(r1)
        r3 = await generator.invoke(r2)
        assert r3["answer"] == "yes"


# ---------------------------------------------------------------------------
# Scenario 2: Contract Review (RAG + EvaluatorOptimizer + GateGuard)
# ---------------------------------------------------------------------------

class TestContractReviewScenario:
    """Three-pattern chained workflow: retrieve → evaluate → guard."""

    @pytest.mark.asyncio
    async def test_retriever_to_evaluator_pipeline(self):
        retriever = MockAgent(
            make_agent("ContractRetriever", outputs=["contract_text"]),
            {"contract_text": "contract content"},
        )
        evaluator = MockAgent(
            make_agent("ContractEvaluator", inputs=["contract_text"], outputs=["quality_score", "feedback"]),
            {"quality_score": "0.9", "feedback": "looks good"},
        )
        guard = MockAgent(
            make_agent("ContractGuard", inputs=["quality_score"], outputs=["approved"]),
            {"approved": "true"},
        )

        retrieved = await retriever.invoke({"contract_id": "C001"})
        evaluated = await evaluator.invoke(retrieved)
        guarded = await guard.invoke(evaluated)

        assert "approved" in guarded
        assert guarded["approved"] == "true"

    @pytest.mark.asyncio
    async def test_evaluator_loop_terminates(self):
        """Evaluator-optimizer pattern: loop until score threshold or max iterations."""
        generator = MockAgent(
            make_agent("Generator", outputs=["draft"]),
            {"draft": "draft text"},
        )
        evaluator = MockAgent(
            make_agent("Evaluator", inputs=["draft"], outputs=["score"]),
            {"score": "0.9"},
        )

        MAX_ITERS = 3
        threshold = 0.85
        result = None

        for i in range(MAX_ITERS):
            draft_out = await generator.invoke({"topic": "contract"})
            eval_out = await evaluator.invoke(draft_out)
            score = float(eval_out["score"])
            if score >= threshold:
                result = draft_out
                break

        assert result is not None, "EO loop did not converge"
        assert generator.calls >= 1
        assert evaluator.calls >= 1

    @pytest.mark.asyncio
    async def test_gate_blocks_low_quality(self):
        """Guard should receive failing score and we check output shape."""
        guard = MockAgent(
            make_agent("Guard", inputs=["quality_score"], outputs=["approved", "reason"]),
            {"approved": "false", "reason": "score below threshold"},
        )
        result = await guard.invoke({"quality_score": "0.4"})
        assert "approved" in result
        assert "reason" in result


# ---------------------------------------------------------------------------
# Scenario 3: Employee Onboarding excerpt (Planning + Reflection + HITL)
# ---------------------------------------------------------------------------

class TestEmployeeOnboardingScenario:
    """Complex workflow excerpt: plan → execute → reflect → human gate."""

    @pytest.mark.asyncio
    async def test_plan_execute_reflect_chain(self):
        planner = MockAgent(
            make_agent("OnboardingPlanner", inputs=["employee_id"], outputs=["plan"]),
            {"plan": "step1, step2, step3"},
        )
        executor = MockAgent(
            make_agent("OnboardingExecutor", inputs=["plan"], outputs=["execution_result"]),
            {"execution_result": "completed"},
        )
        critic = MockAgent(
            make_agent("OnboardingCritic", inputs=["execution_result"], outputs=["feedback"]),
            {"feedback": "all good"},
        )
        refiner = MockAgent(
            make_agent("OnboardingRefiner", inputs=["execution_result", "feedback"], outputs=["refined"]),
            {"refined": "refined output"},
        )
        human_gate = MockAgent(
            make_agent("HRApproval", inputs=["refined"], outputs=["approved"]),
            {"approved": "yes"},
        )

        # Full chain
        plan_out = await planner.invoke({"employee_id": "EMP-001"})
        exec_out = await executor.invoke(plan_out)
        crit_out = await critic.invoke(exec_out)
        refine_out = await refiner.invoke({**exec_out, **crit_out})
        gate_out = await human_gate.invoke(refine_out)

        assert gate_out["approved"] == "yes"
        assert planner.calls == 1
        assert executor.calls == 1
        assert critic.calls == 1
        assert refiner.calls == 1
        assert human_gate.calls == 1

    @pytest.mark.asyncio
    async def test_all_agents_invoked_exactly_once(self):
        """Verify no agent is skipped in the standard happy path."""
        agents = [
            MockAgent(make_agent(f"Agent{i}", outputs=[f"out{i}"]), {f"out{i}": f"val{i}"})
            for i in range(5)
        ]

        inputs = {}
        for agent in agents:
            inputs = await agent.invoke(inputs)

        for i, agent in enumerate(agents):
            assert agent.calls == 1, f"Agent{i} was not called exactly once"

    @pytest.mark.asyncio
    async def test_data_flows_across_stages(self):
        """Output of one stage must be received as input by the next."""
        stage1 = MockAgent(
            make_agent("Stage1", outputs=["payload"]),
            {"payload": "important_data"},
        )
        stage2 = MockAgent(
            make_agent("Stage2", inputs=["payload"], outputs=["processed"]),
            {"processed": "done"},
        )

        out1 = await stage1.invoke({})
        out2 = await stage2.invoke(out1)

        assert stage2.last_input == {"payload": "important_data"}
        assert out2["processed"] == "done"
