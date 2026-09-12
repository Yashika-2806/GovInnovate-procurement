"""Minimal FastAPI boundary for the Pitch Evaluator Agent.

Provides HTTP POST /evaluate endpoint for orchestrator integration.
"""

from __future__ import annotations

import os
from typing import Any

from fastapi import FastAPI, HTTPException, status

from pitch_evaluator.models import PitchEvaluation
from pitch_evaluator.service import EvaluatePitchRequest, PitchEvaluator


def create_app(evaluator: PitchEvaluator | None = None) -> FastAPI:
    """Create and configure the FastAPI application.

    Args:
        evaluator: Optional pre-configured PitchEvaluator service.
                   If None, creates one based on environment variables.
    """
    app = FastAPI(
        title="GovInnovate Pitch Evaluator Agent API",
        description="Deterministic multimodal pitch evaluation service for GovInnovate procurement.",
        version="0.1.0",
    )

    # Initialize evaluator: default to mock mode unless explicitly set to LLM
    if evaluator is None:
        engine_type = os.getenv("PITCH_EVALUATOR_ENGINE", "mock")
        evidence_engine_type = os.getenv("PITCH_EVIDENCE_ENGINE", "mock")
        evaluator_instance = PitchEvaluator(
            engine=engine_type,
            evidence_engine=evidence_engine_type,
        )
    else:
        evaluator_instance = evaluator

    # Store in app state
    app.state.evaluator = evaluator_instance

    @app.get("/health", status_code=status.HTTP_200_OK)
    def health() -> dict[str, Any]:
        """Health check endpoint."""
        return {
            "status": "healthy",
            "service": "pitch-evaluator-agent",
            "version": "0.1.0",
            "active_criteria": len(app.state.evaluator.criteria_config.get_enabled_criteria()),
        }

    @app.post(
        "/evaluate",
        response_model=PitchEvaluation,
        status_code=status.HTTP_200_OK,
        summary="Evaluate a pitch",
        description="Accepts an EvaluatePitchRequest and returns a comprehensive PitchEvaluation.",
    )
    def evaluate(request: EvaluatePitchRequest) -> PitchEvaluation:
        """Evaluate pitch endpoint."""
        try:
            eval_service: PitchEvaluator = app.state.evaluator
            result: PitchEvaluation = eval_service.evaluate_pitch(request)
            return result
        except ValueError as err:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(err),
            ) from err
        except FileNotFoundError as err:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(err),
            ) from err
        except Exception as err:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Evaluation failed: {err!s}",
            ) from err

    return app


app = create_app()
