"""
Base classes and utilities for indicators.
"""
import pandas as pd
from typing import Optional
from dataclasses import dataclass
from enum import Enum

class TrendDirection(Enum):
    UP = "up"
    DOWN = "down"
    SIDEWAYS = "sideways"

@dataclass
class PatternResult:
    """Container for pattern detection results."""
    pattern_type: str
    direction: Optional[str]
    strength: float  # 0.0 to 1.0
    description: str

class IndicatorError(Exception):
    """Custom exception for indicator calculation errors."""
    pass

def validate_data(func):
    """Decorator to validate input data for indicators."""
    def wrapper(*args, **kwargs):
        processed_args = []
        for arg in args:
            if isinstance(arg, pd.Series):
                if arg.empty:
                    raise IndicatorError("Empty data series provided")
                # Fill NaN values with forward fill, then backward fill
                processed_arg = arg.ffill().bfill()
                processed_args.append(processed_arg)
            else:
                processed_args.append(arg)
        return func(*processed_args, **kwargs)
    return wrapper
