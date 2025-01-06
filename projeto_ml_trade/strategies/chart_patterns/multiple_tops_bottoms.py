"""
Multiple tops and bottoms pattern detection.
"""
import numpy as np
import pandas as pd
from datetime import datetime
from typing import List, Dict, Any

from utils.logging_helper import LoggingHelper
from .base_pattern import BasePattern

class MultipleTopBottom(BasePattern):
    """Base class for multiple tops and bottoms patterns."""
    
    def __init__(self):
        """Initialize pattern detector."""
        super().__init__()
        self.min_points = 4  # Need at least 4 points to form double top/bottom
    
    def _is_valid_level(self, prices: List[float], tolerance: float = 0.01) -> bool:
        """Check if prices form a valid level."""
        if len(prices) < 2:
            return False
        
        # Calculate average price
        avg_price = sum(prices) / len(prices)
        
        # Check if all prices are within tolerance
        return all(abs(p - avg_price) / avg_price <= tolerance for p in prices)

class DoubleTop(MultipleTopBottom):
    """Double top pattern detector."""
    
    def __init__(self):
        """Initialize pattern detector."""
        super().__init__()
        self.pattern_type = 'double_top'
    
    def detect_pattern(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect double top pattern."""
        # Get peaks and troughs
        peaks = self._find_peaks(df['close'])
        troughs = self._find_troughs(df['close'])
        
        # Need at least min_points to form the pattern
        if len(df) < self.min_points:
            return []
        
        pattern_points = []
        
        # Look for potential double tops
        for i in range(len(peaks)-1):
            # Get two peaks
            peak1 = peaks[i]
            peak2 = peaks[i+1]
            
            # Get prices
            peak1_price = df['close'].iloc[peak1]
            peak2_price = df['close'].iloc[peak2]
            
            # Check if peaks form a level
            if self._is_valid_level([peak1_price, peak2_price]):
                # Find trough between peaks
                trough = None
                for t in troughs:
                    if peak1 < t < peak2:
                        trough = t
                        break
                
                if trough is not None:
                    # Add pattern points
                    points = [
                        {
                            'timestamp': df.index[peak1],
                            'price': peak1_price,
                            'type': 'peak',
                            'index': peak1
                        },
                        {
                            'timestamp': df.index[peak2],
                            'price': peak2_price,
                            'type': 'peak',
                            'index': peak2
                        },
                        {
                            'timestamp': df.index[trough],
                            'price': df['close'].iloc[trough],
                            'type': 'trough',
                            'index': trough
                        }
                    ]
                    pattern_points = points
                    break  # Found valid pattern
        
        return pattern_points
    
    def calculate_confidence(self, df: pd.DataFrame, pattern: List[Dict[str, Any]]) -> float:
        """Calculate pattern confidence score."""
        if not pattern:
            return 0.0
        
        # Get pattern points
        peaks = [p for p in pattern if p['type'] == 'peak']
        trough = next(p for p in pattern if p['type'] == 'trough')
        
        if len(peaks) != 2 or not trough:
            return 0.0
        
        # Calculate metrics
        peak1, peak2 = peaks
        
        # Level accuracy
        level_diff = abs(peak1['price'] - peak2['price'])
        avg_level = (peak1['price'] + peak2['price']) / 2
        level_accuracy = 1 - (level_diff / avg_level)
        
        # Pattern depth
        pattern_depth = (peak1['price'] - trough['price']) / peak1['price']
        depth_score = min(pattern_depth / 0.05, 1.0)  # Normalize to 5% depth
        
        # Pattern symmetry
        time_diff = abs(
            (peak2['index'] - trough['index']) -
            (trough['index'] - peak1['index'])
        )
        pattern_duration = peak2['index'] - peak1['index']
        pattern_symmetry = 1 - (time_diff / pattern_duration)
        
        # Volume profile
        volume_trend = self._calculate_volume_trend(
            df,
            peak1['index'],
            peak2['index']
        )
        
        # Combine metrics
        confidence = (
            level_accuracy * 0.3 +
            depth_score * 0.3 +
            pattern_symmetry * 0.2 +
            volume_trend * 0.2
        )
        
        return min(max(confidence, 0.0), 1.0)
    
    def get_pattern_direction(self, pattern: List[Dict[str, Any]]) -> str:
        """Get pattern direction (bullish/bearish)."""
        if not pattern:
            return 'neutral'
        
        # Double top is a bearish reversal pattern
        return 'bearish'

class DoubleBottom(MultipleTopBottom):
    """Double bottom pattern detector."""
    
    def __init__(self):
        """Initialize pattern detector."""
        super().__init__()
        self.pattern_type = 'double_bottom'
    
    def detect_pattern(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect double bottom pattern."""
        # Get peaks and troughs
        peaks = self._find_peaks(df['close'])
        troughs = self._find_troughs(df['close'])
        
        # Need at least min_points to form the pattern
        if len(df) < self.min_points:
            return []
        
        pattern_points = []
        
        # Look for potential double bottoms
        for i in range(len(troughs)-1):
            # Get two troughs
            trough1 = troughs[i]
            trough2 = troughs[i+1]
            
            # Get prices
            trough1_price = df['close'].iloc[trough1]
            trough2_price = df['close'].iloc[trough2]
            
            # Check if troughs form a level
            if self._is_valid_level([trough1_price, trough2_price]):
                # Find peak between troughs
                peak = None
                for p in peaks:
                    if trough1 < p < trough2:
                        peak = p
                        break
                
                if peak is not None:
                    # Add pattern points
                    points = [
                        {
                            'timestamp': df.index[trough1],
                            'price': trough1_price,
                            'type': 'trough',
                            'index': trough1
                        },
                        {
                            'timestamp': df.index[trough2],
                            'price': trough2_price,
                            'type': 'trough',
                            'index': trough2
                        },
                        {
                            'timestamp': df.index[peak],
                            'price': df['close'].iloc[peak],
                            'type': 'peak',
                            'index': peak
                        }
                    ]
                    pattern_points = points
                    break  # Found valid pattern
        
        return pattern_points
    
    def calculate_confidence(self, df: pd.DataFrame, pattern: List[Dict[str, Any]]) -> float:
        """Calculate pattern confidence score."""
        if not pattern:
            return 0.0
        
        # Get pattern points
        troughs = [p for p in pattern if p['type'] == 'trough']
        peak = next(p for p in pattern if p['type'] == 'peak')
        
        if len(troughs) != 2 or not peak:
            return 0.0
        
        # Calculate metrics
        trough1, trough2 = troughs
        
        # Level accuracy
        level_diff = abs(trough1['price'] - trough2['price'])
        avg_level = (trough1['price'] + trough2['price']) / 2
        level_accuracy = 1 - (level_diff / avg_level)
        
        # Pattern height
        pattern_height = (peak['price'] - trough1['price']) / trough1['price']
        height_score = min(pattern_height / 0.05, 1.0)  # Normalize to 5% height
        
        # Pattern symmetry
        time_diff = abs(
            (trough2['index'] - peak['index']) -
            (peak['index'] - trough1['index'])
        )
        pattern_duration = trough2['index'] - trough1['index']
        pattern_symmetry = 1 - (time_diff / pattern_duration)
        
        # Volume profile
        volume_trend = self._calculate_volume_trend(
            df,
            trough1['index'],
            trough2['index']
        )
        
        # Combine metrics
        confidence = (
            level_accuracy * 0.3 +
            height_score * 0.3 +
            pattern_symmetry * 0.2 +
            volume_trend * 0.2
        )
        
        return min(max(confidence, 0.0), 1.0)
    
    def get_pattern_direction(self, pattern: List[Dict[str, Any]]) -> str:
        """Get pattern direction (bullish/bearish)."""
        if not pattern:
            return 'neutral'
        
        # Double bottom is a bullish reversal pattern
        return 'bullish'
