"""Command-line entrypoint for the lab starter."""

from typing import Annotated

import typer
from rich.console import Console
from rich.panel import Panel

from multi_agent_research_lab.core.config import get_settings
from multi_agent_research_lab.core.errors import StudentTodoError
from multi_agent_research_lab.core.schemas import ResearchQuery
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.graph.workflow import MultiAgentWorkflow
from multi_agent_research_lab.observability.logging import configure_logging

app = typer.Typer(help="Multi-Agent Research Lab starter CLI")
console = Console()


def _init() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)


from time import perf_counter
from multi_agent_research_lab.services.llm_client import LLMClient
from multi_agent_research_lab.core.schemas import AgentName, AgentResult


@app.command()
def baseline(
    query: Annotated[str, typer.Option("--query", "-q", help="Research query")],
) -> None:
    """Run a minimal single-agent baseline."""

    _init()
    request = ResearchQuery(query=query)
    state = ResearchState(request=request)

    start_time = perf_counter()
    llm = LLMClient()

    system_prompt = (
        "You are an expert researcher. Answer the user query thoroughly, "
        "providing clear analysis and structured insights. Cite sources if appropriate."
    )

    try:
        response = llm.complete(system_prompt=system_prompt, user_prompt=query)
        latency = perf_counter() - start_time

        state.final_answer = response.content
        state.agent_results.append(
            AgentResult(
                agent=AgentName.WRITER,
                content=response.content,
                metadata={
                    "input_tokens": response.input_tokens,
                    "output_tokens": response.output_tokens,
                    "cost_usd": response.cost_usd,
                    "latency": latency,
                },
            )
        )

        console.print(Panel.fit(state.final_answer, title="Single-Agent Baseline"))
        console.print(
            f"[green]Latency:[/] {latency:.2f}s | "
            f"[green]Estimated Cost:[/] ${response.cost_usd or 0:.6f}"
        )
    except Exception as exc:
        console.print(f"[red]Error during baseline execution:[/] {exc}")
        state.errors.append(str(exc))


@app.command("multi-agent")
def multi_agent(
    query: Annotated[str, typer.Option("--query", "-q", help="Research query")],
) -> None:
    """Run the multi-agent workflow skeleton."""

    _init()
    state = ResearchState(request=ResearchQuery(query=query))
    workflow = MultiAgentWorkflow()
    try:
        result = workflow.run(state)
    except StudentTodoError as exc:
        console.print(Panel.fit(str(exc), title="Expected TODO", style="yellow"))
        raise typer.Exit(code=2) from exc
    console.print(result.model_dump_json(indent=2))


@app.command()
def benchmark(
    query: Annotated[str, typer.Option("--query", "-q", help="Research query")],
) -> None:
    """Run both single-agent baseline and multi-agent workflow, then save report."""
    import os
    from multi_agent_research_lab.evaluation.benchmark import run_benchmark
    from multi_agent_research_lab.evaluation.report import render_markdown_report

    _init()
    console.print(f"[bold blue]Starting comparative benchmark for query:[/] {query}\n")

    # 1. Baseline Runner
    def baseline_runner(q: str) -> ResearchState:
        request = ResearchQuery(query=q)
        state = ResearchState(request=request)
        llm = LLMClient()
        system_prompt = (
            "You are an expert researcher. Answer the user query thoroughly, "
            "providing clear analysis and structured insights. Cite sources if appropriate."
        )
        response = llm.complete(system_prompt=system_prompt, user_prompt=q)
        state.final_answer = response.content
        state.agent_results.append(
            AgentResult(
                agent=AgentName.WRITER,
                content=response.content,
                metadata={
                    "input_tokens": response.input_tokens,
                    "output_tokens": response.output_tokens,
                    "cost_usd": response.cost_usd,
                },
            )
        )
        return state

    # 2. Multi-Agent Runner
    def multi_agent_runner(q: str) -> ResearchState:
        state = ResearchState(request=ResearchQuery(query=q))
        workflow = MultiAgentWorkflow()
        return workflow.run(state)

    console.print("[yellow]Running Single-Agent Baseline...[/]")
    state_base, metrics_base = run_benchmark("Single-Agent Baseline", query, baseline_runner)
    console.print(f"[green]Baseline completed in {metrics_base.latency_seconds:.2f}s.[/]\n")

    console.print("[yellow]Running Multi-Agent Workflow...[/]")
    state_multi, metrics_multi = run_benchmark("Multi-Agent Workflow", query, multi_agent_runner)
    console.print(f"[green]Multi-Agent completed in {metrics_multi.latency_seconds:.2f}s.[/]\n")

    # 3. Render and save report
    report_md = render_markdown_report([metrics_base, metrics_multi])
    
    os.makedirs("reports", exist_ok=True)
    report_path = "reports/benchmark_report.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_md)

    console.print(
        Panel.fit(
            f"Benchmark completed successfully!\nReport saved to: {report_path}",
            title="Success",
            style="green",
        )
    )


if __name__ == "__main__":
    app()
