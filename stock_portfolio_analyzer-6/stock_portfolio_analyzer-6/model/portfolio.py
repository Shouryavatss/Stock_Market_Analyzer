"""
portfolio.py
-------------
Analyzes a user's portfolio against the model's predictions. Works with a
holdings export from *any* stock market app — Groww, Zerodha (Kite),
Upstox, Angel One, ICICI Direct, and others all export a CSV with some
variation of "Symbol/Stock Name, Qty, Avg Price" columns — or with holdings
typed in manually / extracted from a screenshot via OCR.
"""

import pandas as pd
import re
import io
import csv as csv_module


# Different brokers use different full/short company names instead of the
# exact NSE ticker, and formatting varies (periods, ampersands, "Ltd"
# suffixes). This maps common variants we've seen (across Groww, Zerodha,
# Upstox, Angel One exports) to the correct ticker used in our STOCKS
# universe (see data/generate_data.py).
SYMBOL_ALIASES = {
    "SBI": "SBIN", "STATE BANK OF INDIA": "SBIN",
    "HCL TECH": "HCLTECH", "HCL TECHNOLOGIES": "HCLTECH",
    "L&T": "LT", "LARSEN": "LT", "LARSEN TOUBRO": "LT", "LARSEN & TOUBRO": "LT",
    "BAJAJ AUTO": "BAJAJ-AUTO",
    "M AND M": "M&M", "MAHINDRA": "M&M", "MAHINDRA MAHINDRA": "M&M",
    "ICICI PRU": "ICICIPRULI", "ICICI PRUDENTIAL": "ICICIPRULI",
    "ICICI LOMBARD": "ICICIGI",
    "BAJAJ FINANCE": "BAJFINANCE", "BAJAJ FINSERV": "BAJAJFINSV",
    "HDFC BANK": "HDFCBANK", "HDFC LIFE": "HDFCLIFE",
    "TATA MOTORS": "TATAMOTORS", "TATA STEEL": "TATASTEEL",
    "TATA POWER": "TATAPOWER", "TATA CONSUMER": "TATACONSUM",
    "ADANI ENTERPRISES": "ADANIENT", "ADANI PORTS": "ADANIPORTS",
    "ADANI GREEN": "ADANIGREEN", "ADANI POWER": "ADANIPOWER",
    "ASIAN PAINTS": "ASIANPAINT", "ULTRATECH": "ULTRACEMCO",
    "ULTRATECH CEMENT": "ULTRACEMCO", "BHARTI AIRTEL": "BHARTIARTL",
    "SUN PHARMA": "SUNPHARMA", "DR REDDY": "DRREDDY", "DR REDDYS": "DRREDDY",
    "HERO MOTOCORP": "HEROMOTOCO", "EICHER MOTORS": "EICHERMOT",
    "AVENUE SUPERMARTS": "DMART", "COAL INDIA": "COALINDIA",
    "POWER GRID": "POWERGRID", "INDUSIND BANK": "INDUSINDBK",
    "FEDERAL BANK": "FEDERALBNK", "BANK OF BARODA": "BANKBARODA",
    "PUNJAB NATIONAL BANK": "PNB", "AU SMALL FINANCE": "AUBANK",
    "GODREJ CONSUMER": "GODREJCP", "GODREJ PROPERTIES": "GODREJPROP",
    "NESTLE": "NESTLEIND", "NESTLE INDIA": "NESTLEIND",
    "PIDILITE": "PIDILITIND", "APOLLO HOSPITALS": "APOLLOHOSP",
    "TORRENT PHARMA": "TORNTPHARM", "AUROBINDO PHARMA": "AUROPHARMA",
    "DIVIS LAB": "DIVISLAB", "DIVIS LABORATORIES": "DIVISLAB",
    "JSW STEEL": "JSWSTEEL", "VEDANTA": "VEDL", "HINDALCO INDUSTRIES": "HINDALCO",
    "INDIGO": "INDIGO", "INTERGLOBE AVIATION": "INDIGO",
    "IRCTC": "IRCTC", "CONTAINER CORPORATION": "CONCOR",
    "BHARAT ELECTRONICS": "BEL", "HINDUSTAN AERONAUTICS": "HAL",
    "PB FINTECH": "POLICYBZR", "POLICYBAZAAR": "POLICYBZR",
    "ONE97": "PAYTM", "ONE97 COMMUNICATIONS": "PAYTM",
}


def _normalize_symbol(raw):
    """Cleans a raw CSV symbol/name and maps it to our canonical ticker
    if it matches a known alias, otherwise returns the cleaned symbol as-is."""
    s = str(raw).upper().strip()
    s = s.replace(".NS", "").replace("-EQ", "")  # -EQ suffix appears in some Zerodha/Upstox exports
    s = re.sub(r"\bLTD\.?\b|\bLIMITED\b", "", s)
    s = re.sub(r"[.\-]+$", "", s).strip()  # trailing punctuation
    s_clean = re.sub(r"[^A-Z& ]", "", s).strip()
    s_clean = re.sub(r"\s+", " ", s_clean)

    if s_clean in SYMBOL_ALIASES:
        return SYMBOL_ALIASES[s_clean]

    # Try without spaces too (e.g. "HCL TECH" vs "HCLTECH")
    s_nospace = s_clean.replace(" ", "")
    if s_nospace in SYMBOL_ALIASES:
        return SYMBOL_ALIASES[s_nospace]

    return s_nospace if s_nospace else s.replace(" ", "")


def _clean_numeric(value):
    """Real exports (and screenshots, and manually-typed test files) format
    numbers messily — '15 shares', '₹16,902.00', '(₹43,537.74)', '1,093.34'
    — this strips everything except digits/decimal point/minus sign so
    conversion doesn't silently fail and fall back to 0."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    s = str(value)
    is_negative = "(" in s and ")" in s  # accounting-style negatives
    s = re.sub(r"[^\d.\-]", "", s)
    if not s or s in ("-", "."):
        return None
    try:
        num = float(s)
        return -abs(num) if is_negative else num
    except ValueError:
        return None


def manual_entries_to_df(entries, known_symbols):
    """Builds the standard holdings DataFrame from manually-entered or
    OCR-extracted rows (list of {symbol, quantity, avg_price} dicts from
    the frontend's editable review table)."""
    rows = []
    for e in entries:
        symbol = _normalize_symbol(e.get("symbol", ""))
        qty = _clean_numeric(e.get("quantity")) or 0
        avg_price = _clean_numeric(e.get("avg_price")) or 0
        if symbol:
            rows.append({"symbol": symbol, "quantity": qty, "avg_price": avg_price})

    if not rows:
        return pd.DataFrame(columns=["symbol", "quantity", "avg_price", "supported"])

    df = pd.DataFrame(rows)
    df["supported"] = df["symbol"].isin(known_symbols)
    return df


def holdings_list_to_df(holdings_list, known_symbols):
    """Converts saved DB holdings (list of dicts) back into the same
    normalized DataFrame shape parse_portfolio_csv produces, so both
    a fresh CSV upload and a reloaded saved portfolio can be analyzed
    the same way."""
    if not holdings_list:
        return pd.DataFrame(columns=["symbol", "quantity", "avg_price", "supported"])
    df = pd.DataFrame(holdings_list)
    df["symbol"] = df["symbol"].astype(str).str.upper().str.strip()
    df["supported"] = df["symbol"].isin(known_symbols)
    return df


# Column names vary a lot by broker — Groww uses "Stock Name"/"Avg Price",
# Zerodha's Kite uses "Instrument"/"Avg. cost", Upstox uses "Symbol"/
# "Average Price", Angel One uses "Scrip Name"/"Buy Avg Price", etc. We try
# every variant we've seen so any of them can be uploaded as-is.
COLUMN_ALIASES = {
    "symbol": [
        "symbol", "stock name", "stock", "scrip", "scrip name", "name",
        "instrument", "tradingsymbol", "company", "company name", "security",
    ],
    "quantity": [
        "qty", "qty.", "quantity", "shares", "units", "net qty", "holding qty",
    ],
    "avg_price": [
        "avg price", "avg. cost price", "average price", "buy price",
        "avg_price", "avg. cost", "avg cost", "buy avg price", "buy avg",
        "average buy price", "avg buy price",
    ],
}


def _find_column(columns, aliases):
    lower_map = {c.lower().strip(): c for c in columns}
    for alias in aliases:
        if alias in lower_map:
            return lower_map[alias]
    return None


def _repair_misaligned_rows(content):
    """Handles a common issue in manually-typed or copy-pasted CSVs: an
    unquoted thousands-separator comma inside a price (e.g. '₹62,499.15')
    creates an extra CSV field, shifting every column after it. Genuine
    broker exports quote such fields properly and are unaffected — this
    only kicks in when a row has more fields than the header, and merges
    the overflow back into the last column (where prices usually live)."""
    reader = csv_module.reader(io.StringIO(content))
    rows = list(reader)
    if not rows:
        return content

    header = rows[0]
    fixed_rows = [header]
    for row in rows[1:]:
        if not any(cell.strip() for cell in row):
            continue
        if len(row) > len(header):
            merged_tail = ",".join(row[len(header) - 1:])
            row = row[:len(header) - 1] + [merged_tail]
        elif len(row) < len(header):
            row = row + [""] * (len(header) - len(row))
        fixed_rows.append(row)

    out = io.StringIO()
    writer = csv_module.writer(out)
    writer.writerows(fixed_rows)
    return out.getvalue()


def parse_portfolio_csv(file_stream, known_symbols):
    """
    Parses an uploaded CSV (file-like object, from any broker's export)
    into a normalized DataFrame: columns = [symbol, quantity, avg_price].
    Unrecognized stock symbols (not in our supported list) are kept but
    flagged rather than dropped.
    """
    content = file_stream.read()
    if isinstance(content, bytes):
        content = content.decode("utf-8", errors="ignore")

    content = _repair_misaligned_rows(content)
    df = pd.read_csv(io.StringIO(content))
    df.columns = [c.strip() for c in df.columns]

    sym_col = _find_column(df.columns, COLUMN_ALIASES["symbol"])
    qty_col = _find_column(df.columns, COLUMN_ALIASES["quantity"])
    price_col = _find_column(df.columns, COLUMN_ALIASES["avg_price"])

    if sym_col is None:
        raise ValueError(
            "Couldn't find a stock symbol/name column. Expected a column like "
            "'Symbol', 'Stock Name', 'Instrument', or 'Scrip Name' — this "
            "works with exports from Groww, Zerodha, Upstox, Angel One, and "
            "most other brokers."
        )

    result = pd.DataFrame()
    result["symbol"] = df[sym_col].apply(_normalize_symbol)
    result["quantity"] = df[qty_col].apply(_clean_numeric).fillna(1) if qty_col else 1
    result["avg_price"] = df[price_col].apply(_clean_numeric).fillna(0) if price_col else 0
    result["supported"] = result["symbol"].isin(known_symbols)

    return result


def analyze_portfolio(portfolio_df, predictor):
    """
    Combines portfolio holdings with model predictions to produce
    per-stock recommendations and portfolio-level summary stats.
    """
    rows = []
    total_invested = 0.0
    total_current = 0.0

    for _, holding in portfolio_df.iterrows():
        symbol = holding["symbol"]
        qty = float(holding["quantity"])
        avg_price = float(holding["avg_price"])

        if not holding["supported"]:
            rows.append({
                "symbol": symbol,
                "quantity": qty,
                "avg_price": avg_price,
                "supported": False,
                "message": "Not in our supported stock list (yet) — no prediction available.",
            })
            continue

        pred = predictor.predict_symbol(symbol)
        if pred is None:
            continue

        current_price = pred["current_price"]
        invested_value = qty * avg_price if avg_price else qty * current_price
        current_value = qty * current_price
        pnl = current_value - invested_value
        pnl_pct = (pnl / invested_value * 100) if invested_value else 0

        total_invested += invested_value
        total_current += current_value

        rows.append({
            "symbol": symbol,
            "quantity": qty,
            "avg_price": round(avg_price, 2) if avg_price else current_price,
            "current_price": current_price,
            "invested_value": round(invested_value, 2),
            "current_value": round(current_value, 2),
            "pnl": round(pnl, 2),
            "pnl_pct": round(pnl_pct, 2),
            "signal": pred["signal"],
            "up_probability": pred["up_probability"],
            "rsi": pred["rsi"],
            "supported": True,
        })

    total_pnl = total_current - total_invested
    total_pnl_pct = (total_pnl / total_invested * 100) if total_invested else 0

    buy_signals = sum(1 for r in rows if r.get("signal") == "BUY")
    sell_signals = sum(1 for r in rows if r.get("signal") == "SELL")
    hold_signals = sum(1 for r in rows if r.get("signal") == "HOLD")

    summary = {
        "total_invested": round(total_invested, 2),
        "total_current": round(total_current, 2),
        "total_pnl": round(total_pnl, 2),
        "total_pnl_pct": round(total_pnl_pct, 2),
        "num_holdings": len(rows),
        "buy_signals": buy_signals,
        "sell_signals": sell_signals,
        "hold_signals": hold_signals,
    }

    return {"holdings": rows, "summary": summary}
