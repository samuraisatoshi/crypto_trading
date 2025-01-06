"""
Main entry point for the crypto trading system.
This file demonstrates how to use the core components.
"""
import os
import numpy as np
from datetime import datetime
import pandas as pd
from utils.binancedownloader import BinanceDownloader
from utils.data_enricher import DataEnricher
from backtester.backtester import Backtester
from strategies.base import BaseStrategy

def download_data(symbol: str, start_date: str, end_date: str, timeframe: str = '1h') -> pd.DataFrame:
    """
    Download historical price data from Binance.
    
    Args:
        symbol: Trading pair symbol (e.g., 'BTCUSDT')
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        timeframe: Candlestick timeframe (e.g., '1h', '1d')
        
    Returns:
        DataFrame with historical price data
    """
    downloader = BinanceDownloader(start_date, end_date, [symbol])
    df = downloader.fetch_data(interval=timeframe)
    
    # Save raw data
    save_dir = os.path.join('data', 'dataset')
    os.makedirs(save_dir, exist_ok=True)
    filename = f"{symbol}_{timeframe}_{start_date}_{end_date}.csv"
    save_path = os.path.join(save_dir, filename)
    df.to_csv(save_path, index=False)
    
    print(f"Downloaded {len(df)} records for {symbol}")
    print(f"Data saved to {save_path}")
    return df

def enrich_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add technical indicators and other features to the price data.
    
    Args:
        df: Raw price data DataFrame
        
    Returns:
        Enriched DataFrame with additional features
    """
    enricher = DataEnricher(df)
    enriched_df = enricher.add_all_features()
    
    # Save enriched data
    save_dir = os.path.join('data', 'enriched_dataset')
    os.makedirs(save_dir, exist_ok=True)
    filename = f"enriched_{datetime.now().strftime('%Y%m%d_%H%M%S')}.parquet"
    save_path = os.path.join(save_dir, filename)
    enriched_df.to_parquet(save_path)
    
    print(f"Added {len(enriched_df.columns)} features")
    print(f"Enriched data saved to {save_path}")
    return enriched_df

def run_backtest(df: pd.DataFrame, strategy_id: str, **kwargs) -> dict:
    """
    Run backtest for a given strategy on historical data.
    
    Args:
        df: Enriched price data DataFrame
        strategy_id: Strategy identifier (e.g., 'rsi', 'macd')
        **kwargs: Additional strategy parameters
        
    Returns:
        Dictionary containing backtest results
    """
    backtester = Backtester(df=df, strategy_id=strategy_id, **kwargs)
    results = backtester.run_backtest()
    
    print("\nBacktest Results:")
    print(f"Strategy: {strategy_id}")
    print(f"Total trades: {results['performance']['completed_trades']}")
    print(f"Win rate: {results['performance']['win_rate']:.2f}%")
    print(f"Total return: {results['performance']['total_return']:.2f}%")
    print(f"Max drawdown: {results['performance']['max_drawdown']:.2f}%")
    profit_factor = results['performance']['profit_factor']
    if np.isfinite(profit_factor):
        print(f"Profit factor: {profit_factor:.2f}")
    else:
        print("Profit factor: ∞ (no losing trades)")
    
    return results

def main():
    # Example usage
    symbol = "BTCUSDT"
    start_date = "2023-01-01"
    end_date = "2023-12-31"
    timeframe = "1h"
    
    # Download historical data
    df = download_data(symbol, start_date, end_date, timeframe)
    
    # Enrich data with technical indicators
    enriched_df = enrich_data(df)
    
    # Run backtest with RSI strategy
    strategy_params = {
        'rsi_period': 14,
        'rsi_overbought': 70,
        'rsi_oversold': 30,
        'risk_reward': 2.0,
        'stop_loss_pct': 2.0,
    }
    results = run_backtest(enriched_df, strategy_id='rsi', **strategy_params)

if __name__ == "__main__":
    main()
