# market_value.py
import pandas as pd
import numpy as np

def add_market_value_metrics(df):
    """
    Adiciona métricas baseadas em valor de mercado usando apenas dados OHLCV
    """
    # Add small epsilon to prevent division by zero
    epsilon = 1e-10
    
    # MVRV usando média móvel de volume
    df['realized_value'] = df['close'] * df['volume'].rolling(30, min_periods=1).mean()
    df['mvrv'] = df['close'] * df['volume'] / (df['realized_value'] + epsilon)
    
    # Calcular z-score com tratamento de NaN/Inf
    mvrv_mean = df['mvrv'].rolling(365, min_periods=1).mean()
    mvrv_std = df['mvrv'].rolling(365, min_periods=1).std()
    df['mvrv_z_score'] = (df['mvrv'] - mvrv_mean) / (mvrv_std + epsilon)
    
    # Métricas de Momentum de Valor com tratamento de NaN
    df['value_momentum'] = df['mvrv'].pct_change(12).fillna(0)  # Momentum de 3h para timeframe 15m
    df['value_trend'] = df['mvrv'].rolling(96, min_periods=1).mean()  # Tendência de 24h
    
    # Oscilador de Valor com tratamento de divisão por zero
    rolling_min = df['mvrv'].rolling(96, min_periods=1).min()
    rolling_max = df['mvrv'].rolling(96, min_periods=1).max()
    denominator = rolling_max - rolling_min
    df['value_oscillator'] = np.where(
        denominator > epsilon,
        (df['mvrv'] - rolling_min) / denominator * 100,
        50  # Valor neutro quando não há variação
    )
    
    return df
