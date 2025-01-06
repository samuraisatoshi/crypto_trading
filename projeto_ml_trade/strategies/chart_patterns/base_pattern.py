"""
Base class for chart pattern detection.
"""
import numpy as np
import pandas as pd
from typing import List, Dict, Any
from abc import ABC, abstractmethod

from utils.logging_helper import LoggingHelper

class BasePattern(ABC):
    """Base class for all chart patterns."""
    
    def __init__(self):
        """Initialize pattern detector."""
        self.pattern_type = 'base'
        self.min_points = 2
    
    def find_patterns(self, df: pd.DataFrame, confidence_threshold: float = 0.7) -> List[Dict[str, Any]]:
        """Find patterns in the data."""
        patterns = []
        
        # Need at least min_points to form the pattern
        if len(df) < self.min_points:
            return patterns
        
        # Detect pattern
        pattern = self.detect_pattern(df)
        if pattern:
            # Calculate confidence
            confidence = self.calculate_confidence(df, pattern)
            
            if confidence >= confidence_threshold:
                # Get pattern direction
                direction = self.get_pattern_direction(pattern)
                
                # Get pattern points
                points = pattern if isinstance(pattern, list) else [pattern]
                
                # Get pattern range
                timestamps = [p['timestamp'] for p in points]
                prices = [p['price'] for p in points]
                
                # Create pattern entry
                pattern_entry = {
                    'type': self.pattern_type,
                    'points': points,
                    'confidence': confidence,
                    'direction': direction,
                    'timestamp': max(timestamps),
                    'price': prices[-1],
                    'start_time': min(timestamps),
                    'end_time': max(timestamps),
                    'high_price': max(prices),
                    'low_price': min(prices)
                }
                
                LoggingHelper.debug(
                    f"Pattern entry created - Type: {self.pattern_type}, "
                    f"Direction: {direction}, Confidence: {confidence:.2f}"
                )
                
                patterns.append(pattern_entry)
                LoggingHelper.log(f"Found {self.pattern_type} pattern with confidence {confidence:.2f}")
        
        return patterns
    
    def _find_peaks(self, series: pd.Series, order: int = 5, min_height: float = 0.015) -> List[int]:
        """Find peaks in a series.
        
        Args:
            series: Price series
            order: Window size for peak detection
            min_height: Minimum relative height difference for a peak
        """
        peaks = []
        for i in range(order, len(series) - order):
            window = series.iloc[i-order:i+order+1]
            center_val = series.iloc[i]
            
            # Check if it's a local maximum
            if center_val == max(window):
                # Calculate relative height from surrounding valleys
                left_min = min(series.iloc[i-order:i])
                right_min = min(series.iloc[i+1:i+order+1])
                rel_height = min(
                    (center_val - left_min) / left_min,
                    (center_val - right_min) / right_min
                )
                
                if rel_height >= min_height:
                    peaks.append(i)
        
        LoggingHelper.log(f"Found {len(peaks)} peaks in series of length {len(series)}")
        return peaks
    
    def _find_troughs(self, series: pd.Series, order: int = 5, min_depth: float = 0.015) -> List[int]:
        """Find troughs in a series.
        
        Args:
            series: Price series
            order: Window size for trough detection
            min_depth: Minimum relative depth difference for a trough
        """
        troughs = []
        for i in range(order, len(series) - order):
            window = series.iloc[i-order:i+order+1]
            center_val = series.iloc[i]
            
            # Check if it's a local minimum
            if center_val == min(window):
                # Calculate relative depth from surrounding peaks
                left_max = max(series.iloc[i-order:i])
                right_max = max(series.iloc[i+1:i+order+1])
                rel_depth = min(
                    (left_max - center_val) / center_val,
                    (right_max - center_val) / center_val
                )
                
                if rel_depth >= min_depth:
                    troughs.append(i)
        
        LoggingHelper.log(f"Found {len(troughs)} troughs in series of length {len(series)}")
        return troughs
    
    def _calculate_trend(self, prices: pd.Series) -> float:
        """Calculate trend strength."""
        if len(prices) < 2:
            return 0.0
        
        x = np.arange(len(prices))
        y = prices.values
        
        # Calculate linear regression
        slope, _ = np.polyfit(x, y, 1)
        
        return slope
    
    def _calculate_volume_trend(self, df: pd.DataFrame, start_idx: int, end_idx: int) -> float:
        """Calculate volume trend confidence."""
        volumes = df['volume'].iloc[start_idx:end_idx + 1]
        
        if len(volumes) < 2:
            return 0.0
        
        # Calculate volume trend using linear regression
        x = np.arange(len(volumes))
        y = volumes.values
        slope, _ = np.polyfit(x, y, 1)
        
        # Normalize slope by average volume
        avg_volume = volumes.mean()
        if avg_volume == 0:
            return 0.0
        
        norm_slope = slope / avg_volume
        
        # Convert to [0, 1] range
        return min(max(norm_slope, 0.0), 1.0)
    
    @abstractmethod
    def detect_pattern(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect pattern in the data."""
        pass
    
    @abstractmethod
    def calculate_confidence(self, df: pd.DataFrame, pattern: List[Dict[str, Any]]) -> float:
        """Calculate pattern confidence score."""
        pass
    
    @abstractmethod
    def get_pattern_direction(self, pattern: List[Dict[str, Any]]) -> str:
        """Get pattern direction (bullish/bearish)."""
        pass
