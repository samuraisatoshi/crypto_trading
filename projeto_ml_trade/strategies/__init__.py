"""
Trading strategies package.
"""
from .base import BaseStrategy
from .candle_patterns import CandlePatternStrategy
from .double_bottom_rsi_strategy import DoubleBottomRSIStrategy
from .ema_trend_strategy import EMATrendStrategy
from .macd_strategy import MACDStrategy
from .moving_averages import MovingAveragesStrategy
from .obv_strategy import OBVStrategy
from .orchestrated_pattern_strategy import OrchestratedPatternStrategy
from .pattern_strategy import PatternStrategy
from .pattern_orchestrator import PatternOrchestrator
from .rsi_strategy import RSIStrategy
from .trend_analysis import TrendAnalysisStrategy
from .volatility_strategy import VolatilityStrategy

# Chart patterns
from .chart_patterns import (
    BasePattern,
    FlagPattern,
    HeadAndShouldersPattern,
    MultipleTopBottom,
    TrianglePattern,
    WedgePattern
)

__all__ = [
    # Base classes
    'BaseStrategy',
    'BasePattern',
    
    # Core strategies
    'CandlePatternStrategy',
    'DoubleBottomRSIStrategy',
    'EMATrendStrategy',
    'MACDStrategy',
    'MovingAveragesStrategy',
    'OBVStrategy',
    'OrchestratedPatternStrategy',
    'PatternStrategy',
    'PatternOrchestrator',
    'RSIStrategy',
    'TrendAnalysisStrategy',
    'VolatilityStrategy',
    
    # Chart patterns
    'FlagPattern',
    'HeadAndShouldersPattern',
    'MultipleTopBottom',
    'TrianglePattern',
    'WedgePattern'
]
