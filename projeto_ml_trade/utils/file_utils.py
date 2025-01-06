"""
File utilities.
"""
import os
import pandas as pd
from datetime import datetime
import json

def save_data(df: pd.DataFrame, symbol: str, timeframe: str, prefix: str = None, suffix: str = None, format: str = 'csv', directory: str = 'data') -> str:
    """Save data to file."""
    try:
        # Create directory if it doesn't exist
        os.makedirs(directory, exist_ok=True)
        
        # Create filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{symbol}_{timeframe}"

        if prefix:
            filename = f"{prefix}_{filename}"

        if suffix:
            filename = f"{filename}_{suffix}"
        
        # Add extension
        if format.lower() == 'parquet':
            filename = f"{filename}.parquet"
        else:
            filename = f"{filename}.csv"
            
        filepath = os.path.join(directory, filename)
        
        # Save data
        if format.lower() == 'parquet':
            df.to_parquet(filepath)
        else:
            # Save with index if it's a DatetimeIndex
            if isinstance(df.index, pd.DatetimeIndex):
                df.to_csv(filepath, index=True)
            else:
                # Check if timestamp column exists
                if 'timestamp' in df.columns:
                    # Set timestamp as index before saving
                    df = df.set_index('timestamp')
                    df.to_csv(filepath, index=True)
                else:
                    # No timestamp column or index, save without index
                    df.to_csv(filepath, index=False)
        
        return filepath
        
    except Exception as e:
        raise Exception(f"Error saving data: {str(e)}")

def load_data(filepath: str) -> pd.DataFrame:
    """Load data from file."""
    try:
        # Check if file exists
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"File not found: {filepath}")
        
        # Load data based on extension
        if filepath.endswith('.parquet'):
            df = pd.read_parquet(filepath)
        else:
            # Try to parse index as datetime
            try:
                df = pd.read_csv(filepath, index_col=0, parse_dates=True)
            except:
                # If parsing index fails, load without index
                df = pd.read_csv(filepath)
                
                # Try to set timestamp column as index if it exists
                if 'timestamp' in df.columns:
                    df['timestamp'] = pd.to_datetime(df['timestamp'])
                    df.set_index('timestamp', inplace=True)
            
            # Convert numeric columns
            numeric_cols = ['open', 'high', 'low', 'close', 'volume']
            for col in numeric_cols:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Ensure index is datetime if timestamp column exists
        if not isinstance(df.index, pd.DatetimeIndex) and 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df.set_index('timestamp', inplace=True)
        
        return df
        
    except Exception as e:
        raise Exception(f"Error loading data: {str(e)}")

def list_data_files(directory: str = 'data', pattern: str = '*.*') -> list:
    """List data files in directory."""
    try:
        # Check if directory exists
        if not os.path.exists(directory):
            raise FileNotFoundError(f"Directory not found: {directory}")
        
        # Get list of files
        import glob
        files = glob.glob(os.path.join(directory, pattern))
        
        # Sort by modification time (newest first)
        files.sort(key=os.path.getmtime, reverse=True)
        
        return files
        
    except Exception as e:
        raise Exception(f"Error listing files: {str(e)}")

def save_json(data: dict, filepath: str):
    """Save data to JSON file."""
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        # Save data
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=4)
            
    except Exception as e:
        raise Exception(f"Error saving JSON: {str(e)}")

def load_json(filepath: str) -> dict:
    """Load data from JSON file."""
    try:
        # Check if file exists
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"File not found: {filepath}")
        
        # Load data
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        return data
        
    except Exception as e:
        raise Exception(f"Error loading JSON: {str(e)}")
