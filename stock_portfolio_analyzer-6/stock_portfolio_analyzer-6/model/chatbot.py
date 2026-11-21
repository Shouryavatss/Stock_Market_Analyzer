"""
chatbot.py
-----------
Quant Copilot: AI-Powered Financial & Stock Market Analyst using Google Gemini API.

Strict Domain Scope:
  - ONLY answers questions related to the stock market, equities, NSE stocks, indices,
    portfolio analysis, risk management, technical indicators (RSI, MACD, etc.),
    trading concepts, and platform model predictions.
  - Politely and firmly refuses any non-financial/non-stock-market queries.
  - Dynamically grounds responses with live market predictions and model metrics.
"""

import os
import json
import re
import urllib.request
import urllib.error

# Load environment variable if present
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()

SYSTEM_INSTRUCTION = """
You are Quant Copilot, an elite institutional financial analyst and quantitative portfolio intelligence assistant for the Stock Portfolio Analyzer platform.

CRITICAL DOMAIN GUARDRAILS & BOUNDARIES:
1. STRICT TOPIC MANDATE:
   You are strictly restricted to answering questions related to:
   - Stock markets, equities, NSE/BSE stocks, global markets, indices (NIFTY 50, SENSEX, S&P 500).
   - Portfolio analysis, asset allocation, diversification, P&L calculations, risk management (Beta, Sharpe ratio, drawdowns).
   - Technical analysis & indicators (RSI, MACD, Moving Averages SMA/EMA, Bollinger Bands, Stochastics, Williams %R, Volatility).
   - Fundamental analysis, earnings, valuation metrics (P/E, P/B, EV/EBITDA, dividend yields).
   - The quantitative model predictions, BUY/SELL/HOLD signals, and features of this Stock Portfolio Analyzer app.

2. REJECTION POLICY (STRICT):
   If the user asks about ANY topic outside the stock market, investing, trading, portfolio management, finance, economics, and technical analysis (for example: coding outside financial algorithms, entertainment, sports, cooking, history, recipes, creative writing, weather, or general knowledge):
   You MUST immediately and politely decline by responding:
   "I am specialized strictly as a Quantitative Stock Market & Portfolio Analyst. I can only assist with stock markets, equities, technical indicators, portfolio analytics, and stock predictions. Please ask a market or portfolio-related question."

3. LIVE PLATFORM GROUNDING:
   - The platform tracks 131 NSE equities.
   - The GBDT model has a held-out test accuracy of 87.99% (Precision 87.77%, Recall 88.91%, ROC-AUC 0.9547) using 34 multi-timeframe technical features.
   - Reference the provided live stock context (prices, RSI, MACD, signals) when discussing specific stocks.

4. STYLE & TONE:
   - Institutional, calm, concise, analytical, and professional (like a Bloomberg/Morningstar research note).
   - Use clean Markdown formatting, bullet points, and tabular figures.
   - Never provide reckless guarantees; maintain appropriate financial risk context.
"""

# Keywords for local guardrail and fallback detection
FINANCE_KEYWORDS = [
    "stock", "market", "share", "equity", "portfolio", "invest", "trade", "trading",
    "rsi", "macd", "sma", "ema", "bollinger", "stochastic", "williams", "volatility",
    "buy", "sell", "hold", "signal", "pnl", "profit", "loss", "return", "gain",
    "nse", "bse", "nifty", "sensex", "groww", "zerodha", "upstox", "broker",
    "dividend", "valuation", "pe ratio", "beta", "alpha", "sharpe", "drawdown",
    "risk", "diversification", "accuracy", "model", "prediction", "forecast", "price",
    "reliance", "tcs", "infy", "hdfc", "sbin", "itc", "icici", "tatamotors", "maruti"
]

FALLBACK_NON_FINANCE_MSG = (
    "I am specialized strictly as a Quantitative Stock Market & Portfolio Analyst. "
    "I can only assist with stock markets, equities, technical indicators, portfolio analytics, "
    "and stock predictions. Please ask a financial or market-related question."
)

FAQ = [
    (
        ["what is rsi", "rsi mean", "explain rsi"],
        "RSI (Relative Strength Index) measures the speed and change of price movements "
        "on a 0-100 scale across multiple timeframes (7, 14, 21 days). Above 70 indicates "
        "overbought conditions (potential pullback), and below 30 indicates oversold conditions "
        "(potential bounce). It is one of the 34 technical features the model evaluates.",
    ),
    (
        ["what is macd", "macd mean", "explain macd"],
        "MACD (Moving Average Convergence Divergence) compares short-term and long-term "
        "exponential moving averages to detect momentum shifts. The engine analyzes the MACD line, "
        "signal line, histogram, and histogram slope to gauge trend velocity.",
    ),
    (
        ["what does buy mean", "buy signal", "what is buy"],
        "A BUY signal means this stock ranks in the top 20% of all tracked stocks by "
        "predicted next-day upside probability, showing strong bullish technical alignment.",
    ),
    (
        ["what does sell mean", "sell signal", "what is sell"],
        "A SELL signal means this stock ranks in the bottom 20% by predicted upside "
        "probability — indicating bearish momentum and technical weakness.",
    ),
    (
        ["what does hold mean", "hold signal", "what is hold"],
        "HOLD means the stock's technical indicators are neutral or in a consolidation phase, "
        "falling in the middle 60% of ranked probabilities.",
    ),
    (
        ["how accurate", "accuracy", "how good is the model", "how reliable"],
        "The upgraded model achieves **87.99% accuracy** on unseen held-out test data, "
        "with **87.77% precision**, **88.91% recall**, and an **ROC-AUC of 0.9547**. "
        "It uses a Gradient Boosted Decision Tree (HistGradientBoosting) trained on 34 multi-timeframe "
        "technical indicators.",
    ),
    (
        ["how does the model work", "what model", "gradient boost", "algorithm", "features"],
        "It is a Gradient Boosted Decision Tree (HistGradientBoosting) classifier trained on 34 "
        "technical indicators — including multi-span EMAs/SMAs, MACD suite, multi-period RSI (7/14/21), "
        "Stochastics, Williams %R, Bollinger Bands (%B/Width), return lags, volatility, candlestick price action, "
        "and volume dynamics — to predict next-day price direction.",
    ),
    (
        ["upload portfolio", "how do i upload", "add my portfolio", "import holdings", "screenshot"],
        "Go to the My Portfolio tab. You can: click 'Import Broker CSV' (works with Groww, Zerodha, Upstox, etc.), "
        "click 'Scan Screenshot OCR' to extract holdings from a photo of your screen, or click 'Load Demo Portfolio'.",
    ),
    (
        ["how many stocks", "which stocks", "what stocks", "supported stocks"],
        "131 NSE stocks are tracked across banking, IT, FMCG, auto, energy, pharma, metals, infra, insurance, retail, and new-age companies.",
    ),
]


def is_financial_query(message_lower, predictor=None):
    """Checks if the query is strictly related to finance, stocks, trading, or portfolio analytics."""
    if any(kw in message_lower for kw in FINANCE_KEYWORDS):
        return True
    if predictor:
        words = re.findall(r"[A-Za-z&]+", message_lower.upper())
        if any(w in predictor.symbols for w in words):
            return True
    return False


def _call_gemini_api(prompt, live_context, api_key):
    """
    Invokes Google Gemini API with system instruction and live platform context.
    Uses model gemini-2.5-flash for fast, high-quality responses.
    """
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"

    full_user_content = f"{live_context}\n\nUser Question: {prompt}"

    payload = {
        "systemInstruction": {
            "parts": [{"text": SYSTEM_INSTRUCTION}]
        },
        "contents": [
            {
                "parts": [{"text": full_user_content}]
            }
        ],
        "generationConfig": {
            "temperature": 0.2,
            "maxOutputTokens": 800
        }
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    import ssl
    try:
        ctx = ssl.create_default_context()
    except Exception:
        ctx = ssl._create_unverified_context()

    try:
        with urllib.request.urlopen(req, timeout=12, context=ctx) as response:
            res_data = json.loads(response.read().decode("utf-8"))
            candidates = res_data.get("candidates", [])
            if candidates and "content" in candidates[0]:
                parts = candidates[0]["content"].get("parts", [])
                if parts:
                    return parts[0].get("text", "").strip()
    except urllib.error.URLError:
        ctx_unverified = ssl._create_unverified_context()
        with urllib.request.urlopen(req, timeout=12, context=ctx_unverified) as response:
            res_data = json.loads(response.read().decode("utf-8"))
            candidates = res_data.get("candidates", [])
            if candidates and "content" in candidates[0]:
                parts = candidates[0]["content"].get("parts", [])
                if parts:
                    return parts[0].get("text", "").strip()

    return None


def _build_live_context(message, predictor):
    """Extracts live technical data for any mentioned symbols to ground the AI response."""
    context_parts = [
        f"Platform Live Metrics: 131 NSE Equities Tracked, Model Accuracy 87.99%, Precision 87.77%, Recall 88.91%."
    ]
    if predictor:
        words = re.findall(r"[A-Za-z&]+", message.upper())
        matched = []
        for word in words:
            if word in predictor.symbols:
                pred = predictor.predict_symbol(word)
                if pred:
                    matched.append(
                        f"Stock {pred['symbol']}: Price ₹{pred['current_price']}, Signal {pred['signal']}, "
                        f"Upside Probability {pred['up_probability']}%, RSI(14) {pred['rsi']}, MACD {pred['macd']}, "
                        f"20D SMA ₹{pred['sma_20']}, 5D Momentum {pred['momentum_5d']}%."
                    )
        if matched:
            context_parts.append("Live Stock Data for Mentioned Equities:\n" + "\n".join(matched))
    return "\n\n".join(context_parts)


def get_response(message, predictor=None, api_key=None):
    """
    Primary handler for Quant Copilot queries.
    Uses Gemini API if key is available; otherwise uses strict quantitative fallback engine.
    """
    message = (message or "").strip()
    if not message:
        return "Please ask a question regarding stock market predictions, portfolio analytics, or technical indicators."

    message_lower = message.lower()

    # Domain Guardrail Check
    if not is_financial_query(message_lower, predictor):
        return FALLBACK_NON_FINANCE_MSG

    # Determine effective Gemini API Key
    effective_api_key = api_key or os.environ.get("GEMINI_API_KEY", "").strip() or GEMINI_API_KEY

    if effective_api_key:
        try:
            live_context = _build_live_context(message, predictor)
            gemini_reply = _call_gemini_api(message, live_context, effective_api_key)
            if gemini_reply:
                return gemini_reply
        except Exception as e:
            print(f"Gemini API call failed: {e}. Falling back to quantitative engine.")

    # Fallback to local high-precision quant engine
    # Check for direct stock query
    if predictor:
        words = re.findall(r"[A-Za-z&]+", message.upper())
        for word in words:
            if word in predictor.symbols:
                pred = predictor.predict_symbol(word)
                if pred:
                    return (
                        f"**{pred['symbol']}** (NSE Listed Equity):\n"
                        f"- **Current Market Price:** ₹{pred['current_price']}\n"
                        f"- **Quant Signal:** **{pred['signal']}** ({pred['up_probability']}% predicted upside probability)\n"
                        f"- **RSI (14-Day):** {pred['rsi']}\n"
                        f"- **20-Day SMA:** ₹{pred['sma_20']}\n"
                        f"- **MACD:** {pred['macd']}\n"
                        f"- **5-Day Momentum:** {pred['momentum_5d']}%\n\n"
                        f"*Analysis:* Evaluated using the 34-feature GBDT model with 87.99% held-out test accuracy."
                    )

    # Check for FAQ match
    for keywords, answer in FAQ:
        if any(kw in message_lower for kw in keywords):
            return answer

    return (
        "I am your Quantitative Stock Market Copilot. Ask about specific NSE symbols (e.g. *'Signal for TCS'* or *'RELIANCE'*), "
        "technical indicators (RSI, MACD, Bollinger Bands), model accuracy, or portfolio allocation strategies."
    )
