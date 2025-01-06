"""
On Balance Volume (OBV) strategy implementation.
"""
from typing import List, Dict, Optional, Tuple
import pandas as pd
import numpy as np
from utils.indicators import calculate_obv, calculate_sma, calculate_slope
from utils.logging_helper import LoggingHelper
from .base import BaseStrategy

class OBVStrategy(BaseStrategy):
    def __init__(self,
                ma_period: int = 20,
                obv_ma_period: int = 20,
                slope_period: int = 5,
                divergence_threshold: float = 0.1,
                volume_threshold: float = 1.5,  # Volume mínimo em relação à média
                confidence_threshold: float = 0.6):
        """
        Initialize OBV strategy.
        
        Args:
            ma_period: Period for price moving average
            obv_ma_period: Period for OBV moving average
            slope_period: Period for slope calculation
            divergence_threshold: Minimum divergence for signal generation
            volume_threshold: Minimum volume multiplier vs average
            confidence_threshold: Minimum confidence level for signals
        """
        super().__init__()
        self.ma_period = ma_period
        self.obv_ma_period = obv_ma_period
        self.slope_period = slope_period
        self.divergence_threshold = divergence_threshold
        self.volume_threshold = volume_threshold
        self.confidence_threshold = confidence_threshold
        
        LoggingHelper.log(f"Initialized OBV Strategy with parameters:")
        LoggingHelper.log(f"MA Period: {ma_period}")
        LoggingHelper.log(f"OBV MA Period: {obv_ma_period}")
        LoggingHelper.log(f"Slope Period: {slope_period}")
        LoggingHelper.log(f"Divergence Threshold: {divergence_threshold}")
        LoggingHelper.log(f"Volume Threshold: {volume_threshold}")
        LoggingHelper.log(f"Confidence Threshold: {confidence_threshold}")

    def detect_divergence(self, 
                         price_slope: float, 
                         obv_slope: float) -> Optional[str]:
        """
        Detect divergence between price and OBV.
        
        Args:
            price_slope: Slope of price
            obv_slope: Slope of OBV
            
        Returns:
            str: 'bullish', 'bearish', or None
        """
        # Verificar se há divergência significativa
        if abs(price_slope - obv_slope) < self.divergence_threshold:
            return None
            
        # Divergência baixista: preço sobe mas OBV cai
        if price_slope > 0 and obv_slope < 0:
            return 'bearish'
            
        # Divergência altista: preço cai mas OBV sobe
        if price_slope < 0 and obv_slope > 0:
            return 'bullish'
            
        return None

    def analyze_volume_trend(self, 
                           df: pd.DataFrame, 
                           lookback: int = 10) -> Dict[str, float]:
        """
        Analyze volume trend and accumulation/distribution.
        
        Args:
            df: DataFrame with price and volume data
            lookback: Period for volume analysis
            
        Returns:
            Dictionary with volume analysis metrics
        """
        recent_volume = df['volume'].tail(lookback)
        avg_volume = recent_volume.mean()
        current_volume = recent_volume.iloc[-1]
        
        # Calcular razão do volume atual vs média
        volume_ratio = current_volume / avg_volume
        
        # Calcular distribuição de volume up/down
        up_volume = recent_volume[df['close'].diff().tail(lookback) > 0].sum()
        down_volume = recent_volume[df['close'].diff().tail(lookback) < 0].sum()
        
        # Calcular razão up/down volume
        volume_trend = up_volume / (down_volume + 1e-9)
        
        return {
            'volume_ratio': volume_ratio,
            'volume_trend': volume_trend,
            'is_high_volume': volume_ratio > self.volume_threshold
        }

    def generate_signals(self, df: pd.DataFrame) -> List[Dict]:
        """
        Generate trading signals based on OBV analysis.
        
        Args:
            df: DataFrame with price and volume data
            
        Returns:
            List of signal dictionaries
        """
        signals = []
        
        # Calculate indicators
        df['obv'] = calculate_obv(df['close'], df['volume'])
        df['price_ma'] = calculate_sma(df['close'], self.ma_period)
        df['obv_ma'] = calculate_sma(df['obv'], self.obv_ma_period)
        
        # Calculate slopes
        df['price_slope'] = calculate_slope(df['price_ma'], self.slope_period)
        df['obv_slope'] = calculate_slope(df['obv_ma'], self.slope_period)
        
        # Get current values
        current = df.iloc[-1]
        
        # Detect divergences
        divergence = self.detect_divergence(
            current['price_slope'],
            current['obv_slope']
        )
        
        # Analyze volume
        volume_analysis = self.analyze_volume_trend(df)
        
        # Calculate base confidence from volume
        base_confidence = min(volume_analysis['volume_ratio'] / self.volume_threshold, 1.0)
        
        # Adjust confidence based on volume trend
        if volume_analysis['volume_trend'] > 1.5:  # Strong up volume
            base_confidence *= 1.2
        elif volume_analysis['volume_trend'] < 0.67:  # Strong down volume
            base_confidence *= 0.8
            
        confidence = min(base_confidence, 1.0)
        
        # Generate signals based on divergence and volume
        if divergence == 'bullish' and volume_analysis['is_high_volume']:
            if confidence >= self.confidence_threshold:
                signals.append({
                    'type': 'long',
                    'confidence': confidence,
                    'price': current['close'],
                    'pattern': 'obv_bullish_divergence',
                    'volume_ratio': volume_analysis['volume_ratio']
                })
                LoggingHelper.log(f"Generated bullish signal with confidence {confidence:.2f}")
                
        elif divergence == 'bearish' and volume_analysis['is_high_volume']:
            if confidence >= self.confidence_threshold:
                signals.append({
                    'type': 'short',
                    'confidence': confidence,
                    'price': current['close'],
                    'pattern': 'obv_bearish_divergence',
                    'volume_ratio': volume_analysis['volume_ratio']
                })
                LoggingHelper.log(f"Generated bearish signal with confidence {confidence:.2f}")
        
        return signals

    def should_exit(self, df: pd.DataFrame, current_idx: int, position: Dict) -> bool:
        """
        Determine if current position should be exited based on OBV.
        
        Args:
            df: DataFrame with price and volume data
            current_idx: Current index in DataFrame
            position: Current position information
            
        Returns:
            bool: True if position should be exited
        """
        if current_idx < 1:
            return False
            
        current = df.iloc[current_idx]
        previous = df.iloc[current_idx - 1]
        
        # Detect divergence
        divergence = self.detect_divergence(
            current['price_slope'],
            current['obv_slope']
        )
        
        # Analyze volume
        volume_analysis = self.analyze_volume_trend(
            df.iloc[:current_idx + 1]
        )
        
        # Exit long position
        if position['type'] == 'long':
            # Exit on bearish divergence with high volume
            if (divergence == 'bearish' and 
                volume_analysis['is_high_volume'] and
                volume_analysis['volume_trend'] < 0.67):
                LoggingHelper.log("Exiting long position on bearish divergence")
                return True
                
        # Exit short position
        elif position['type'] == 'short':
            # Exit on bullish divergence with high volume
            if (divergence == 'bullish' and 
                volume_analysis['is_high_volume'] and
                volume_analysis['volume_trend'] > 1.5):
                LoggingHelper.log("Exiting short position on bullish divergence")
                return True
        
        return False

    def calculate_position_size(self, df: pd.DataFrame, signal: Dict) -> float:
        """
        Calculate position size based on signal confidence and volume.
        
        Args:
            df: DataFrame with price and volume data
            signal: Signal dictionary with confidence level
            
        Returns:
            float: Position size multiplier (0.0 to 1.0)
        """
        # Base size from signal confidence
        base_size = 0.5
        
        # Adjust based on volume ratio
        volume_multiplier = min(signal['volume_ratio'] / self.volume_threshold, 1.5)
        
        # Get volume trend
        volume_analysis = self.analyze_volume_trend(df)
        
        # Adjust based on volume trend
        trend_multiplier = 1.0
        if volume_analysis['volume_trend'] > 1.5:
            trend_multiplier = 1.2
        elif volume_analysis['volume_trend'] < 0.67:
            trend_multiplier = 0.8
        
        return min(base_size * volume_multiplier * trend_multiplier * signal['confidence'], 1.0)
