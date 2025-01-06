"""
Wedge pattern detection.
"""
import numpy as np
import pandas as pd
from datetime import datetime
from typing import List, Dict, Any

from utils.logging_helper import LoggingHelper
from .base_pattern import BasePattern

class WedgePattern(BasePattern):
    """Base class for wedge patterns."""
    
    def __init__(self):
        """Initialize pattern detector."""
        super().__init__()
        self.min_points = 5  # Need at least 5 points to form a wedge
    
    def _is_valid_wedge(self, df: pd.DataFrame, peaks: List[int], troughs: List[int]) -> bool:
        """Check if points form a valid wedge."""
        if len(peaks) < 2 or len(troughs) < 2:
            return False
        
        # Get trend lines
        upper_line = self._get_trend_line(df, peaks)
        lower_line = self._get_trend_line(df, troughs)
        
        # Lines should converge
        if upper_line['slope'] * lower_line['slope'] <= 0:  # Different directions
            return False
        
        return True
    
    def _get_trend_line(self, df: pd.DataFrame, points: List[int]) -> Dict[str, float]:
        """Calculate trend line parameters."""
        if len(points) < 2:
            return {'slope': 0, 'intercept': 0}
        
        x = np.array(points)
        y = df['close'].iloc[points].values
        
        slope, intercept = np.polyfit(x, y, 1)
        return {'slope': slope, 'intercept': intercept}

class RisingWedge(WedgePattern):
    """Rising wedge pattern detector."""
    
    def __init__(self):
        """Initialize pattern detector."""
        super().__init__()
        self.pattern_type = 'rising_wedge'
    
    def detect_pattern(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect rising wedge pattern."""
        # Get peaks and troughs
        peaks = self._find_peaks(df['close'])
        troughs = self._find_troughs(df['close'])
        
        # Need at least min_points to form the pattern
        if len(df) < self.min_points:
            return []
        
        pattern_points = []
        
        # Check for valid wedge
        if self._is_valid_wedge(df, peaks, troughs):
            # Get trend lines
            upper_line = self._get_trend_line(df, peaks)
            lower_line = self._get_trend_line(df, troughs)
            
            # Check for rising wedge (both lines rising, upper line less steep)
            if upper_line['slope'] > 0 and lower_line['slope'] > 0 and upper_line['slope'] < lower_line['slope']:
                # Add peak points
                for peak in peaks:
                    pattern_points.append({
                        'timestamp': df.index[peak],
                        'price': df['close'].iloc[peak],
                        'type': 'peak',
                        'index': peak
                    })
                
                # Add trough points
                for trough in troughs:
                    pattern_points.append({
                        'timestamp': df.index[trough],
                        'price': df['close'].iloc[trough],
                        'type': 'trough',
                        'index': trough
                    })
                
                # Sort points by time
                pattern_points.sort(key=lambda x: x['index'])
        
        return pattern_points
    
    def calculate_confidence(self, df: pd.DataFrame, pattern: List[Dict[str, Any]]) -> float:
        """Calculate pattern confidence score."""
        if not pattern:
            return 0.0
        
        # Get pattern points
        peaks = [p for p in pattern if p['type'] == 'peak']
        troughs = [p for p in pattern if p['type'] == 'trough']
        
        if len(peaks) < 2 or len(troughs) < 2:
            return 0.0
        
        # Calculate metrics
        # Get trend lines
        peak_indices = [p['index'] for p in peaks]
        trough_indices = [p['index'] for p in troughs]
        
        upper_line = self._get_trend_line(df, peak_indices)
        lower_line = self._get_trend_line(df, trough_indices)
        
        # Slope convergence
        slope_diff = abs(upper_line['slope'] - lower_line['slope'])
        convergence = min(slope_diff / 0.015, 1.0)  # Increased slope difference threshold
        
        # Pattern height
        pattern_height = (peaks[-1]['price'] - troughs[0]['price']) / troughs[0]['price']
        height_score = min(pattern_height / 0.08, 1.0)  # Increased height threshold
        
        # Volume profile
        volume_trend = self._calculate_volume_trend(
            df,
            min(peak_indices + trough_indices),
            max(peak_indices + trough_indices)
        )
        
        # Combine metrics
        confidence = (
            convergence * 0.4 +
            height_score * 0.4 +
            volume_trend * 0.2
        )
        
        return min(max(confidence, 0.0), 1.0)
    
    def get_pattern_direction(self, pattern: List[Dict[str, Any]]) -> str:
        """Get pattern direction (bullish/bearish)."""
        if not pattern:
            return 'neutral'
        
        # Rising wedge is a bearish reversal pattern
        return 'bearish'

class FallingWedge(WedgePattern):
    """Falling wedge pattern detector."""
    
    def __init__(self):
        """Initialize pattern detector."""
        super().__init__()
        self.pattern_type = 'falling_wedge'
    
    def detect_pattern(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect falling wedge pattern."""
        # Get peaks and troughs
        peaks = self._find_peaks(df['close'])
        troughs = self._find_troughs(df['close'])
        
        # Need at least min_points to form the pattern
        if len(df) < self.min_points:
            return []
        
        pattern_points = []
        
        # Check for valid wedge
        if self._is_valid_wedge(df, peaks, troughs):
            # Get trend lines
            upper_line = self._get_trend_line(df, peaks)
            lower_line = self._get_trend_line(df, troughs)
            
            # Check for falling wedge (both lines falling, lower line less steep)
            if upper_line['slope'] < 0 and lower_line['slope'] < 0 and upper_line['slope'] < lower_line['slope']:
                # Add peak points
                for peak in peaks:
                    pattern_points.append({
                        'timestamp': df.index[peak],
                        'price': df['close'].iloc[peak],
                        'type': 'peak',
                        'index': peak
                    })
                
                # Add trough points
                for trough in troughs:
                    pattern_points.append({
                        'timestamp': df.index[trough],
                        'price': df['close'].iloc[trough],
                        'type': 'trough',
                        'index': trough
                    })
                
                # Sort points by time
                pattern_points.sort(key=lambda x: x['index'])
        
        return pattern_points
    
    def calculate_confidence(self, df: pd.DataFrame, pattern: List[Dict[str, Any]]) -> float:
        """Calculate pattern confidence score."""
        if not pattern:
            return 0.0
        
        # Get pattern points
        peaks = [p for p in pattern if p['type'] == 'peak']
        troughs = [p for p in pattern if p['type'] == 'trough']
        
        if len(peaks) < 2 or len(troughs) < 2:
            return 0.0
        
        # Calculate metrics
        # Get trend lines
        peak_indices = [p['index'] for p in peaks]
        trough_indices = [p['index'] for p in troughs]
        
        upper_line = self._get_trend_line(df, peak_indices)
        lower_line = self._get_trend_line(df, trough_indices)
        
        # Slope convergence
        slope_diff = abs(upper_line['slope'] - lower_line['slope'])
        convergence = min(slope_diff / 0.015, 1.0)  # Increased slope difference threshold
        
        # Pattern height
        pattern_height = abs(peaks[0]['price'] - troughs[-1]['price']) / peaks[0]['price']
        height_score = min(pattern_height / 0.08, 1.0)  # Increased height threshold
        
        # Volume profile
        volume_trend = self._calculate_volume_trend(
            df,
            min(peak_indices + trough_indices),
            max(peak_indices + trough_indices)
        )
        
        # Combine metrics
        confidence = (
            convergence * 0.4 +
            height_score * 0.4 +
            volume_trend * 0.2
        )
        
        return min(max(confidence, 0.0), 1.0)
    
    def get_pattern_direction(self, pattern: List[Dict[str, Any]]) -> str:
        """Get pattern direction (bullish/bearish)."""
        if not pattern:
            return 'neutral'
        
        # Falling wedge is a bullish reversal pattern
        return 'bullish'
