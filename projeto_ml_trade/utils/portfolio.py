"""
Portfolio analysis and metrics calculation.
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from utils.logging_helper import LoggingHelper

def calculate_portfolio_metrics(df: pd.DataFrame,
                              initial_capital: float = 10000.0,
                              position_size: float = 0.1,
                              max_positions: int = 4) -> Dict[str, any]:
    """
    Calculate portfolio performance metrics from trade results.
    
    Args:
        df: DataFrame with trade labels and results
        initial_capital: Starting capital amount
        position_size: Position size as fraction of capital
        max_positions: Maximum number of concurrent positions
        
    Returns:
        Dictionary containing portfolio metrics
    """
    logger = LoggingHelper()
    
    # Get all trades
    trades = df[df['trade_entry'] != 0].copy()
    
    if len(trades) == 0:
        return {
            'total_return': 0.0,
            'max_drawdown': 0.0,
            'sharpe_ratio': 0.0,
            'win_rate': 0.0,
            'profit_factor': 0.0,
            'avg_win': 0.0,
            'avg_loss': 0.0,
            'max_consecutive_losses': 0,
            'max_consecutive_wins': 0,
            'total_trades': 0,
            'avg_trade_duration': 0.0,
            'capital_curve': pd.Series(dtype=float)
        }
    
    # Initialize portfolio tracking
    capital = initial_capital
    capital_curve = [capital]
    position_value = capital * position_size
    
    # Track consecutive wins/losses
    max_cons_wins = 0
    max_cons_losses = 0
    current_cons_wins = 0
    current_cons_losses = 0
    
    # Track returns
    returns = []
    trade_durations = []
    wins = []
    losses = []
    
    # Process each trade
    for i, trade in trades.iterrows():
        # Calculate trade return
        if trade['trade_result'] == 'win':
            trade_return = position_value * (trade['trade_rr'] * 0.5)  # Assume 50% of theoretical R:R
            wins.append(trade_return)
            current_cons_wins += 1
            current_cons_losses = 0
            max_cons_wins = max(max_cons_wins, current_cons_wins)
        else:  # Loss
            trade_return = -position_value
            losses.append(trade_return)
            current_cons_losses += 1
            current_cons_wins = 0
            max_cons_losses = max(max_cons_losses, current_cons_losses)
        
        # Update capital
        capital += trade_return
        capital_curve.append(capital)
        returns.append(trade_return / position_value)  # Percentage return
        
        # Calculate trade duration
        exit_idx = df[df.index > i]['trade_exit'].ne(0).idxmax()
        duration = (exit_idx - i).total_seconds() / 3600  # Hours
        trade_durations.append(duration)
    
    # Convert to numpy arrays for calculations
    returns = np.array(returns)
    capital_curve = np.array(capital_curve)
    
    # Calculate drawdown
    peak = np.maximum.accumulate(capital_curve)
    drawdown = (capital_curve - peak) / peak
    max_drawdown = abs(drawdown.min())
    
    # Calculate Sharpe ratio (assuming risk-free rate = 0)
    if len(returns) > 1:
        sharpe = np.sqrt(252) * (returns.mean() / returns.std())
    else:
        sharpe = 0.0
    
    # Calculate profit factor
    total_wins = sum(wins) if wins else 0
    total_losses = abs(sum(losses)) if losses else 0
    profit_factor = total_wins / total_losses if total_losses > 0 else float('inf')
    
    metrics = {
        'total_return': (capital - initial_capital) / initial_capital * 100,
        'max_drawdown': max_drawdown * 100,
        'sharpe_ratio': sharpe,
        'win_rate': len(wins) / len(trades) * 100,
        'profit_factor': profit_factor,
        'avg_win': np.mean(wins) if wins else 0,
        'avg_loss': abs(np.mean(losses)) if losses else 0,
        'max_consecutive_losses': max_cons_losses,
        'max_consecutive_wins': max_cons_wins,
        'total_trades': len(trades),
        'avg_trade_duration': np.mean(trade_durations),
        'capital_curve': pd.Series(capital_curve, index=[trades.index[0]] + list(trades.index))
    }
    
    logger.log(f"Portfolio Analysis:")
    logger.log(f"Total Return: {metrics['total_return']:.1f}%")
    logger.log(f"Max Drawdown: {metrics['max_drawdown']:.1f}%")
    logger.log(f"Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
    logger.log(f"Win Rate: {metrics['win_rate']:.1f}%")
    logger.log(f"Profit Factor: {metrics['profit_factor']:.2f}")
    
    return metrics
