"""
Example script showing how to use the trained MLP model for making new predictions.

This script demonstrates:
1. Loading the saved model and scaler
2. Downloading recent data
3. Computing features
4. Making predictions

Usage:
    python predict_example.py
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import yfinance as yf
import ta
from tensorflow.keras.models import load_model
import joblib

# Set random seed
np.random.seed(42)


def download_recent_data(days=300):
    """Download recent S&P 500 data for prediction."""
    print(f"Downloading recent S&P 500 data ({days} days)...")
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    df = yf.download("^GSPC", start=start_date, end=end_date, progress=False)
    print(f"Downloaded {len(df)} trading days")
    
    return df


def compute_all_features(df):
    """
    Compute all features exactly as in training.
    This must match the feature engineering in mlp_snp500_predictor.py
    """
    print("Computing features...")
    
    # Lagged features (10 days)
    for i in range(1, 11):
        df[f'Close_lag_{i}'] = df['Close'].shift(i)
    
    df['Returns'] = df['Close'].pct_change()
    for i in range(1, 11):
        df[f'Returns_lag_{i}'] = df['Returns'].shift(i)
    
    for i in range(1, 11):
        df[f'Volume_lag_{i}'] = df['Volume'].shift(i)
    
    # Technical indicators
    high, low, close, volume = df['High'], df['Low'], df['Close'], df['Volume']
    
    # Trend indicators
    df['SMA_5'] = ta.trend.sma_indicator(close, window=5)
    df['SMA_10'] = ta.trend.sma_indicator(close, window=10)
    df['SMA_20'] = ta.trend.sma_indicator(close, window=20)
    df['SMA_50'] = ta.trend.sma_indicator(close, window=50)
    df['SMA_200'] = ta.trend.sma_indicator(close, window=200)
    
    df['EMA_5'] = ta.trend.ema_indicator(close, window=5)
    df['EMA_10'] = ta.trend.ema_indicator(close, window=10)
    df['EMA_20'] = ta.trend.ema_indicator(close, window=20)
    df['EMA_50'] = ta.trend.ema_indicator(close, window=50)
    
    macd = ta.trend.MACD(close)
    df['MACD'] = macd.macd()
    df['MACD_signal'] = macd.macd_signal()
    df['MACD_diff'] = macd.macd_diff()
    
    adx = ta.trend.ADXIndicator(high, low, close)
    df['ADX'] = adx.adx()
    df['ADX_pos'] = adx.adx_pos()
    df['ADX_neg'] = adx.adx_neg()
    
    # Momentum indicators
    df['RSI_14'] = ta.momentum.rsi(close, window=14)
    df['RSI_7'] = ta.momentum.rsi(close, window=7)
    df['RSI_21'] = ta.momentum.rsi(close, window=21)
    
    stoch = ta.momentum.StochasticOscillator(high, low, close)
    df['Stoch_K'] = stoch.stoch()
    df['Stoch_D'] = stoch.stoch_signal()
    
    df['CCI'] = ta.trend.cci(high, low, close, window=20)
    df['ROC'] = ta.momentum.roc(close, window=12)
    df['Williams_R'] = ta.momentum.williams_r(high, low, close)
    
    # Volatility indicators
    df['ATR'] = ta.volatility.average_true_range(high, low, close)
    
    bollinger = ta.volatility.BollingerBands(close)
    df['BB_high'] = bollinger.bollinger_hband()
    df['BB_mid'] = bollinger.bollinger_mavg()
    df['BB_low'] = bollinger.bollinger_lband()
    df['BB_width'] = bollinger.bollinger_wband()
    df['BB_pct'] = bollinger.bollinger_pband()
    
    keltner = ta.volatility.KeltnerChannel(high, low, close)
    df['Keltner_high'] = keltner.keltner_channel_hband()
    df['Keltner_low'] = keltner.keltner_channel_lband()
    
    # Volume indicators
    df['OBV'] = ta.volume.on_balance_volume(close, volume)
    df['CMF'] = ta.volume.chaikin_money_flow(high, low, close, volume)
    df['MFI'] = ta.volume.money_flow_index(high, low, close, volume)
    df['VPT'] = ta.volume.volume_price_trend(close, volume)
    
    # Additional features
    df['Daily_Return'] = close.pct_change()
    df['Log_Return'] = np.log(close / close.shift(1))
    df['Volatility_10'] = df['Daily_Return'].rolling(window=10).std()
    df['Volatility_20'] = df['Daily_Return'].rolling(window=20).std()
    df['High_Low_Ratio'] = (close - low) / (high - low + 1e-10)
    df['SMA_5_20_cross'] = df['SMA_5'] - df['SMA_20']
    df['SMA_20_50_cross'] = df['SMA_20'] - df['SMA_50']
    df['EMA_5_20_cross'] = df['EMA_5'] - df['EMA_20']
    
    return df


def prepare_features_for_prediction(df):
    """Extract feature matrix matching training format."""
    # Exclude OHLCV columns (same as training)
    exclude_cols = ['Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume']
    feature_cols = [col for col in df.columns if col not in exclude_cols]
    
    # Get features and handle NaN
    X = df[feature_cols].values
    
    # Replace infinite values
    X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)
    
    return X


def make_prediction(model, scaler, X):
    """Make predictions using the trained model."""
    # Scale features
    X_scaled = scaler.transform(X)
    
    # Predict
    predictions_proba = model.predict(X_scaled, verbose=0)
    predictions = (predictions_proba > 0.5).astype(int).flatten()
    
    return predictions, predictions_proba.flatten()


def main():
    """Main function to demonstrate model usage."""
    print("="*70)
    print("S&P 500 PREDICTION EXAMPLE")
    print("="*70)
    
    # Check if model files exist
    try:
        print("\nLoading trained model and scaler...")
        model = load_model('mlp_snp500.h5')
        scaler = joblib.load('scaler.pkl')
        print("✓ Model and scaler loaded successfully")
    except FileNotFoundError:
        print("\n❌ Error: Model files not found!")
        print("Please run 'mlp_snp500_predictor.py' first to train the model.")
        return
    
    # Download recent data
    df = download_recent_data(days=300)
    
    # Compute features
    df = compute_all_features(df)
    
    # Remove NaN rows
    df_clean = df.dropna()
    print(f"Clean data points: {len(df_clean)}")
    
    # Prepare features
    X = prepare_features_for_prediction(df_clean)
    
    # Make predictions
    print("\nMaking predictions...")
    predictions, predictions_proba = make_prediction(model, scaler, X)
    
    # Get the last N predictions
    n_display = min(10, len(predictions))
    
    print("\n" + "="*70)
    print(f"MOST RECENT {n_display} PREDICTIONS")
    print("="*70)
    
    dates = df_clean.index[-n_display:]
    closes = df_clean['Close'].values[-n_display:]
    preds = predictions[-n_display:]
    probas = predictions_proba[-n_display:]
    
    print(f"\n{'Date':<12} {'Close Price':<12} {'Prediction':<15} {'Confidence':<12} {'Signal':<10}")
    print("-" * 70)
    
    for i, (date, close_price, pred, proba) in enumerate(zip(dates, closes, preds, probas)):
        pred_text = "UP ↑" if pred == 1 else "DOWN ↓"
        signal = "BUY" if pred == 1 else "SELL"
        confidence = proba if pred == 1 else (1 - proba)
        
        print(f"{date.strftime('%Y-%m-%d'):<12} ${close_price:>9.2f}   {pred_text:<13} {confidence:>6.1%}      {signal:<10}")
    
    # Most recent prediction (tomorrow)
    print("\n" + "="*70)
    print("NEXT DAY PREDICTION")
    print("="*70)
    
    latest_date = dates[-1]
    latest_close = closes[-1]
    latest_pred = preds[-1]
    latest_proba = probas[-1]
    latest_confidence = latest_proba if latest_pred == 1 else (1 - latest_proba)
    
    print(f"\nBased on data up to: {latest_date.strftime('%Y-%m-%d')}")
    print(f"Latest close price: ${latest_close:.2f}")
    print(f"\nPrediction for next trading day:")
    
    if latest_pred == 1:
        print(f"  📈 Market expected to go UP")
        print(f"  🟢 Signal: BUY")
    else:
        print(f"  📉 Market expected to go DOWN")
        print(f"  🔴 Signal: SELL")
    
    print(f"  Confidence: {latest_confidence:.1%}")
    
    print("\n" + "="*70)
    print("DISCLAIMER")
    print("="*70)
    print("This is for educational purposes only and NOT financial advice.")
    print("Past performance does not guarantee future results.")
    print("Always consult a qualified financial advisor before trading.")
    print("="*70)


if __name__ == "__main__":
    main()



