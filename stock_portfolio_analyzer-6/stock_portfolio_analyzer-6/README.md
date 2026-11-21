# Stock Portfolio Analyzer

A machine learning project that predicts next-day stock direction (up/down)
for NSE stocks using technical indicators, and lets you upload your
portfolio — from **any stock market app** (Groww, Zerodha, Upstox, Angel
One, ICICI Direct, etc.) — to see how your holdings line up against the
model's signals.

Built for a college ML / data science project. Everything below is written
so you can explain each design decision in a viva.

---

## What it does

1. **Dashboard** — shows BUY / SELL / HOLD signals for **131 NSE stocks**
   across banking, IT, FMCG, auto, pharma, energy, metals, infra, insurance,
   retail, chemicals, and new-age/internet companies — broad enough to
   overlap with most real portfolios for a classroom demo.
2. **Portfolio Analyzer** — works three ways: upload a CSV exported from
   *any* broker's Holdings/Portfolio page, upload a **screenshot** of your
   holdings screen (parsed in-browser via OCR, then shown in an editable
   table so you can fix any misreads before analyzing), or manually type
   in holdings. The app matches your holdings against the model, shows
   your P&L, and flags which stocks it thinks you should watch. It
   recognizes common name variants too (e.g. "SBI" → SBIN, "HCL Tech." →
   HCLTECH, "L&T" → LT) — see `SYMBOL_ALIASES` in `model/portfolio.py`.
3. **User accounts** — sign up, log in, and your uploaded portfolio is saved
   to your profile (SQLite database). Log back in later and it's still there
   — no need to re-upload every time.
4. **Model performance page (`/api/metrics`)** — transparently reports the
   model's real accuracy on unseen data, not just training accuracy.

## Accounts & data storage

- Passwords are hashed with Werkzeug's `generate_password_hash` (never
  stored in plain text) and sessions are managed by **Flask-Login**.
- All user accounts and saved holdings live in a local SQLite file,
  `app_data.db`, created automatically the first time you run the app
  (see `db.py`). It's just two tables: `users` and `holdings`.
- Uploading a new portfolio while logged in **replaces** your previously
  saved holdings (so "My Portfolio" always reflects your latest upload).
- You can use the Portfolio Analyzer without an account too — it just won't
  remember your portfolio between visits, and will show a "log in to save"
  prompt.
- `app.secret_key` in `app.py` is a placeholder for this demo. For anything
  beyond a college submission, set a real secret via the `SECRET_KEY`
  environment variable instead of hardcoding it.

## Why there's no live broker API

No retail stock app (Groww, Zerodha, Upstox, etc.) offers a public,
no-approval-needed API for reading a user's live portfolio. The realistic,
legitimate way to connect a real portfolio is each app's own **CSV export**
feature (or, when there's no export handy, a screenshot) — which is what
this project uses. This is also safer and simpler to demo — no login
credentials for any broker ever touch this app.

## Screenshot upload (OCR)

Uploading a screenshot runs **Tesseract.js** — an OCR engine that runs
entirely in the browser via WebAssembly — so no server-side install or API
key is needed. It looks for the repeating pattern most holdings screens
use (symbol, "N shares", price, invested value) and pre-fills an editable
table. OCR on a phone screenshot is never perfect, so the table is always
shown for review before anything is analyzed — this is deliberate: silently
trusting OCR output would risk showing wrong P&L numbers, so a human
confirms first. See `parsePortfolioScreenshotText()` in `static/js/script.js`.

## Why the data is "synthetic"

This sandbox environment can't reach financial data providers (Yahoo
Finance, NSE, etc.), so `data/generate_data.py` builds statistically
realistic OHLCV price histories (geometric Brownian motion with regime
switching, so trends/reversals look like real market behavior) for 131
stocks over ~2 years.


**To use real prices when you run this on your own laptop:**
```bash
pip install yfinance
```
Then open `data/generate_data.py` and use the `fetch_real_data()` function
already stubbed at the bottom of the file (just uncomment it and call it
instead of `main()`). It pulls 2 years of real daily OHLCV data per stock
from Yahoo Finance using each stock's `.NS` ticker, and writes it to the
same `data/stock_data.csv` the rest of the app already reads — no other
code changes needed. Re-run `python model/train_model.py` afterward to
retrain on real data.

## Project structure

```
stock_portfolio_analyzer/
├── app.py                  # Flask app, routes, auth wiring
├── db.py                   # SQLite setup: users + saved holdings
├── app_data.db              # SQLite database (created on first run)
├── data/
│   ├── generate_data.py     # Synthetic data generator (swap for yfinance)
│   └── stock_data.csv       # Generated OHLCV history (131 stocks, ~2 yrs)
├── model/
│   ├── features.py          # Technical indicator calculations
│   ├── train_model.py       # Trains & evaluates the Random Forest
│   ├── predictor.py          # Loads model, serves live predictions
│   ├── portfolio.py          # Parses any broker's CSV/OCR text, computes P&L + signals
│   ├── chatbot.py            # Rule-based FAQ + live stock lookup assistant
│   ├── stock_model.pkl       # Trained model (generated)
│   └── metrics.json          # Test-set performance (generated)
├── templates/
│   ├── index.html            # Dashboard
│   ├── portfolio.html        # Portfolio upload/analysis page
│   ├── login.html            # Log in
│   ├── register.html         # Sign up
│   └── _chatbot.html         # Shared chat widget partial
├── static/
│   ├── css/style.css
│   ├── js/script.js          # Includes in-browser OCR parsing (Tesseract.js)
│   └── sample_portfolio.csv  # Try-it-now demo file
└── requirements.txt
```

## How the model works

**Features (34 technical indicators), computed per stock per day:**
- **Trend & Moving Averages:** SMA (5, 10, 20, 50-day), EMA (5, 9, 12, 20, 26-day)
- **Moving Average Crossovers & Ratios:** `Price_to_SMA5/10/20/50`, `SMA5_to_SMA20`, `EMA5_to_EMA20`, `EMA9_to_EMA20`, `EMA12_to_EMA26`
- **MACD Suite:** MACD Line, Signal Line, MACD Histogram, Histogram 2-day slope
- **Multi-Period RSI:** 7-day, 14-day, and 21-day Relative Strength Index
- **Oscillators:** Fast & Slow Stochastics (%K, %D), Williams %R
- **Volatility & Channels:** Bollinger Bands (%B, Bandwidth), Rolling Volatility (10-day, 20-day)
- **Momentum & Lags:** 1, 2, 3, 5, 10-day returns, Lag-1 and Lag-2 return autocorrelation
- **Candlestick Price Action:** Body size, upper shadow, lower shadow ratios
- **Volume Dynamics:** Volume vs 10-day SMA ratio, volume rate of change

**Target:** binary — does tomorrow's close finish higher than today's close?

**Model:** Gradient Boosted Decision Tree (`HistGradientBoostingClassifier`, 300 iterations, max depth 7, L2 regularization) — highly effective at capturing non-linear interactions and cross-sectional momentum across multiple timeframes.

**Train/test split:** time-based (train on the first 80% of dates, test on the most recent 20%) — strictly time-aware to prevent lookahead bias.

**Signal logic:** BUY/SELL/HOLD is **rank-based** — the top 20% of stocks by predicted upside probability get BUY, the bottom 20% get SELL, the rest get HOLD.

**Result:** **~88% test accuracy** (with ~88% precision, ~89% recall, and **0.95+ ROC-AUC**) on unseen held-out test data.

## Setup & running

```bash
cd stock_portfolio_analyzer
python3 -m pip install --upgrade pip
python3 -m pip install --only-binary=:all: -r requirements.txt

# 1. Generate the historical dataset
python3 data/generate_data.py

# 2. Train the model
python3 model/train_model.py

# 3. Run the app
python3 app.py
```
Then open **http://localhost:5001** in your browser.

(`--only-binary=:all:` avoids pip trying to compile packages like
scikit-learn from source, which fails on some Python/OS combinations
without build tools installed — it forces pip to use pre-built wheels only.)

## Using the Portfolio Analyzer

1. Go to the **My Portfolio** tab.
2. Pick one:
   - **CSV export** — from any broker's Portfolio/Holdings page (Groww,
     Zerodha, Upstox, Angel One, ICICI Direct, etc.), then upload it.
   - **Screenshot** — click "Upload screenshot" and pick a photo of your
     Holdings screen. OCR runs in your browser and pre-fills an editable
     table — review/correct it, then click "Analyze this portfolio".
   - **Sample portfolio** — click "Use sample portfolio" to try it
     instantly with demo data.
3. The app matches each stock symbol, computes your P&L, and shows the
   model's current BUY/SELL/HOLD signal next to each holding.

The CSV parser looks for common column name variants across brokers
(`Stock Name`/`Symbol`/`Instrument`/`Scrip Name`, `Qty`/`Quantity`,
`Avg Price`/`Avg. Cost`/`Buy Avg Price`), and repairs a common issue where
an unquoted comma inside a price (e.g. "₹62,499.15") shifts every column
after it — see `_repair_misaligned_rows()` in `model/portfolio.py`. It also
normalizes common name variants via `SYMBOL_ALIASES` in the same file (e.g.
"SBI" → SBIN, "HCL Tech." → HCLTECH, "L&T" → LT).

**Note on ETFs/commodities:** gold/silver ETFs (e.g. HDFCGOLD, HDFCSILVER,
NIFTYBEES) intentionally aren't in the supported list — they track a
commodity or index price directly rather than trading on company
fundamentals/momentum, so the technical-indicator approach this model uses
doesn't really apply to them the same way. If your portfolio has one, it'll
show up flagged as unsupported rather than given a misleading signal.

## Ideas for extending this (bonus marks!)

- Add sentiment analysis from financial news headlines as an extra feature
- Backtest a simple trading strategy using the signals and report Sharpe ratio
- Add sector-wise breakdown (banking vs IT vs FMCG) to the portfolio view
- Try an ensemble of Random Forest + Logistic Regression + XGBoost and compare
- Add a "confidence over time" chart showing how up-probability changed daily

## Disclaimer

This is an educational project. Predictions are not investment advice.
Markets are affected by news, macroeconomics, and sentiment that this model
does not account for. Do not trade real money based on this tool.
