"""
EMA trend strategy implementation.
"""
from typing import List, Dict, Any
import pandas as pd
import numpy as np
import mplfinance as mpf
import matplotlib.pyplot as plt
from datetime import datetime
import os

from strategies.base import BaseStrategy
from utils.indicators import calculate_ema, calculate_slope
from utils.logging_helper import LoggingHelper

# Constants for chart generation
LOOKBACK_PERIODS = 50  # Number of candles to show before signal
CHART_STYLE = mpf.make_mpf_style(base_mpf_style='charles', gridstyle='')

class EMATrendStrategy(BaseStrategy):
    def __init__(self, 
                 ema21_period: int = 21,
                 ema55_period: int = 55,
                 ema80_period: int = 80,
                 ema100_period: int = 100,
                 slope_window: int = 10,
                 confidence_threshold: float = 0.5,
                 percentile_window: int = 100):
        super().__init__()
        self.ema21_period = ema21_period
        self.ema55_period = ema55_period
        self.ema80_period = ema80_period
        self.ema100_period = ema100_period
        self.slope_window = slope_window
        self.confidence_threshold = confidence_threshold
        self.percentile_window = percentile_window

    def generate_signals(self, df: pd.DataFrame) -> List[Dict]:
        signals = []
        
        # Calculate EMAs
        df.loc[:, 'EMA21'] = calculate_ema(df['close'], self.ema21_period)
        df.loc[:, 'EMA55'] = calculate_ema(df['close'], self.ema55_period)
        df.loc[:, 'EMA80'] = calculate_ema(df['close'], self.ema80_period)
        df.loc[:, 'EMA100'] = calculate_ema(df['close'], self.ema100_period)
        
        # Calculate percentage difference between EMA21 and EMA100
        df.loc[:, 'PercentDiff'] = abs((df['EMA21'] - df['EMA100']) / df['EMA100']) * 100
        
        # Calculate historical percentiles over a rolling window
        df.loc[:, 'LowerBound'] = df['PercentDiff'].rolling(window=self.percentile_window).quantile(0.10)
        df.loc[:, 'UpperBound'] = df['PercentDiff'].rolling(window=self.percentile_window).quantile(0.90)
        
        # Determine trend
        df.loc[:, 'Uptrend'] = (df['EMA21'] > df['EMA55']) & (df['EMA55'] > df['EMA80']) & (df['EMA80'] > df['EMA100'])
        df.loc[:, 'Downtrend'] = (df['EMA100'] > df['EMA80']) & (df['EMA80'] > df['EMA55']) & (df['EMA55'] > df['EMA21'])
        
        # Calculate slopes
        df.loc[:, 'EMA21_Slope'] = calculate_slope(df['EMA21'], self.slope_window)
        df.loc[:, 'EMA55_Slope'] = calculate_slope(df['EMA55'], self.slope_window)
        df.loc[:, 'EMA80_Slope'] = calculate_slope(df['EMA80'], self.slope_window)
        df.loc[:, 'EMA100_Slope'] = calculate_slope(df['EMA100'], self.slope_window)
        
        # Avoid long entries if EMA21 slope is negative while others are positive
        df.loc[:, 'AvoidLong'] = df['Uptrend'] & (df['EMA21_Slope'] < 0) & \
                          (df['EMA55_Slope'] > 0) & (df['EMA80_Slope'] > 0) & (df['EMA100_Slope'] > 0)
        
        # Entry conditions
        current_row = df.iloc[-1]
        current_price = current_row['close']
        current_percent_diff = current_row['PercentDiff']
        lower_bound = current_row['LowerBound']
        upper_bound = current_row['UpperBound']
        
        # Check if within balance range
        if lower_bound is not np.nan and upper_bound is not np.nan:
            if lower_bound <= current_percent_diff <= upper_bound:
                if current_row['Uptrend'] and not current_row['AvoidLong']:
                    confidence = self.calculate_confidence(df)
                    if confidence >= self.confidence_threshold:
                        signals.append({
                            'type': 'long',
                            'confidence': confidence,
                            'price': current_price,
                            'pattern': 'bullish_ema_alignment'
                        })
                        LoggingHelper.log(f"Long signal generated with confidence {confidence:.2f}")
                
                if current_row['Downtrend']:
                    confidence = self.calculate_confidence(df)
                    if confidence >= self.confidence_threshold:
                        signals.append({
                            'type': 'short',
                            'confidence': confidence,
                            'price': current_price,
                            'pattern': 'bearish_ema_alignment'
                        })
                        LoggingHelper.log(f"Short signal generated with confidence {confidence:.2f}")
            else:
                LoggingHelper.log("Percentage difference outside balance range. No signals generated.")
        else:
            LoggingHelper.log("Insufficient data to calculate balance range. No signals generated.")
        
        return signals

    def should_exit(self, df: pd.DataFrame, current_idx: int, position: Dict) -> bool:
        current_row = df.iloc[current_idx]
        current_price = current_row['close']
        
        if position['type'] == 'long':
            # Stop loss 2% below EMA100
            stop_loss_price = current_row['EMA100'] * 0.98
            if current_price <= stop_loss_price:
                return True
            # Take profit based on risk-reward ratio of 2
            risk = current_price - stop_loss_price
            take_profit_price = current_price + 2 * risk
            if current_price >= take_profit_price:
                return True
        elif position['type'] == 'short':
            # Stop loss 2% above EMA100
            stop_loss_price = current_row['EMA100'] * 1.02
            if current_price >= stop_loss_price:
                return True
            # Take profit based on risk-reward ratio of 2
            risk = stop_loss_price - current_price
            take_profit_price = current_price - 2 * risk
            if current_price <= take_profit_price:
                return True
        return False

    def calculate_confidence(self, df: pd.DataFrame) -> float:
        # Example confidence calculation based on trend strength and slope consistency
        current_row = df.iloc[-1]
        trend_confidence = 0.0
        if current_row['Uptrend']:
            trend_confidence += 0.5
            if current_row['EMA21_Slope'] > 0 and current_row['EMA55_Slope'] > 0 and current_row['EMA80_Slope'] > 0 and current_row['EMA100_Slope'] > 0:
                trend_confidence += 0.5
        elif current_row['Downtrend']:
            trend_confidence += 0.5
            if current_row['EMA21_Slope'] < 0 and current_row['EMA55_Slope'] < 0 and current_row['EMA80_Slope'] < 0 and current_row['EMA100_Slope'] < 0:
                trend_confidence += 0.5
        return min(trend_confidence, 1.0)
