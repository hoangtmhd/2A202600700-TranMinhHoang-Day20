"""Benchmark skeleton for single-agent vs multi-agent."""

import json
import re
from time import perf_counter
from typing import Callable

from multi_agent_research_lab.core.schemas import BenchmarkMetrics
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.services.llm_client import LLMClient


Runner = Callable[[str], ResearchState]


def run_benchmark(run_name: str, query: str, runner: Runner) -> tuple[ResearchState, BenchmarkMetrics]:
    """Measure latency, cost, citation coverage, and evaluate report quality using LLM-as-a-judge."""
    started = perf_counter()
    state = runner(query)
    latency = perf_counter() - started

    # 1. Sum up token costs across all agents
    total_cost = sum(
        res.metadata.get("cost_usd", 0.0) or 0.0 for res in state.agent_results
    )

    # 2. Calculate Citation Coverage
    citations = re.findall(r"\[\d+\]", state.final_answer or "")
    unique_citations = set(citations)
    citation_count = len(unique_citations)
    sources_count = len(state.sources)
    coverage_str = f"Cited {citation_count}/{sources_count} sources."

    # 3. LLM-as-a-judge evaluation for Quality Score (0-10)
    quality_score = 5.0
    feedback = "Failed to evaluate quality."

    if state.final_answer and not state.errors:
        try:
            llm = LLMClient()
            system_prompt = (
                "You are an expert academic evaluator. Your job is to grade a research report "
                "on a scale from 0.0 to 10.0 based on:\n"
                "1. Factuality & Depth: how well it answers the query.\n"
                "2. Structure & Clarity.\n"
                "3. Citation Usage: whether it integrates sources correctly.\n\n"
                "Return ONLY a JSON object containing keys:\n"
                "- 'score': a float value between 0.0 and 10.0.\n"
                "- 'feedback': a brief one-sentence reason."
            )
            user_prompt = f"Query: {query}\n\nReport:\n{state.final_answer}"
            response = llm.complete(system_prompt, user_prompt)
            
            content = response.content.strip()
            if content.startswith("```"):
                content = content.replace("```json", "").replace("```", "").strip()
            
            data = json.loads(content)
            quality_score = float(data.get("score", 7.0))
            feedback = data.get("feedback", "No feedback provided.")
        except Exception as e:
            feedback = f"Error during evaluation: {e}"
            quality_score = 6.0
    elif state.errors:
        feedback = f"Execution encountered errors: {state.errors[0]}"
        quality_score = 0.0

    metrics = BenchmarkMetrics(
        run_name=run_name,
        latency_seconds=latency,
        estimated_cost_usd=total_cost,
        quality_score=quality_score,
        notes=f"{coverage_str} | Feedback: {feedback}",
    )
    return state, metrics
