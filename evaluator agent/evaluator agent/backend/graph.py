from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

try:
    from backend.state import EvaluatorState
    from backend.nodes import (
        initialize_milestone_node,
        ingest_evidence_node,
        evaluate_evidence_node,
        analyze_security_and_telemetry_subagent_node,
        calculate_milestone_score_node,
        generate_justification_node,
        calculate_escrow_disbursement_node,
        update_startup_performance_node,
        determine_next_action_node
    )
except (ImportError, ModuleNotFoundError):
    from state import EvaluatorState
    from nodes import (
        initialize_milestone_node,
        ingest_evidence_node,
        evaluate_evidence_node,
        analyze_security_and_telemetry_subagent_node,
        calculate_milestone_score_node,
        generate_justification_node,
        calculate_escrow_disbursement_node,
        update_startup_performance_node,
        determine_next_action_node
    )

def route_after_init(state: EvaluatorState) -> str:
    """Conditional router checking if contractual approval blocks evaluation."""
    if state.get("status") == "Blocked":
        return "blocked_end"
    return "ingest_evidence"

# Global memory checkpointer for state persistence across execution sessions
checkpointer = MemorySaver()

def create_evaluator_graph():
    """Build and compile the LangGraph StateGraph workflow with specialist subagent nodes and memory persistence."""
    workflow = StateGraph(EvaluatorState)

    # Add Evaluation & Specialist Subagent Nodes
    workflow.add_node("initialize_milestone", initialize_milestone_node)
    workflow.add_node("ingest_evidence", ingest_evidence_node)
    workflow.add_node("evaluate_evidence", evaluate_evidence_node)
    workflow.add_node("analyze_security_telemetry", analyze_security_and_telemetry_subagent_node)
    workflow.add_node("calculate_score", calculate_milestone_score_node)
    workflow.add_node("generate_justification", generate_justification_node)
    workflow.add_node("calculate_escrow", calculate_escrow_disbursement_node)
    workflow.add_node("update_performance", update_startup_performance_node)
    workflow.add_node("determine_next_action", determine_next_action_node)

    # Set Entry Point
    workflow.set_entry_point("initialize_milestone")

    # Conditional Edge after Initialization
    workflow.add_conditional_edges(
        "initialize_milestone",
        route_after_init,
        {
            "blocked_end": END,
            "ingest_evidence": "ingest_evidence"
        }
    )

    # Sequential & Specialist Subagent Transitions
    workflow.add_edge("ingest_evidence", "evaluate_evidence")
    workflow.add_edge("evaluate_evidence", "analyze_security_telemetry")
    workflow.add_edge("analyze_security_telemetry", "calculate_score")
    workflow.add_edge("calculate_score", "generate_justification")
    workflow.add_edge("generate_justification", "calculate_escrow")
    workflow.add_edge("calculate_escrow", "update_performance")
    workflow.add_edge("update_performance", "determine_next_action")
    workflow.add_edge("determine_next_action", END)

    # Compile Graph with Checkpointer
    app_graph = workflow.compile(checkpointer=checkpointer)
    return app_graph

# Global compiled graph instance
evaluator_graph = create_evaluator_graph()

