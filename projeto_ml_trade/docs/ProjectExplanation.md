# Project Overview

This document provides a comprehensive overview of the ML Trade project structure and functionality.

## Project Structure

```
projeto_ml_trade/
├── app/                    # Streamlit web application
│   ├── components/        # Reusable UI components
│   │   ├── backtest/     # Backtesting components
│   │   ├── data/        # Data handling components
│   │   └── storage/     # Storage management components
│   ├── managers/         # Business logic managers
│   └── pages/           # Application pages
├── backtester/           # Backtesting engine
├── data/                 # Data storage
├── docs/                 # Documentation
├── strategies/           # Trading strategies
│   └── chart_patterns/  # Chart pattern detectors
└── utils/               # Utility modules
```

## Core Components

### 1. Web Application (app/)

The Streamlit-based web interface provides:
- Data downloading and management
- Dataset enrichment with technical indicators
- Backtesting configuration and execution
- Results visualization and analysis

#### Key Pages:
- Download Page: Fetch market data from Binance
- Enrich Page: Add technical indicators and features
- Backtest Page: Test trading strategies

### 2. Backtesting Engine (backtester/)

Provides functionality for:
- Strategy testing
- Performance analysis
- Risk management
- Trade execution simulation

Components:
- Account: Manages portfolio and positions
- Backtester: Core backtesting logic
- Trading Orders: Order management
- Risk Manager: Risk control and position sizing

### 3. Trading Strategies (strategies/)

Available strategies:
- EMATrendStrategy: Trend following using multiple EMAs
- Pattern Strategy: Chart pattern recognition
- Pattern Orchestrator: Multiple pattern coordination

Features:
- Configurable parameters
- Signal generation
- Entry/exit rules
- Risk management integration

### 4. Utilities (utils/)

Core functionality modules:
- Technical Indicators
- Market Regime Analysis
- Volatility Metrics
- Data Enrichment
- Temporal Features
- Logging

## Key Features

### 1. Data Management
- Multiple data sources support (Binance, FinRL)
- Automated data downloading
- Data validation and preprocessing
- Feature enrichment

### 2. Technical Analysis
- Moving Averages (SMA, EMA)
- Momentum Indicators (RSI, MACD)
- Volatility Indicators (BB, ATR)
- Volume Analysis (OBV)
- Chart Pattern Recognition

### 3. Backtesting
- Multiple timeframe support
- Flexible strategy configuration
- Performance metrics
- Trade visualization
- Risk analysis

### 4. Market Analysis
- Temporal feature analysis
- Bitcoin halving cycle tracking
- Market regime detection
- Volatility analysis
- Liquidity analysis

## Usage Workflow

1. Data Preparation:
   ```
   Download Data → Validate → Enrich → Save
   ```

2. Strategy Development:
   ```
   Create Strategy → Configure Parameters → Test → Optimize
   ```

3. Backtesting:
   ```
   Load Data → Select Strategy → Configure → Run → Analyze Results
   ```

## Configuration

### 1. Environment Setup
- Python 3.8+
- Required packages in requirements.txt
- TA-Lib installation
- Streamlit configuration

### 2. Data Sources
- Binance API credentials
- Data storage configuration
- File format preferences

### 3. Strategy Parameters
- Moving average periods
- Pattern detection settings
- Risk management rules
- Entry/exit conditions

## Performance Considerations

1. Data Processing:
   - Use Parquet for large datasets
   - Enable caching for repeated operations
   - Optimize indicator calculations

2. Backtesting:
   - Monitor memory usage with large datasets
   - Use appropriate timeframes
   - Balance precision vs performance

3. Visualization:
   - Limit chart data points
   - Use efficient plotting methods
   - Cache rendered components

## Development Guidelines

1. Code Organization:
   - Follow modular structure
   - Use type hints
   - Document functions and classes
   - Include logging

2. Testing:
   - Unit tests for core functionality
   - Integration tests for workflows
   - Strategy validation tests

3. Documentation:
   - Keep docs updated
   - Include examples
   - Document configuration options

## Future Enhancements

1. Planned Features:
   - Additional strategies
   - Machine learning integration
   - Real-time trading
   - Portfolio optimization

2. Improvements:
   - Performance optimization
   - Enhanced visualization
   - More technical indicators
   - Advanced risk management

## Support and Maintenance

1. Issue Tracking:
   - Bug reports
   - Feature requests
   - Performance issues

2. Updates:
   - Regular dependency updates
   - Security patches
   - Feature additions

3. Documentation:
   - Usage guides
   - API documentation
   - Configuration reference
