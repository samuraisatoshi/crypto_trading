"""
Backtester implementation.
"""
from typing import Dict, Any, List, Generator, Tuple, Optional
import pandas as pd

from utils.logging_helper import LoggingHelper
from .account import Account
from .trading_orders import Order
from strategies import PatternStrategy, PatternOrchestrator, EMATrendStrategy

class Backtester:
    """Backtester class for running trading strategies."""
    
    def __init__(
        self,
        df: pd.DataFrame,
        strategy_id: str,
        initial_balance: float = 10000,
        risk_per_trade: float = 0.02,
        max_positions: int = 3,
        min_confidence: float = 0.7,
        strategy_params: Optional[Dict[str, Any]] = None
    ):
        """Initialize backtester."""
        self.df = df.copy()
        self.strategy_id = strategy_id
        self.strategy_params = strategy_params or {}
        
        # Initialize account
        self.account = Account(
            initial_balance=initial_balance,
            risk_per_trade=risk_per_trade,
            max_positions=max_positions
        )
        
        # Initialize strategy
        self.strategy = self._create_strategy(min_confidence)
        
        # Store results
        self.results = []
        
    def _create_strategy(self, min_confidence: float) -> Any:
        """Create strategy instance based on strategy type."""
        LoggingHelper.log(f"Creating strategy: {self.strategy_id}")
        LoggingHelper.log(f"Strategy params: {self.strategy_params}")
        
        if self.strategy_id == 'patterns':
            if 'pattern_types' in self.strategy_params:
                return PatternOrchestrator(
                    pattern_types=self.strategy_params['pattern_types'],
                    min_confidence=min_confidence
                )
            return PatternStrategy(min_confidence=min_confidence)
            
        elif self.strategy_id == 'ema_trend':
            return EMATrendStrategy(
                ema21_period=self.strategy_params.get('ema21_period', 21),
                ema55_period=self.strategy_params.get('ema55_period', 55),
                ema80_period=self.strategy_params.get('ema80_period', 80),
                ema100_period=self.strategy_params.get('ema100_period', 100),
                slope_window=self.strategy_params.get('slope_window', 10),
                confidence_threshold=self.strategy_params.get('confidence_threshold', 0.5),
                percentile_window=self.strategy_params.get('percentile_window', 100)
            )
        
        raise ValueError(f"Unknown strategy type: {self.strategy_id}")
    
    def run_backtest_generator(self) -> Generator[Tuple[List[Dict], List[Dict]], None, None]:
        """Run backtest and yield signals and patterns."""
        try:
            LoggingHelper.log("Starting backtest")
            LoggingHelper.log(f"Data range: {self.df.index[0]} to {self.df.index[-1]}")
            
            for i in range(len(self.df)):
                current_data = self.df.iloc[:i+1]
                current_bar = current_data.iloc[-1]
                
                # Generate signals
                signals = self.strategy.generate_signals(current_data)
                patterns = []  # Store any detected patterns
                
                # Process signals
                if signals:
                    for signal in signals:
                        # Create order
                        order = Order(
                            type=signal['type'],
                            price=signal['price'],
                            confidence=signal.get('confidence', 1.0)
                        )
                        
                        # Execute order
                        if self.account.can_place_order(order):
                            self.account.place_order(order)
                            
                            # Store trade result
                            self.results.append({
                                'date': current_bar.name,
                                'type': order.type,
                                'price': order.price,
                                'confidence': order.confidence,
                                'pattern': signal.get('pattern', None)
                            })
                            
                            # Store pattern if available
                            if 'pattern_data' in signal:
                                patterns.append(signal['pattern_data'])
                
                # Check for exits
                for position in self.account.positions:
                    if self.strategy.should_exit(current_data, i, position):
                        self.account.close_position(position, current_bar['close'])
                
                yield signals, patterns
                
            LoggingHelper.log("Backtest complete")
            LoggingHelper.log(f"Total trades: {len(self.results)}")
            
        except Exception as e:
            LoggingHelper.log(f"Error during backtest: {str(e)}")
            raise
    
    def get_results(self) -> List[Dict[str, Any]]:
        """Get backtest results."""
        return self.results
