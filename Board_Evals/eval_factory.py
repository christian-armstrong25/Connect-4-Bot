#!/usr/bin/env python3
"""Factory for creating different board evaluators."""

from .eval_old import BoardEvaluator as OldEvaluator
from .eval_new import BoardEvaluator as NewEvaluator


def create_evaluator(evaluator_type: str):
    """Create an evaluator based on the type string."""
    if evaluator_type == "old":
        return OldEvaluator()
    elif evaluator_type == "new":
        return NewEvaluator()
    else:
        raise ValueError(f"Unknown evaluator type: {evaluator_type}")
