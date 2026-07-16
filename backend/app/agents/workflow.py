from __future__ import annotations

import time
from collections.abc import Callable
from typing import TypedDict
from uuid import UUID

from langgraph.graph import END, StateGraph
from sqlalchemy.orm import Session

from app.db.models import AgentRun, AgentTrace, Dataset
from app.services.sql import classify_intent, generate_sql, validate_sql


class AgentState(TypedDict, total=False):
    question: str
    dataset_id: str | None
    intent: str
    schema_columns: list[str]
    plan: list[str]
    candidate_sql: str
    safety_status: str
    safety_findings: list[str]
    critic: str
    traces: list[dict]


def _timed(name: str, fn: Callable[[AgentState], dict]) -> Callable[[AgentState], dict]:
    def wrapped(state: AgentState) -> dict:
        start = time.perf_counter()
        update = fn(state)
        latency_ms = max(1, int((time.perf_counter() - start) * 1000))
        summary = update.pop("_summary", "")
        traces = list(state.get("traces", []))
        traces.append({"node": name, "output": summary, "latency_ms": latency_ms})
        return {**update, "traces": traces}

    wrapped.__name__ = name
    return wrapped


def build_graph(dataset: Dataset | None):
    def intent_node(state: AgentState) -> dict:
        intent = classify_intent(state["question"])
        return {"intent": intent, "_summary": f"Classified intent as '{intent}'."}

    def schema_node(state: AgentState) -> dict:
        if dataset is not None and dataset.columns:
            cols = [c.column_name for c in dataset.columns]
            return {
                "schema_columns": cols,
                "_summary": (
                    f"Inspected '{dataset.original_filename}': "
                    f"{len(cols)} columns, {dataset.row_count} rows."
                ),
            }
        return {"schema_columns": [], "_summary": "No dataset selected; schema inspection skipped."}

    def planner_node(state: AgentState) -> dict:
        intent = state.get("intent", "sql_analytics")
        base = {
            "sql_analytics": ["generate governed SQL", "validate SQL", "execute only after approval", "summarize result"],
            "forecasting": ["profile revenue series", "fit forecasting model", "summarize horizon"],
            "modeling": ["prepare features", "score churn risk", "surface at-risk cohort"],
            "eda": ["profile dataset", "surface drivers", "summarize findings"],
        }.get(intent, ["profile dataset", "summarize findings"])

        update: dict = {"plan": base}
        # For analytics questions, actually produce + govern candidate SQL.
        if intent == "sql_analytics" and dataset is not None and dataset.duckdb_table_name:
            try:
                candidate_sql, _ = generate_sql(state["question"], dataset)
                safety = validate_sql(candidate_sql, dataset, {c.column_name for c in dataset.columns})
                update["candidate_sql"] = candidate_sql
                update["safety_status"] = safety.status
                update["safety_findings"] = safety.findings
                update["_summary"] = (
                    f"Planned {len(base)} steps; generated candidate SQL "
                    f"(governance: {safety.status})."
                )
                return update
            except ValueError:
                pass
        update["_summary"] = f"Planned {len(base)} steps for intent '{intent}'."
        return update

    def critic_node(state: AgentState) -> dict:
        notes: list[str] = []
        if dataset is None:
            notes.append("No dataset attached — results cannot be grounded in data.")
        if state.get("safety_status") == "blocked":
            notes.append(f"Generated SQL failed governance: {'; '.join(state.get('safety_findings', []))}.")
        elif state.get("safety_status") == "safe":
            notes.append("Generated SQL passed governance and references only allowed columns.")
        if not notes:
            notes.append("No governance gaps detected for this intent.")
        return {"critic": " ".join(notes), "_summary": notes[0]}

    graph = StateGraph(AgentState)
    graph.add_node("intent_classifier", _timed("intent_classifier", intent_node))
    graph.add_node("schema_inspector", _timed("schema_inspector", schema_node))
    graph.add_node("planner", _timed("planner", planner_node))
    graph.add_node("critic", _timed("critic", critic_node))
    graph.set_entry_point("intent_classifier")
    graph.add_edge("intent_classifier", "schema_inspector")
    graph.add_edge("schema_inspector", "planner")
    graph.add_edge("planner", "critic")
    graph.add_edge("critic", END)
    return graph.compile()


def _confidence(state: AgentState) -> tuple[float, dict]:
    """Confidence derived from real run signals, not a constant."""
    signals: dict[str, float] = {}
    score = 0.35
    if state.get("schema_columns"):
        signals["dataset_grounded"] = 0.20
    if state.get("candidate_sql"):
        signals["sql_generated"] = 0.15
    status = state.get("safety_status")
    if status == "safe":
        signals["governance_safe"] = 0.20
    elif status == "blocked":
        signals["governance_blocked"] = -0.25
    if status == "safe" and not any("Unknown column" in f for f in state.get("safety_findings", [])):
        signals["columns_valid"] = 0.10
    score += sum(signals.values())
    score = max(0.05, min(0.98, score))
    return round(score, 4), signals


def run_agent(db: Session, user_id: UUID, question: str, dataset: Dataset | None) -> AgentRun:
    start = time.time()
    run = AgentRun(
        user_id=user_id,
        dataset_id=dataset.id if dataset else None,
        question=question,
        intent="unknown",
        status="running",
    )
    db.add(run)
    db.flush()

    initial: AgentState = AgentState(question=question, dataset_id=str(dataset.id) if dataset else None, traces=[])
    final = build_graph(dataset).invoke(initial)

    for tr in final.get("traces", []):
        db.add(
            AgentTrace(
                agent_run_id=run.id,
                node_name=tr["node"],
                input_summary=question[:500],
                output_summary=str(tr["output"])[:1000],
                status="completed",
                latency_ms=tr["latency_ms"],
            )
        )

    confidence, signals = _confidence(final)
    run.intent = final.get("intent", "unknown")
    run.status = "completed"
    run.confidence_score = confidence
    run.latency_ms = int((time.time() - start) * 1000)
    # Persist the confidence rationale on the critic trace for auditability.
    db.add(
        AgentTrace(
            agent_run_id=run.id,
            node_name="confidence",
            input_summary=question[:500],
            output_summary=f"confidence={confidence} signals={signals}"[:1000],
            status="completed",
            latency_ms=1,
        )
    )
    return run
