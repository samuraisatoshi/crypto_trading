"""Contains methods and classes to collect data from Binance API"""

from __future__ import annotations

import pandas as pd
from binance import Client
from datetime import datetime
from dateutil import parser

class BinanceDownloader:
    """Provides methods for retrieving historical price data from Binance API

    Attributes
    ----------
        start_date : str
            start date of the data (e.g., '2023-01-01')
        end_date : str
            end date of the data (e.g., '2023-12-31')
        ticker_list : list
            a list of trading pairs (e.g., ['BTCUSDT', 'ETHUSDT'])
        api_key : str, optional
            Binance API key (default is None)
        api_secret : str, optional
            Binance API secret (default is None)

    Methods
    -------
    fetch_data(interval)
        Fetches historical price data from Binance API for the specified interval

    """

    def __init__(self, start_date: str, end_date: str, ticker_list: list, 
                 api_key: str = None, api_secret: str = None):
        self.start_date = start_date
        self.end_date = end_date
        self.ticker_list = ticker_list
        self.api_key = api_key
        self.api_secret = api_secret

    def fetch_data(self, interval: str = '1d') -> pd.DataFrame:
        """Fetches historical price data from Binance API

        Parameters
        ----------
        interval : str, optional
            The time interval for candlestick data (default is '1d' for daily).
            Valid intervals: '1m', '3m', '5m', '15m', '30m', '1h', '2h', '4h',
            '6h', '8h', '12h', '1d', '3d', '1w', '1M'

        Returns
        -------
        `pd.DataFrame`
            DataFrame containing the historical price data
        """
        # List of valid intervals
        valid_intervals = ['1m', '3m', '5m', '15m', '30m', '1h', '2h', '4h',
                           '6h', '8h', '12h', '1d', '3d', '1w', '1M']

        # Validate the interval
        if interval not in valid_intervals:
            raise ValueError(f"Invalid interval '{interval}'. Must be one of {valid_intervals}.")

        # Initialize Binance client with provided API keys if available
        if self.api_key and self.api_secret:
            client = Client(self.api_key, self.api_secret)
        else:
            client = Client()

        # Convert start and end dates to Binance timestamp
        start_ts = int(parser.parse(self.start_date).timestamp() * 1000)
        end_ts = int(parser.parse(self.end_date).timestamp() * 1000)

        ticker_data = {}
        num_failures = 0

        for tic in self.ticker_list:
            try:
                # Fetch historical data from spot market with pagination
                print(f"\nFetching data for {tic}...")
                all_klines = []
                current_start = start_ts
                
                while current_start < end_ts:
                    klines = client.get_klines(
                        symbol=tic,
                        interval=interval,
                        startTime=current_start,
                        endTime=end_ts,
                        limit=1000
                    )
                    
                    if not klines:
                        break
                        
                    all_klines.extend(klines)
                    # Update start time for next batch
                    current_start = klines[-1][0] + 1
                    print(f"Retrieved {len(klines)} records... Total: {len(all_klines)}")
                
                if not all_klines:
                    print(f"No data available for {tic}")
                    num_failures += 1
                    continue

                print(f"Total records for {tic}: {len(all_klines)}")
                
                # Create DataFrame
                temp_df = pd.DataFrame(all_klines, columns=['date', 'open', 'high', 'low', 'close', 'volume',
                                                      'close_time', 'quote_asset_volume', 'number_of_trades',
                                                      'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'])

                # Convert timestamp to datetime
                temp_df['date'] = pd.to_datetime(temp_df['date'], unit='ms')
                
                # Keep only necessary columns and convert to float
                temp_df = temp_df[['date', 'open', 'high', 'low', 'close', 'volume']]
                for col in ['open', 'high', 'low', 'close', 'volume']:
                    temp_df[col] = pd.to_numeric(temp_df[col], errors='coerce')
                
                # Add symbol column
                temp_df['tic'] = tic
                
                # Assign to ticker_data
                ticker_data[tic] = temp_df
                
            except Exception as e:
                print(f"Error fetching data for {tic}: {str(e)}")
                num_failures += 1

        if num_failures == len(self.ticker_list):
            raise ValueError("No data fetched for any ticker.")

        # Find the intersection of dates across all tickers
        common_dates = set(ticker_data[self.ticker_list[0]]['date'])
        for tic in self.ticker_list[1:]:
            common_dates.intersection_update(ticker_data[tic]['date'])
        
        # Convert to sorted list
        common_dates = sorted(common_dates)

        # Check if common_dates is empty
        if not common_dates:
            raise ValueError("No common dates found across all tickers.")

        # For each ticker, subset data to common_dates
        for tic in self.ticker_list:
            df = ticker_data[tic][ticker_data[tic]['date'].isin(common_dates)]
            if df.empty:
                raise ValueError(f"No data available for ticker {tic} in the common date range.")
            ticker_data[tic] = df

        # Concatenate all data
        data_df = pd.concat(ticker_data.values(), ignore_index=True)

        # Set 'tic' as a categorical variable with ordered categories
        data_df['tic'] = pd.Categorical(data_df['tic'], categories=self.ticker_list, ordered=True)

        # Sort by date and tic
        data_df = data_df.sort_values(by=['date', 'tic']).reset_index(drop=True)

        # Ensure day column is correctly calculated
        data_df['day'] = data_df['date'].dt.dayofweek

        # Keep date as datetime and add timestamp column
        data_df['timestamp'] = data_df['date']
        
        # Ensure data types are correct
        data_df['timestamp'] = pd.to_datetime(data_df['timestamp'])
        data_df['date'] = data_df['date'].dt.strftime('%Y-%m-%d')  # Keep date as string for compatibility
        data_df['open'] = data_df['open'].astype(float)
        data_df['high'] = data_df['high'].astype(float)
        data_df['low'] = data_df['low'].astype(float)
        data_df['close'] = data_df['close'].astype(float)
        data_df['volume'] = data_df['volume'].astype(float)
        data_df['tic'] = data_df['tic'].astype(str)
        data_df['day'] = data_df['day'].astype(int)

        # Drop any remaining missing values
        data_df = data_df.dropna().reset_index(drop=True)

        print("Shape of DataFrame: ", data_df.shape)

        return data_df

    def select_equal_rows_stock(self, df):
        df_check = df.tic.value_counts()
        df_check = pd.DataFrame(df_check).reset_index()
        df_check.columns = ["tic", "counts"]
        mean_df = df_check.counts.mean()
        equal_list = list(df.tic.value_counts() >= mean_df)
        names = df.tic.value_counts().index
        select_stocks_list = list(names[equal_list])
        df = df[df.tic.isin(select_stocks_list)]
        return df
