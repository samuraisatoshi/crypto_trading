"""
Results display component.
"""
import streamlit as st
from typing import Dict, List, Any

class ResultsDisplay:
    """Component for displaying backtest results."""
    
    @staticmethod
    def display_results_matrix(results: List[Dict[str, Any]], pattern_counts: Dict[str, int]):
        """Display results matrix."""
        if not results:
            st.warning("No trades executed during backtest")
            return
        
        # Calculate basic metrics
        total_trades = len(results)
        long_trades = len([r for r in results if r['type'] == 'long'])
        short_trades = len([r for r in results if r['type'] == 'short'])
        
        # Calculate confidence metrics
        avg_confidence = sum(r['confidence'] for r in results) / total_trades if total_trades > 0 else 0
        high_conf_trades = len([r for r in results if r['confidence'] >= 0.8])
        
        # Display trade metrics
        st.subheader("Trade Metrics")
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric("Total Trades", total_trades)
        with col2:
            st.metric("Long Trades", long_trades)
        with col3:
            st.metric("Short Trades", short_trades)
        with col4:
            st.metric("Avg Confidence", f"{avg_confidence:.1%}")
        with col5:
            st.metric("High Conf Trades", high_conf_trades)
        
        # Display pattern/signal distribution
        st.subheader("Signal Distribution")
        if pattern_counts:
            # For pattern-based strategies
            cols = st.columns(len(pattern_counts))
            for i, (pattern_type, count) in enumerate(pattern_counts.items()):
                with cols[i]:
                    st.metric(pattern_type, count)
        else:
            # For trend-based strategies
            signal_types = set(r.get('pattern', 'Unknown') for r in results)
            if len(signal_types) > 1:  # Only show if we have different signal types
                signal_counts = {}
                for signal_type in signal_types:
                    count = len([r for r in results if r.get('pattern') == signal_type])
                    signal_counts[signal_type] = count
                
                cols = st.columns(len(signal_counts))
                for i, (signal_type, count) in enumerate(signal_counts.items()):
                    with cols[i]:
                        st.metric(signal_type, count)
        
        # Display trade details with expanded information
        st.subheader("Trade Details")
        trade_data = []
        for trade in results:
            trade_info = {
                'Date': trade['date'],
                'Type': trade['type'].capitalize(),
                'Price': f"{trade['price']:.2f}",
                'Confidence': f"{trade['confidence']:.2%}",
                'Signal': trade.get('pattern', 'N/A')
            }
            
            # Add any additional trade information
            for key, value in trade.items():
                if key not in ['date', 'type', 'price', 'confidence', 'pattern'] and value is not None:
                    trade_info[key.capitalize()] = value
            
            trade_data.append(trade_info)
        
        if trade_data:
            st.dataframe(trade_data)
