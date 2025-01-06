# Dataset Types and Column Specifications

This document describes the different types of datasets used in the project and their expected column structures.

## 1. Native Dataset

Native datasets are those downloaded directly from Binance using the project's downloader. They include basic OHLCV data plus symbol and timeframe information.

### Required Columns
- `date` (index): Datetime of the candle
- `symbol`: Trading pair (e.g., 'BTCUSDT')
- `timeframe`: Candle timeframe (e.g., '1d', '4h', '1h')
- `open`: Opening price
- `high`: Highest price
- `low`: Lowest price
- `close`: Closing price
- `volume`: Trading volume

## 2. FinRL Dataset

FinRL datasets follow the format used by the FinRL library for reinforcement learning. They contain OHLCV data but may not include symbol and timeframe information.

### Required Columns
- `date` (index): Datetime of the candle
- `open`: Opening price
- `high`: Highest price
- `low`: Lowest price
- `close`: Closing price
- `volume`: Trading volume

Note: When using FinRL datasets, the system automatically adds:
- `symbol`: Set to 'UNKNOWN'
- `timeframe`: Set to '1d'

## 3. Enriched Dataset

Enriched datasets include all basic columns plus additional technical indicators and features. The exact columns depend on the enrichment configuration.

### Base Columns (Always Present)
- All columns from Native/FinRL dataset
- `day_of_week`: Day of week (0=Monday to 6=Sunday)
- `quarter`: Quarter of the year (1-4)
- `days_since_halving`: Days since last Bitcoin halving

### Bitcoin Halving Data
The system tracks Bitcoin halving events to provide temporal context:

| Sequence | Date       | Block Reward | Initial Price |
|----------|------------|--------------|---------------|
| 2        | 2016-07-09 | 12.5 BTC    | $680.00      |
| 3        | 2020-05-11 | 6.25 BTC    | $8,590.00    |
| 4        | 2024-04-20 | 3.125 BTC   | $64,025.00   |
| 5        | 2028-03-17 | 1.5625 BTC  | -            |
| 6        | 2032-02-12 | 0.78125 BTC | -            |
| 7        | 2036-01-08 | 0.390625 BTC| -            |
| 8        | 2039-12-04 | 0.1953125 BTC| -           |
| 9        | 2043-10-30 | 0.09765625 BTC| -          |
| 10       | 2047-09-25 | 0.04882813 BTC| -          |

Notes:
- Dates after 2024 are estimated based on average block time
- Prices are only available for historical events
- Block rewards halve approximately every 4 years

### Moving Averages (Optional)
When enabled, for each period (e.g., 21, 55, 80, 100):

#### SMA Features
- `SMA_{period}`: Simple Moving Average value
- `SMA_{period}_Distance`: Percentage distance from price (if enabled)
- `SMA_{period}_Slope`: Rate of change (if enabled)

#### EMA Features
- `EMA_{period}`: Exponential Moving Average value
- `EMA_{period}_Distance`: Percentage distance from price (if enabled)
- `EMA_{period}_Slope`: Rate of change (if enabled)

### Technical Indicators (Optional)

#### RSI
- `RSI`: Relative Strength Index

#### MACD
- `MACD`: MACD line
- `MACD_Signal`: Signal line
- `MACD_Hist`: MACD histogram

#### Bollinger Bands
- `BB_Upper`: Upper band
- `BB_Middle`: Middle band
- `BB_Lower`: Lower band

#### Other Indicators
- `ATR`: Average True Range
- `OBV`: On Balance Volume (requires volume data)

## Example Column Structure

Here's an example of a fully enriched dataset with all features enabled:

```python
[
    'date',             # Index
    'symbol',           # Trading pair
    'timeframe',        # Candle timeframe
    'open',            # OHLCV data
    'high',
    'low',
    'close',
    'volume',
    'day_of_week',     # Temporal features
    'quarter',
    'days_since_halving',
    'EMA_21',          # Moving averages
    'EMA_21_Distance',
    'EMA_21_Slope',
    'EMA_55',
    'EMA_55_Distance',
    'EMA_55_Slope',
    'EMA_80',
    'EMA_80_Distance',
    'EMA_80_Slope',
    'EMA_100',
    'EMA_100_Distance',
    'EMA_100_Slope',
    'RSI',             # Technical indicators
    'MACD',
    'MACD_Signal',
    'MACD_Hist',
    'BB_Upper',
    'BB_Middle',
    'BB_Lower',
    'ATR',
    'OBV'
]
```

## Directory Structure

The project organizes datasets in the following directory structure:

```
projeto_ml_trade/
└── data/
    ├── raw/                  # Raw downloaded data
    │   └── binance/         # Binance OHLCV data
    │       ├── spot/        # Spot market data
    │       └── futures/     # Futures market data
    ├── dataset/             # Processed datasets
    │   ├── native/          # Native format datasets
    │   └── finrl/          # FinRL format datasets
    └── enriched/            # Enriched datasets
```

## File Naming Conventions

### Raw Data Files
Format: `{symbol}_{timeframe}_{start_date}_{end_date}.{format}`
Example: `BTCUSDT_1d_20210101_20211231.csv`

### Native Dataset Files
Format: `{symbol}_{timeframe}_{start_date}_{end_date}.{format}`
Example: `BTCUSDT_1d_20210101_20211231.parquet`

### FinRL Dataset Files
Format: `finrl_{symbol}_{timeframe}_{start_date}_{end_date}.{format}`
Example: `finrl_BTCUSDT_1d_20210101_20211231.csv`

### Enriched Dataset Files
Format: `Enriched_{symbol}_{timeframe}_{start_date}_{end_date}.{format}`
Example: `Enriched_BTCUSDT_1d_20210101_20211231.parquet`

## Data Validation and Preprocessing

### Validation Checks
1. Datetime index or 'date' column presence and format
2. Required columns presence (OHLCV)
3. Data types correctness
4. Price values > 0
5. Volume values >= 0
6. No duplicate timestamps
7. Chronological order of data

### Preprocessing Steps
1. Missing values handling:
   - NaN values are dropped by default
   - Forward fill can be enabled for certain indicators
   - Missing columns are added with default values for FinRL datasets

2. Date/Time processing:
   - All dates are converted to UTC
   - Timezone information is preserved if present
   - Timestamps are sorted chronologically
   - Duplicate timestamps are removed (keeping last)

3. Data type conversion:
   - Numeric columns are converted to float64
   - Date columns are converted to datetime64[ns]
   - Categorical columns (symbol, timeframe) are converted to string

4. Index handling:
   - 'date' column is set as index if not already
   - Index is validated to be datetime type
   - Index is ensured to be unique and sorted

## Notes

1. Data Quality:
   - All datasets must have a datetime index or a 'date' column that can be converted to datetime
   - Price and volume data must be numeric and non-negative
   - Gaps in data (missing candles) are preserved to maintain accuracy

2. Dataset Handling:
   - Missing columns in FinRL datasets are automatically added with default values
   - Technical indicators are optional and can be selected during enrichment
   - Moving average periods and types (SMA/EMA) are configurable
   - All percentage values (e.g., EMA_21_Distance) are calculated as ((price - indicator) / indicator) * 100

3. File Formats:
   - The system supports both CSV and Parquet file formats
   - Parquet is recommended for large datasets due to better compression and faster read/write operations
   - All datetime values are stored in UTC timezone

4. Performance Considerations:
   - Large datasets should use Parquet format
   - Enrichment process may take longer with many indicators enabled
   - Memory usage increases with dataset size and number of indicators
