"""
Performance metrics calculation utilities.
"""
import numpy as np
import pandas as pd
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

def calculate_sharpe_ratio(returns: np.ndarray, risk_free_rate: float = 0.0) -> float:
    """Calculate Sharpe Ratio based on returns.
    
    Args:
        returns: Array of returns
        risk_free_rate: Risk-free rate (default: 0.0)
        
    Returns:
        float: Sharpe ratio
    """
    mean_return = np.mean(returns)
    std_dev = np.std(returns)
    if std_dev == 0:
        return 0
    return (mean_return - risk_free_rate) / std_dev

def calculate_drawdown(balance_history: np.ndarray) -> float:
    """Calculate maximum drawdown from balance history.
    
    Args:
        balance_history: Array of account balance values
        
    Returns:
        float: Maximum drawdown as a percentage
    """
    peak = np.maximum.accumulate(balance_history)
    drawdown = (peak - balance_history) / peak
    return np.max(drawdown)

def calculate_metrics(df: pd.DataFrame, 
                     initial_capital: float = 10000.0,
                     risk_free_rate: float = 0.0) -> Dict[str, Any]:
    """Calculate comprehensive performance metrics.
    
    Args:
        df: DataFrame with trade results
        initial_capital: Initial capital amount
        risk_free_rate: Risk-free rate for Sharpe ratio
        
    Returns:
        Dictionary containing performance metrics
    """
    try:
        # Validate input
        required_cols = ['trade_entry', 'trade_result', 'trade_rr']
        if not all(col in df.columns for col in required_cols):
            raise ValueError("Missing required columns for metrics calculation")
        
        # Get trades
        trades = df[df['trade_entry'] != 0].copy()
        if len(trades) == 0:
            logger.warning("No trades found for metrics calculation")
            return {
                'total_trades': 0,
                'win_rate': 0.0,
                'profit_factor': 0.0,
                'avg_win': 0.0,
                'avg_loss': 0.0,
                'max_drawdown': 0.0,
                'sharpe_ratio': 0.0,
                'risk_reward_ratio': 0.0,
                'expectancy': 0.0,
                'total_return': 0.0
            }
        
        # Calculate basic metrics
        wins = trades[trades['trade_result'] == 'win']
        losses = trades[trades['trade_result'] == 'loss']
        
        total_trades = len(trades)
        win_rate = len(wins) / total_trades if total_trades > 0 else 0
        
        # Calculate returns
        position_size = initial_capital * 0.1  # 10% per trade
        win_returns = [position_size * (trade['trade_rr'] * 0.5) for _, trade in wins.iterrows()]
        loss_returns = [-position_size for _ in losses.iterrows()]
        
        total_wins = sum(win_returns) if win_returns else 0
        total_losses = abs(sum(loss_returns)) if loss_returns else 0
        
        # Calculate profit factor and averages
        profit_factor = total_wins / total_losses if total_losses > 0 else float('inf')
        avg_win = np.mean(win_returns) if win_returns else 0
        avg_loss = abs(np.mean(loss_returns)) if loss_returns else 0
        
        # Calculate returns array for Sharpe ratio
        all_returns = win_returns + loss_returns
        returns_array = np.array(all_returns) / initial_capital
        
        # Calculate balance history for drawdown
        balance = initial_capital
        balance_history = [balance]
        for ret in all_returns:
            balance += ret
            balance_history.append(balance)
        
        # Calculate risk-reward and expectancy
        risk_reward = avg_win / avg_loss if avg_loss > 0 else float('inf')
        expectancy = (win_rate * avg_win) - ((1 - win_rate) * avg_loss)
        
        metrics = {
            'total_trades': total_trades,
            'win_rate': win_rate * 100,
            'profit_factor': profit_factor,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'max_drawdown': calculate_drawdown(np.array(balance_history)) * 100,
            'sharpe_ratio': calculate_sharpe_ratio(returns_array, risk_free_rate),
            'risk_reward_ratio': risk_reward,
            'expectancy': expectancy,
            'total_return': ((balance - initial_capital) / initial_capital) * 100
        }
        
        logger.info("Performance metrics calculated successfully")
        return metrics
        
    except Exception as e:
        logger.error(f"Error calculating metrics: {str(e)}")
        raise
