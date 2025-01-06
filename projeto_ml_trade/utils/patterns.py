"""
Pattern detection and analysis utilities.
"""
import pandas as pd
import numpy as np
import talib
import logging
from .candles import add_price_action_features

logger = logging.getLogger(__name__)

def identify_patterns_and_confirm(df: pd.DataFrame, 
                                timeframe: str, 
                                trade_type: str, 
                                validity_window: int) -> pd.DataFrame:
    """Identify and confirm candlestick patterns.
    
    Args:
        df: DataFrame with OHLCV data
        timeframe: Data timeframe ('15m', '30m', '1h', etc.)
        trade_type: Trade type ('scalp', 'day_trade', 'swing_trade', 'position')
        validity_window: Number of candles to validate pattern
        
    Returns:
        DataFrame with identified and confirmed patterns
    """
    try:
        # Candlestick Patterns using TA-lib
        pattern_functions = {
            'CDL2CROWS': talib.CDL2CROWS,
            'CDL3BLACKCROWS': talib.CDL3BLACKCROWS,
            'CDL3INSIDE': talib.CDL3INSIDE,
            'CDL3LINESTRIKE': talib.CDL3LINESTRIKE,
            'CDL3OUTSIDE': talib.CDL3OUTSIDE,
            'CDL3STARSINSOUTH': talib.CDL3STARSINSOUTH,
            'CDL3WHITESOLDIERS': talib.CDL3WHITESOLDIERS,
            'CDLABANDONEDBABY': talib.CDLABANDONEDBABY,
            'CDLADVANCEBLOCK': talib.CDLADVANCEBLOCK,
            'CDLBELTHOLD': talib.CDLBELTHOLD,
            'CDLBREAKAWAY': talib.CDLBREAKAWAY,
            'CDLCLOSINGMARUBOZU': talib.CDLCLOSINGMARUBOZU,
            'CDLCONCEALBABYSWALL': talib.CDLCONCEALBABYSWALL,
            'CDLCOUNTERATTACK': talib.CDLCOUNTERATTACK,
            'CDLDARKCLOUDCOVER': talib.CDLDARKCLOUDCOVER,
            'CDLDOJI': talib.CDLDOJI,
            'CDLDOJISTAR': talib.CDLDOJISTAR,
            'CDLDRAGONFLYDOJI': talib.CDLDRAGONFLYDOJI,
            'CDLENGULFING': talib.CDLENGULFING,
            'CDLEVENINGDOJISTAR': talib.CDLEVENINGDOJISTAR,
            'CDLEVENINGSTAR': talib.CDLEVENINGSTAR,
            'CDLGAPSIDESIDEWHITE': talib.CDLGAPSIDESIDEWHITE,
            'CDLGRAVESTONEDOJI': talib.CDLGRAVESTONEDOJI,
            'CDLHAMMER': talib.CDLHAMMER,
            'CDLHANGINGMAN': talib.CDLHANGINGMAN,
            'CDLHARAMI': talib.CDLHARAMI,
            'CDLHARAMICROSS': talib.CDLHARAMICROSS,
            'CDLHIGHWAVE': talib.CDLHIGHWAVE,
            'CDLHIKKAKE': talib.CDLHIKKAKE,
            'CDLHIKKAKEMOD': talib.CDLHIKKAKEMOD,
            'CDLHOMINGPIGEON': talib.CDLHOMINGPIGEON,
            'CDLIDENTICAL3CROWS': talib.CDLIDENTICAL3CROWS,
            'CDLINNECK': talib.CDLINNECK,
            'CDLINVERTEDHAMMER': talib.CDLINVERTEDHAMMER,
            'CDLKICKING': talib.CDLKICKING,
            'CDLKICKINGBYLENGTH': talib.CDLKICKINGBYLENGTH,
            'CDLLADDERBOTTOM': talib.CDLLADDERBOTTOM,
            'CDLLONGLEGGEDDOJI': talib.CDLLONGLEGGEDDOJI,
            'CDLLONGLINE': talib.CDLLONGLINE,
            'CDLMARUBOZU': talib.CDLMARUBOZU,
            'CDLMATCHINGLOW': talib.CDLMATCHINGLOW,
            'CDLMATHOLD': talib.CDLMATHOLD,
            'CDLMORNINGDOJISTAR': talib.CDLMORNINGDOJISTAR,
            'CDLMORNINGSTAR': talib.CDLMORNINGSTAR,
            'CDLONNECK': talib.CDLONNECK,
            'CDLPIERCING': talib.CDLPIERCING,
            'CDLRICKSHAWMAN': talib.CDLRICKSHAWMAN,
            'CDLRISEFALL3METHODS': talib.CDLRISEFALL3METHODS,
            'CDLSEPARATINGLINES': talib.CDLSEPARATINGLINES,
            'CDLSHOOTINGSTAR': talib.CDLSHOOTINGSTAR,
            'CDLSHORTLINE': talib.CDLSHORTLINE,
            'CDLSPINNINGTOP': talib.CDLSPINNINGTOP,
            'CDLSTALLEDPATTERN': talib.CDLSTALLEDPATTERN,
            'CDLSTICKSANDWICH': talib.CDLSTICKSANDWICH,
            'CDLTAKURI': talib.CDLTAKURI,
            'CDLTASUKIGAP': talib.CDLTASUKIGAP,
            'CDLTHRUSTING': talib.CDLTHRUSTING,
            'CDLTRISTAR': talib.CDLTRISTAR,
            'CDLUNIQUE3RIVER': talib.CDLUNIQUE3RIVER,
            'CDLUPSIDEGAP2CROWS': talib.CDLUPSIDEGAP2CROWS,
            'CDLXSIDEGAP3METHODS': talib.CDLXSIDEGAP3METHODS
        }

        # Identify patterns
        patterns_found = {}
        for pattern_name, pattern_func in pattern_functions.items():
            df[f'pattern_{pattern_name}'] = pattern_func(df['open'], df['high'], df['low'], df['close'])
            patterns_found[pattern_name] = (df[f'pattern_{pattern_name}'] != 0).sum()

        # Log found patterns
        logger.info("\nPatterns found:")
        for pattern, count in patterns_found.items():
            if count > 0:
                logger.info(f"{pattern}: {count} occurrences")

        # Confirm patterns within validity window
        for pattern_name in pattern_functions.keys():
            pattern_col = f'pattern_{pattern_name}'
            confirmation_col = f'confirmed_{pattern_name}'
            
            # Convert signals (-100/100) to binary (0/1)
            df[pattern_col] = (df[pattern_col] != 0).astype(int)
            
            # Confirm pattern within validity window
            df[confirmation_col] = (
                df[pattern_col]
                .rolling(window=validity_window)
                .max()
                .shift(-validity_window + 1)
                .fillna(0)
                .astype(int)
            )

        # Add breakouts
        df['pattern_bullish_breakout'] = (
            (df['close'] > df['high'].shift(1)) & 
            (df['close'] > df['open']) &
            (df['volume'] > df['volume'].rolling(20).mean())
        ).astype(int)

        df['pattern_bearish_breakout'] = (
            (df['close'] < df['low'].shift(1)) & 
            (df['close'] < df['open']) &
            (df['volume'] > df['volume'].rolling(20).mean())
        ).astype(int)

        # Log statistics
        total_patterns = sum(patterns_found.values())
        logger.info(f"\nTotal patterns found: {total_patterns}")
        logger.info(f"Average patterns per day: {total_patterns/len(df):.2f}")
        
        return df

    except Exception as e:
        logger.error(f"Error identifying patterns: {str(e)}")
        raise

def identify_fvg(df: pd.DataFrame, validity_window: int = 5) -> pd.DataFrame:
    """Identify Fair Value Gaps (FVG).
    
    Args:
        df: DataFrame with OHLCV data
        validity_window: Maximum number of candles FVG remains active
        
    Returns:
        DataFrame with identified FVGs
    """
    try:
        logger.info("\nStarting FVG identification...")
        logger.info(f"Validity window: {validity_window} periods")
        
        df = df.copy()
        
        # Initialize columns
        df['fvg_active'] = 0
        df['fvg_size'] = 0.0
        df['fvg_type'] = 0
        df['fvg_start'] = -1.0
        df['fvg_end'] = -1.0
        
        # Use HT_TRENDLINE to identify trend direction
        df['trend'] = talib.HT_TRENDLINE(df['close'])
        
        # Calculate gaps using high/low
        df['gap_up'] = df['low'] > df['high'].shift(1)
        df['gap_down'] = df['high'] < df['low'].shift(1)
        
        # Calculate relative gap size to ATR
        df['gap_size'] = np.where(
            df['gap_up'],
            df['low'] - df['high'].shift(1),
            np.where(
                df['gap_down'],
                df['low'].shift(1) - df['high'],
                0
            )
        )
        df['gap_size_atr'] = df['gap_size'] / df['atr']
        
        bullish_fvgs = 0
        bearish_fvgs = 0
        
        # Identify significant FVGs
        for i in range(1, len(df) - 1):
            # Bullish FVG
            if df['gap_down'].iloc[i] and df['gap_size_atr'].iloc[i] > 0.1:
                fvg_size = abs(df['gap_size'].iloc[i])
                bullish_fvgs += 1
                
                # Mark FVG active until filled or expired
                for j in range(i, min(i + validity_window, len(df))):
                    if df['high'].iloc[j] > df['low'].iloc[i-1]:
                        break
                    df.at[j, 'fvg_active'] = 1
                    df.at[j, 'fvg_size'] = fvg_size
                    df.at[j, 'fvg_type'] = 1
                    df.at[j, 'fvg_start'] = df['high'].iloc[i]
                    df.at[j, 'fvg_end'] = df['low'].iloc[i-1]
            
            # Bearish FVG
            elif df['gap_up'].iloc[i] and df['gap_size_atr'].iloc[i] > 0.1:
                fvg_size = abs(df['gap_size'].iloc[i])
                bearish_fvgs += 1
                
                # Mark FVG active until filled or expired
                for j in range(i, min(i + validity_window, len(df))):
                    if df['low'].iloc[j] < df['high'].iloc[i-1]:
                        break
                    df.at[j, 'fvg_active'] = 1
                    df.at[j, 'fvg_size'] = fvg_size
                    df.at[j, 'fvg_type'] = -1
                    df.at[j, 'fvg_start'] = df['low'].iloc[i]
                    df.at[j, 'fvg_end'] = df['high'].iloc[i-1]
        
        # Log statistics
        logger.info(f"FVGs found: {bullish_fvgs + bearish_fvgs}")
        logger.info(f"  - Bullish: {bullish_fvgs}")
        logger.info(f"  - Bearish: {bearish_fvgs}")
        logger.info(f"Average size (ATR): {df[df['fvg_active'] == 1]['gap_size_atr'].mean():.2f}")
        
        # Clean temporary columns
        df = df.drop(['gap_up', 'gap_down', 'gap_size', 'gap_size_atr', 'trend'], axis=1)
        
        return df
        
    except Exception as e:
        logger.error(f"Error identifying FVGs: {str(e)}")
        raise

def add_candlestick_patterns(df: pd.DataFrame) -> pd.DataFrame:
    """Add candlestick patterns to DataFrame.
    
    Args:
        df: DataFrame with OHLCV data
        
    Returns:
        DataFrame with added candlestick patterns
    """
    try:
        logger.info("Adding candlestick patterns...")
        
        # Identify patterns with default validity window
        df = identify_patterns_and_confirm(df, timeframe='', trade_type='', validity_window=5)
        
        # Add FVGs
        df = identify_fvg(df)
        
        # Add price action features from candles module
        df = add_price_action_features(df)
        
        return df
        
    except Exception as e:
        logger.error(f"Error adding candlestick patterns: {str(e)}")
        raise
