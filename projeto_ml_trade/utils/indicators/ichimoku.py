"""
Ichimoku Cloud indicator calculations.
"""
import pandas as pd
from typing import Dict
from .base import validate_data, IndicatorError

@validate_data
def calculate_ichimoku(high: pd.Series,
                      low: pd.Series,
                      close: pd.Series,
                      conversion_period: int = 9,
                      base_period: int = 26,
                      span_b_period: int = 52,
                      displacement: int = 26) -> Dict[str, pd.Series]:
    """Calculate Ichimoku Cloud components.
    
    Args:
        high: High prices
        low: Low prices
        close: Close prices
        conversion_period: Tenkan-sen period (default: 9)
        base_period: Kijun-sen period (default: 26)
        span_b_period: Senkou Span B period (default: 52)
        displacement: Displacement period (default: 26)
        
    Returns:
        Dictionary containing Ichimoku components
    """
    if any(p <= 0 for p in [conversion_period, base_period, span_b_period, displacement]):
        raise IndicatorError("All periods must be positive")
    
    # Calculate Tenkan-sen (Conversion Line)
    tenkan_sen = (high.rolling(window=conversion_period).max() + 
                 low.rolling(window=conversion_period).min()) / 2
    
    # Calculate Kijun-sen (Base Line)
    kijun_sen = (high.rolling(window=base_period).max() + 
                low.rolling(window=base_period).min()) / 2
    
    # Calculate Senkou Span A (Leading Span A)
    span_a = ((tenkan_sen + kijun_sen) / 2).shift(displacement)
    
    # Calculate Senkou Span B (Leading Span B)
    span_b = ((high.rolling(window=span_b_period).max() + 
              low.rolling(window=span_b_period).min()) / 2).shift(displacement)
    
    # Calculate Chikou Span (Lagging Span)
    chikou_span = close.shift(-displacement)
    
    return {
        'tenkan_sen': tenkan_sen,
        'kijun_sen': kijun_sen,
        'senkou_span_a': span_a,
        'senkou_span_b': span_b,
        'chikou_span': chikou_span
    }
