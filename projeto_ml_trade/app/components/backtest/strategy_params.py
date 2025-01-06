"""
Strategy parameters component.
"""
import streamlit as st
from typing import Dict, Any, Optional
from app.components.base import UIComponent

def get_strategy_params(strategy_id: str) -> Optional[Dict[str, Any]]:
    """
    Get strategy parameters from UI.
    
    Args:
        strategy_id: Strategy identifier
        
    Returns:
        Dictionary of strategy parameters
    """
    params = StrategyParams()
    return params.render(strategy_id)

class StrategyParams(UIComponent):
    """Component for managing strategy parameters."""
    
    def __init__(self):
        """Initialize strategy parameters component."""
        super().__init__()
    
    def render(self, strategy_id: str) -> Optional[Dict[str, Any]]:
        """
        Render strategy parameters UI.
        
        Args:
            strategy_id: Strategy identifier
            
        Returns:
            Dictionary of strategy parameters
        """
        if strategy_id == 'patterns':
            return self._render_pattern_params()
        elif strategy_id == 'ema_trend':
            return self._render_ema_trend_params()
        return None
    
    def _render_pattern_params(self) -> Dict[str, Any]:
        """Render pattern strategy parameters."""
        return {
            'pattern_types': st.multiselect(
                "Pattern Types",
                options=[
                    'Double Bottom',
                    'Double Top',
                    'Head and Shoulders',
                    'Inverse Head and Shoulders',
                    'Triple Bottom',
                    'Triple Top'
                ],
                default=['Double Bottom', 'Double Top']
            )
        }
    
    def _render_ema_trend_params(self) -> Dict[str, Any]:
        """Render EMA trend strategy parameters."""
        col1, col2 = st.columns(2)
        
        with col1:
            ema21_period = st.number_input("EMA21 Period", value=21, min_value=1)
            ema55_period = st.number_input("EMA55 Period", value=55, min_value=1)
            ema80_period = st.number_input("EMA80 Period", value=80, min_value=1)
            ema100_period = st.number_input("EMA100 Period", value=100, min_value=1)
        
        with col2:
            slope_window = st.number_input("Slope Window", value=10, min_value=2)
            confidence_threshold = st.slider(
                "Confidence Threshold",
                min_value=0.1,
                max_value=1.0,
                value=0.5,
                step=0.1
            )
            percentile_window = st.number_input("Percentile Window", value=100, min_value=10)
        
        return {
            'ema21_period': ema21_period,
            'ema55_period': ema55_period,
            'ema80_period': ema80_period,
            'ema100_period': ema100_period,
            'slope_window': slope_window,
            'confidence_threshold': confidence_threshold,
            'percentile_window': percentile_window
        }
