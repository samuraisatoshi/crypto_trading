"""
Enrich data page.
"""
import streamlit as st
from datetime import datetime
import os
import pandas as pd

from app.managers import EnrichManager
from app.components.storage import render_storage_selector
from utils.logging_helper import LoggingHelper
from .base import Page

class EnrichPage(Page):
    """Enrich data page."""
    
    def __init__(self):
        """Initialize enrich page."""
        super().__init__()
        self.title = "Enrich Data"
    
    def render(self):
        """Render enrich page."""
        st.title(self.title)
        
        # Initialize manager in session state if needed
        if 'enrich_manager' not in st.session_state:
            st.session_state.enrich_manager = EnrichManager()
        
        # Storage selection
        storage_info = render_storage_selector()
        st.session_state.enrich_manager.set_storage(storage_info)
        
        # Data source selection
        from app.components.data import render_data_source_selector
        df = render_data_source_selector(st.session_state.enrich_manager.storage)
        
        if df is not None:
            st.session_state['data'] = df
            
            # Show data preview
            st.subheader("Data Preview")
            st.dataframe(df.head())
            
            # Show data info
            st.subheader("Data Info")
            st.write(f"Total rows: {len(df)}")
            st.write(f"Date range: {df.index[0]} to {df.index[-1]}")
            st.write("Available columns:", ", ".join(df.columns))
            
            # Enrichment options
            st.subheader("Select Enrichments")
            
            enrichments = []
            
            # Technical indicators in two columns
            col1, col2 = st.columns(2)
            
            # Moving Averages Configuration
            with col1:
                with st.container():
                    st.subheader("Moving Averages")
                    if st.checkbox("Enable Moving Averages", key="enable_ma"):
                        ma_type = st.radio(
                            "Moving Average Type",
                            options=['SMA', 'EMA', 'Both'],
                            horizontal=True
                        )
                        
                        ma_periods = st.text_input(
                            "Moving Average Periods",
                            value="8,21,50,80,100",
                            help="Enter periods separated by commas (e.g., 8,21,50,80,100)"
                        )
                        
                        # Output type selection
                        output_options = {
                            'Value': 'Value',
                            'Price Distance %': 'Price Distance %',
                            'Both': 'Both'
                        }
                        ma_output = st.radio(
                            "Output Type",
                            options=list(output_options.keys()),
                            format_func=lambda x: output_options[x],
                            horizontal=True,
                            help="Value: MA values, Distance: % difference from close price",
                            key="ma_output"
                        )
                        
                        # Debug output
                        LoggingHelper.log(f"Selected output type: {ma_output}")
                        LoggingHelper.log(f"Output value: {output_options[ma_output]}")
                        
                        with st.expander("Slope Configuration"):
                            include_slope = st.checkbox("Include Slope", value=True)
                            if include_slope:
                                slope_periods = st.number_input(
                                    "Slope Window Size",
                                    min_value=2,
                                    max_value=20,
                                    value=5,
                                    help="Number of candles to calculate slope"
                                )
                        
                        # Add moving averages to enrichments with config
                        if ma_periods.strip():
                            try:
                                periods = [int(p.strip()) for p in ma_periods.split(',')]
                                ma_config = {
                                    'type': ma_type,
                                    'periods': periods,
                                    'output': output_options[ma_output],  # Use the mapped value
                                    'slope': {
                                        'enabled': include_slope,
                                        'window': slope_periods if include_slope else None
                                    }
                                }
                                LoggingHelper.log(f"Moving averages config: {ma_config}")
                                enrichments.append(('moving_averages', ma_config))
                            except ValueError:
                                st.error("Invalid period format. Use comma-separated numbers.")
            
            # Other indicators
            with col2:
                with st.container():
                    st.subheader("Other Indicators")
                    if st.checkbox("Enable Other Indicators", key="enable_other"):
                        other_indicators = [
                            "RSI",
                            "MACD",
                            "Bollinger Bands",
                            "ATR",
                            "OBV"
                        ]
                        selected_indicators = st.multiselect(
                            "Select Indicators",
                            options=other_indicators,
                            default=["RSI", "MACD"]
                        )
                        enrichments.extend(selected_indicators)
            
            if enrichments:
                # Column selection
                st.subheader("Column Selection")
                with st.container():
                    st.write("Select which columns from the original dataset to keep:")
                    
                    # Always include required columns
                    required_columns = ['open', 'high', 'low', 'close']
                    
                    # Add optional but important columns if they exist
                    for col in ['volume', 'symbol', 'timeframe']:
                        if col in df.columns:
                            required_columns.append(col)
                    
                    # Let user select additional columns
                    optional_columns = [col for col in df.columns if col not in required_columns]
                    selected_columns = required_columns.copy()
                    
                    if optional_columns:
                        st.info("Required columns (always included): " + ", ".join(required_columns))
                        additional_columns = st.multiselect(
                            "Additional columns to keep",
                            options=optional_columns,
                            default=[],
                            help="Select additional columns from the original dataset to keep in the enriched data"
                        )
                        selected_columns.extend(additional_columns)
                
                # Save options
                st.subheader("Save Options")
                with st.container():
                    save_format = st.radio(
                        "Save Format",
                        options=['CSV', 'Parquet'],
                        help="Select the format to save the enriched data"
                    )
                    
                    # Generate default filename
                    symbol = df['symbol'].iloc[0] if 'symbol' in df else 'unknown'
                    timeframe = df['timeframe'].iloc[0] if 'timeframe' in df else 'unknown'
                    start_date = df.index[0].strftime('%Y-%m-%d') if isinstance(df.index, pd.DatetimeIndex) else 'unknown'
                    end_date = df.index[-1].strftime('%Y-%m-%d') if isinstance(df.index, pd.DatetimeIndex) else 'unknown'
                    extension = '.parquet' if save_format == 'Parquet' else '.csv'
                    default_filename = f"Enriched_{symbol}_{timeframe}_{start_date}_{end_date}{extension}"
                    
                    save_path = st.text_input(
                        "Save Path",
                        value=os.path.join('enriched', default_filename),
                        help="Path to save enriched data (relative to storage root)"
                    )
                
                # Advanced options
                st.subheader("Advanced Options")
                with st.expander("Show Details"):
                    st.markdown("""
                    ### Moving Averages
                    - SMA: Simple Moving Average
                    - EMA: Exponential Moving Average
                    - Price Distance: Percentage difference between price and MA
                    - Slope: Rate of change of the moving average
                    
                    ### Technical Indicators
                    - RSI: Relative Strength Index for momentum analysis
                    - MACD: Moving Average Convergence Divergence for trend following
                    - Bollinger Bands: Volatility bands around price
                    - ATR: Average True Range for volatility measurement
                    - OBV: On-Balance Volume for volume analysis
                    """)
                
                # Enrich button
                if st.button("Enrich Data"):
                    with st.spinner("Enriching data..."):
                        # Log enrichments before processing
                        print("\nSelected enrichments:")
                        for e in enrichments:
                            if isinstance(e, tuple):
                                name, config = e
                                print(f"- {name}: {config}")
                            else:
                                print(f"- {e}")
                        
                        # Filter DataFrame to keep only selected columns
                        filtered_df = df[selected_columns].copy()
                        
                        # Create a deep copy of enrichments to avoid modifications
                        enrichments_copy = []
                        for e in enrichments:
                            if isinstance(e, tuple):
                                name, config = e
                                config_copy = {k: v.copy() if isinstance(v, dict) else v for k, v in config.items()}
                                enrichments_copy.append((name, config_copy))
                            else:
                                enrichments_copy.append(e)
                        
                        result = st.session_state.enrich_manager.enrich_data(
                            filtered_df,
                            enrichments_copy,
                            save_path,
                            format=save_format.lower()
                        )
                        
                        if result:
                            # Store enriched data
                            st.session_state['data'] = result['df']
                            
                            # Show success message
                            st.success(f"Data enriched and saved to {result['filename']}")
                            
                            # Show results
                            st.subheader("Enrichment Results")
                            
                            # Show results in tabs
                            tab1, tab2, tab3 = st.tabs(["Data Preview", "Enrichment Info", "Column Details"])
                            
                            with tab1:
                                st.dataframe(result['df'].head())
                                
                                # Show metrics
                                col1, col2, col3 = st.columns(3)
                                with col1:
                                    st.metric(
                                        "Selected Original Columns",
                                        len(selected_columns)
                                    )
                                with col2:
                                    st.metric(
                                        "Added Features",
                                        len(result['info']['columns'])
                                    )
                                with col3:
                                    st.metric(
                                        "Total Features",
                                        len(selected_columns) + len(result['info']['columns'])
                                    )
                            
                            with tab2:
                                # Format enrichments for display
                                formatted_enrichments = []
                                for e in result['info']['enrichments']:
                                    if isinstance(e, tuple):
                                        name, config = e
                                        if name == 'moving_averages':
                                            details = []
                                            details.append(f"Type: {config['type']}")
                                            details.append(f"Periods: {','.join(map(str, config['periods']))}")
                                            details.append(f"Output: {config['output']}")
                                            if config['slope']['enabled']:
                                                details.append(f"Slope Window: {config['slope']['window']}")
                                            formatted_enrichments.append(
                                                f"Moving Averages ({'; '.join(details)})"
                                            )
                                    else:
                                        formatted_enrichments.append(e)
                                
                                st.write("Applied enrichments:", ", ".join(formatted_enrichments))
                                st.write(f"Total rows: {result['info']['rows']}")
                            
                            with tab3:
                                col1, col2 = st.columns(2)
                                with col1:
                                    st.write("Original columns kept:")
                                    st.json(selected_columns)
                                with col2:
                                    st.write("Added columns:")
                                    st.json(result['info']['columns'])
