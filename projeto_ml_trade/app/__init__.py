"""
ML Trade application package.
"""
from .components.base import UIComponent
from .components.data import DataSourceSelector
from .components.storage import StorageSelector
from .components.backtest import (
    ChartComponent,
    ResultsDisplay,
    StrategyParams
)

from .pages.base import Page
from .pages.backtest_page import BacktestPage
from .pages.download_page import DownloadPage
from .pages.enrich_page import EnrichPage
from .pages.storage_config_page import StorageConfigPage

from .managers.download_manager import DownloadManager
from .managers.enrich_manager import EnrichManager
from .managers.storage_manager import StorageManager

from .utils.binance_client import BinanceClient
from .utils.data_enricher import DataEnricher
from .utils.file_utils import FileUtils
from .utils.preprocessor import DataPreprocessor

__all__ = [
    # Base components
    'UIComponent',
    'Page',
    
    # Components
    'DataSourceSelector',
    'StorageSelector',
    'ChartComponent',
    'ResultsDisplay',
    'StrategyParams',
    
    # Pages
    'BacktestPage',
    'DownloadPage',
    'EnrichPage',
    'StorageConfigPage',
    
    # Managers
    'DownloadManager',
    'EnrichManager',
    'StorageManager',
    
    # Utils
    'BinanceClient',
    'DataEnricher',
    'FileUtils',
    'DataPreprocessor'
]
