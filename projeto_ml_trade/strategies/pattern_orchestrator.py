"""
Pattern orchestrator for coordinating pattern detection.
"""
from typing import List, Dict, Any
import pandas as pd
import numpy as np
from scipy.signal import find_peaks

class PatternOrchestrator:
    """Orchestrates pattern detection across different types."""
    
    def __init__(self):
        """Initialize orchestrator."""
        pass
    
    def find_peaks_troughs(self, prices: np.array, prominence: float = 0.02) -> tuple:
        """Find peaks and troughs in price series."""
        try:
            # Find peaks with prominence relative to price
            peak_idx, peak_props = find_peaks(prices, prominence=prominence*np.mean(prices))
            peaks = [(int(idx), float(prices[idx])) for idx in peak_idx]
            
            # Find troughs (peaks in inverted series)
            trough_idx, trough_props = find_peaks(-prices, prominence=prominence*np.mean(prices))
            troughs = [(int(idx), float(prices[idx])) for idx in trough_idx]
            
            # Sort by index
            peaks.sort(key=lambda x: x[0])
            troughs.sort(key=lambda x: x[0])
            
            return peaks, troughs
            
        except Exception as e:
            print(f"Error finding peaks/troughs: {str(e)}")
            return [], []
    
    def detect_falling_wedge(self, df: pd.DataFrame, peaks: List, troughs: List) -> Dict:
        """Detect falling wedge pattern."""
        try:
            if len(peaks) < 3 or len(troughs) < 2:
                return None
                
            # Get last peaks and troughs
            last_peaks = peaks[-3:]  # Need at least 3 peaks
            last_troughs = troughs[-2:]  # Need at least 2 troughs
            
            # Check if peaks and troughs are falling
            peak_prices = [p[1] for p in last_peaks]
            trough_prices = [t[1] for t in last_troughs]
            
            if not (all(peak_prices[i] > peak_prices[i+1] for i in range(len(peak_prices)-1)) and
                    all(trough_prices[i] > trough_prices[i+1] for i in range(len(trough_prices)-1))):
                return None
                
            # Calculate slopes
            peak_slope = (peak_prices[-1] - peak_prices[0]) / (last_peaks[-1][0] - last_peaks[0][0])
            trough_slope = (trough_prices[-1] - trough_prices[0]) / (last_troughs[-1][0] - last_troughs[0][0])
            
            # Check if trough line is less steep (converging)
            if trough_slope <= peak_slope:
                return None
                
            # Calculate confidence based on pattern clarity
            slope_diff = abs(peak_slope - trough_slope)
            price_range = max(peak_prices) - min(trough_prices)
            time_range = max(last_peaks[-1][0], last_troughs[-1][0]) - min(last_peaks[0][0], last_troughs[0][0])
            
            confidence = min(1.0, (
                min(slope_diff/0.01, 1.0) * 0.4 +     # Slope difference
                min(price_range/peak_prices[0], 0.1)/0.1 * 0.3 +  # Price range
                min(time_range/20, 1.0) * 0.3         # Time range
            ))
            
            return {
                'type': 'falling_wedge',
                'confidence': confidence,
                'peaks': last_peaks,
                'troughs': last_troughs,
                'start_idx': min(last_peaks[0][0], last_troughs[0][0]),
                'end_idx': max(last_peaks[-1][0], last_troughs[-1][0])
            }
            
        except Exception as e:
            print(f"Error detecting falling wedge: {str(e)}")
            return None
    
    def detect_rising_wedge(self, df: pd.DataFrame, peaks: List, troughs: List) -> Dict:
        """Detect rising wedge pattern."""
        try:
            if len(peaks) < 2 or len(troughs) < 3:
                return None
                
            # Get last peaks and troughs
            last_peaks = peaks[-2:]  # Need at least 2 peaks
            last_troughs = troughs[-3:]  # Need at least 3 troughs
            
            # Check if peaks and troughs are rising
            peak_prices = [p[1] for p in last_peaks]
            trough_prices = [t[1] for t in last_troughs]
            
            if not (all(peak_prices[i] < peak_prices[i+1] for i in range(len(peak_prices)-1)) and
                    all(trough_prices[i] < trough_prices[i+1] for i in range(len(trough_prices)-1))):
                return None
                
            # Calculate slopes
            peak_slope = (peak_prices[-1] - peak_prices[0]) / (last_peaks[-1][0] - last_peaks[0][0])
            trough_slope = (trough_prices[-1] - trough_prices[0]) / (last_troughs[-1][0] - last_troughs[0][0])
            
            # Check if peak line is less steep (converging)
            if peak_slope <= trough_slope:
                return None
                
            # Calculate confidence based on pattern clarity
            slope_diff = abs(peak_slope - trough_slope)
            price_range = max(peak_prices) - min(trough_prices)
            time_range = max(last_peaks[-1][0], last_troughs[-1][0]) - min(last_peaks[0][0], last_troughs[0][0])
            
            confidence = min(1.0, (
                min(slope_diff/0.01, 1.0) * 0.4 +     # Slope difference
                min(price_range/peak_prices[0], 0.1)/0.1 * 0.3 +  # Price range
                min(time_range/20, 1.0) * 0.3         # Time range
            ))
            
            return {
                'type': 'rising_wedge',
                'confidence': confidence,
                'peaks': last_peaks,
                'troughs': last_troughs,
                'start_idx': min(last_peaks[0][0], last_troughs[0][0]),
                'end_idx': max(last_peaks[-1][0], last_troughs[-1][0])
            }
            
        except Exception as e:
            print(f"Error detecting rising wedge: {str(e)}")
            return None
    
    def detect_patterns(self, df: pd.DataFrame) -> List[Dict]:
        """Detect all patterns in data."""
        try:
            # Find peaks and troughs
            peaks, troughs = self.find_peaks_troughs(df['close'].values)
            
            # Detect patterns
            patterns = []
            
            # Wedge patterns
            falling_wedge = self.detect_falling_wedge(df, peaks, troughs)
            if falling_wedge:
                patterns.append(falling_wedge)
                
            rising_wedge = self.detect_rising_wedge(df, peaks, troughs)
            if rising_wedge:
                patterns.append(rising_wedge)
            
            return patterns
            
        except Exception as e:
            print(f"Error detecting patterns: {str(e)}")
            return []
