"""
Chart component for backtesting visualization.
"""
import mplfinance as mpf
import pandas as pd
from typing import List, Dict, Any
import os

class ChartComponent:
    """Component for creating and saving trading charts."""
    
    def __init__(self):
        """Initialize chart component."""
        # Create charts directory if it doesn't exist
        os.makedirs('data/charts', exist_ok=True)
    
    def save_chart(
        self,
        df: pd.DataFrame,
        patterns: List[Dict[str, Any]],
        symbol: str,
        timeframe: str,
        sequence: int
    ) -> None:
        """Save chart with patterns/signals."""
        try:
            # Create plot style
            style = mpf.make_mpf_style(
                base_mpf_style='charles',
                gridstyle='',
                y_on_right=False
            )
            
            # Prepare additional plots for EMAs if they exist
            addplot = []
            for col in df.columns:
                if col.startswith('EMA_'):
                    addplot.append(
                        mpf.make_addplot(
                            df[col],
                            color='blue' if 'EMA_21' in col else 'orange' if 'EMA_55' in col else 'green',
                            width=0.8,
                            alpha=0.6
                        )
                    )
            
            # Create figure
            fig, axlist = mpf.plot(
                df,
                type='candle',
                style=style,
                volume=True,
                figsize=(15, 8),
                panel_ratios=(3, 1),
                addplot=addplot,
                returnfig=True
            )
            
            # Add pattern/signal annotations
            for pattern in patterns:
                pattern_type = pattern.get('type', 'Unknown')
                start_idx = pattern.get('start_idx', 0)
                end_idx = pattern.get('end_idx', len(df)-1)
                confidence = pattern.get('confidence', 0)
                
                # Get price levels
                if 'price_levels' in pattern:
                    levels = pattern['price_levels']
                    for level_name, price in levels.items():
                        axlist[0].axhline(
                            y=price,
                            color='gray',
                            linestyle='--',
                            alpha=0.5,
                            label=level_name
                        )
                
                # Add pattern/signal label
                if pattern_type in ['bullish_ema_alignment', 'bearish_ema_alignment']:
                    # For trend signals, place label near the signal bar
                    label = f"{pattern_type.replace('_', ' ').title()} ({confidence:.1%})"
                    x_pos = end_idx
                    y_pos = df['high'].iloc[x_pos] * 1.02  # Slightly above the high
                else:
                    # For pattern signals, place label between start and end
                    label = f"{pattern_type} ({confidence:.1%})"
                    x_pos = (start_idx + end_idx) // 2
                    y_pos = df['high'].iloc[x_pos]
                axlist[0].annotate(
                    label,
                    xy=(x_pos, y_pos),
                    xytext=(0, 20),
                    textcoords='offset points',
                    ha='center',
                    va='bottom',
                    bbox=dict(
                        boxstyle='round,pad=0.5',
                        fc='yellow',
                        alpha=0.5
                    ),
                    arrowprops=dict(
                        arrowstyle='->',
                        connectionstyle='arc3,rad=0'
                    )
                )
            
            # Save chart
            filename = f"{symbol}_{timeframe}_{df.index[0].strftime('%Y%m%d')}_{sequence:04d}.jpg"
            filepath = os.path.join('data/charts', filename)
            fig.savefig(filepath, bbox_inches='tight', dpi=150)
            
        except Exception as e:
            print(f"Error saving chart: {str(e)}")
    
    def create_trade_chart(
        self,
        df: pd.DataFrame,
        trades: List[Dict[str, Any]],
        filename: str
    ) -> None:
        """Create chart with trade history."""
        try:
            # Create plot style
            style = mpf.make_mpf_style(
                base_mpf_style='charles',
                gridstyle='',
                y_on_right=False
            )
            
            # Create markers for trades
            markers = []
            for trade in trades:
                date = trade['date']
                price = trade['price']
                trade_type = trade['type']
                
                marker = None
                if trade_type == 'long':
                    marker = '^'  # Triangle up for long
                elif trade_type == 'short':
                    marker = 'v'  # Triangle down for short
                
                if marker:
                    markers.append(
                        dict(
                            date=date,
                            marker=marker,
                            color='g' if trade_type == 'long' else 'r',
                            size=100
                        )
                    )
            
            # Prepare additional plots for EMAs if they exist
            addplot = []
            for col in df.columns:
                if col.startswith('EMA_'):
                    addplot.append(
                        mpf.make_addplot(
                            df[col],
                            color='blue' if 'EMA_21' in col else 'orange' if 'EMA_55' in col else 'green',
                            width=0.8,
                            alpha=0.6
                        )
                    )
            
            # Create figure with trades
            fig, axlist = mpf.plot(
                df,
                type='candle',
                style=style,
                volume=True,
                figsize=(15, 8),
                panel_ratios=(3, 1),
                markers=markers,
                addplot=addplot,
                returnfig=True
            )
            
            # Add legend if EMAs are present
            if addplot:
                ema_lines = []
                ema_labels = []
                for line in axlist[0].get_lines():
                    if line.get_alpha() == 0.6:  # EMA lines have alpha=0.6
                        ema_lines.append(line)
                        color = line.get_color()
                        if color == 'blue':
                            ema_labels.append('EMA 21')
                        elif color == 'orange':
                            ema_labels.append('EMA 55')
                        elif color == 'green':
                            ema_labels.append('EMA 80/100')
                if ema_lines:
                    axlist[0].legend(ema_lines, ema_labels, loc='upper left')
            
            # Save chart
            filepath = os.path.join('data/charts', filename)
            fig.savefig(filepath, bbox_inches='tight', dpi=150)
            
        except Exception as e:
            print(f"Error creating trade chart: {str(e)}")
