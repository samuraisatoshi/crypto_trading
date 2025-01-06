"""
ML Trade Project
A machine learning-based cryptocurrency trading system
"""
from .app_streamlit import main
from .strategies import BaseStrategy
from .backtester import Backtester, AccountBalance, TradingOrders
from .utils.data import DataProvider, DataFormatter, DataMerger
from .utils.binance_client import BinanceClient
from .utils.indicators import calculate_indicators
from .utils.market_regime import MarketRegimeAnalyzer
from .utils.volatility_metrics import VolatilityAnalyzer

__version__ = '0.1.0'

__all__ = [
    # Core functionality
    'main',
    'BaseStrategy',
    'Backtester',
    'AccountBalance',
    'TradingOrders',
    
    # Data utilities
    'DataProvider',
    'DataFormatter',
    'DataMerger',
    'BinanceClient',
    
    # Analysis utilities
    'calculate_indicators',
    'MarketRegimeAnalyzer',
    'VolatilityAnalyzer'
]
