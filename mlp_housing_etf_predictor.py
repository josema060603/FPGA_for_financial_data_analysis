"""
Housing ETF Daily Movement Prediction using Neural Network
============================================================
This script grabs historical Housing ETF data (like VNQ or XHB), 
calculates a bunch of technical indicators, and trains a neural network
to predict if the ETF will go up or down tomorrow.

Has multiple data sources in case one fails.
"""

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
    start_date = end_date - timedelta(days=years*365)
    print(f"Date range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    
    df = None
    
    # Trying yfinance first (usually works, sometimes needs a retry)
    print(f"\nMethod 1: yfinance")
    for attempt in range(1, 4):
        df = download_with_yfinance(ticker, start_date, end_date, attempt, 3)
        if df is not None and len(df) > 0:
            break
        if attempt < 3:
            time.sleep(2)  # wait a bit before retry
    
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
    
    print("\n" + "="*70)
    print("DATA DOWNLOAD SUMMARY")
    print("="*70)
    print(f"✓ Successfully obtained {len(df)} trading days of data")
    print(f"  Date range: {df.index[0].strftime('%Y-%m-%d')} to {df.index[-1].strftime('%Y-%m-%d')}")
    print(f"  Price range: ${df['Close'].min():.2f} to ${df['Close'].max():.2f}")
    print(f"  Data type: {'Synthetic (simulated)' if df.attrs.get('synthetic', False) else 'Real market data'}")
    print("="*70)
    
    return df


# ============================================================================
# DATA PREPROCESSING AND FEATURE ENGINEERING
# ============================================================================

def create_target_variable(df):
    """Creates the thing we're trying to predict - will it go up (1) or down (0) tomorrow?"""
    print("\nCreating target variable...")
    df['Next_Close'] = df['Close'].shift(-1)  # get tomorrow's close
    df['target'] = (df['Next_Close'] > df['Close']).astype(int)  # 1 if up, 0 if down
    df = df[:-1].copy()  # drop last row since we dont know next day
    print(f"Target distribution:\n{df['target'].value_counts()}")
    print(f"Percentage of up days: {df['target'].mean()*100:.2f}%")
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
    
    high, low, close, volume = df['High'], df['Low'], df['Close'], df['Volume']
    
    # Moving averages and trend stuff
    print("  - Trend indicators...")
    df['SMA_5'] = ta.trend.sma_indicator(close, window=5)
    df['SMA_10'] = ta.trend.sma_indicator(close, window=10)
    df['SMA_20'] = ta.trend.sma_indicator(close, window=20)
    df['SMA_50'] = ta.trend.sma_indicator(close, window=50)
    df['SMA_200'] = ta.trend.sma_indicator(close, window=200)  # the famous 200-day MA
    
    df['EMA_5'] = ta.trend.ema_indicator(close, window=5)
    df['EMA_10'] = ta.trend.ema_indicator(close, window=10)
    df['EMA_20'] = ta.trend.ema_indicator(close, window=20)
    df['EMA_50'] = ta.trend.ema_indicator(close, window=50)
    
    # MACD - moving average convergence divergence
    macd = ta.trend.MACD(close)
    df['MACD'] = macd.macd()
    df['MACD_signal'] = macd.macd_signal()
    df['MACD_diff'] = macd.macd_diff()
    
    # ADX shows trend strength
    adx = ta.trend.ADXIndicator(high, low, close)
    df['ADX'] = adx.adx()
    df['ADX_pos'] = adx.adx_pos()
    df['ADX_neg'] = adx.adx_neg()
    
    # Momentum stuff - shows if price movements are getting stronger or weaker
    print("  - Momentum indicators...")
    df['RSI_14'] = ta.momentum.rsi(close, window=14)  # standard RSI
    df['RSI_7'] = ta.momentum.rsi(close, window=7)
    df['RSI_21'] = ta.momentum.rsi(close, window=21)
    
    stoch = ta.momentum.StochasticOscillator(high, low, close)
    df['Stoch_K'] = stoch.stoch()
    df['Stoch_D'] = stoch.stoch_signal()
    
    df['CCI'] = ta.trend.cci(high, low, close, window=20)
    df['ROC'] = ta.momentum.roc(close, window=12)  # rate of change
    df['Williams_R'] = ta.momentum.williams_r(high, low, close)
    
    # Volatility indicators - how much the price is moving around
    print("  - Volatility indicators...")
    df['ATR'] = ta.volatility.average_true_range(high, low, close)
    
    # Bollinger Bands - price channels
    bollinger = ta.volatility.BollingerBands(close)
    df['BB_high'] = bollinger.bollinger_hband()
    df['BB_mid'] = bollinger.bollinger_mavg()
    df['BB_low'] = bollinger.bollinger_lband()
    df['BB_width'] = bollinger.bollinger_wband()
    df['BB_pct'] = bollinger.bollinger_pband()
    
    # Keltner Channels - similar to Bollinger but uses ATR
    keltner = ta.volatility.KeltnerChannel(high, low, close)
    df['Keltner_high'] = keltner.keltner_channel_hband()
    df['Keltner_low'] = keltner.keltner_channel_lband()
    
    # Volume based indicators - follow the money
    print("  - Volume indicators...")
    df['OBV'] = ta.volume.on_balance_volume(close, volume)
    df['CMF'] = ta.volume.chaikin_money_flow(high, low, close, volume)
    df['MFI'] = ta.volume.money_flow_index(high, low, close, volume)  # RSI but with volume
    df['VPT'] = ta.volume.volume_price_trend(close, volume)
    
    # Some custom features that might be useful
    print("  - Additional features...")
    df['Daily_Return'] = close.pct_change()
    df['Log_Return'] = np.log(close / close.shift(1))
    df['Volatility_10'] = df['Daily_Return'].rolling(window=10).std()
    df['Volatility_20'] = df['Daily_Return'].rolling(window=20).std()
    df['High_Low_Ratio'] = (close - low) / (high - low + 1e-10)  # where in daily range we closed
    df['SMA_5_20_cross'] = df['SMA_5'] - df['SMA_20']  # looking for golden/death crosses
    df['SMA_20_50_cross'] = df['SMA_20'] - df['SMA_50']
    df['EMA_5_20_cross'] = df['EMA_5'] - df['EMA_20']
    
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


def build_mlp_model(input_dim):
    """Build the neural network - 3 hidden layers with dropout to prevent overfitting."""
    print(f"\nBuilding MLP model with input dimension: {input_dim}")
    
    model = Sequential([
        Dense(64, activation='relu', input_dim=input_dim, name='hidden_1'),  # first hidden layer
        Dropout(0.3, name='dropout_1'),  # randomly drop 30% of neurons during training
        Dense(32, activation='relu', name='hidden_2'),  # second hidden layer
        Dropout(0.2, name='dropout_2'),
        Dense(16, activation='relu', name='hidden_3'),  # third hidden layer
        Dropout(0.2, name='dropout_3'),
        Dense(1, activation='sigmoid', name='output')  # output layer (sigmoid for binary classification)
    ])
    
    # Using adam optimizer and binary crossentropy since this is a binary classification problem
    model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])
    print("\nModel Summary:")
    model.summary()
    return model


def train_model(model, X_train, y_train, X_val, y_val, epochs=50, batch_size=32):
    """Train the model - using early stopping so it doesnt overtrain."""
    print(f"\nTraining model for up to {epochs} epochs...")
    
    # Stop training if validation loss stops improving (prevents overfitting)
    early_stop = callbacks.EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True, verbose=1)
    # Reduce learning rate if loss plateaus (helps with convergence)
    reduce_lr = callbacks.ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=5, min_lr=1e-6, verbose=1)
    
    history = model.fit(
        X_train, y_train,
        validation_data=(X_val, y_val),
        epochs=epochs,
        batch_size=batch_size,
        callbacks=[early_stop, reduce_lr],
        verbose=1
    )
    
    print("\nTraining completed!")
    return history


def plot_training_history(history, ticker):
    """Make some nice plots showing how the model trained."""
    fig, axes = plt.subplots(1, 2, figsize=(15, 5))
    
    axes[0].plot(history.history['accuracy'], label='Train Accuracy', linewidth=2)
    axes[0].plot(history.history['val_accuracy'], label='Val Accuracy', linewidth=2)
    axes[0].set_title(f'{ticker} Model Accuracy', fontsize=14, fontweight='bold')
    axes[0].set_xlabel('Epoch')
    axes[0].set_ylabel('Accuracy')
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)
    
    axes[1].plot(history.history['loss'], label='Train Loss', linewidth=2)
    axes[1].plot(history.history['val_loss'], label='Val Loss', linewidth=2)
    axes[1].set_title(f'{ticker} Model Loss', fontsize=14, fontweight='bold')
    axes[1].set_xlabel('Epoch')
    axes[1].set_ylabel('Loss')
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(f'training_history_{ticker.lower()}.png', dpi=300, bbox_inches='tight')
    print(f"\nTraining history saved as 'training_history_{ticker.lower()}.png'")
    plt.close()


def evaluate_model(model, X_test, y_test):
    """See how well the model actually performs on data it hasnt seen before."""
    print("\n" + "="*70)
    print("MODEL EVALUATION ON TEST SET")
    print("="*70)
    
    y_pred_proba = model.predict(X_test, verbose=0)  # get probabilities
    y_pred = (y_pred_proba > 0.5).astype(int).flatten()  # convert to 0 or 1
    
    # Calculate all the standard metrics
    accuracy = accuracy_score(y_test, y_pred)
    precision = precision_score(y_test, y_pred)
    recall = recall_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred)
    
    print(f"\nTest Set Metrics:")
    print(f"  Accuracy:  {accuracy:.4f} ({accuracy*100:.2f}%)")
    print(f"  Precision: {precision:.4f}")
    print(f"  Recall:    {recall:.4f}")
    print(f"  F1-Score:  {f1:.4f}")
    
    cm = confusion_matrix(y_test, y_pred)
    print(f"\nConfusion Matrix:")
    print(cm)
    
    print(f"\nDetailed Classification Report:")
    print(classification_report(y_test, y_pred, target_names=['Down (0)', 'Up (1)']))
    
    return y_pred, y_pred_proba.flatten()


def plot_confusion_matrix(y_test, y_pred, ticker):
    """Make a confusion matrix to visualize true positives, false positives, etc."""
    cm = confusion_matrix(y_test, y_pred)
    
    plt.figure(figsize=(8, 6))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', cbar=True,
                xticklabels=['Down (0)', 'Up (1)'],
                yticklabels=['Down (0)', 'Up (1)'])
    plt.title(f'{ticker} Confusion Matrix', fontsize=14, fontweight='bold')
    plt.ylabel('Actual')
    plt.xlabel('Predicted')
    plt.tight_layout()
    plt.savefig(f'confusion_matrix_{ticker.lower()}.png', dpi=300, bbox_inches='tight')
    print(f"\nConfusion matrix saved as 'confusion_matrix_{ticker.lower()}.png'")
    plt.close()


def save_model_and_scaler(model, scaler, ticker):
    """Save the trained model and scaler so we can use them later without retraining."""
    model_path = f'mlp_{ticker.lower()}.h5'
    scaler_path = f'scaler_{ticker.lower()}.pkl'
    
    print(f"\nSaving model to '{model_path}'...")
    model.save(model_path)
    print(f"Saving scaler to '{scaler_path}'...")
    joblib.dump(scaler, scaler_path)
    print("Model and scaler saved successfully!")


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
    
    print(f"\nTrain set: {len(X_train)} samples")
    print(f"Test set:  {len(X_test)} samples")
    
    # Split off some training data for validation
    X_train, X_val, y_train, y_val = train_test_split(
        X_train, y_train, test_size=0.1, random_state=42, stratify=y_train
    )
    
    # Step 5: Normalize the features
    X_train_scaled, X_val_scaled, scaler = normalize_features(X_train, X_val)
    X_test_scaled = scaler.transform(X_test)
    
    # Step 6: Build and train the model
    print("\n" + "="*70)
    print("MODEL BUILDING & TRAINING")
    print("="*70)
    
    model = build_mlp_model(input_dim=X_train_scaled.shape[1])
    history = train_model(model, X_train_scaled, y_train, X_val_scaled, y_val, epochs=50, batch_size=32)
    
    plot_training_history(history, ticker)
    
    # Step 7: Evaluate performance
    y_pred, y_pred_proba = evaluate_model(model, X_test_scaled, y_test)
    plot_confusion_matrix(y_test, y_pred, ticker)
    
    # Step 8: Save everything
    print("\n" + "="*70)
    print("SAVING MODEL")
    print("="*70)
    save_model_and_scaler(model, scaler, ticker)
    
    print("\n" + "="*70)
    print("COMPLETED SUCCESSFULLY!")
    print("="*70)
    print(f"\nGenerated Files:")
    print(f"  1. mlp_{ticker.lower()}.h5           - Trained model")
    print(f"  2. scaler_{ticker.lower()}.pkl       - Fitted scaler")
    print(f"  3. feature_names_{ticker.lower()}.txt - Feature list")
    print(f"  4. training_history_{ticker.lower()}.png - Training curves")
    print(f"  5. confusion_matrix_{ticker.lower()}.png - Performance matrix")
    print(f"\nETF: {ticker} - Housing/Real Estate sector")
    print(f"Data type: {'Synthetic' if df.attrs.get('synthetic', False) else 'Real market data'}")
    print("="*70)


if __name__ == "__main__":
    main()

