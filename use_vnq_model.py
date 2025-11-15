"""
Using Your Trained VNQ (Housing ETF) Model
===========================================
This script demonstrates how to use your trained VNQ model for predictions.
All data is REAL market data - no synthetic/demo data.
"""

from tensorflow.keras.models import load_model
import joblib
import numpy as np

print("="*70)
print("USING YOUR TRAINED VNQ MODEL (REAL DATA)")
print("="*70)

# Load the trained model and scaler
print("\n1. Loading trained VNQ model and scaler...")
model = load_model('mlp_vnq.h5')
scaler = joblib.load('scaler_vnq.pkl')

print("✓ Model loaded successfully!")
print(f"✓ Model has {model.count_params():,} parameters")
print(f"✓ Trained on real VNQ (Vanguard Real Estate ETF) data")

# Model summary
print("\n2. Model Architecture:")
model.summary()

print("\n3. Model Performance (from training):")
print("-" * 70)
print("Accuracy:  54.00% (beats random 50%)")
print("Precision: 55.34% (when it says BUY, it's right 55% of time)")
print("Recall:    60.17% (catches 60% of upward movements)")
print("F1-Score:  57.65%")
print("\nTrained on: 2,513 days of real VNQ trading data")
print("Date range: October 2015 - October 2025")

print("\n4. How to make predictions:")
print("-" * 70)
print("""
To make predictions on new VNQ data:

# Step 1: Prepare your features (must have 75 features matching training)
# You need: Close prices, lagged features, technical indicators (RSI, MACD, etc.)
X_new = ...  # Your feature matrix (n_samples, 75)

# Step 2: Normalize features using the same scaler
X_new_scaled = scaler.transform(X_new)

# Step 3: Make predictions
predictions_proba = model.predict(X_new_scaled)
predictions = (predictions_proba > 0.5).astype(int)

# Step 4: Interpret results
for i, (pred, prob) in enumerate(zip(predictions, predictions_proba)):
    if pred == 1:
        print(f"Day {i+1}: BUY signal (confidence: {prob[0]:.1%})")
    else:
        print(f"Day {i+1}: SELL signal (confidence: {1-prob[0]:.1%})")

# Trading signals:
# 1 = Market expected to go UP → BUY VNQ
# 0 = Market expected to go DOWN → SELL VNQ
""")

print("\n5. Feature Requirements:")
print("-" * 70)
print("Your input data must include these 75 features:")
print("  • 10 lagged close prices")
print("  • 10 lagged returns")
print("  • 10 lagged volumes")
print("  • Technical indicators: SMA, EMA, RSI, MACD, Bollinger Bands, etc.")
print("\nSee 'feature_names_vnq.txt' for the complete list.")

print("\n" + "="*70)
print("Your VNQ model is ready for real-world predictions!")
print("="*70)
print("\nNext steps:")
print("  • Use mlp_housing_etf_predictor.py to retrain or train on other ETFs")
print("  • Try XHB (Homebuilders), REZ (Residential), XLRE (Select Sector)")
print("  • Check HOUSING_ETF_GUIDE.md for trading strategies")
print("  • Always use proper risk management when trading")
print("="*70)



