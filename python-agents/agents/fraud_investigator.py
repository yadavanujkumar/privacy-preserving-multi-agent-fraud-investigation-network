import logging
import os
from typing import TypedDict
from langgraph.graph import StateGraph, END
from neo4j import GraphDatabase

logger = logging.getLogger(__name__)

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASS = os.getenv("NEO4J_PASS", "secretpassword")

HIGH_VALUE_THRESHOLD = float(os.getenv("HIGH_VALUE_THRESHOLD", "10000"))
HIGH_CONNECTIONS_THRESHOLD = int(os.getenv("HIGH_CONNECTIONS_THRESHOLD", "10"))


class AgentState(TypedDict):
    transaction: dict
    risk_score: float
    graph_connections: int
    risk_factors: list
    summary: str


def fetch_graph_features(state: AgentState) -> AgentState:
    try:
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))
        with driver.session() as session:
            result = session.run(
                """
                MATCH (a:Account {id: $source})-[:TRANSACTED_WITH*1..2]-(connected)
                RETURN count(DISTINCT connected) AS connections
                """,
                source=state["transaction"].get("source", ""),
            )
            record = result.single()
            state["graph_connections"] = record["connections"] if record else 0
        driver.close()
    except Exception as exc:  # noqa: BLE001
        logger.warning("Neo4j unavailable, defaulting graph_connections to 0: %s", exc)
        state["graph_connections"] = 0
    return state


def run_federated_model(state: AgentState) -> AgentState:
    score = 0.0
    factors: list[str] = []
    tx = state["transaction"]
    amount = tx.get("amount", 0)

    # Factor 1: high transaction amount
    if amount > HIGH_VALUE_THRESHOLD:
        score += 0.45
        factors.append(f"high_amount:{amount}")

    # Factor 2: dense graph neighbourhood (potential fraud ring)
    if state["graph_connections"] > HIGH_CONNECTIONS_THRESHOLD:
        score += 0.35
        factors.append(f"high_connections:{state['graph_connections']}")

    # Factor 3: cross-border heuristic (source/target on different continents)
    source = tx.get("source", "")
    target = tx.get("target", "")
    if source and target and source[:2] != target[:2]:
        score += 0.10
        factors.append("cross_region")

    # Factor 4: velocity – repeated source within session
    if tx.get("is_velocity_breach"):
        score += 0.10
        factors.append("velocity_breach")

    state["risk_score"] = min(round(score, 4), 1.0)
    state["risk_factors"] = factors
    return state


def generate_explanation(state: AgentState) -> AgentState:
    score = state["risk_score"]
    factors = state["risk_factors"]
    tx = state["transaction"]

    if score >= 0.75:
        level = "CRITICAL"
    elif score >= 0.45:
        level = "HIGH"
    elif score >= 0.20:
        level = "MEDIUM"
    else:
        level = "LOW"

    if factors:
        factor_text = ", ".join(factors)
        state["summary"] = (
            f"[{level}] Risk score {score:.2f} – contributing factors: {factor_text}. "
            f"Transaction amount {tx.get('amount')} from {tx.get('source')} to {tx.get('target')}. "
            f"Graph context: {state['graph_connections']} connected accounts."
        )
    else:
        state["summary"] = (
            f"[{level}] Transaction from {tx.get('source')} to {tx.get('target')} "
            f"appears normal (risk score {score:.2f})."
        )
    return state


workflow = StateGraph(AgentState)
workflow.add_node("fetch_graph", fetch_graph_features)
workflow.add_node("run_model", run_federated_model)
workflow.add_node("generate_xai", generate_explanation)

workflow.set_entry_point("fetch_graph")
workflow.add_edge("fetch_graph", "run_model")
workflow.add_edge("run_model", "generate_xai")
workflow.add_edge("generate_xai", END)

app_graph = workflow.compile()


def process_alert(transaction_data: dict) -> AgentState:
    initial_state = AgentState(
        transaction=transaction_data,
        risk_score=0.0,
        graph_connections=0,
        risk_factors=[],
        summary="",
    )
    return app_graph.invoke(initial_state)
