"""
Technical analysis indicators package.
"""
from .base import TrendDirection, PatternResult, IndicatorError, validate_data
from .moving_averages import (
    calculate_sma, calculate_ema, calculate_slope,
    calculate_macd, calculate_macd_divergence
)
from .oscillators import (
    calculate_rsi, calculate_stochastic, calculate_obv,
    calculate_adx
)
from .volatility import (
    calculate_bollinger_bands, calculate_atr
)
from .ichimoku import calculate_ichimoku
from .dataset import (
    add_indicators_and_oscillators,
    add_advanced_indicators
)

__all__ = [
    # Base
    'TrendDirection',
    'PatternResult',
    'IndicatorError',
    'validate_data',
    
    # Moving Averages
    'calculate_sma',
    'calculate_ema',
    'calculate_slope',
    'calculate_macd',
    'calculate_macd_divergence',
    
    # Oscillators
    'calculate_rsi',
    'calculate_stochastic',
    'calculate_obv',
    'calculate_adx',
    
    # Volatility
    'calculate_bollinger_bands',
    'calculate_atr',
    
    # Ichimoku
    'calculate_ichimoku',
    
    # Dataset-level functions
    'add_indicators_and_oscillators',
    'add_advanced_indicators'
]
