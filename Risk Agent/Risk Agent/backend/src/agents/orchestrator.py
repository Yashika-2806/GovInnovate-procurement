import traceback
from typing import TypedDict, Optional, Dict, Any, List
from langgraph.graph import StateGraph, START, END

from src.models.startup_profile import StartupProfile
from src.models.research_data import (
    ResearchResults, IndustryResearch, MarketResearch, 
    RegulatoryResearch, CompetitorResearch, FailedStartup, SuccessfulStartup
)
from src.models.risk_scores import CumulativeRiskAssessment, SimilarCompany
from src.models.report import FullReport
from src.agents.input_parser import InputParserAgent
from src.agents.industry_researcher import IndustryResearchAgent
from src.agents.market_researcher import MarketResearchAgent
from src.agents.failure_analyzer import FailureAnalyzerAgent
from src.agents.success_analyzer import SuccessAnalyzerAgent
from src.agents.regulatory_researcher import RegulatoryResearchAgent
from src.agents.competitor_researcher import CompetitorResearchAgent
from src.scoring.risk_engine import RiskEngine
from src.scoring.weight_selector import WeightSelector
from src.scoring.similarity_engine import SimilarityEngine
from src.scoring.statistical_analyzer import StatisticalAnalyzer
from src.reporting.report_generator import ReportGenerator
from src.reporting.explainability import ExplainabilityEngine


class RiskAgentState(TypedDict, total=False):
    analysis_id: str
    problem_statement: str
    progress: int
    current_step: str
    profile: Optional[StartupProfile]
    industry_data: Optional[IndustryResearch]
    market_data: Optional[MarketResearch]
    failures: List[FailedStartup]
    successes: List[SuccessfulStartup]
    regulatory_data: Optional[RegulatoryResearch]
    competitor_data: Optional[CompetitorResearch]
    research_results: Optional[ResearchResults]
    risk_assessment: Optional[CumulativeRiskAssessment]
    similar_failures: List[SimilarCompany]
    similar_successes: List[SimilarCompany]
    stats: Dict[str, Any]
    report: Optional[FullReport]
    error: Optional[str]


class RunOrchestrator:
    def __init__(self, llm_client, search_client, citation_tracker):
        self.llm_client = llm_client
        self.search_client = search_client
        self.citation_tracker = citation_tracker
        self.analyses: Dict[str, Dict[str, Any]] = {}

        self.input_parser = InputParserAgent(llm_client)
        self.industry_researcher = IndustryResearchAgent(llm_client, search_client)
        self.market_researcher = MarketResearchAgent(llm_client, search_client)
        self.failure_analyzer = FailureAnalyzerAgent(llm_client, search_client)
        self.success_analyzer = SuccessAnalyzerAgent(llm_client, search_client)
        self.regulatory_researcher = RegulatoryResearchAgent(llm_client, search_client)
        self.competitor_researcher = CompetitorResearchAgent(llm_client, search_client)

        self.weight_selector = WeightSelector()
        self.risk_engine = RiskEngine(llm_client, self.weight_selector)
        self.similarity_engine = SimilarityEngine()
        self.statistical_analyzer = StatisticalAnalyzer()
        self.report_generator = ReportGenerator()
        self.explainability_engine = ExplainabilityEngine()

        # Build the LangGraph StateGraph workflow
        self.graph = self._build_graph()

    def _build_graph(self):
        """Constructs the LangGraph multi-agent workflow DAG."""
        workflow = StateGraph(RiskAgentState)

        # 1. Add all nodes to graph
        workflow.add_node("parse_input", self._node_parse_input)
        workflow.add_node("industry_research", self._node_industry_research)
        workflow.add_node("market_research", self._node_market_research)
        workflow.add_node("failure_analysis", self._node_failure_analysis)
        workflow.add_node("success_analysis", self._node_success_analysis)
        workflow.add_node("regulatory_research", self._node_regulatory_research)
        workflow.add_node("competitor_research", self._node_competitor_research)
        workflow.add_node("synthesize_research", self._node_synthesize_research)
        workflow.add_node("score_risks", self._node_score_risks)
        workflow.add_node("similarity_analysis", self._node_similarity_analysis)
        workflow.add_node("statistical_analysis", self._node_statistical_analysis)
        workflow.add_node("generate_report", self._node_generate_report)

        # 2. Add edges defining sequential and fan-out/fan-in flow
        workflow.add_edge(START, "parse_input")
        
        # Sequential multi-agent pipeline through specialized research agents
        workflow.add_edge("parse_input", "industry_research")
        workflow.add_edge("industry_research", "market_research")
        workflow.add_edge("market_research", "failure_analysis")
        workflow.add_edge("failure_analysis", "success_analysis")
        workflow.add_edge("success_analysis", "regulatory_research")
        workflow.add_edge("regulatory_research", "competitor_research")
        workflow.add_edge("competitor_research", "synthesize_research")
        
        # Scoring & Reporting stages
        workflow.add_edge("synthesize_research", "score_risks")
        workflow.add_edge("score_risks", "similarity_analysis")
        workflow.add_edge("similarity_analysis", "statistical_analysis")
        workflow.add_edge("statistical_analysis", "generate_report")
        workflow.add_edge("generate_report", END)

        return workflow.compile()

    # --- Node Implementations ---

    async def _node_parse_input(self, state: RiskAgentState) -> Dict[str, Any]:
        analysis_id = state.get("analysis_id", "")
        self._update_status(analysis_id, 10, "Parsing startup problem statement with LLM...")
        try:
            profile = await self.input_parser.parse(state["problem_statement"])
            return {"profile": profile, "current_step": "Input Parsed", "progress": 10}
        except Exception as e:
            print(f"Error in parse_input: {e}")
            profile = StartupProfile()
            return {"profile": profile, "error": str(e)}

    async def _node_industry_research(self, state: RiskAgentState) -> Dict[str, Any]:
        analysis_id = state.get("analysis_id", "")
        self._update_status(analysis_id, 20, "Researching industry dynamics & benchmarks...")
        try:
            data = await self.industry_researcher.research(state["profile"])
            return {"industry_data": data, "current_step": "Industry Researched", "progress": 20}
        except Exception as e:
            print(f"Error in industry_research: {e}")
            return {"industry_data": None}

    async def _node_market_research(self, state: RiskAgentState) -> Dict[str, Any]:
        analysis_id = state.get("analysis_id", "")
        self._update_status(analysis_id, 30, "Analyzing TAM, SAM, SOM and market growth...")
        try:
            data = await self.market_researcher.research(state["profile"])
            return {"market_data": data, "current_step": "Market Researched", "progress": 30}
        except Exception as e:
            print(f"Error in market_research: {e}")
            return {"market_data": None}

    async def _node_failure_analysis(self, state: RiskAgentState) -> Dict[str, Any]:
        analysis_id = state.get("analysis_id", "")
        self._update_status(analysis_id, 45, "Investigating historical startup failures & post-mortems...")
        try:
            failures = await self.failure_analyzer.analyze(state["profile"])
            return {"failures": failures, "current_step": "Failures Analyzed", "progress": 45}
        except Exception as e:
            print(f"Error in failure_analysis: {e}")
            return {"failures": []}

    async def _node_success_analysis(self, state: RiskAgentState) -> Dict[str, Any]:
        analysis_id = state.get("analysis_id", "")
        self._update_status(analysis_id, 55, "Benchmarking against successful startups...")
        try:
            successes = await self.success_analyzer.analyze(state["profile"])
            return {"successes": successes, "current_step": "Successes Benchmarked", "progress": 55}
        except Exception as e:
            print(f"Error in success_analysis: {e}")
            return {"successes": []}

    async def _node_regulatory_research(self, state: RiskAgentState) -> Dict[str, Any]:
        analysis_id = state.get("analysis_id", "")
        self._update_status(analysis_id, 65, "Researching regulatory & compliance barriers...")
        try:
            reg = await self.regulatory_researcher.research(state["profile"])
            return {"regulatory_data": reg, "current_step": "Regulatory Evaluated", "progress": 65}
        except Exception as e:
            print(f"Error in regulatory_research: {e}")
            return {"regulatory_data": None}

    async def _node_competitor_research(self, state: RiskAgentState) -> Dict[str, Any]:
        analysis_id = state.get("analysis_id", "")
        self._update_status(analysis_id, 75, "Profiling competitive landscape & moat risks...")
        try:
            comp = await self.competitor_researcher.research(state["profile"])
            return {"competitor_data": comp, "current_step": "Competitors Analyzed", "progress": 75}
        except Exception as e:
            print(f"Error in competitor_research: {e}")
            return {"competitor_data": None}

    async def _node_synthesize_research(self, state: RiskAgentState) -> Dict[str, Any]:
        analysis_id = state.get("analysis_id", "")
        self._update_status(analysis_id, 80, "Synthesizing research intelligence...")
        results = ResearchResults(
            industry=state.get("industry_data"),
            market=state.get("market_data"),
            failures=state.get("failures", []),
            successes=state.get("successes", []),
            regulatory=state.get("regulatory_data"),
            competitors=state.get("competitor_data")
        )
        return {"research_results": results, "progress": 80}

    async def _node_score_risks(self, state: RiskAgentState) -> Dict[str, Any]:
        analysis_id = state.get("analysis_id", "")
        self._update_status(analysis_id, 85, "Evaluating 12 risk categories & calculating weighted score...")
        try:
            risk_assessment = await self.risk_engine.score_all(
                state["profile"], 
                state["research_results"]
            )
            return {"risk_assessment": risk_assessment, "progress": 85}
        except Exception as e:
            print(f"Error in score_risks: {e}")
            return {"error": str(e)}

    async def _node_similarity_analysis(self, state: RiskAgentState) -> Dict[str, Any]:
        analysis_id = state.get("analysis_id", "")
        self._update_status(analysis_id, 90, "Computing multi-dimensional similarity with historical companies...")
        profile = state.get("profile")
        failures = state.get("failures", [])
        successes = state.get("successes", [])
        
        sim_failures = self.similarity_engine.rank_similar_companies(profile, failures, outcome_filter="FAILED")
        sim_successes = self.similarity_engine.rank_similar_companies(profile, successes, outcome_filter="SUCCEEDED")
        
        return {
            "similar_failures": sim_failures,
            "similar_successes": sim_successes,
            "progress": 90
        }

    async def _node_statistical_analysis(self, state: RiskAgentState) -> Dict[str, Any]:
        analysis_id = state.get("analysis_id", "")
        self._update_status(analysis_id, 93, "Performing statistical failure factor frequency analysis...")
        stats = self.statistical_analyzer.analyze(
            state.get("failures", []),
            state.get("successes", [])
        )
        return {"stats": stats, "progress": 93}

    async def _node_generate_report(self, state: RiskAgentState) -> Dict[str, Any]:
        analysis_id = state.get("analysis_id", "")
        self._update_status(analysis_id, 97, "Compiling final explainable risk assessment memo...")
        try:
            report = self.report_generator.generate(
                profile=state["profile"],
                research=state["research_results"],
                risk=state["risk_assessment"],
                similar_failures=state.get("similar_failures", []),
                similar_successes=state.get("similar_successes", []),
                stats=state.get("stats", {})
            )
            return {"report": report, "progress": 100, "current_step": "Completed"}
        except Exception as e:
            print(f"Error in generate_report: {e}")
            return {"error": str(e)}

    # --- Orchestrator Runner API ---

    async def run(self, problem_statement: str, analysis_id: str):
        self.analyses[analysis_id] = {
            'status': 'processing',
            'progress': 0,
            'current_step': 'Initializing LangGraph...',
            'result': None,
            'error': None
        }

        initial_state: RiskAgentState = {
            "analysis_id": analysis_id,
            "problem_statement": problem_statement,
            "progress": 0,
            "current_step": "Initializing",
            "failures": [],
            "successes": [],
            "similar_failures": [],
            "similar_successes": [],
            "stats": {}
        }

        try:
            # Execute the LangGraph StateGraph
            final_state = await self.graph.ainvoke(initial_state)

            if final_state.get("report"):
                self.analyses[analysis_id]['result'] = final_state["report"]
                self._update_status(analysis_id, 100, 'Complete', status='completed')
            elif final_state.get("error"):
                self.analyses[analysis_id]['status'] = 'error'
                self.analyses[analysis_id]['error'] = final_state["error"]
            else:
                self.analyses[analysis_id]['status'] = 'completed'
                
        except Exception as e:
            self.analyses[analysis_id]['status'] = 'error'
            self.analyses[analysis_id]['error'] = str(e)
            print(f'Error in LangGraph execution {analysis_id}: {traceback.format_exc()}')
            raise

    def _update_status(self, analysis_id: str, progress: int, current_step: str, status: str = 'processing'):
        if analysis_id in self.analyses:
            self.analyses[analysis_id]['progress'] = progress
            self.analyses[analysis_id]['current_step'] = current_step
            self.analyses[analysis_id]['status'] = status

    def get_status(self, analysis_id: str) -> Dict[str, Any]:
        if analysis_id not in self.analyses:
            return {'status': 'not_found', 'progress': 0, 'current_step': '', 'error': 'Analysis not found'}
        analysis = self.analyses[analysis_id]
        return {
            'status': analysis['status'],
            'progress': analysis['progress'],
            'current_step': analysis['current_step'],
            'error': analysis.get('error')
        }

    def get_result(self, analysis_id: str) -> Optional[FullReport]:
        analysis = self.analyses.get(analysis_id)
        if analysis and analysis.get('result'):
            return analysis['result']
        return None
