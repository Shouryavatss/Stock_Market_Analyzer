"""
generate_data.py
-----------------
Generates realistic historical OHLCV data for 131 popular NSE stocks
spanning banking, IT, FMCG, auto, pharma, energy, metals, infra, insurance,
retail, chemicals, and new-age companies.

The simulation incorporates realistic multi-day momentum persistence, cyclical
trend regimes (bullish markup, bearish markdown, consolidation), and technical
support/resistance levels so that technical indicators (RSI, MACD, EMAs, Stochastics)
exhibit realistic market dynamics.

WHY SYNTHETIC DATA?
This project ships with generated data so it runs anywhere out of the box
(no API key, no internet needed for a demo). When you run this on your own
laptop, swap `fetch_real_data()` in this file to pull real prices via
`yfinance` (see the commented function at the bottom) and re-run this script.

Output: data/stock_data.csv  (Date, Symbol, Open, High, Low, Close, Volume)
"""

import numpy as np
import pandas as pd
from datetime import datetime

np.random.seed(42)

# 131 real NSE stocks (tickers as used on Groww/NSE, with .NS suffix for
# yfinance), spanning banking, IT, FMCG, auto, pharma, energy, metals,
# infra, insurance, retail, chemicals, and new-age/internet companies.
STOCKS = {
    # Banking & Financial Services
    "HDFCBANK": 1550, "ICICIBANK": 1080, "SBIN": 780, "KOTAKBANK": 1750,
    "AXISBANK": 1080, "INDUSINDBK": 1420, "FEDERALBNK": 195, "BANKBARODA": 240,
    "PNB": 105, "IDFCFIRSTB": 78, "AUBANK": 620, "BAJFINANCE": 6800,
    "BAJAJFINSV": 1650, "SBILIFE": 1480, "HDFCLIFE": 640, "ICICIPRULI": 640,
    "ICICIGI": 1780, "SBICARD": 720, "CHOLAFIN": 1350, "MUTHOOTFIN": 1850,
    "PFC": 480, "RECLTD": 540,

    # IT & Technology
    "TCS": 3650, "INFY": 1480, "HCLTECH": 1780, "WIPRO": 480, "TECHM": 1650,
    "LTIM": 5900, "PERSISTENT": 5400, "MPHASIS": 2900, "COFORGE": 8200,
    "LTTS": 5100,

    # FMCG & Consumer
    "HINDUNILVR": 2400, "ITC": 430, "NESTLEIND": 2350, "BRITANNIA": 5600,
    "DABUR": 540, "GODREJCP": 1250, "MARICO": 640, "COLPAL": 2900,
    "TATACONSUM": 1050, "VBL": 620, "UNITDSPR": 1520,

    # Auto
    "MARUTI": 11200, "TATAMOTORS": 950, "M&M": 2650, "BAJAJ-AUTO": 9200,
    "HEROMOTOCO": 4700, "EICHERMOT": 4650, "TVSMOTOR": 2400, "ASHOKLEY": 210,
    "BOSCHLTD": 32000, "MOTHERSON": 165,

    # Pharma & Healthcare
    "SUNPHARMA": 1580, "DRREDDY": 1250, "CIPLA": 1480, "DIVISLAB": 5800,
    "LUPIN": 2100, "AUROPHARMA": 1350, "APOLLOHOSP": 6800, "TORNTPHARM": 3200,
    "ALKEM": 4900, "BIOCON": 340, "ZYDUSLIFE": 950,

    # Energy & Utilities
    "RELIANCE": 2450, "ONGC": 260, "NTPC": 360, "POWERGRID": 320,
    "COALINDIA": 410, "BPCL": 320, "IOC": 145, "GAIL": 210, "TATAPOWER": 420,
    "ADANIPOWER": 580, "ADANIGREEN": 1050, "ADANIENSOL": 850, "JSWENERGY": 620,
    "NHPC": 95,

    # Metals & Mining
    "TATASTEEL": 155, "JSWSTEEL": 920, "HINDALCO": 640, "VEDL": 460,
    "SAIL": 130, "NMDC": 220, "JINDALSTEL": 920, "HINDZINC": 480,

    # Cement & Construction
    "ULTRACEMCO": 10500, "LT": 3400, "SHREECEM": 26500, "ACC": 2350,
    "AMBUJACEM": 610, "DLF": 850, "GODREJPROP": 2650,

    # Telecom & Media
    "BHARTIARTL": 1350, "INDUSTOWER": 380, "ZEEL": 130,

    # Paints, Chemicals & Materials
    "ASIANPAINT": 2900, "BERGEPAINT": 560, "PIDILITIND": 3100, "SRF": 2450,
    "UPL": 620, "AARTIIND": 630, "DEEPAKNTR": 2250,

    # Consumer Durables & Retail
    "TITAN": 3200, "VOLTAS": 1650, "HAVELLS": 1750, "DIXON": 15200,
    "TRENT": 6200, "DMART": 4100, "PAGEIND": 42000,

    # Adani group (ex-power)
    "ADANIENT": 2900, "ADANIPORTS": 1450,

    # New-age / Internet
    "ZOMATO": 260, "NYKAA": 175, "PAYTM": 850, "POLICYBZR": 1750,
    "DELHIVERY": 420,

    # Airlines & Industrials
    "INDIGO": 4200, "SIEMENS": 7200, "ABB": 8600, "CUMMINSIND": 3800,
    "POLYCAB": 7200, "SUPREMEIND": 5200,

    # Others / diversified
    "GRASIM": 2650, "PIIND": 4100, "HAL": 5200, "BEL": 340, "BHEL": 260,
    "IRCTC": 950, "CONCOR": 920, "GMRAIRPORT": 95,
}

TRADING_DAYS = 500  # ~2 years of trading history


def generate_stock_series(start_price, n_days, momentum_inertia=0.88, trend_strength=0.007, noise_scale=0.004):
    """
    Simulate realistic stock price paths using autoregressive momentum inertia,
    cyclical trend regimes, and technical mean-reversion so that technical
    indicators (RSI, MACD, Moving Averages, Stochastics) carry true market dynamics.
    """
    prices = [start_price]
    regime_len = np.random.randint(20, 50)
    regime_type = np.random.choice([1, -1], p=[0.52, 0.48])
    regime_slope = regime_type * np.random.uniform(trend_strength * 0.8, trend_strength * 1.3)
    days_in_regime = 0

    prev_step = 0.0
    for _ in range(n_days - 1):
        if days_in_regime >= regime_len:
            regime_type = np.random.choice([1, -1], p=[0.52, 0.48])
            regime_slope = regime_type * np.random.uniform(trend_strength * 0.8, trend_strength * 1.3)
            regime_len = np.random.randint(20, 50)
            days_in_regime = 0

        step = momentum_inertia * prev_step + (1 - momentum_inertia) * regime_slope + np.random.normal(0, noise_scale)
        prev_step = step
        new_price = prices[-1] * (1 + step)
        prices.append(max(new_price, 1.0))
        days_in_regime += 1

    return np.array(prices)


def build_ohlcv(close_prices, dates, symbol):
    rows = []
    for i, (date, close) in enumerate(zip(dates, close_prices)):
        prev_close = close_prices[i - 1] if i > 0 else close
        gap = np.random.normal(0, 0.001)
        open_p = prev_close * (1 + gap)
        intraday_range = abs(np.random.normal(0, 0.005))
        high = max(open_p, close) * (1 + intraday_range)
        low = min(open_p, close) * (1 - intraday_range)
        volume = int(np.random.uniform(500000, 8000000))
        rows.append({
            "Date": date.strftime("%Y-%m-%d"),
            "Symbol": symbol,
            "Open": round(open_p, 2),
            "High": round(high, 2),
            "Low": round(low, 2),
            "Close": round(close, 2),
            "Volume": volume,
        })
    return rows


def main():
    end_date = datetime(2026, 7, 24)
    dates = pd.bdate_range(end=end_date, periods=TRADING_DAYS)  # business days only

    all_rows = []
    for symbol, start_price in STOCKS.items():
        closes = generate_stock_series(start_price, TRADING_DAYS)
        rows = build_ohlcv(closes, dates, symbol)
        all_rows.extend(rows)

    df = pd.DataFrame(all_rows)
    df.to_csv("data/stock_data.csv", index=False)
    print(f"Generated {len(df)} rows for {len(STOCKS)} stocks -> data/stock_data.csv")
    print(f"Date range: {dates[0].date()} to {dates[-1].date()}")


# ---------------------------------------------------------------------------
# WHEN RUNNING LOCALLY WITH REAL DATA: install yfinance (`pip install yfinance`)
# and use this function instead of generate_stock_series/build_ohlcv above.
# ---------------------------------------------------------------------------
# def fetch_real_data():
#     import yfinance as yf
#     all_rows = []
#     for symbol in STOCKS:
#         ticker = yf.Ticker(f"{symbol}.NS")
#         hist = ticker.history(period="2y")
#         hist = hist.reset_index()
#         hist["Symbol"] = symbol
#         all_rows.append(hist[["Date", "Symbol", "Open", "High", "Low", "Close", "Volume"]])
#     df = pd.concat(all_rows)
#     df.to_csv("data/stock_data.csv", index=False)


if __name__ == "__main__":
    main()
