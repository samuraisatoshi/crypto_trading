"""
Moving Averages strategy implementation with slope analysis.
"""
from typing import List, Dict, Optional, Tuple
import pandas as pd
import numpy as np
from utils.indicators import calculate_sma, calculate_ema, calculate_slope
from utils.logging_helper import LoggingHelper
from .base import BaseStrategy

class MovingAveragesStrategy(BaseStrategy):
    def __init__(self,
                ma_type: str = 'EMA',
                fast_period: int = 20,
                slow_period: int = 50,
                trend_period: int = 200,
                min_distance: float = 0.5,
                slope_period: int = 5,
                slope_threshold: float = 45.0,  # Ângulo em graus para considerar movimento brusco
                confidence_threshold: float = 0.6):
        """
        Initialize Moving Averages strategy.
        
        Args:
            ma_type: Type of moving average ('SMA' or 'EMA')
            fast_period: Fast MA period
            slow_period: Slow MA period
            trend_period: Trend MA period
            min_distance: Minimum distance between MAs for signal generation (%)
            slope_period: Period for slope calculation
            slope_threshold: Angle threshold for sharp movements (degrees)
            confidence_threshold: Minimum confidence level for signals
        """
        super().__init__()
        self.ma_type = ma_type
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.trend_period = trend_period
        self.min_distance = min_distance
        self.slope_period = slope_period
        self.slope_threshold = slope_threshold
        self.confidence_threshold = confidence_threshold
        
        LoggingHelper.log(f"Initialized Moving Averages Strategy with parameters:")
        LoggingHelper.log(f"MA Type: {ma_type}")
        LoggingHelper.log(f"Fast Period: {fast_period}")
        LoggingHelper.log(f"Slow Period: {slow_period}")
        LoggingHelper.log(f"Trend Period: {trend_period}")
        LoggingHelper.log(f"Min Distance: {min_distance}%")
        LoggingHelper.log(f"Slope Period: {slope_period}")
        LoggingHelper.log(f"Slope Threshold: {slope_threshold}°")
        LoggingHelper.log(f"Confidence Threshold: {confidence_threshold}")

    def calculate_ma(self, prices: pd.Series, period: int) -> pd.Series:
        """Calculate moving average based on type."""
        if self.ma_type == 'SMA':
            return calculate_sma(prices, period)
        return calculate_ema(prices, period)

    def calculate_slopes(self, ma_series: pd.Series) -> Tuple[pd.Series, pd.Series]:
        """
        Calculate slope and angle of moving average.
        
        Returns:
            Tuple of (slope values, slope angles in degrees)
        """
        slopes = calculate_slope(ma_series, self.slope_period)
        # Converter slope para ângulos em graus
        angles = np.degrees(np.arctan(slopes))
        return slopes, angles

    def analyze_slope_velocity(self, 
                             fast_angle: float, 
                             slow_angle: float, 
                             prev_fast_angle: float) -> Dict[str, any]:
        """
        Analyze slope velocity and direction changes.
        
        Args:
            fast_angle: Current fast MA slope angle
            slow_angle: Current slow MA slope angle
            prev_fast_angle: Previous fast MA slope angle
            
        Returns:
            Dictionary with slope analysis results
        """
        # Calcular mudança na velocidade do slope
        angle_change = fast_angle - prev_fast_angle
        angle_diff = fast_angle - slow_angle
        
        # Detectar movimentos bruscos
        is_sharp_movement = abs(fast_angle) > self.slope_threshold
        is_acceleration = angle_change > 10  # Aceleração significativa
        is_reversal = angle_change * prev_fast_angle < 0  # Mudança de direção
        
        # Análise da divergência entre fast e slow
        is_diverging = abs(angle_diff) > 20  # Divergência significativa
        
        return {
            'is_sharp_movement': is_sharp_movement,
            'is_acceleration': is_acceleration,
            'is_reversal': is_reversal,
            'is_diverging': is_diverging,
            'angle_change': angle_change,
            'angle_diff': angle_diff
        }

    def generate_signals(self, df: pd.DataFrame) -> List[Dict]:
        """
        Generate trading signals based on moving averages and slope analysis.
        
        Args:
            df: DataFrame with price data
            
        Returns:
            List of signal dictionaries
        """
        signals = []
        
        # Calculate moving averages
        df['fast_ma'] = self.calculate_ma(df['close'], self.fast_period)
        df['slow_ma'] = self.calculate_ma(df['close'], self.slow_period)
        df['trend_ma'] = self.calculate_ma(df['close'], self.trend_period)
        
        # Calculate slopes and angles
        df['fast_slope'], df['fast_angle'] = self.calculate_slopes(df['fast_ma'])
        df['slow_slope'], df['slow_angle'] = self.calculate_slopes(df['slow_ma'])
        df['trend_slope'], df['trend_angle'] = self.calculate_slopes(df['trend_ma'])
        
        # Get current and previous values
        current = df.iloc[-1]
        previous = df.iloc[-2]
        
        # Analyze slope velocity
        slope_analysis = self.analyze_slope_velocity(
            current['fast_angle'],
            current['slow_angle'],
            previous['fast_angle']
        )
        
        # Calculate distances
        fast_slow_dist = abs((current['fast_ma'] - current['slow_ma']) / current['slow_ma'] * 100)
        price_trend_dist = abs((current['close'] - current['trend_ma']) / current['trend_ma'] * 100)
        
        # Check crossovers
        current_cross = current['fast_ma'] - current['slow_ma']
        previous_cross = previous['fast_ma'] - previous['slow_ma']
        
        # Adjust confidence based on slope analysis
        base_confidence = min(fast_slow_dist / self.min_distance, 1.0)
        
        # Aumentar confiança se houver movimento brusco alinhado com a direção
        if slope_analysis['is_sharp_movement']:
            if slope_analysis['is_acceleration']:
                base_confidence *= 1.2  # Acentuação do movimento
            elif slope_analysis['is_reversal']:
                base_confidence *= 0.8  # Possível reversão
        
        # Ajustar confiança baseado na divergência entre fast e slow
        if slope_analysis['is_diverging']:
            base_confidence *= 1.1  # Movimento mais forte
        
        confidence = min(base_confidence, 1.0)
        
        # Bullish signals
        if ((previous_cross <= 0 and current_cross > 0) or  # Crossover clássico
            (slope_analysis['is_sharp_movement'] and current['fast_angle'] > self.slope_threshold)):  # Movimento brusco para cima
            
            if confidence >= self.confidence_threshold:
                signal_type = 'acceleration' if slope_analysis['is_acceleration'] else 'reversal'
                signals.append({
                    'type': 'long',
                    'confidence': confidence,
                    'price': current['close'],
                    'pattern': f'{self.ma_type}_bullish_{signal_type}',
                    'slope_angle': current['fast_angle']
                })
                LoggingHelper.log(f"Generated bullish {signal_type} signal with confidence {confidence:.2f}")
        
        # Bearish signals
        elif ((previous_cross >= 0 and current_cross < 0) or  # Crossover clássico
              (slope_analysis['is_sharp_movement'] and current['fast_angle'] < -self.slope_threshold)):  # Movimento brusco para baixo
            
            if confidence >= self.confidence_threshold:
                signal_type = 'acceleration' if slope_analysis['is_acceleration'] else 'reversal'
                signals.append({
                    'type': 'short',
                    'confidence': confidence,
                    'price': current['close'],
                    'pattern': f'{self.ma_type}_bearish_{signal_type}',
                    'slope_angle': current['fast_angle']
                })
                LoggingHelper.log(f"Generated bearish {signal_type} signal with confidence {confidence:.2f}")
        
        return signals

    def should_exit(self, df: pd.DataFrame, current_idx: int, position: Dict) -> bool:
        """
        Determine if current position should be exited based on slope analysis.
        
        Args:
            df: DataFrame with price data
            current_idx: Current index in DataFrame
            position: Current position information
            
        Returns:
            bool: True if position should be exited
        """
        if current_idx < 1:
            return False
            
        current = df.iloc[current_idx]
        previous = df.iloc[current_idx - 1]
        
        # Analyze current slope conditions
        slope_analysis = self.analyze_slope_velocity(
            current['fast_angle'],
            current['slow_angle'],
            previous['fast_angle']
        )
        
        # Exit long position
        if position['type'] == 'long':
            # Exit on sharp downward movement or strong reversal
            if (current['fast_angle'] < -self.slope_threshold or
                (slope_analysis['is_reversal'] and slope_analysis['angle_change'] < -20)):
                LoggingHelper.log(f"Exiting long position on sharp downward movement (angle: {current['fast_angle']:.1f}°)")
                return True
                
        # Exit short position
        elif position['type'] == 'short':
            # Exit on sharp upward movement or strong reversal
            if (current['fast_angle'] > self.slope_threshold or
                (slope_analysis['is_reversal'] and slope_analysis['angle_change'] > 20)):
                LoggingHelper.log(f"Exiting short position on sharp upward movement (angle: {current['fast_angle']:.1f}°)")
                return True
        
        return False

    def calculate_position_size(self, df: pd.DataFrame, signal: Dict) -> float:
        """
        Calculate position size based on signal confidence and slope intensity.
        
        Args:
            df: DataFrame with price data
            signal: Signal dictionary with confidence level
            
        Returns:
            float: Position size multiplier (0.0 to 1.0)
        """
        current = df.iloc[-1]
        
        # Base size from signal confidence
        base_size = 0.5
        
        # Adjust based on slope intensity
        slope_intensity = abs(current['fast_angle']) / self.slope_threshold
        slope_multiplier = min(1.0 + (slope_intensity - 1) * 0.2, 1.5)
        
        # Adjust based on slope alignment
        slope_alignment = (
            (current['fast_slope'] > 0 and current['slow_slope'] > 0 and current['trend_slope'] > 0) or
            (current['fast_slope'] < 0 and current['slow_slope'] < 0 and current['trend_slope'] < 0)
        )
        alignment_multiplier = 1.2 if slope_alignment else 0.8
        
        return min(base_size * slope_multiplier * alignment_multiplier * signal['confidence'], 1.0)
