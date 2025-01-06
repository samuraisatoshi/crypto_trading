"""
Comprehensive technical analysis indicators and pattern detection.
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Union
from utils.logging_helper import LoggingHelper
from dataclasses import dataclass
from enum import Enum

class TrendDirection(Enum):
    UP = "up"
    DOWN = "down"
    SIDEWAYS = "sideways"

@dataclass
class PatternResult:
    """Container for pattern detection results."""
    pattern_type: str
    direction: Optional[str]
    strength: float  # 0.0 to 1.0
    description: str

class IndicatorError(Exception):
    """Custom exception for indicator calculation errors."""
    pass

def validate_data(func):
    """Decorator to validate input data for indicators."""
    def wrapper(*args, **kwargs):
        processed_args = []
        for arg in args:
            if isinstance(arg, pd.Series):
                if arg.empty:
                    raise IndicatorError("Empty data series provided")
                # Fill NaN values before calculation
                processed_args.append(arg.ffill().bfill())
            else:
                processed_args.append(arg)
        return func(*processed_args, **kwargs)
    return wrapper

@validate_data
def calculate_sma(series: pd.Series, period: int) -> pd.Series:
    """Calculate Simple Moving Average."""
    if period <= 0:
        raise IndicatorError("Period must be positive")
    if period > len(series):
        raise IndicatorError("Period longer than series length")
    return series.rolling(window=period, min_periods=1).mean()

@validate_data
def calculate_ema(series: pd.Series, period: int) -> pd.Series:
    """Calculate Exponential Moving Average."""
    if period <= 0:
        raise IndicatorError("Period must be positive")
    if period > len(series):
        raise IndicatorError("Period longer than series length")
    return series.ewm(span=period, adjust=False, min_periods=1).mean()

@validate_data
def calculate_slope(series: pd.Series, period: int = 5) -> pd.Series:
    """Calculate linear regression slope."""
    if period <= 1:
        raise IndicatorError("Period must be greater than 1")
    
    slopes = pd.Series(index=series.index, dtype=float)
    x = np.arange(period)
    
    for i in range(period, len(series) + 1):
        y = series.iloc[i-period:i].values
        slope, _ = np.polyfit(x, y, 1)
        slopes.iloc[i-1] = slope
    
    return slopes

@validate_data
def calculate_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """Calculate Relative Strength Index."""
    if period <= 0:
        raise IndicatorError("Period must be positive")
        
    delta = series.diff()
    gains = delta.where(delta > 0, 0.0)
    losses = -delta.where(delta < 0, 0.0)
    
    avg_gain = gains.rolling(window=period, min_periods=1).mean()
    avg_loss = losses.rolling(window=period, min_periods=1).mean()
    
    for i in range(period, len(gains)):
        avg_gain.iloc[i] = (avg_gain.iloc[i-1] * (period-1) + gains.iloc[i]) / period
        avg_loss.iloc[i] = (avg_loss.iloc[i-1] * (period-1) + losses.iloc[i]) / period
    
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def calculate_macd_divergence(price: pd.Series, macd: pd.Series) -> pd.Series:
    """Calculate MACD divergence."""
    divergence = pd.Series(0, index=price.index)
    
    for i in range(20, len(price)):
        window = slice(i-20, i+1)
        
        price_high = price[window].max() == price.iloc[i]
        price_low = price[window].min() == price.iloc[i]
        
        macd_high = macd[window].max() == macd.iloc[i]
        macd_low = macd[window].min() == macd.iloc[i]
        
        if price_high and macd_low:
            divergence.iloc[i] = -1  # Bearish
        elif price_low and macd_high:
            divergence.iloc[i] = 1   # Bullish
            
    return divergence

@validate_data
def calculate_macd(series: pd.Series, 
                  fast_period: int = 12, 
                  slow_period: int = 26, 
                  signal_period: int = 9) -> Dict[str, pd.Series]:
    """Calculate Moving Average Convergence Divergence."""
    if fast_period >= slow_period:
        raise IndicatorError("Fast period must be less than slow period")
    
    fast_ema = calculate_ema(series, fast_period)
    slow_ema = calculate_ema(series, slow_period)
    macd_line = fast_ema - slow_ema
    signal_line = calculate_ema(macd_line, signal_period)
    histogram = macd_line - signal_line
    
    return {
        'macd': macd_line,
        'signal': signal_line,
        'histogram': histogram,
        'divergence': calculate_macd_divergence(series, macd_line)
    }

@validate_data
def calculate_bollinger_bands(series: pd.Series, 
                            period: int = 20, 
                            std_dev: float = 2.0) -> Dict[str, pd.Series]:
    """Calculate Bollinger Bands."""
    if period <= 0:
        raise IndicatorError("Period must be positive")
    if std_dev <= 0:
        raise IndicatorError("Standard deviation multiplier must be positive")
    
    middle_band = calculate_sma(series, period)
    std = series.rolling(window=period, min_periods=1).std()
    upper_band = middle_band + (std * std_dev)
    lower_band = middle_band - (std * std_dev)
    
    bandwidth = (upper_band - lower_band) / middle_band
    percent_b = (series - lower_band) / (upper_band - lower_band)
    
    return {
        'bb_upper': upper_band,
        'bb_middle': middle_band,
        'bb_lower': lower_band,
        'bb_bandwidth': bandwidth,
        'bb_percent_b': percent_b
    }

@validate_data
def calculate_atr(high: pd.Series, 
                 low: pd.Series, 
                 close: pd.Series, 
                 period: int = 14) -> Dict[str, pd.Series]:
    """Calculate Average True Range."""
    if period <= 0:
        raise IndicatorError("Period must be positive")
    
    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    
    atr = pd.Series(index=tr.index, dtype=float)
    atr.iloc[period-1] = tr.iloc[0:period].mean()
    
    for i in range(period, len(tr)):
        atr.iloc[i] = (atr.iloc[i-1] * (period-1) + tr.iloc[i]) / period
    
    natr = (atr / close) * 100
    
    return {
        'atr': atr,
        'natr': natr
    }

@validate_data
def calculate_obv(close: pd.Series, volume: pd.Series) -> Dict[str, pd.Series]:
    """Calculate On Balance Volume with signal line."""
    direction = np.where(close > close.shift(1), 1, 
                        np.where(close < close.shift(1), -1, 0))
    obv = (direction * volume).cumsum()
    
    signal = calculate_ema(obv, 21)
    
    return {
        'obv': obv,
        'signal': signal,
        'histogram': obv - signal
    }

@validate_data
def calculate_stochastic(high: pd.Series,
                        low: pd.Series,
                        close: pd.Series,
                        k_period: int = 14,
                        d_period: int = 3,
                        smooth_k: int = 3) -> Dict[str, pd.Series]:
    """Calculate Stochastic Oscillator."""
    if k_period <= 0 or d_period <= 0 or smooth_k <= 0:
        raise IndicatorError("Periods must be positive")
    
    lowest_low = low.rolling(window=k_period, min_periods=1).min()
    highest_high = high.rolling(window=k_period, min_periods=1).max()
    k = 100 * (close - lowest_low) / (highest_high - lowest_low)
    
    if smooth_k > 1:
        k = k.rolling(window=smooth_k, min_periods=1).mean()
    
    d = k.rolling(window=d_period, min_periods=1).mean()
    
    return {
        'k': k,
        'd': d
    }

@validate_data
def calculate_adx(high: pd.Series,
                 low: pd.Series,
                 close: pd.Series,
                 period: int = 14) -> Dict[str, pd.Series]:
    """Calculate Average Directional Index."""
    if period <= 0:
        raise IndicatorError("Period must be positive")
    
    # Calculate True Range
    tr = pd.DataFrame(index=high.index)
    tr['h-l'] = high - low
    tr['h-c'] = abs(high - close.shift())
    tr['l-c'] = abs(low - close.shift())
    tr = tr.max(axis=1)
    
    # Calculate Directional Movement
    pos_dm = high - high.shift(1)
    neg_dm = low.shift(1) - low
    pos_dm = pos_dm.where((pos_dm > neg_dm) & (pos_dm > 0), 0)
    neg_dm = neg_dm.where((neg_dm > pos_dm) & (neg_dm > 0), 0)
    
    # Calculate smoothed values
    tr_smooth = calculate_ema(tr, period)
    pos_dm_smooth = calculate_ema(pos_dm, period)
    neg_dm_smooth = calculate_ema(neg_dm, period)
    
    # Calculate Directional Indicators
    pos_di = 100 * pos_dm_smooth / tr_smooth
    neg_di = 100 * neg_dm_smooth / tr_smooth
    
    # Calculate ADX
    dx = 100 * abs(pos_di - neg_di) / (pos_di + neg_di)
    adx = calculate_ema(dx, period)
    
    return {
        'adx': adx,
        'pos_di': pos_di,
        'neg_di': neg_di
    }

def add_indicators_and_oscillators(df: pd.DataFrame) -> pd.DataFrame:
    """Add basic technical indicators and oscillators to DataFrame."""
    # Moving Averages
    df['sma_20'] = calculate_sma(df['close'], 20)
    df['sma_50'] = calculate_sma(df['close'], 50)
    df['sma_200'] = calculate_sma(df['close'], 200)
    
    df['ema_12'] = calculate_ema(df['close'], 12)
    df['ema_26'] = calculate_ema(df['close'], 26)
    
    # RSI
    df['rsi'] = calculate_rsi(df['close'])
    
    # MACD
    macd_data = calculate_macd(df['close'])
    df['macd'] = macd_data['macd']
    df['macd_signal'] = macd_data['signal']
    df['macd_hist'] = macd_data['histogram']
    df['macd_divergence'] = macd_data['divergence']
    
    # Bollinger Bands
    bb_data = calculate_bollinger_bands(df['close'])
    df['bb_upper'] = bb_data['bb_upper']
    df['bb_middle'] = bb_data['bb_middle']
    df['bb_lower'] = bb_data['bb_lower']
    df['bb_bandwidth'] = bb_data['bb_bandwidth']
    df['bb_percent_b'] = bb_data['bb_percent_b']
    
    # ATR
    atr_data = calculate_atr(df['high'], df['low'], df['close'])
    df['atr'] = atr_data['atr']
    df['natr'] = atr_data['natr']
    
    # Stochastic
    stoch_data = calculate_stochastic(df['high'], df['low'], df['close'])
    df['stoch_k'] = stoch_data['k']
    df['stoch_d'] = stoch_data['d']
    
    return df

def add_advanced_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Add advanced technical indicators to DataFrame."""
    # Price slopes
    df['slope_close'] = calculate_slope(df['close'])
    df['slope_volume'] = calculate_slope(df['volume'])
    
    # Moving average slopes
    df['slope_sma20'] = calculate_slope(df['sma_20'])
    df['slope_sma50'] = calculate_slope(df['sma_50'])
    
    # Indicator slopes
    df['slope_rsi'] = calculate_slope(df['rsi'])
    df['slope_macd'] = calculate_slope(df['macd'])
    
    # Indicator crosses
    df['ma_cross'] = np.where(
        (df['sma_20'] > df['sma_50']) & (df['sma_20'].shift(1) <= df['sma_50'].shift(1)),
        1,
        np.where(
            (df['sma_20'] < df['sma_50']) & (df['sma_20'].shift(1) >= df['sma_50'].shift(1)),
            -1,
            0
        )
    )
    
    df['macd_cross'] = np.where(
        (df['macd'] > df['macd_signal']) & (df['macd'].shift(1) <= df['macd_signal'].shift(1)),
        1,
        np.where(
            (df['macd'] < df['macd_signal']) & (df['macd'].shift(1) >= df['macd_signal'].shift(1)),
            -1,
            0
        )
    )
    
    return df
