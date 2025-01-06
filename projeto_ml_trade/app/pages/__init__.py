"""
Pages package for ML Trade application.
"""
from .base import Page
from .backtest_page import BacktestPage
from .download_page import DownloadPage
from .enrich_page import EnrichPage
from .storage_config_page import StorageConfigPage

__all__ = [
    # Base page
    'Page',
    
    # Application pages
    'BacktestPage',
    'DownloadPage',
    'EnrichPage',
    'StorageConfigPage'
]
