"""
Download data page component.
"""
import streamlit as st
from datetime import datetime
from typing import List, Optional, Dict, Any
from app.managers import DownloadManager
from app.components.storage import StorageSelector
from app.pages.base import Page

class DownloadPage(Page):
    """Page component for downloading data."""
    
    TIMEFRAMES = ['1m', '5m', '15m', '1h', '4h', '1d']
    DEFAULT_TIMEFRAME = '15m'
    DEFAULT_START_DATE = datetime(2017, 10, 1).date()
    DEFAULT_END_DATE = datetime(2024, 12, 31).date()
    DEFAULT_SYMBOLS = "BTCUSDT\nETHUSDT\nBNBUSDT"
    
    def __init__(self):
        """Initialize download page."""
        super().__init__()
        self.download_manager = DownloadManager()
        self.storage_selector = StorageSelector()
    
    def render(self):
        """Render download page content."""
        self.render_title("Download Data")
        
        # Format selection
        data_format = self._render_format_selection()
        
        # Symbol input
        symbols = self._render_symbol_input(data_format)
        
        # Timeframe and date range
        timeframe = self._render_timeframe_selection()
        start_date, end_date = self._render_date_range()
        
        # Storage selection
        storage_info = self.storage_selector.render()
        
        # Download button
        if st.button("Download Data"):
            self._handle_download(
                data_format,
                symbols,
                timeframe,
                start_date,
                end_date,
                storage_info
            )
    
    def _render_format_selection(self) -> str:
        """Render data format selection.
        
        Returns:
            Selected format
        """
        return st.radio(
            "Data Format",
            options=['Native', 'FinRL'],
            help="Native: Single asset OHLCV format\nFinRL: Multi-asset format for reinforcement learning"
        )
    
    def _render_symbol_input(self, data_format: str) -> List[str]:
        """Render symbol input based on format.
        
        Args:
            data_format: Selected data format
            
        Returns:
            List of symbols
        """
        if data_format == 'Native':
            symbol = st.text_input("Symbol", value="BTCUSDT")
            return [symbol]
        else:
            symbols_text = st.text_area(
                "Symbols (one per line)",
                value=self.DEFAULT_SYMBOLS,
                help="Enter multiple symbols, one per line"
            )
            return [s.strip() for s in symbols_text.split('\n') if s.strip()]
    
    def _render_timeframe_selection(self) -> str:
        """Render timeframe selection.
        
        Returns:
            Selected timeframe
        """
        return st.selectbox(
            "Timeframe",
            options=self.TIMEFRAMES,
            index=self.TIMEFRAMES.index(self.DEFAULT_TIMEFRAME),
            help="Select data timeframe"
        )
    
    def _render_date_range(self) -> tuple:
        """Render date range selection.
        
        Returns:
            Tuple of (start_date, end_date)
        """
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input(
                "Start Date",
                value=self.DEFAULT_START_DATE,
                help="Data download start date"
            )
        with col2:
            end_date = st.date_input(
                "End Date",
                value=self.DEFAULT_END_DATE,
                help="Data download end date"
            )
        return start_date, end_date
    
    def _handle_download(
        self,
        data_format: str,
        symbols: List[str],
        timeframe: str,
        start_date: datetime,
        end_date: datetime,
        storage_info: Dict[str, Any]
    ):
        """Handle data download process.
        
        Args:
            data_format: Selected data format
            symbols: List of symbols to download
            timeframe: Selected timeframe
            start_date: Start date
            end_date: End date
            storage_info: Storage configuration
        """
        try:
            # Configure storage
            self.download_manager.set_storage(storage_info)
            
            # Download data
            self.show_progress("Downloading data...")
            if data_format == 'Native':
                result = self.download_manager.download_data(
                    symbol=symbols[0],
                    timeframe=timeframe,
                    start_date=start_date,
                    end_date=end_date,
                    format='native'
                )
            else:
                result = self.download_manager.download_multi_symbol(
                    symbols=symbols,
                    timeframe=timeframe,
                    start_date=start_date,
                    end_date=end_date
                )
            
            if result:
                # Store in session state
                st.session_state['data'] = result['df']
                
                # Show success
                self.show_success(f"Data saved to {result['filename']}")
                
                # Show preview and info
                self.show_data_preview(result['df'])
                self.show_data_info({
                    'Total Rows': result['info']['rows'],
                    'Date Range': f"{result['info']['start_date']} to {result['info']['end_date']}",
                    **(
                        {'Symbols': ', '.join(result['info']['symbols'])}
                        if data_format == 'FinRL' else {}
                    )
                })
            else:
                self.show_error("No data found for the selected parameters")
                
        except Exception as e:
            self.show_error("Error downloading data", e)
            st.exception(e)

def render():
    """Render download page."""
    page = DownloadPage()
    page.render()
