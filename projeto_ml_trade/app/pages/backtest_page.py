"""
Backtest page.
"""
import streamlit as st
import pandas as pd
from typing import Dict, Any
from datetime import datetime
import os

from utils.logging_helper import LoggingHelper
from backtester.backtester import Backtester
from app.components.backtest import ChartComponent
from app.components.backtest.results_display import ResultsDisplay
from app.components.backtest.strategy_params import get_strategy_params
from app.managers import StorageManager
from .base import Page

def get_pattern_window(df: pd.DataFrame, pattern: Dict, window_size: int = 20) -> pd.DataFrame:
    """Get window of data around pattern."""
    try:
        # Get pattern range
        start_idx = pattern.get('start_idx', 0)
        end_idx = pattern.get('end_idx', len(df)-1)
        
        # Add context around pattern
        window_start = max(0, start_idx - window_size)
        window_end = min(len(df), end_idx + window_size)
        
        return df.iloc[window_start:window_end].copy()
        
    except Exception as e:
        print(f"Error getting pattern window: {str(e)}")
        return df

class BacktestPage(Page):
    """Backtest page."""
    
    def __init__(self):
        """Initialize backtest page."""
        super().__init__()
        self.title = "Backtest"
    
    def render(self):
        """Render backtest page."""
        st.title(self.title)
        
        # Initialize storage manager
        storage_manager = StorageManager()
        
        # Storage selection
        from app.components.storage import render_storage_selector
        storage_info = render_storage_selector()
        storage_manager.set_storage(storage_info)
        
        # Data source selection
        from app.components.data import render_data_source_selector
        df = render_data_source_selector(storage_manager)
        
        if df is None:
            st.warning("Please select a dataset to backtest")
            return
        
        # Strategy selection
        strategy_id = st.selectbox(
            "Strategy",
            options=['patterns', 'ema_trend'],
            format_func=lambda x: x.title().replace('_', ' ')
        )
        
        # Get strategy parameters
        strategy_params = get_strategy_params(strategy_id)
        
        # Extract symbol and timeframe from DataFrame
        symbol = df['symbol'].iloc[0] if 'symbol' in df else 'unknown'
        timeframe = df['timeframe'].iloc[0] if 'timeframe' in df else 'unknown'
        
        # Show data info
        st.subheader("Data Info")
        st.write(f"Symbol: {symbol}")
        st.write(f"Timeframe: {timeframe}")
        st.write(f"Total rows: {len(df)}")
        st.write(f"Date range: {df.index[0]} to {df.index[-1]}")
        
        # Risk parameters
        col1, col2 = st.columns(2)
        with col1:
            initial_balance = st.number_input(
                "Initial Balance",
                min_value=100.0,
                value=10000.0,
                step=1000.0
            )
            risk_per_trade = st.number_input(
                "Risk Per Trade (%)",
                min_value=0.1,
                max_value=10.0,
                value=2.0,
                step=0.1
            ) / 100
        
        with col2:
            max_positions = st.number_input(
                "Max Positions",
                min_value=1,
                max_value=10,
                value=3
            )
            min_confidence = st.number_input(
                "Min Pattern Confidence",
                min_value=0.5,
                max_value=1.0,
                value=0.7,
                step=0.1
            )
        
        # Run backtest button
        if st.button("Run Backtest"):
            try:
                # Initialize components
                chart_component = ChartComponent()
                
                # Initialize backtester
                backtester = Backtester(
                    df=df,
                    strategy_id=strategy_id,
                    initial_balance=initial_balance,
                    risk_per_trade=risk_per_trade,
                    max_positions=max_positions,
                    min_confidence=min_confidence,
                    strategy_params=strategy_params
                )
                
                # Create progress bar
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # Initialize pattern counts
                pattern_counts = {}
                chart_sequence = 0
                
                # Run backtest
                total_bars = len(df)
                backtest_generator = backtester.run_backtest_generator()
                
                try:
                    for i, (signals, patterns) in enumerate(backtest_generator):
                        # Update progress
                        progress = (i + 1) / total_bars
                        progress_bar.progress(progress)
                        
                        # Update status
                        current_time = df.index[i]
                        status_text.text(f"Processing bar {i+1}/{total_bars} ({current_time})")
                        
                        # Save chart if patterns detected
                        if patterns:
                            try:
                                # Get window around pattern
                                window_df = get_pattern_window(df.iloc[:i+1], patterns[0])
                                
                                # Save chart
                                chart_component.save_chart(
                                    window_df,
                                    patterns,
                                    symbol,
                                    timeframe,
                                    chart_sequence
                                )
                                chart_sequence += 1
                                
                                # Update pattern counts
                                for pattern in patterns:
                                    pattern_type = pattern['type']
                                    pattern_counts[pattern_type] = pattern_counts.get(pattern_type, 0) + 1
                                    
                            except Exception as e:
                                print(f"Error saving pattern chart: {str(e)}")
                                continue
                    
                    # Ensure generator completes
                    try:
                        while True:
                            next(backtest_generator)
                    except StopIteration:
                        pass
                        
                except Exception as e:
                    st.error(f"Error during backtest: {str(e)}")
                    st.exception(e)
                    return
                
                # Clear progress indicators
                progress_bar.empty()
                status_text.empty()
                
                # Get results after generator completes
                results = backtester.get_results()
                
                if results:
                    # Display results matrix
                    ResultsDisplay.display_results_matrix(results, pattern_counts)
                    
                    # Create trade history chart
                    chart_component.create_trade_chart(
                        df,
                        results,
                        f"trade_history_{symbol}_{timeframe}.jpg"
                    )
                    
                    # Show chart directory info
                    st.info(
                        f"Charts have been saved to data/charts/:\n\n"
                        f"- Pattern charts: {chart_sequence} files\n"
                        f"- Trade history: trade_history_{symbol}_{timeframe}.jpg"
                    )
                else:
                    st.error("Backtest failed. Check logs for details.")
                
            except Exception as e:
                st.error(f"Error running backtest: {str(e)}")
                st.exception(e)
