"""
Pattern-based trading strategy.
"""
from typing import Dict, List, Tuple, Any
import pandas as pd
import numpy as np

from .base import BaseStrategy
from .pattern_orchestrator import PatternOrchestrator

class PatternStrategy(BaseStrategy):
    """Strategy based on chart patterns."""
    
    def __init__(self, min_confidence: float = 0.7):
        """Initialize strategy."""
        super().__init__()
        self.min_confidence = min_confidence
        self.orchestrator = PatternOrchestrator()
        self.current_patterns = []
    
    def generate_signals(self, df: pd.DataFrame) -> List[Dict]:
        """Generate trading signals."""
        try:
            # Get current index
            current_idx = len(df) - 1
            
            # Analyze current state
            signals, patterns = self.analyze(df, current_idx)
            
            return signals
            
        except Exception as e:
            print(f"Error generating signals: {str(e)}")
            return []
    
    def analyze(self, df: pd.DataFrame, current_idx: int) -> Tuple[List[Dict], List[Dict]]:
        """Analyze current market state."""
        try:
            # Get window of data
            window_size = 100  # Fixed window for pattern detection
            start_idx = max(0, current_idx - window_size)
            window = df.iloc[start_idx:current_idx + 1].copy()
            
            # Detect patterns
            patterns = self.orchestrator.detect_patterns(window)
            
            # Filter patterns by confidence
            patterns = [p for p in patterns if p.get('confidence', 0) >= self.min_confidence]
            
            # Adjust pattern indices to full dataframe
            for pattern in patterns:
                # Adjust peaks
                if 'peaks' in pattern:
                    pattern['peaks'] = [(idx + start_idx, price) 
                                      for idx, price in pattern['peaks']]
                
                # Adjust troughs
                if 'troughs' in pattern:
                    pattern['troughs'] = [(idx + start_idx, price) 
                                        for idx, price in pattern['troughs']]
                
                # Adjust pattern range
                if 'start_idx' in pattern:
                    pattern['start_idx'] += start_idx
                if 'end_idx' in pattern:
                    pattern['end_idx'] += start_idx
            
            # Store current patterns
            self.current_patterns = patterns
            
            # Generate signals
            signals = []
            for pattern in patterns:
                pattern_type = pattern['type']
                confidence = pattern.get('confidence', 0)
                
                # Generate signal based on pattern type
                if pattern_type == 'falling_wedge':
                    signals.append({
                        'type': 'long',
                        'confidence': confidence,
                        'price': window['close'].iloc[-1],
                        'pattern': pattern_type
                    })
                elif pattern_type == 'rising_wedge':
                    signals.append({
                        'type': 'short',
                        'confidence': confidence,
                        'price': window['close'].iloc[-1],
                        'pattern': pattern_type
                    })
            
            return signals, patterns
            
        except Exception as e:
            print(f"Error in pattern analysis: {str(e)}")
            return [], []
    
    def should_exit(self, df: pd.DataFrame, current_idx: int, position: Dict) -> bool:
        """Determine if position should be exited."""
        try:
            # Get current price
            current_price = df['close'].iloc[current_idx]
            entry_price = position['entry_price']
            
            # Exit conditions based on position type
            if position['type'] == 'long':
                # Take profit at 3% gain
                if current_price >= entry_price * 1.03:
                    return True
                # Stop loss at 2% loss
                if current_price <= entry_price * 0.98:
                    return True
                    
            else:  # short position
                # Take profit at 3% drop
                if current_price <= entry_price * 0.97:
                    return True
                # Stop loss at 2% rise
                if current_price >= entry_price * 1.02:
                    return True
            
            return False
            
        except Exception as e:
            print(f"Error in exit check: {str(e)}")
            return False
