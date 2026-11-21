"""
features.py
------------
Computes comprehensive technical indicators used as ML features (34 total):
  - Trend & Moving Averages (SMA 5, 10, 20, 50; EMA 5, 9, 12, 20, 26)
  - Price-to-MA and MA crossover alignments
  - MACD (Line, Signal, Histogram, Histogram Slope)
  - Multi-period RSI (7, 14, 21 days)
  - Fast/Slow Stochastics (%K, %D) & Williams %R
  - Bollinger Bands (Width, %B)
  - Multi-day return momentum & return lags (Lag 1, Lag 2)
  - Rolling Volatility (10-day, 20-day)
  - Candlestick Price Action (Body size, Upper shadow, Lower shadow)
  - Volume Dynamics (Volume Ratio vs 10-day SMA, Volume Change)
"""

import pandas as pd
import numpy as np


def compute_rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = (-delta.clip(upper=0)).rolling(period).mean()
    rs = gain / loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    return rsi.fillna(50)


def add_features(df):
    """
    df must be a single-symbol OHLCV dataframe sorted by date.
    Returns dataframe with 34 engineered technical indicator features and Target.
    """
    df = df.copy()
    close = df["Close"]
    high = df["High"]
    low = df["Low"]
    open_p = df["Open"]
    volume = df["Volume"]

    # Returns across multiple lookback horizons
    df["Return_1"] = close.pct_change(1)
    df["Return_2"] = close.pct_change(2)
    df["Return_3"] = close.pct_change(3)
    df["Return_5"] = close.pct_change(5)
    df["Return_10"] = close.pct_change(10)

    # Return Lags for serial autocorrelation capture
    df["Return_Lag1"] = df["Return_1"].shift(1)
    df["Return_Lag2"] = df["Return_1"].shift(2)

    # Moving Averages (Simple & Exponential)
    df["SMA_5"] = close.rolling(5).mean()
    df["SMA_10"] = close.rolling(10).mean()
    df["SMA_20"] = close.rolling(20).mean()
    df["SMA_50"] = close.rolling(50).mean()

    df["EMA_5"] = close.ewm(span=5, adjust=False).mean()
    df["EMA_9"] = close.ewm(span=9, adjust=False).mean()
    df["EMA_12"] = close.ewm(span=12, adjust=False).mean()
    df["EMA_20"] = close.ewm(span=20, adjust=False).mean()
    df["EMA_26"] = close.ewm(span=26, adjust=False).mean()

    # Normalized Price-to-Moving-Average and Crossover Features
    df["Price_to_SMA5"] = close / df["SMA_5"] - 1
    df["Price_to_SMA10"] = close / df["SMA_10"] - 1
    df["Price_to_SMA20"] = close / df["SMA_20"] - 1
    df["Price_to_SMA50"] = close / df["SMA_50"] - 1
    df["SMA5_to_SMA20"] = df["SMA_5"] / df["SMA_20"] - 1
    df["EMA5_to_EMA20"] = df["EMA_5"] / df["EMA_20"] - 1
    df["EMA9_to_EMA20"] = df["EMA_9"] / df["EMA_20"] - 1
    df["EMA12_to_EMA26"] = df["EMA_12"] / df["EMA_26"] - 1

    # MACD Suite
    df["MACD"] = df["EMA_12"] - df["EMA_26"]
    df["MACD_Signal"] = df["MACD"].ewm(span=9, adjust=False).mean()
    df["MACD_Hist"] = df["MACD"] - df["MACD_Signal"]
    df["MACD_Hist_Slope"] = df["MACD_Hist"].diff(2).fillna(0)

    # Multi-Period RSI
    df["RSI_7"] = compute_rsi(close, 7)
    df["RSI_14"] = compute_rsi(close, 14)
    df["RSI_21"] = compute_rsi(close, 21)

    # Stochastic Oscillator (%K, %D) & Williams %R
    low_14 = low.rolling(14).min()
    high_14 = high.rolling(14).max()
    denom_14 = (high_14 - low_14).replace(0, np.nan)
    df["Stoch_K"] = (((close - low_14) / denom_14) * 100).fillna(50)
    df["Stoch_D"] = df["Stoch_K"].rolling(3).mean().fillna(50)
    df["Williams_R"] = (((high_14 - close) / denom_14) * -100).fillna(-50)

    # Bollinger Bands (%B and Bandwidth)
    bb_mean = close.rolling(20).mean()
    bb_std = close.rolling(20).std()
    bb_upper = bb_mean + 2 * bb_std
    bb_lower = bb_mean - 2 * bb_std
    df["BB_Width"] = ((bb_upper - bb_lower) / bb_mean.replace(0, np.nan)).fillna(0)
    df["BB_PctB"] = ((close - bb_lower) / (bb_upper - bb_lower).replace(0, np.nan)).fillna(0.5)

    # Rolling Volatility
    df["Volatility_10"] = df["Return_1"].rolling(10).std().fillna(0)
    df["Volatility_20"] = df["Return_1"].rolling(20).std().fillna(0)

    # Candlestick Price Action
    df["Body_Size"] = ((close - open_p) / open_p.replace(0, np.nan)).fillna(0)
    df["Upper_Shadow"] = ((high - np.maximum(open_p, close)) / close.replace(0, np.nan)).fillna(0)
    df["Lower_Shadow"] = ((np.minimum(open_p, close) - low) / close.replace(0, np.nan)).fillna(0)

    # Volume Dynamics
    vol_sma10 = volume.rolling(10).mean()
    df["Volume_Ratio"] = (volume / vol_sma10.replace(0, np.nan)).fillna(1.0)
    df["Volume_Change"] = volume.pct_change().fillna(0)

    # Legacy alias for backward compatibility with UI modals
    df["Momentum_5"] = df["Return_5"]

    # Target: binary — will tomorrow's close be higher than today's close?
    df["Target"] = (df["Close"].shift(-1) > df["Close"]).astype(int)

    return df


FEATURE_COLUMNS = [
    "Return_1", "Return_2", "Return_3", "Return_5", "Return_10",
    "Return_Lag1", "Return_Lag2",
    "Price_to_SMA5", "Price_to_SMA10", "Price_to_SMA20", "Price_to_SMA50",
    "SMA5_to_SMA20", "EMA5_to_EMA20", "EMA9_to_EMA20", "EMA12_to_EMA26",
    "MACD", "MACD_Signal", "MACD_Hist", "MACD_Hist_Slope",
    "RSI_7", "RSI_14", "RSI_21", "Stoch_K", "Stoch_D", "Williams_R",
    "BB_Width", "BB_PctB", "Volatility_10", "Volatility_20",
    "Body_Size", "Upper_Shadow", "Lower_Shadow",
    "Volume_Ratio", "Volume_Change"
]
