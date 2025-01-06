"""
Backtesting orchestrator.
"""
from typing import Dict, List, Any, Optional, Callable
import pandas as pd
from datetime import datetime
from utils.logging_helper import LoggingHelper
from .data_handler import DataHandler
from .account import Account
from .risk_manager import RiskManager

class BacktestOrchestrator:
    """Orchestrates backtesting process."""
    
    def __init__(self,
                df: pd.DataFrame,
                initial_balance: float = 10000,
                risk_per_trade: float = 0.02,
                max_trades: int = 1,
                progress_callback: Optional[Callable] = None):
        """
        Initialize backtesting orchestrator.
        
        Args:
            df: DataFrame with OHLCV data
            initial_balance: Initial account balance
            risk_per_trade: Maximum risk per trade (0.0 to 1.0)
            max_trades: Maximum concurrent trades
            progress_callback: Optional callback for progress updates
        """
        self.data_handler = DataHandler(df)
        self.account = Account(initial_balance)
        self.risk_manager = RiskManager(risk_per_trade, max_trades)
        self.progress_callback = progress_callback
        
        LoggingHelper.log(f"Initialized BacktestOrchestrator with parameters:")
        LoggingHelper.log(f"Initial Balance: {initial_balance}")
        LoggingHelper.log(f"Risk Per Trade: {risk_per_trade:.1%}")
        LoggingHelper.log(f"Max Trades: {max_trades}")
    
    def run_backtest(self, strategy: Any) -> Dict[str, Any]:
        """
        Run backtest with given strategy.
        
        Args:
            strategy: Trading strategy instance
            
        Returns:
            Dict with backtest results
        """
        try:
            # Reset components
            self.data_handler.reset()
            self.account.reset()
            self.risk_manager.reset()
            
            trades = []
            last_update = datetime.now()
            update_interval = pd.Timedelta(seconds=1)
            
            # Process each candle
            while True:
                # Get current data
                current_data = self.data_handler.get_current_data()
                current_candle = self.data_handler.get_current_candle()
                
                # Update progress
                current_time = datetime.now()
                if self.progress_callback and current_time - last_update > update_interval:
                    progress = self.data_handler.get_progress()
                    timestamp = self.data_handler.get_current_timestamp()
                    self.progress_callback(progress * 100, timestamp, {
                        'equity': self.account.equity,
                        'trades': len(trades)
                    })
                    last_update = current_time
                
                # Check for exit signals
                for position in self.account.positions:
                    if strategy.should_exit(current_data, self.data_handler.current_idx, position):
                        # Record trade
                        trades.append({
                            'entry_time': position['entry_time'],
                            'exit_time': current_candle.name,
                            'type': position['type'],
                            'entry_price': position['entry_price'],
                            'exit_price': current_candle['close'],
                            'size': position['size'],
                            'pnl': position['pnl']
                        })
                        
                        # Close position
                        self.account.execute_order({
                            'type': 'sell' if position['type'] == 'long' else 'buy',
                            'price': current_candle['close'],
                            'size': position['size'],
                            'time': current_candle.name
                        })
                
                # Generate signals
                signals = strategy.generate_signals(current_data)
                
                # Process signals
                for signal in signals:
                    # Check risk limits
                    if not self.risk_manager.check_limits(self.account, signal):
                        continue
                    
                    # Calculate position size
                    size = strategy.calculate_position_size(current_data, signal)
                    size = self.risk_manager.adjust_position_size(
                        size,
                        signal['price'],
                        self.account.equity
                    )
                    
                    # Execute order
                    self.account.execute_order({
                        'type': signal['type'],
                        'price': signal['price'],
                        'size': size,
                        'time': current_candle.name
                    })
                
                # Move to next candle
                if not self.data_handler.advance():
                    break
            
            # Calculate metrics
            metrics = self._calculate_metrics(trades)
            
            # Final progress update
            if self.progress_callback:
                self.progress_callback(100, self.data_handler.get_current_timestamp(), {
                    'equity': self.account.equity,
                    'trades': len(trades),
                    'metrics': metrics
                })
            
            return {
                'trades': trades,
                'metrics': metrics,
                'equity': self.account.equity,
                'initial_balance': self.account.initial_balance
            }
            
        except Exception as e:
            LoggingHelper.log(f"Error in backtest: {str(e)}")
            raise
    
    def _calculate_metrics(self, trades: List[Dict]) -> Dict[str, float]:
        """Calculate backtest performance metrics."""
        if not trades:
            return {
                'total_trades': 0,
                'win_rate': 0.0,
                'profit_factor': 0.0,
                'avg_win': 0.0,
                'avg_loss': 0.0,
                'max_drawdown': 0.0,
                'sharpe_ratio': 0.0,
                'total_return': 0.0
            }
        
        # Basic metrics
        total_trades = len(trades)
        winning_trades = len([t for t in trades if t['pnl'] > 0])
        win_rate = winning_trades / total_trades
        
        # Profit metrics
        gross_profits = sum(t['pnl'] for t in trades if t['pnl'] > 0)
        gross_losses = abs(sum(t['pnl'] for t in trades if t['pnl'] < 0))
        profit_factor = gross_profits / gross_losses if gross_losses else float('inf')
        
        # Average trade metrics
        winning_trades_list = [t['pnl'] for t in trades if t['pnl'] > 0]
        losing_trades_list = [t['pnl'] for t in trades if t['pnl'] < 0]
        avg_win = sum(winning_trades_list) / len(winning_trades_list) if winning_trades_list else 0
        avg_loss = sum(losing_trades_list) / len(losing_trades_list) if losing_trades_list else 0
        
        # Returns and drawdown
        equity_curve = []
        equity = self.account.initial_balance
        max_equity = equity
        max_drawdown = 0
        
        for trade in trades:
            equity += trade['pnl']
            equity_curve.append(equity)
            max_equity = max(max_equity, equity)
            drawdown = (max_equity - equity) / max_equity
            max_drawdown = max(max_drawdown, drawdown)
        
        total_return = (equity - self.account.initial_balance) / self.account.initial_balance
        
        # Risk-adjusted returns
        if len(equity_curve) > 1:
            returns = pd.Series(equity_curve).pct_change().dropna()
            sharpe_ratio = returns.mean() / returns.std() * (252 ** 0.5) if returns.std() != 0 else 0
        else:
            sharpe_ratio = 0
        
        return {
            'total_trades': total_trades,
            'win_rate': win_rate,
            'profit_factor': profit_factor,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'max_drawdown': max_drawdown,
            'sharpe_ratio': sharpe_ratio,
            'total_return': total_return
        }
