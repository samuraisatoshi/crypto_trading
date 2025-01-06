"""
Trade labeling and analysis functionality.
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from utils.logging_helper import LoggingHelper

def identify_perfect_trades(df: pd.DataFrame,
                          timeframe: str,
                          min_rr_ratio: float = 2.5,
                          max_open_positions: int = 4) -> pd.DataFrame:
    """
    Identify perfect trade entry and exit points based on price action.
    
    Args:
        df: DataFrame with OHLCV data
        timeframe: Data timeframe (e.g., '1h', '4h', '1d')
        min_rr_ratio: Minimum risk-reward ratio for trade consideration
        max_open_positions: Maximum number of concurrent open positions
        
    Returns:
        DataFrame with added trade labels
    """
    logger = LoggingHelper()
    
    # Initialize trade columns
    df['trade_entry'] = 0  # 1 for long entry, -1 for short entry
    df['trade_exit'] = 0   # 1 for exit
    df['trade_type'] = None  # 'long' or 'short'
    df['trade_rr'] = 0.0
    df['trade_result'] = None  # 'win' or 'loss'
    
    # Parameters based on timeframe
    if timeframe == '1h':
        sl_atr_mult = 1.5
        tp_atr_mult = 4.0
        min_swing = 10
    elif timeframe == '4h':
        sl_atr_mult = 2.0
        tp_atr_mult = 5.0
        min_swing = 20
    else:  # 1d
        sl_atr_mult = 2.5
        tp_atr_mult = 6.0
        min_swing = 30
    
    # Track open positions
    open_positions = []
    
    for i in range(min_swing, len(df)-1):
        current = df.iloc[i]
        
        # Skip if maximum positions reached
        if len(open_positions) >= max_open_positions:
            continue
        
        # Calculate potential long entry
        long_sl = current['low'] - (current['atr'] * sl_atr_mult)
        long_tp = current['close'] + (current['atr'] * tp_atr_mult)
        long_rr = (long_tp - current['close']) / (current['close'] - long_sl)
        
        # Calculate potential short entry
        short_sl = current['high'] + (current['atr'] * sl_atr_mult)
        short_tp = current['close'] - (current['atr'] * tp_atr_mult)
        short_rr = (current['close'] - short_tp) / (short_sl - current['close'])
        
        # Check for long setup
        if (long_rr >= min_rr_ratio and
            current['trend_strength'] in ['strong_bullish', 'weak_bullish'] and
            current['volatility_regime'] != 'extreme'):
            
            df.loc[df.index[i], 'trade_entry'] = 1
            df.loc[df.index[i], 'trade_type'] = 'long'
            df.loc[df.index[i], 'trade_rr'] = long_rr
            
            open_positions.append({
                'entry_idx': i,
                'type': 'long',
                'entry_price': current['close'],
                'sl': long_sl,
                'tp': long_tp
            })
            
        # Check for short setup
        elif (short_rr >= min_rr_ratio and
              current['trend_strength'] in ['strong_bearish', 'weak_bearish'] and
              current['volatility_regime'] != 'extreme'):
            
            df.loc[df.index[i], 'trade_entry'] = -1
            df.loc[df.index[i], 'trade_type'] = 'short'
            df.loc[df.index[i], 'trade_rr'] = short_rr
            
            open_positions.append({
                'entry_idx': i,
                'type': 'short',
                'entry_price': current['close'],
                'sl': short_sl,
                'tp': short_tp
            })
        
        # Check open positions for exits
        for pos in open_positions[:]:
            if pos['type'] == 'long':
                if current['low'] <= pos['sl']:  # Stop loss hit
                    df.loc[df.index[i], 'trade_exit'] = 1
                    df.loc[df.index[pos['entry_idx']], 'trade_result'] = 'loss'
                    open_positions.remove(pos)
                elif current['high'] >= pos['tp']:  # Take profit hit
                    df.loc[df.index[i], 'trade_exit'] = 1
                    df.loc[df.index[pos['entry_idx']], 'trade_result'] = 'win'
                    open_positions.remove(pos)
            else:  # Short position
                if current['high'] >= pos['sl']:  # Stop loss hit
                    df.loc[df.index[i], 'trade_exit'] = 1
                    df.loc[df.index[pos['entry_idx']], 'trade_result'] = 'loss'
                    open_positions.remove(pos)
                elif current['low'] <= pos['tp']:  # Take profit hit
                    df.loc[df.index[i], 'trade_exit'] = 1
                    df.loc[df.index[pos['entry_idx']], 'trade_result'] = 'win'
                    open_positions.remove(pos)
    
    logger.log(f"Identified trades: {len(df[df['trade_entry'] != 0])}")
    logger.log(f"Win rate: {len(df[df['trade_result'] == 'win']) / len(df[df['trade_result'].notna()]) * 100:.1f}%")
    
    return df

def analyze_perfect_trades(df: pd.DataFrame) -> Dict[str, any]:
    """
    Analyze identified perfect trades.
    
    Args:
        df: DataFrame with trade labels
        
    Returns:
        Dictionary with trade analysis metrics
    """
    # Get all trades
    trades = df[df['trade_entry'] != 0].copy()
    
    # Calculate basic metrics
    total_trades = len(trades)
    if total_trades == 0:
        return {
            'total_trades': 0,
            'win_rate': 0,
            'avg_rr': 0,
            'profit_factor': 0,
            'max_consecutive_losses': 0,
            'avg_bars_in_trade': 0,
            'best_setup': None
        }
    
    wins = len(trades[trades['trade_result'] == 'win'])
    win_rate = wins / total_trades
    
    # Calculate consecutive losses
    results = trades['trade_result'].map({'win': 1, 'loss': 0}).values
    cons_losses = 0
    current_losses = 0
    for result in results:
        if result == 0:
            current_losses += 1
            cons_losses = max(cons_losses, current_losses)
        else:
            current_losses = 0
    
    # Calculate average bars in trade
    trades['exit_idx'] = trades.index.map(lambda x: df[df.index > x]['trade_exit'].ne(0).idxmax())
    trades['bars_in_trade'] = (trades['exit_idx'] - trades.index).dt.total_seconds() / pd.Timedelta(minutes=1)
    
    # Analyze setups
    setups = []
    for _, trade in trades.iterrows():
        setup = {
            'type': trade['trade_type'],
            'trend': trade['trend_strength'],
            'regime': trade['volatility_regime'],
            'result': trade['trade_result']
        }
        setups.append(setup)
    
    # Find best setup
    setup_results = pd.DataFrame(setups)
    best_setup = (
        setup_results.groupby(['type', 'trend', 'regime'])
        .agg({'result': lambda x: (x == 'win').mean()})
        .sort_values('result', ascending=False)
        .iloc[0]
    )
    
    return {
        'total_trades': total_trades,
        'win_rate': win_rate,
        'avg_rr': trades['trade_rr'].mean(),
        'profit_factor': len(trades[trades['trade_result'] == 'win']) / len(trades[trades['trade_result'] == 'loss']) if len(trades[trades['trade_result'] == 'loss']) > 0 else float('inf'),
        'max_consecutive_losses': cons_losses,
        'avg_bars_in_trade': trades['bars_in_trade'].mean(),
        'best_setup': {
            'type': best_setup.name[0],
            'trend': best_setup.name[1],
            'regime': best_setup.name[2],
            'win_rate': best_setup['result']
        }
    }
