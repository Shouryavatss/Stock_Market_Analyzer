"""
predictor.py
-------------
Loads the trained model and stock data to generate live-style predictions
(BUY / SELL / HOLD signals) for any supported stock.
"""

import os
import pickle
import json

import pandas as pd
import numpy as np

from .features import add_features, FEATURE_COLUMNS

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class StockPredictor:
    def __init__(self):
        with open(os.path.join(BASE_DIR, "model", "stock_model.pkl"), "rb") as f:
            self.model = pickle.load(f)

        with open(os.path.join(BASE_DIR, "model", "metrics.json")) as f:
            self.metrics = json.load(f)

        raw = pd.read_csv(os.path.join(BASE_DIR, "data", "stock_data.csv"), parse_dates=["Date"])
        self.symbols = sorted(raw["Symbol"].unique().tolist())

        # Pre-compute features per symbol so lookups are fast
        self.feature_cache = {}
        self.latest_price = {}
        for symbol, group in raw.groupby("Symbol"):
            group = group.sort_values("Date")
            feat = add_features(group)
            self.feature_cache[symbol] = feat
            self.latest_price[symbol] = float(group["Close"].iloc[-1])

        # ---- Rank-based signal thresholds ----
        # A fixed probability cutoff (e.g. "BUY if up_prob >= 58%") looks great
        # in theory, but on real technical-indicator models the predicted
        # probabilities for next-day direction cluster tightly around 50%
        # (that's *expected* — see README on the Efficient Market Hypothesis).
        # A fixed cutoff can end up flagging almost nothing as BUY/SELL.
        # A cross-sectional / rank-based signal — "today's top 20% of stocks
        # by predicted upside get BUY, bottom 20% get SELL" — is standard
        # practice in quant screening for exactly this reason, and guarantees
        # a usable spread of signals every trading day.
        self._up_prob_cache = {}
        for symbol in self.symbols:
            up_prob = self._raw_up_probability(symbol)
            if up_prob is not None:
                self._up_prob_cache[symbol] = up_prob

        probs = sorted(self._up_prob_cache.values())
        if probs:
            self.buy_threshold = np.percentile(probs, 80)
            self.sell_threshold = np.percentile(probs, 20)
        else:
            self.buy_threshold, self.sell_threshold = 0.55, 0.45

    def _raw_up_probability(self, symbol):
        feat = self.feature_cache.get(symbol)
        if feat is None:
            return None
        latest_row = feat.dropna(subset=FEATURE_COLUMNS).iloc[-1:]
        if latest_row.empty:
            return None
        X = latest_row[FEATURE_COLUMNS]
        proba = self.model.predict_proba(X)[0]
        return float(proba[1])

    def _signal_for(self, up_prob):
        if up_prob >= self.buy_threshold:
            return "BUY"
        elif up_prob <= self.sell_threshold:
            return "SELL"
        return "HOLD"

    def list_symbols(self):
        return self.symbols

    def predict_symbol(self, symbol):
        symbol = symbol.upper().strip()
        if symbol not in self.feature_cache:
            return None

        feat = self.feature_cache[symbol]
        latest_row = feat.dropna(subset=FEATURE_COLUMNS).iloc[-1:]
        if latest_row.empty:
            return None

        X = latest_row[FEATURE_COLUMNS]
        proba = self.model.predict_proba(X)[0]  # [P(down), P(up)]
        up_prob = float(proba[1])
        signal = self._signal_for(up_prob)

        row = latest_row.iloc[0]
        return {
            "symbol": symbol,
            "current_price": round(float(row["Close"]), 2),
            "date": row["Date"].strftime("%Y-%m-%d"),
            "up_probability": round(up_prob * 100, 1),
            "signal": signal,
            "rsi": round(float(row["RSI_14"]), 1),
            "sma_20": round(float(row["SMA_20"]), 2),
            "macd": round(float(row["MACD"]), 2),
            "momentum_5d": round(float(row["Momentum_5"]) * 100, 2),
        }

    def predict_all(self):
        results = []
        for symbol in self.symbols:
            pred = self.predict_symbol(symbol)
            if pred:
                results.append(pred)
        return sorted(results, key=lambda x: -x["up_probability"])

    def get_history(self, symbol, days=60):
        symbol = symbol.upper().strip()
        if symbol not in self.feature_cache:
            return None
        feat = self.feature_cache[symbol].tail(days)
        return {
            "dates": feat["Date"].dt.strftime("%Y-%m-%d").tolist(),
            "close": feat["Close"].round(2).tolist(),
            "sma_20": feat["SMA_20"].round(2).tolist(),
        }


# Singleton instance used by the Flask app
_predictor_instance = None


def get_predictor():
    global _predictor_instance
    if _predictor_instance is None:
        _predictor_instance = StockPredictor()
    return _predictor_instance
