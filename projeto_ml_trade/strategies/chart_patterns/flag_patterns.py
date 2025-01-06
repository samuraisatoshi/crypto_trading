"""
Flag pattern detection.
"""
import numpy as np
import pandas as pd
from datetime import datetime
from typing import List, Dict, Any

from utils.logging_helper import LoggingHelper
from .base_pattern import BasePattern

class FlagPattern(BasePattern):
    """Base class for flag patterns."""
    
    def __init__(self):
        """Initialize pattern detector."""
        super().__init__()
        self.min_points = 4  # Need at least 4 points to form a flag
    
    def _is_valid_flag(self, df: pd.DataFrame, pole_start: int, pole_end: int, flag_points: List[int]) -> bool:
        """Check if points form a valid flag."""
        if len(flag_points) < 2:
            return False
        
        # Get pole trend
        pole_trend = self._calculate_trend(df['close'].iloc[pole_start:pole_end+1])
        
        # Get flag trend
        flag_trend = self._calculate_trend(df['close'].iloc[flag_points])
        
        # Flag should be counter to pole trend
        if pole_trend * flag_trend > 0:  # Same direction
            return False
        
        return True

class BullFlag(FlagPattern):
    """Bull flag pattern detector."""
    
    def __init__(self):
        """Initialize pattern detector."""
        super().__init__()
        self.pattern_type = 'bull_flag'
    
    def detect_pattern(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect bull flag pattern."""
        # Get peaks and troughs
        peaks = self._find_peaks(df['close'])
        troughs = self._find_troughs(df['close'])
        
        # Need at least min_points to form the pattern
        if len(df) < self.min_points:
            return []
        
        pattern_points = []
        
        # Look for strong upward moves (poles)
        for i in range(len(peaks)-1):
            pole_start = troughs[i] if i < len(troughs) else 0
            pole_end = peaks[i]
            
            # Check pole characteristics
            pole_move = df['close'].iloc[pole_end] - df['close'].iloc[pole_start]
            pole_height = pole_move / df['close'].iloc[pole_start]
            
            if pole_height > 0.02:  # Minimum 2% move
                # Look for consolidation after pole
                flag_points = []
                for j in range(pole_end+1, min(pole_end+20, len(df))):
                    if j in peaks or j in troughs:
                        flag_points.append(j)
                
                # Check for valid flag
                if self._is_valid_flag(df, pole_start, pole_end, flag_points):
                    # Add pattern points
                    points = []
                    
                    # Add pole points
                    points.append({
                        'timestamp': df.index[pole_start],
                        'price': df['close'].iloc[pole_start],
                        'type': 'pole_start',
                        'index': pole_start
                    })
                    
                    points.append({
                        'timestamp': df.index[pole_end],
                        'price': df['close'].iloc[pole_end],
                        'type': 'pole_end',
                        'index': pole_end
                    })
                    
                    # Add flag points
                    for point in flag_points:
                        points.append({
                            'timestamp': df.index[point],
                            'price': df['close'].iloc[point],
                            'type': 'flag',
                            'index': point
                        })
                    
                    pattern_points = points
                    break  # Found valid pattern
        
        return pattern_points
    
    def calculate_confidence(self, df: pd.DataFrame, pattern: List[Dict[str, Any]]) -> float:
        """Calculate pattern confidence score."""
        if not pattern:
            return 0.0
        
        # Get pattern points
        pole_start = next(p for p in pattern if p['type'] == 'pole_start')
        pole_end = next(p for p in pattern if p['type'] == 'pole_end')
        flag_points = [p for p in pattern if p['type'] == 'flag']
        
        if not pole_start or not pole_end or len(flag_points) < 2:
            return 0.0
        
        # Calculate metrics
        # Pole strength
        pole_move = pole_end['price'] - pole_start['price']
        pole_height = pole_move / pole_start['price']
        pole_strength = min(pole_height / 0.05, 1.0)  # Normalize to 5% move
        
        # Flag characteristics
        flag_prices = [p['price'] for p in flag_points]
        flag_trend = abs(self._calculate_trend(pd.Series(flag_prices)))
        flag_tightness = 1 - min(flag_trend / 0.01, 1.0)  # Tighter consolidation = higher score
        
        # Volume profile
        volume_trend = self._calculate_volume_trend(
            df,
            pole_start['index'],
            flag_points[-1]['index']
        )
        
        # Combine metrics
        confidence = (
            pole_strength * 0.4 +
            flag_tightness * 0.4 +
            volume_trend * 0.2
        )
        
        return min(max(confidence, 0.0), 1.0)
    
    def get_pattern_direction(self, pattern: List[Dict[str, Any]]) -> str:
        """Get pattern direction (bullish/bearish)."""
        if not pattern:
            return 'neutral'
        
        # Bull flag is a bullish continuation pattern
        return 'bullish'

class BearFlag(FlagPattern):
    """Bear flag pattern detector."""
    
    def __init__(self):
        """Initialize pattern detector."""
        super().__init__()
        self.pattern_type = 'bear_flag'
    
    def detect_pattern(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect bear flag pattern."""
        # Get peaks and troughs
        peaks = self._find_peaks(df['close'])
        troughs = self._find_troughs(df['close'])
        
        # Need at least min_points to form the pattern
        if len(df) < self.min_points:
            return []
        
        pattern_points = []
        
        # Look for strong downward moves (poles)
        for i in range(len(troughs)-1):
            pole_start = peaks[i] if i < len(peaks) else 0
            pole_end = troughs[i]
            
            # Check pole characteristics
            pole_move = df['close'].iloc[pole_end] - df['close'].iloc[pole_start]
            pole_height = abs(pole_move / df['close'].iloc[pole_start])
            
            if pole_height > 0.02:  # Minimum 2% move
                # Look for consolidation after pole
                flag_points = []
                for j in range(pole_end+1, min(pole_end+20, len(df))):
                    if j in peaks or j in troughs:
                        flag_points.append(j)
                
                # Check for valid flag
                if self._is_valid_flag(df, pole_start, pole_end, flag_points):
                    # Add pattern points
                    points = []
                    
                    # Add pole points
                    points.append({
                        'timestamp': df.index[pole_start],
                        'price': df['close'].iloc[pole_start],
                        'type': 'pole_start',
                        'index': pole_start
                    })
                    
                    points.append({
                        'timestamp': df.index[pole_end],
                        'price': df['close'].iloc[pole_end],
                        'type': 'pole_end',
                        'index': pole_end
                    })
                    
                    # Add flag points
                    for point in flag_points:
                        points.append({
                            'timestamp': df.index[point],
                            'price': df['close'].iloc[point],
                            'type': 'flag',
                            'index': point
                        })
                    
                    pattern_points = points
                    break  # Found valid pattern
        
        return pattern_points
    
    def calculate_confidence(self, df: pd.DataFrame, pattern: List[Dict[str, Any]]) -> float:
        """Calculate pattern confidence score."""
        if not pattern:
            return 0.0
        
        # Get pattern points
        pole_start = next(p for p in pattern if p['type'] == 'pole_start')
        pole_end = next(p for p in pattern if p['type'] == 'pole_end')
        flag_points = [p for p in pattern if p['type'] == 'flag']
        
        if not pole_start or not pole_end or len(flag_points) < 2:
            return 0.0
        
        # Calculate metrics
        # Pole strength
        pole_move = pole_start['price'] - pole_end['price']
        pole_height = pole_move / pole_start['price']
        pole_strength = min(pole_height / 0.05, 1.0)  # Normalize to 5% move
        
        # Flag characteristics
        flag_prices = [p['price'] for p in flag_points]
        flag_trend = abs(self._calculate_trend(pd.Series(flag_prices)))
        flag_tightness = 1 - min(flag_trend / 0.01, 1.0)  # Tighter consolidation = higher score
        
        # Volume profile
        volume_trend = self._calculate_volume_trend(
            df,
            pole_start['index'],
            flag_points[-1]['index']
        )
        
        # Combine metrics
        confidence = (
            pole_strength * 0.4 +
            flag_tightness * 0.4 +
            volume_trend * 0.2
        )
        
        return min(max(confidence, 0.0), 1.0)
    
    def get_pattern_direction(self, pattern: List[Dict[str, Any]]) -> str:
        """Get pattern direction (bullish/bearish)."""
        if not pattern:
            return 'neutral'
        
        # Bear flag is a bearish continuation pattern
        return 'bearish'
