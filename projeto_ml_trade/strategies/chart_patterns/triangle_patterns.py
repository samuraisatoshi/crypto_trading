"""
Triangle pattern detection.
"""
import numpy as np
import pandas as pd
from datetime import datetime
from typing import List, Dict, Any, Tuple

from utils.logging_helper import LoggingHelper
from .base_pattern import BasePattern

class TrianglePattern(BasePattern):
    """Base class for triangle patterns."""
    
    def __init__(self):
        """Initialize pattern detector."""
        super().__init__()
        self.min_points = 5  # Need at least 5 points to form a triangle
    
    def _is_valid_triangle(self, df: pd.DataFrame, peaks: List[int], troughs: List[int]) -> Tuple[bool, Dict[str, float], Dict[str, float]]:
        """Check if points form a valid triangle."""
        if len(peaks) < 2 or len(troughs) < 2:
            LoggingHelper.debug(f"Not enough points for triangle: peaks={len(peaks)}, troughs={len(troughs)}")
            return False, None, None
        
        # Sort points by time
        peaks = sorted(peaks)
        troughs = sorted(troughs)
        
        # Get trend lines using most recent points
        upper_line = self._get_trend_line(df, peaks[-3:])  # Use last 3 peaks
        lower_line = self._get_trend_line(df, troughs[-3:])  # Use last 3 troughs
        
        LoggingHelper.debug(f"Trend lines - Upper: slope={upper_line['slope']:.4f}, Lower: slope={lower_line['slope']:.4f}")
        
        # Get pattern-specific price range
        pattern_points = sorted(peaks[-3:] + troughs[-3:])
        pattern_prices = df['close'].iloc[pattern_points]
        price_range = pattern_prices.max() - pattern_prices.min()
        if price_range == 0:
            return False, None, None
        
        # Calculate normalized slopes
        scale_factor = np.sqrt(len(df))  # Use square root to make slopes more reasonable
        norm_upper_slope = upper_line['slope'] / (price_range * scale_factor)
        norm_lower_slope = lower_line['slope'] / (price_range * scale_factor)
        
        LoggingHelper.debug(f"Normalized slopes - Upper: {norm_upper_slope:.4f}, Lower: {norm_lower_slope:.4f}")
        
        # Check if both trend lines are too flat
        if abs(norm_upper_slope) < 0.0001 and abs(norm_lower_slope) < 0.0001:  # More lenient flatness check
            LoggingHelper.debug("Invalid triangle: slopes too flat")
            return False, None, None
        
        return True, upper_line, lower_line
    
    def _get_trend_line(self, df: pd.DataFrame, points: List[int]) -> Dict[str, float]:
        """Calculate trend line parameters."""
        if len(points) < 2:
            return {'slope': 0, 'intercept': 0}
        
        # Normalize x values to [0, 1] range
        x = np.array(points)
        x_norm = (x - min(points)) / (max(points) - min(points))
        y = df['close'].iloc[points].values
        
        # Calculate trend line
        slope, intercept = np.polyfit(x_norm, y, 1)
        
        # Log trend line details
        LoggingHelper.debug(f"Trend line points - x: {points}, y: {y.tolist()}")
        LoggingHelper.debug(f"Normalized x: {x_norm.tolist()}")
        
        return {'slope': slope, 'intercept': intercept}

class AscendingTriangle(TrianglePattern):
    """Ascending triangle pattern detector."""
    
    def __init__(self):
        """Initialize pattern detector."""
        super().__init__()
        self.pattern_type = 'ascending_triangle'
    
    def detect_pattern(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect ascending triangle pattern."""
        # Get peaks and troughs
        peaks = self._find_peaks(df['close'])
        troughs = self._find_troughs(df['close'])
        
        # Need at least min_points to form the pattern
        if len(df) < self.min_points:
            return []
        
        pattern_points = []
        
        # Check for valid triangle
        valid, upper_line, lower_line = self._is_valid_triangle(df, peaks, troughs)
        if valid:
            # Sort points by time
            peaks = sorted(peaks)
            troughs = sorted(troughs)
            
            # Calculate normalized slopes
            price_range = df['close'].max() - df['close'].min()
            norm_upper_slope = upper_line['slope'] / (price_range * len(df))
            norm_lower_slope = lower_line['slope'] / (price_range * len(df))
            
            # Check for ascending triangle (relatively flat resistance, rising support)
            LoggingHelper.debug(f"Ascending triangle check - Upper slope: {norm_upper_slope:.4f}, Lower slope: {norm_lower_slope:.4f}")
            # For ascending triangle: relatively flat resistance (can slightly rise or fall)
            # and rising support
            if abs(norm_upper_slope) < 0.01 and norm_lower_slope > 0.005:  # Adjusted thresholds
                LoggingHelper.info(f"Found ascending triangle - Resistance slope: {abs(upper_line['slope']):.4f}, Support slope: {lower_line['slope']:.4f}")
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
        
        # Calculate normalized slopes
        price_range = df['close'].max() - df['close'].min()
        norm_upper_slope = upper_line['slope'] / (price_range * len(df))
        norm_lower_slope = lower_line['slope'] / (price_range * len(df))
        
        # Resistance flatness
        resistance_flatness = 1 - min(abs(norm_upper_slope), 1.0)  # Normalize slope
        
        # Support trend
        support_trend = min(norm_lower_slope, 1.0)  # Normalize slope
        
        # Pattern height
        pattern_height = (peaks[-1]['price'] - troughs[0]['price']) / troughs[0]['price']
        height_score = min(pattern_height / 0.05, 1.0)  # Normalize to 5% height
        
        # Volume profile - use pattern-specific range
        pattern_start = min(peak_indices + trough_indices)
        pattern_end = max(peak_indices + trough_indices)
        
        # Calculate volume trend using rolling averages
        volumes = df['volume'].iloc[pattern_start:pattern_end + 1]
        window = max(3, len(volumes) // 5)  # Use 20% of pattern length or minimum 3 points
        rolling_vol = volumes.rolling(window=window).mean()
        
        # Compare start and end volume trends
        start_window = min(window, len(volumes) // 3)  # Use smaller window if pattern is short
        volume_start = rolling_vol.iloc[:start_window].mean()
        volume_end = rolling_vol.iloc[-start_window:].mean()
        
        # Calculate relative volume change
        volume_change = (volume_end - volume_start) / volume_start if volume_start > 0 else 0
        # Normalize to [0, 1] range with a threshold of 100% increase
        volume_trend = min(max(volume_change / 1.0, 0.0), 1.0)
        
        # Calculate base confidence
        confidence = (
            resistance_flatness * 0.35 +  # Weight for flat resistance
            support_trend * 0.35 +        # Weight for rising support
            height_score * 0.15 +         # Weight for pattern height
            volume_trend * 0.15           # Weight for volume trend
        )
        
        # Add bonus for strong pattern characteristics
        if resistance_flatness > 0.8 and support_trend > 0.6:  # Strong pattern formation
            confidence = min(confidence * 1.3, 1.0)  # 30% bonus
        elif volume_trend > 0.7:  # Strong volume confirmation
            confidence = min(confidence * 1.2, 1.0)  # 20% bonus
        
        return min(max(confidence, 0.0), 1.0)
    
    def get_pattern_direction(self, pattern: List[Dict[str, Any]]) -> str:
        """Get pattern direction (bullish/bearish)."""
        if not pattern:
            return 'neutral'
        
        # Ascending triangle is a bullish continuation pattern
        return 'bullish'

class DescendingTriangle(TrianglePattern):
    """Descending triangle pattern detector."""
    
    def __init__(self):
        """Initialize pattern detector."""
        super().__init__()
        self.pattern_type = 'descending_triangle'
    
    def detect_pattern(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect descending triangle pattern."""
        # Get peaks and troughs
        peaks = self._find_peaks(df['close'])
        troughs = self._find_troughs(df['close'])
        
        # Need at least min_points to form the pattern
        if len(df) < self.min_points:
            return []
        
        pattern_points = []
        
        # Check for valid triangle
        valid, upper_line, lower_line = self._is_valid_triangle(df, peaks, troughs)
        if valid:
            # Sort points by time
            peaks = sorted(peaks)
            troughs = sorted(troughs)
            
            # Calculate normalized slopes
            price_range = df['close'].max() - df['close'].min()
            norm_upper_slope = upper_line['slope'] / (price_range * len(df))
            norm_lower_slope = lower_line['slope'] / (price_range * len(df))
            
            # Check for descending triangle (relatively flat support, falling resistance)
            LoggingHelper.debug(f"Descending triangle check - Upper slope: {norm_upper_slope:.4f}, Lower slope: {norm_lower_slope:.4f}")
            # For descending triangle: relatively flat support (can slightly rise or fall)
            # and falling resistance
            if abs(norm_lower_slope) < 0.01 and norm_upper_slope < -0.005:  # Adjusted thresholds
                LoggingHelper.info(f"Found descending triangle - Support slope: {abs(lower_line['slope']):.4f}, Resistance slope: {upper_line['slope']:.4f}")
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
        
        # Calculate normalized slopes
        price_range = df['close'].max() - df['close'].min()
        norm_upper_slope = upper_line['slope'] / (price_range * len(df))
        norm_lower_slope = lower_line['slope'] / (price_range * len(df))
        
        # Support flatness
        support_flatness = 1 - min(abs(norm_lower_slope), 1.0)  # Normalize slope
        
        # Resistance trend
        resistance_trend = min(abs(norm_upper_slope), 1.0)  # Normalize slope
        
        # Pattern height
        pattern_height = abs(peaks[0]['price'] - troughs[-1]['price']) / peaks[0]['price']
        height_score = min(pattern_height / 0.05, 1.0)  # Normalize to 5% height
        
        # Volume profile - use pattern-specific range
        pattern_start = min(peak_indices + trough_indices)
        pattern_end = max(peak_indices + trough_indices)
        
        # Calculate volume trend using rolling averages
        volumes = df['volume'].iloc[pattern_start:pattern_end + 1]
        window = max(3, len(volumes) // 5)  # Use 20% of pattern length or minimum 3 points
        rolling_vol = volumes.rolling(window=window).mean()
        
        # Compare start and end volume trends
        start_window = min(window, len(volumes) // 3)  # Use smaller window if pattern is short
        volume_start = rolling_vol.iloc[:start_window].mean()
        volume_end = rolling_vol.iloc[-start_window:].mean()
        
        # Calculate relative volume change
        volume_change = (volume_end - volume_start) / volume_start if volume_start > 0 else 0
        # Normalize to [0, 1] range with a threshold of 100% increase
        volume_trend = min(max(volume_change / 1.0, 0.0), 1.0)
        
        # Calculate base confidence
        confidence = (
            support_flatness * 0.35 +     # Weight for flat support
            resistance_trend * 0.35 +      # Weight for falling resistance
            height_score * 0.15 +         # Weight for pattern height
            volume_trend * 0.15           # Weight for volume trend
        )
        
        # Add bonus for strong pattern characteristics
        if support_flatness > 0.8 and resistance_trend > 0.6:  # Strong pattern formation
            confidence = min(confidence * 1.3, 1.0)  # 30% bonus
        elif volume_trend > 0.7:  # Strong volume confirmation
            confidence = min(confidence * 1.2, 1.0)  # 20% bonus
        
        return min(max(confidence, 0.0), 1.0)
    
    def get_pattern_direction(self, pattern: List[Dict[str, Any]]) -> str:
        """Get pattern direction (bullish/bearish)."""
        if not pattern:
            return 'neutral'
        
        # Descending triangle is a bearish continuation pattern
        return 'bearish'

class SymmetricalTriangle(TrianglePattern):
    """Symmetrical triangle pattern detector."""
    
    def __init__(self):
        """Initialize pattern detector."""
        super().__init__()
        self.pattern_type = 'symmetrical_triangle'
    
    def detect_pattern(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect symmetrical triangle pattern."""
        # Get peaks and troughs
        peaks = self._find_peaks(df['close'])
        troughs = self._find_troughs(df['close'])
        
        # Need at least min_points to form the pattern
        if len(df) < self.min_points:
            return []
        
        pattern_points = []
        
        # Check for valid triangle
        valid, upper_line, lower_line = self._is_valid_triangle(df, peaks, troughs)
        if valid:
            # Sort points by time
            peaks = sorted(peaks)
            troughs = sorted(troughs)
            
            # Calculate normalized slopes
            price_range = df['close'].max() - df['close'].min()
            norm_upper_slope = upper_line['slope'] / (price_range * len(df))
            norm_lower_slope = lower_line['slope'] / (price_range * len(df))
            
            # Check for symmetrical triangle (converging trend lines)
            # Upper line should be falling, lower line should be rising
            # Calculate slope ratio regardless of direction
            slope_ratio = min(abs(norm_upper_slope), abs(norm_lower_slope)) / max(abs(norm_upper_slope), abs(norm_lower_slope))
            LoggingHelper.debug(f"Symmetrical triangle check - Upper: {norm_upper_slope:.4f}, Lower: {norm_lower_slope:.4f}, Ratio: {slope_ratio:.4f}")
            
            # For symmetrical triangle:
            # 1. Upper line should be falling (negative slope)
            # 2. Lower line should be rising (positive slope)
            # 3. Slopes should be similar in magnitude
            if (norm_upper_slope < -0.005 and  # Upper line falling
                norm_lower_slope > 0.005 and   # Lower line rising
                slope_ratio > 0.6):            # Keep lenient ratio
                    LoggingHelper.info("Found symmetrical triangle")
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
        
        # Calculate normalized slopes
        price_range = df['close'].max() - df['close'].min()
        norm_upper_slope = upper_line['slope'] / (price_range * len(df))
        norm_lower_slope = lower_line['slope'] / (price_range * len(df))
        
        # Slope symmetry
        slope_diff = abs(abs(norm_upper_slope) - abs(norm_lower_slope))
        slope_symmetry = 1 - min(slope_diff, 1.0)  # Normalize difference
        
        # Convergence
        convergence = min((abs(norm_upper_slope) + abs(norm_lower_slope)), 1.0)
        
        # Pattern height
        pattern_height = abs(peaks[0]['price'] - troughs[-1]['price']) / peaks[0]['price']
        height_score = min(pattern_height / 0.05, 1.0)  # Normalize to 5% height
        
        # Volume profile - use pattern-specific range
        pattern_start = min(peak_indices + trough_indices)
        pattern_end = max(peak_indices + trough_indices)
        
        # Calculate volume trend using rolling averages
        volumes = df['volume'].iloc[pattern_start:pattern_end + 1]
        window = max(3, len(volumes) // 5)  # Use 20% of pattern length or minimum 3 points
        rolling_vol = volumes.rolling(window=window).mean()
        
        # Compare start and end volume trends
        start_window = min(window, len(volumes) // 3)  # Use smaller window if pattern is short
        volume_start = rolling_vol.iloc[:start_window].mean()
        volume_end = rolling_vol.iloc[-start_window:].mean()
        
        # Calculate relative volume change
        volume_change = (volume_end - volume_start) / volume_start if volume_start > 0 else 0
        # Normalize to [0, 1] range with a threshold of 100% increase
        volume_trend = min(max(volume_change / 1.0, 0.0), 1.0)
        
        # Calculate base confidence
        confidence = (
            slope_symmetry * 0.35 +       # Weight for similar slope magnitudes
            convergence * 0.35 +          # Weight for strong convergence
            height_score * 0.15 +         # Weight for pattern height
            volume_trend * 0.15           # Weight for volume trend
        )
        
        # Add bonus for strong pattern characteristics
        if slope_symmetry > 0.8 and convergence > 0.6:  # Strong pattern formation
            confidence = min(confidence * 1.3, 1.0)  # 30% bonus
        elif volume_trend > 0.7:  # Strong volume confirmation
            confidence = min(confidence * 1.2, 1.0)  # 20% bonus
        
        return min(max(confidence, 0.0), 1.0)
    
    def get_pattern_direction(self, pattern: List[Dict[str, Any]]) -> str:
        """Get pattern direction (bullish/bearish)."""
        if not pattern:
            return 'neutral'
        
        # Symmetrical triangle can break either way
        # Use prior trend to determine direction
        peaks = [p for p in pattern if p['type'] == 'peak']
        if len(peaks) >= 2:
            if peaks[-1]['price'] > peaks[0]['price']:
                return 'bullish'
            else:
                return 'bearish'
        
        return 'neutral'
