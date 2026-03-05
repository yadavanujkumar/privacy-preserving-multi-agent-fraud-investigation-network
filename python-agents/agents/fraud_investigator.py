from typing import TypedDict
from langgraph.graph import StateGraph, END
from neo4j import GraphDatabase
import os

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASS = os.getenv("NEO4J_PASS", "secretpassword")

class AgentState(TypedDict):
    transaction: dict
    risk_score: float
    graph_connections: int
    summary: str

def fetch_graph_features(state: AgentState) -> AgentState:
    try:
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))
        with driver.session() as session:
            state['graph_connections'] = 5
        driver.close()
    except Exception as e:
        state['graph_connections'] = 0
    return state

def run_federated_model(state: AgentState) -> AgentState:
    state['risk_score'] = 0.85 if state['transaction'].get('amount', 0) > 10000 else 0.1
    return state

def generate_explanation(state: AgentState) -> AgentState:
    if state['risk_score'] > 0.8:
        state['summary'] = f"High risk transaction detected. Amount {state['transaction'].get('amount')} exceeds threshold. Graph context shows {state['graph_connections']} connections."
    else:
        state['summary'] = "Transaction appears normal."
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

def process_alert(transaction_data: dict):
    initial_state = AgentState(transaction=transaction_data, risk_score=0.0, graph_connections=0, summary="")
    return app_graph.invoke(initial_state)