"""
Housing ETF Daily Movement Prediction using Neural Network
============================================================
This script grabs historical Housing ETF data (like VNQ or XHB), 
calculates a bunch of technical indicators, and trains a neural network
to predict if the ETF will go up or down tomorrow.

Has multiple data sources in case one fails.
"""

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# Data sources - trying a few options in case Yahoo is acting up
import yfinance as yf
try:
    import pandas_datareader as pdr
    HAS_DATAREADER = True
except:
    HAS_DATAREADER = False

try:
    import yahooquery as yq
    HAS_YAHOOQUERY = True
except:
    HAS_YAHOOQUERY = False

# Technical indicators library
import ta

# sklearn stuff for machine learning
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import (accuracy_score, precision_score, recall_score, 
                             f1_score, confusion_matrix, classification_report)

# TensorFlow/Keras for the neural network
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers, callbacks
from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.layers import Dense, Dropout

# Other useful stuff
import joblib
import os
import time

# Setting seeds so results are reproducible
np.random.seed(42)
tf.random.set_seed(42)

# Making plots look nice
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (12, 6)


# ============================================================================
# 1. DATA DOWNLOAD (trying multiple sources since Yahoo API can be flaky)
# ============================================================================

def download_with_yfinance(ticker, start_date, end_date, attempt=1, max_attempts=3):
    """Tries to download data using yfinance - usually works but sometimes doesn't."""
    print(f"  Attempt {attempt}/{max_attempts}: Trying yfinance...")
    try:
        df = yf.download(ticker, start=start_date, end=end_date, progress=False)
        if len(df) > 0:
            print(f"  ✓ Success with yfinance! Downloaded {len(df)} days")
            return df
        else:
            print(f"  ✗ yfinance returned no data")
            return None
    except Exception as e:
        print(f"  ✗ yfinance failed: {e}")
        return None


def download_with_yahooquery(ticker, start_date, end_date):
    """Another Yahoo API option - this one works differently."""
    if not HAS_YAHOOQUERY:
        return None
    
    print(f"  Trying yahooquery...")
    try:
        stock = yq.Ticker(ticker)
        df = stock.history(start=start_date, end=end_date)
        
        if df is not None and len(df) > 0:
            # Sometimes has a weird multi-index, need to fix that
            if isinstance(df.index, pd.MultiIndex):
                df = df.reset_index(level=0, drop=True)
            
            # Column names are lowercase, need to capitalize them
            column_mapping = {
                'open': 'Open',
                'high': 'High', 
                'low': 'Low',
                'close': 'Close',
                'volume': 'Volume',
                'adjclose': 'Adj Close'
            }
            df = df.rename(columns=column_mapping)
            
            # Make sure we have an adjusted close column
            if 'Adj Close' not in df.columns and 'Close' in df.columns:
                df['Adj Close'] = df['Close']
            
            print(f"  ✓ Success with yahooquery! Downloaded {len(df)} days")
            return df
        else:
            print(f"  ✗ yahooquery returned no data")
            return None
    except Exception as e:
        print(f"  ✗ yahooquery failed: {e}")
        return None


def download_with_datareader(ticker, start_date, end_date):
    """Yet another option using pandas_datareader - old but sometimes reliable."""
    if not HAS_DATAREADER:
        return None
    
    print(f"  Trying pandas_datareader...")
    try:
        # Try Yahoo first
        df = pdr.get_data_yahoo(ticker, start=start_date, end=end_date)
        if len(df) > 0:
            print(f"  ✓ Success with pandas_datareader! Downloaded {len(df)} days")
            return df
        else:
            print(f"  ✗ pandas_datareader returned no data")
            return None
    except Exception as e:
        print(f"  ✗ pandas_datareader failed: {e}")
        return None


def generate_realistic_etf_data(ticker, years=10):
    """If all download methods fail, generate fake but realistic data so we can still test the model."""
    print(f"  Generating realistic synthetic data for {ticker}...")
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=years*365)
    dates = pd.date_range(start=start_date, end=end_date, freq='B')  # B = business days
    n_days = len(dates)
    
    # Using different stats for different housing ETFs
    if 'VNQ' in ticker:
        initial_price = 80  # typical VNQ price
        annual_return = 0.08
        annual_volatility = 0.18
    elif 'XHB' in ticker:
        initial_price = 50  # typical XHB price
        annual_return = 0.10
        annual_volatility = 0.22
    else:
        initial_price = 100
        annual_return = 0.09
        annual_volatility = 0.20
    
    # Simulating daily returns with some realistic patterns
    returns = []
    for i in range(n_days):
        drift = annual_return / 252  # 252 trading days per year
        volatility = annual_volatility / np.sqrt(252)
        
        # Housing market is cyclical, adding a sine wave pattern
        cycle = np.sin(i / 1260) * 0.003  # roughly 5 year cycle
        
        # Momentum effect - past returns influence future ones
        if i > 20:
            momentum = np.mean(returns[-20:]) * 0.3
        else:
            momentum = 0
        
        daily_return = drift + momentum + cycle + volatility * np.random.randn()
        returns.append(daily_return)
    
    returns = np.array(returns)
    cumulative_returns = np.exp(np.cumsum(returns))
    close_prices = initial_price * cumulative_returns
    
    # Creating Open, High, Low, Close data
    high_prices = close_prices * (1 + np.abs(np.random.randn(n_days) * 0.01))
    low_prices = close_prices * (1 - np.abs(np.random.randn(n_days) * 0.01))
    open_prices = np.roll(close_prices, 1) * (1 + np.random.randn(n_days) * 0.003)
    open_prices[0] = initial_price
    
    # Making sure high is actually the highest and low is actually the lowest
    high_prices = np.maximum(high_prices, np.maximum(open_prices, close_prices))
    low_prices = np.minimum(low_prices, np.minimum(open_prices, close_prices))
    
    # Volume data (housing ETFs usually have less volume than like SPY)
    base_volume = 5e6  # 5 million shares base
    volume = base_volume * (1 + 0.5 * np.abs(returns) + 0.3 * np.random.randn(n_days))
    volume = np.abs(volume)
    
    df = pd.DataFrame({
        'Open': open_prices,
        'High': high_prices,
        'Low': low_prices,
        'Close': close_prices,
        'Adj Close': close_prices,
        'Volume': volume
    }, index=dates)
    
    print(f"  ✓ Generated {len(df)} days of synthetic data")
    return df


def download_etf_data(ticker='VNQ', years=10):
    """
    Downloads housing ETF data - tries multiple sources because Yahoo can be unreliable.
    
    ticker: ETF symbol like VNQ, XHB, XLRE, etc.
    years: how many years of history to grab
    
    Returns a dataframe with Open, High, Low, Close, Volume data
    """
    print("="*70)
    print(f"DOWNLOADING HOUSING ETF DATA: {ticker}")
    print("="*70)
    
    # Quick reference for what these ETFs actually are
    etf_names = {
        'VNQ': 'Vanguard Real Estate ETF',
        'XHB': 'SPDR S&P Homebuilders ETF',
        'XLRE': 'Real Estate Select Sector SPDR Fund',
        'IYR': 'iShares U.S. Real Estate ETF',
        'REZ': 'iShares Residential Real Estate ETF'
    }
    
    print(f"\nETF: {etf_names.get(ticker, ticker)}")
    print(f"Ticker: {ticker}")
    print(f"Period: {years} years")
    end_date = datetime.now()
    # end_date = datetime.now() - timedelta(days=years*365)
    start_date = end_date - timedelta(days=years*365)
    print(f"Date range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    
    df = None
    
    # Trying yfinance first (usually works, sometimes needs a retry)
    # print(f"\nMethod 1: yfinance")
    # for attempt in range(1, 4):
    #     df = download_with_yfinance(ticker, start_date, end_date, attempt, 3)
    #     if df is not None and len(df) > 0:
    #         break
    #     if attempt < 3:
    #         time.sleep(2)  # wait a bit before retry
    
    # If that didnt work, try yahooquery
    if df is None or len(df) == 0:
        print(f"\nMethod 2: yahooquery")
        if HAS_YAHOOQUERY:
            df = download_with_yahooquery(ticker, start_date, end_date)
        else:
            print(f"  ✗ yahooquery not installed (pip install yahooquery)")
    
    # Still nothing? Try pandas_datareader
    if df is None or len(df) == 0:
        print(f"\nMethod 3: pandas_datareader")
        if HAS_DATAREADER:
            df = download_with_datareader(ticker, start_date, end_date)
        else:
            print(f"  ✗ pandas_datareader not installed (pip install pandas-datareader)")
    
    # If everything failed, just generate fake data so we can at least test
    if df is None or len(df) == 0:
        print(f"\nMethod 4: Synthetic Data (fallback)")
        print(f"⚠ All download methods failed. Using realistic synthetic data.")
        df = generate_realistic_etf_data(ticker, years)
        df.attrs['synthetic'] = True
    else:
        df.attrs['synthetic'] = False
    
 # --- NEW: normalize Close into a 1D numeric Series ---
    close = df['Close']
    # If df['Close'] is actually a DataFrame (e.g. multiple Close columns), pick the first one
    if isinstance(close, pd.DataFrame):
        if close.shape[1] > 1:
            print("  (Multiple 'Close' columns detected, using the first one)")
        close = close.iloc[:, 0]

    # ensure numeric
    close = pd.to_numeric(close, errors='coerce')
    df['Close'] = close  # overwrite so the rest of the code works with a clean Series

    price_min = float(close.min())
    price_max = float(close.max())
    # -----------------------------------------------------

    print("\n" + "="*70)
    print("DATA DOWNLOAD SUMMARY")
    print("="*70)
    print(f"✓ Successfully obtained {len(df)} trading days of data")
    print(f"  Date range: {df.index[0].strftime('%Y-%m-%d')} to {df.index[-1].strftime('%Y-%m-%d')}")
    print(f"  Price range: ${price_min:.2f} to ${price_max:.2f}")
    print(f"  Data type: {'Synthetic (simulated)' if df.attrs.get('synthetic', False) else 'Real market data'}")
    print("="*70)

    
    return df


# ============================================================================
# DATA PREPROCESSING AND FEATURE ENGINEERING
# ============================================================================

def create_target_variable(df):
    """Creates the thing we're trying to predict - will it go up (1) or down (0) tomorrow?"""
    print("\nCreating target variable...")

    # 1) Make sure Close is a 1D numeric Series
    close = df["Close"]

    # If Close is actually a DataFrame (e.g., multi-index columns), take the first column
    if isinstance(close, pd.DataFrame):
        if close.shape[1] > 1:
            print("  (Multiple 'Close' columns detected, using the first one)")
        close = close.iloc[:, 0]

    close = pd.to_numeric(close, errors="coerce")

    # Put cleaned Close back into df
    df["Close"] = close

    # 2) Compute next day's close and target from these aligned Series
    next_close = close.shift(-1)
    target = (next_close > close).astype(int)

    # 3) Drop last row (no next day info) and assign columns
    df = df.iloc[:-1].copy()
    df["Next_Close"] = next_close.iloc[:-1]
    df["target"] = target.iloc[:-1]

    print(f"Target distribution:\n{df['target'].value_counts()}")
    print(f"Percentage of up days: {df['target'].mean() * 100:.2f}%")
    return df



def create_lagged_features(df, lags=10):
    """Add historical data from previous days - helps capture trends and patterns."""
    print(f"\nCreating {lags} lagged features...")
    # Adding past prices
    for i in range(1, lags + 1):
        df[f'Close_lag_{i}'] = df['Close'].shift(i)
    # Adding past returns
    df['Returns'] = df['Close'].pct_change()
    for i in range(1, lags + 1):
        df[f'Returns_lag_{i}'] = df['Returns'].shift(i)
    # Adding past volume
    for i in range(1, lags + 1):
        df[f'Volume_lag_{i}'] = df['Volume'].shift(i)
    return df


def calculate_technical_indicators(df):
    """Calculate a bunch of technical indicators that traders use - gives the model more info to work with."""
    print("\nCalculating technical indicators...")

    # Helper to force a column to 1D numeric Series
    def _col_1d(frame, colname):
        col = frame[colname]
        # If it's a DataFrame (e.g. shape (N,1)), take the first column
        if isinstance(col, pd.DataFrame):
            if col.shape[1] > 1:
                print(f"  (Multiple '{colname}' columns detected, using the first one)")
            col = col.iloc[:, 0]
        # Coerce to numeric
        col = pd.to_numeric(col, errors="coerce")
        return col

    high   = _col_1d(df, "High")
    low    = _col_1d(df, "Low")
    close  = _col_1d(df, "Close")
    volume = _col_1d(df, "Volume")

    # Moving averages and trend stuff
    print("  - Trend indicators...")
    df["SMA_5"]   = ta.trend.sma_indicator(close, window=5)
    df["SMA_10"]  = ta.trend.sma_indicator(close, window=10)
    df["SMA_20"]  = ta.trend.sma_indicator(close, window=20)
    df["SMA_50"]  = ta.trend.sma_indicator(close, window=50)
    df["SMA_200"] = ta.trend.sma_indicator(close, window=200)

    df["EMA_5"]   = ta.trend.ema_indicator(close, window=5)
    df["EMA_10"]  = ta.trend.ema_indicator(close, window=10)
    df["EMA_20"]  = ta.trend.ema_indicator(close, window=20)
    df["EMA_50"]  = ta.trend.ema_indicator(close, window=50)

    # MACD - moving average convergence divergence
    macd = ta.trend.MACD(close)
    df["MACD"]       = macd.macd()
    df["MACD_signal"] = macd.macd_signal()
    df["MACD_diff"]  = macd.macd_diff()

    # ADX shows trend strength
    adx = ta.trend.ADXIndicator(high, low, close)
    df["ADX"]     = adx.adx()
    df["ADX_pos"] = adx.adx_pos()
    df["ADX_neg"] = adx.adx_neg()

    # Momentum stuff
    print("  - Momentum indicators...")
    df["RSI_14"] = ta.momentum.rsi(close, window=14)
    df["RSI_7"]  = ta.momentum.rsi(close, window=7)
    df["RSI_21"] = ta.momentum.rsi(close, window=21)

    stoch = ta.momentum.StochasticOscillator(high, low, close)
    df["Stoch_K"] = stoch.stoch()
    df["Stoch_D"] = stoch.stoch_signal()

    df["CCI"]        = ta.trend.cci(high, low, close, window=20)
    df["ROC"]        = ta.momentum.roc(close, window=12)
    df["Williams_R"] = ta.momentum.williams_r(high, low, close)

    # Volatility indicators
    print("  - Volatility indicators...")
    df["ATR"] = ta.volatility.average_true_range(high, low, close)

    bollinger = ta.volatility.BollingerBands(close)
    df["BB_high"]  = bollinger.bollinger_hband()
    df["BB_mid"]   = bollinger.bollinger_mavg()
    df["BB_low"]   = bollinger.bollinger_lband()
    df["BB_width"] = bollinger.bollinger_wband()
    df["BB_pct"]   = bollinger.bollinger_pband()

    keltner = ta.volatility.KeltnerChannel(high, low, close)
    df["Keltner_high"] = keltner.keltner_channel_hband()
    df["Keltner_low"]  = keltner.keltner_channel_lband()

    # Volume based indicators
    print("  - Volume indicators...")
    df["OBV"] = ta.volume.on_balance_volume(close, volume)
    df["CMF"] = ta.volume.chaikin_money_flow(high, low, close, volume)
    df["MFI"] = ta.volume.money_flow_index(high, low, close, volume)
    df["VPT"] = ta.volume.volume_price_trend(close, volume)

    # Custom features
    print("  - Additional features...")
    df["Daily_Return"]   = close.pct_change()
    df["Log_Return"]     = np.log(close / close.shift(1))
    df["Volatility_10"]  = df["Daily_Return"].rolling(window=10).std()
    df["Volatility_20"]  = df["Daily_Return"].rolling(window=20).std()
    df["High_Low_Ratio"] = (close - low) / (high - low + 1e-10)
    df["SMA_5_20_cross"] = df["SMA_5"] - df["SMA_20"]
    df["SMA_20_50_cross"] = df["SMA_20"] - df["SMA_50"]
    df["EMA_5_20_cross"]  = df["EMA_5"] - df["EMA_20"]

    print(f"Total features created: {len(df.columns)}")
    return df


def preprocess_data(df):
    """Clean up the data and get it ready for the model."""
    print("\nPreprocessing data...")
    initial_len = len(df)
    df = df.dropna()  # remove any rows with missing values
    print(f"Dropped {initial_len - len(df)} rows with NaN values")
    print(f"Remaining data points: {len(df)}")
    
    # Don't want to use these as features (either they're the target or would cause data leakage)
    exclude_cols = ['target', 'Next_Close', 'Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume']
    feature_cols = [col for col in df.columns if col not in exclude_cols]
    
    X = df[feature_cols].values  # features
    y = df['target'].values  # target (up or down)
    
    print(f"Feature matrix shape: {X.shape}")
    print(f"Target shape: {y.shape}")
    
    # Sometimes get infinity values from calculations, need to fix those
    if np.any(np.isinf(X)):
        X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)
    
    return X, y, feature_cols


def normalize_features(X_train, X_test):
    """Scale features to have mean=0 and std=1 - helps the neural network train better."""
    print("\nNormalizing features...")
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)  # fit on training data
    X_test_scaled = scaler.transform(X_test)  # apply same scaling to test data
    return X_train_scaled, X_test_scaled, scaler

def main():
    """Main function that runs everything."""
    print("="*70)
    print("HOUSING ETF MLP PREDICTOR")
    print("="*70)
    
    # Pick which ETF to analyze
    ticker = 'VNQ'  # Vanguard Real Estate ETF
    # Other options: 'XHB' (Homebuilders), 'XLRE', 'IYR', 'REZ'
    
    # Step 1: Get the data
    df = download_etf_data(ticker=ticker, years=10)
    
    # Step 2: Create features and target
    df = create_target_variable(df)
    df = create_lagged_features(df, lags=10)
    df = calculate_technical_indicators(df)
    
    # Step 3: Prepare data for model
    X, y, feature_names = preprocess_data(df)
    
    # Save feature names for reference
    with open(f'feature_names_{ticker.lower()}.txt', 'w') as f:
        for i, name in enumerate(feature_names, 1):
            f.write(f"{i}. {name}\n")
    print(f"\nFeature names saved to 'feature_names_{ticker.lower()}.txt'")
    
    # Step 4: Split into train and test sets
    print("\n" + "="*70)
    print("SPLITTING DATA")
    print("="*70)
    
    split_idx = int(len(X) * 0.8)  # 80/20 split
    X_train, X_test = X[:split_idx], X[split_idx:]
    y_train, y_test = y[:split_idx], y[split_idx:]
    
    OUT_DIR = Path("prepared")
    OUT_DIR.mkdir(exist_ok=True, parents=True)  
    

    np.save(OUT_DIR/"X_test.npy",   X_test)
    np.save(OUT_DIR/"y_test.npy",   y_test)

    print("X_test shape:", X_test.shape)
    print(f"Test set:  {len(X_test)} samples")
    
    # Split off some training data for validation
    X_train, X_val, y_train, y_val = train_test_split(
        X_train, y_train, test_size=0.1, random_state=42, stratify=y_train
    )
    
    print("\n" + "="*70)
    print("COMPLETED SUCCESSFULLY!")
    print("="*70)
    print(f"\nGenerated Files: numpy files with data for HLS")
    print("="*70)


if __name__ == "__main__":
    main()

