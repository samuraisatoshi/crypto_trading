"""
Head and shoulders pattern detection.
"""
import numpy as np
import pandas as pd
from datetime import datetime
from typing import List, Dict, Any

from utils.logging_helper import LoggingHelper
from .base_pattern import BasePattern

class HeadAndShouldersPattern(BasePattern):
    """Head and shoulders pattern detector."""
    
    def __init__(self):
        """Initialize pattern detector."""
        super().__init__()
        self.pattern_type = 'head_and_shoulders'
        self.min_points = 5  # Left shoulder, head, right shoulder, two neckline points
    
    def detect_pattern(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect head and shoulders pattern."""
        # Get peaks and troughs
        peaks = self._find_peaks(df['close'])
        troughs = self._find_troughs(df['close'])
        
        # Need at least 3 peaks (shoulders and head) and 2 troughs
        if len(peaks) < 3 or len(troughs) < 2:
            return []
        
        pattern_points = []
        
        # Look for pattern formations
        for i in range(len(peaks) - 2):
            # Get potential pattern points
            left_shoulder = peaks[i]
            head = peaks[i + 1]
            right_shoulder = peaks[i + 2]
            
            # Check if it forms a valid head and shoulders pattern
            if self._is_valid_pattern(df, left_shoulder, head, right_shoulder):
                # Find neckline points
                left_trough = None
                right_trough = None
                
                # Find trough between left shoulder and head
                for t in troughs:
                    if left_shoulder < t < head:
                        left_trough = t
                        break
                
                # Find trough between head and right shoulder
                for t in troughs:
                    if head < t < right_shoulder:
                        right_trough = t
                        break
                
                if left_trough is not None and right_trough is not None:
                    # Add pattern points
                    pattern_points = [
                        {
                            'timestamp': df.index[left_shoulder],
                            'price': df['close'].iloc[left_shoulder],
                            'type': 'shoulder',
                            'index': left_shoulder
                        },
                        {
                            'timestamp': df.index[head],
                            'price': df['close'].iloc[head],
                            'type': 'head',
                            'index': head
                        },
                        {
                            'timestamp': df.index[right_shoulder],
                            'price': df['close'].iloc[right_shoulder],
                            'type': 'shoulder',
                            'index': right_shoulder
                        },
                        {
                            'timestamp': df.index[left_trough],
                            'price': df['close'].iloc[left_trough],
                            'type': 'neckline',
                            'index': left_trough
                        },
                        {
                            'timestamp': df.index[right_trough],
                            'price': df['close'].iloc[right_trough],
                            'type': 'neckline',
                            'index': right_trough
                        }
                    ]
                    break  # Found valid pattern
        
        return pattern_points
    
    def calculate_confidence(self, df: pd.DataFrame, pattern: List[Dict[str, Any]]) -> float:
        """Calculate pattern confidence score."""
        if not pattern:
            return 0.0
        
        # Get pattern points
        shoulders = [p for p in pattern if p['type'] == 'shoulder']
        head = next(p for p in pattern if p['type'] == 'head')
        neckline = [p for p in pattern if p['type'] == 'neckline']
        
        if len(shoulders) != 2 or not head or len(neckline) != 2:
            return 0.0
        
        # Calculate metrics
        left_shoulder, right_shoulder = shoulders
        left_trough, right_trough = neckline
        
        # Shoulder symmetry (height and time)
        shoulder_height_diff = abs(left_shoulder['price'] - right_shoulder['price'])
        avg_shoulder_height = (left_shoulder['price'] + right_shoulder['price']) / 2
        shoulder_symmetry = 1 - (shoulder_height_diff / avg_shoulder_height)
        
        # Use index positions for time calculations
        shoulder_time_diff = abs(
            (head['index'] - left_shoulder['index']) -
            (right_shoulder['index'] - head['index'])
        )
        pattern_duration = right_shoulder['index'] - left_shoulder['index']
        time_symmetry = 1 - (shoulder_time_diff / pattern_duration)
        
        # Head prominence
        head_height = head['price'] - max(left_shoulder['price'], right_shoulder['price'])
        head_prominence = head_height / avg_shoulder_height
        
        # Neckline slope
        neckline_slope = abs(
            (right_trough['price'] - left_trough['price']) /
            (right_trough['index'] - left_trough['index'])
        )
        neckline_flatness = 1 - min(neckline_slope * 10, 1.0)  # Normalize slope
        
        # Volume profile
        volume_trend = self._calculate_volume_trend(
            df,
            left_shoulder['index'],
            right_shoulder['index']
        )
        
        # Combine metrics
        confidence = (
            shoulder_symmetry * 0.3 +
            time_symmetry * 0.2 +
            head_prominence * 0.2 +
            neckline_flatness * 0.2 +
            volume_trend * 0.1
        )
        
        return min(max(confidence, 0.0), 1.0)
    
    def get_pattern_direction(self, pattern: List[Dict[str, Any]]) -> str:
        """Get pattern direction (bullish/bearish)."""
        if not pattern:
            return 'neutral'
        
        # Head and shoulders is a bearish reversal pattern
        return 'bearish'
    
    def _is_valid_pattern(self, df: pd.DataFrame, left_shoulder: int, head: int, right_shoulder: int) -> bool:
        """Check if points form a valid head and shoulders pattern."""
        # Get prices
        left_price = df['close'].iloc[left_shoulder]
        head_price = df['close'].iloc[head]
        right_price = df['close'].iloc[right_shoulder]
        
        # Head should be higher than shoulders
        if not (head_price > left_price and head_price > right_price):
            return False
        
        # Shoulders should be at similar levels
        shoulder_diff = abs(left_price - right_price)
        avg_shoulder_price = (left_price + right_price) / 2
        if shoulder_diff > avg_shoulder_price * 0.1:  # 10% tolerance
            return False
        
        # Points should be in chronological order
        if not (left_shoulder < head < right_shoulder):
            return False
        
        return True
