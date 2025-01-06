# ML Trade Project

A comprehensive cryptocurrency trading analysis and backtesting platform with support for technical indicators, chart pattern recognition, and Bitcoin halving cycle analysis.

## Features

- 📊 Technical Analysis
  - Moving Averages (SMA, EMA)
  - Momentum Indicators (RSI, MACD)
  - Volatility Indicators (BB, ATR)
  - Volume Analysis (OBV)
  - Chart Pattern Recognition

- 📈 Backtesting Engine
  - Multiple timeframe support
  - Flexible strategy configuration
  - Performance metrics
  - Trade visualization
  - Risk analysis

- 🔄 Data Management
  - Binance data integration
  - FinRL dataset support
  - Automated enrichment
  - Feature engineering

- 🕒 Temporal Analysis
  - Bitcoin halving cycles
  - Market regime detection
  - Volatility analysis
  - Liquidity metrics

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/projeto_ml_trade.git
cd projeto_ml_trade
```

2. Install system requirements:

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install -y build-essential python3-dev python3-pip ta-lib
```

**macOS:**
```bash
brew install ta-lib
```

**Windows:**
Download and install [TA-Lib](http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-msvc.zip)

3. Set up Python environment:

**Using Conda (Recommended):**
```bash
# Create and activate conda environment
conda env create -f environment.yml
conda activate ml_trade_env

# Install the package in development mode
pip install -e .
```

**Using venv (Alternative):**
```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Install the package in development mode
pip install -e .
```

4. Configure settings:
```bash
# Edit attribs.env with your Binance API credentials and preferences
nano attribs.env
```

5. Run the application:
```bash
streamlit run app_streamlit.py
```

The installation process will:
- Install all required dependencies
- Create necessary directories
- Set up environment configuration
- Verify system requirements

## Documentation

- [Installation Guide](docs/Installation.md) - Detailed setup instructions
- [Project Overview](docs/ProjectExplanation.md) - Architecture and components
- [Dataset Guide](docs/DataSetExplain.md) - Data formats and enrichment

## Project Structure

```
projeto_ml_trade/
├── app/                    # Streamlit web application
├── backtester/           # Backtesting engine
├── data/                 # Data storage
├── docs/                 # Documentation
├── strategies/           # Trading strategies
└── utils/               # Utility modules
```

## Usage Examples

1. Download market data:
```python
from utils.binance_client import BinanceClient

client = BinanceClient()
data = client.download_data(
    symbol="BTCUSDT",
    timeframe="1d",
    start_date="2020-01-01"
)
```

2. Enrich dataset:
```python
from utils.data_enricher import DataEnricher

enricher = DataEnricher()
enriched_data = enricher.enrich_data(
    df=data,
    enrichments=[
        ('moving_averages', {'type': 'EMA', 'periods': [21, 55, 80, 100]}),
        'RSI',
        'MACD'
    ]
)
```

3. Run backtest:
```python
from backtester import Backtester
from strategies import EMATrendStrategy

strategy = EMATrendStrategy(
    ema21_period=21,
    ema55_period=55,
    ema80_period=80,
    ema100_period=100
)

backtester = Backtester(
    df=enriched_data,
    strategy=strategy,
    initial_balance=10000
)

results = backtester.run()
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [TA-Lib](https://ta-lib.org/) for technical analysis functions
- [Streamlit](https://streamlit.io/) for the web interface
- [Binance](https://binance.com/) for market data
- [FinRL](https://github.com/AI4Finance-Foundation/FinRL) for dataset format inspiration

## Support

If you encounter any issues or have questions:
1. Check the documentation
2. Review common issues in Installation Guide
3. Open a GitHub issue

## Roadmap

- [ ] Additional trading strategies
- [ ] Machine learning integration
- [ ] Real-time trading support
- [ ] Portfolio optimization
- [ ] Enhanced visualization
