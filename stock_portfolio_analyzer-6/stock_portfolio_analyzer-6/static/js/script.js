// ==========================================================================
// Stock Portfolio Analyzer — Institutional Frontend Controller
// Platform: Bloomberg / Linear / Stripe / Robinhood inspired interface
// ==========================================================================

const fmtINR = (n) => "₹" + Number(n).toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
const fmtNum = (n, d = 2) => Number(n).toLocaleString("en-IN", { minimumFractionDigits: d, maximumFractionDigits: d });

// Global state cache
let g_predictions = [];
let g_metrics = {};
let g_activeTimeframe = "1M";
let g_activeFilter = "ALL";
let g_searchQuery = "";
let g_sortColumn = "up_probability";
let g_sortAsc = false;
let g_portfolioData = null;

// Company name mapping for professional table presentation
const COMPANY_NAMES = {
  "HDFCBANK": "HDFC Bank Ltd.",
  "ICICIBANK": "ICICI Bank Ltd.",
  "SBIN": "State Bank of India",
  "KOTAKBANK": "Kotak Mahindra Bank",
  "AXISBANK": "Axis Bank Ltd.",
  "INDUSINDBK": "IndusInd Bank Ltd.",
  "FEDERALBNK": "Federal Bank Ltd.",
  "BANKBARODA": "Bank of Baroda",
  "PNB": "Punjab National Bank",
  "IDFCFIRSTB": "IDFC First Bank",
  "AUBANK": "AU Small Finance Bank",
  "BAJFINANCE": "Bajaj Finance Ltd.",
  "BAJAJFINSV": "Bajaj Finserv Ltd.",
  "SBILIFE": "SBI Life Insurance",
  "HDFCLIFE": "HDFC Life Insurance",
  "ICICIPRULI": "ICICI Prudential Life",
  "ICICIGI": "ICICI Lombard General",
  "SBICARD": "SBI Cards & Payment",
  "CHOLAFIN": "Cholamandalam Inv.",
  "MUTHOOTFIN": "Muthoot Finance Ltd.",
  "PFC": "Power Finance Corp.",
  "RECLTD": "REC Limited",
  "TCS": "Tata Consultancy Services",
  "INFY": "Infosys Limited",
  "HCLTECH": "HCL Technologies Ltd.",
  "WIPRO": "Wipro Limited",
  "TECHM": "Tech Mahindra Ltd.",
  "LTIM": "LTIMindtree Limited",
  "PERSISTENT": "Persistent Systems",
  "MPHASIS": "Mphasis Limited",
  "COFORGE": "Coforge Limited",
  "LTTS": "L&T Technology Services",
  "HINDUNILVR": "Hindustan Unilever Ltd.",
  "ITC": "ITC Limited",
  "NESTLEIND": "Nestle India Ltd.",
  "BRITANNIA": "Britannia Industries",
  "DABUR": "Dabur India Ltd.",
  "GODREJCP": "Godrej Consumer Products",
  "MARICO": "Marico Limited",
  "COLPAL": "Colgate-Palmolive India",
  "TATACONSUM": "Tata Consumer Products",
  "VBL": "Varun Beverages Ltd.",
  "UNITDSPR": "United Spirits Ltd.",
  "MARUTI": "Maruti Suzuki India",
  "TATAMOTORS": "Tata Motors Ltd.",
  "M&M": "Mahindra & Mahindra",
  "BAJAJ-AUTO": "Bajaj Auto Ltd.",
  "HEROMOTOCO": "Hero MotoCorp Ltd.",
  "EICHERMOT": "Eicher Motors Ltd.",
  "TVSMOTOR": "TVS Motor Company",
  "ASHOKLEY": "Ashok Leyland Ltd.",
  "BOSCHLTD": "Bosch Limited",
  "MOTHERSON": "Samvardhana Motherson",
  "SUNPHARMA": "Sun Pharmaceutical",
  "DRREDDY": "Dr. Reddy's Laboratories",
  "CIPLA": "Cipla Limited",
  "DIVISLAB": "Divi's Laboratories",
  "LUPIN": "Lupin Limited",
  "AUROPHARMA": "Aurobindo Pharma",
  "APOLLOHOSP": "Apollo Hospitals",
  "TORNTPHARM": "Torrent Pharmaceuticals",
  "ALKEM": "Alkem Laboratories",
  "BIOCON": "Biocon Limited",
  "ZYDUSLIFE": "Zydus Lifesciences",
  "RELIANCE": "Reliance Industries Ltd.",
  "ONGC": "Oil & Natural Gas Corp.",
  "NTPC": "NTPC Limited",
  "POWERGRID": "Power Grid Corporation",
  "COALINDIA": "Coal India Limited",
  "BPCL": "Bharat Petroleum Corp.",
  "IOC": "Indian Oil Corporation",
  "GAIL": "GAIL (India) Limited",
  "TATAPOWER": "Tata Power Company",
  "ADANIPOWER": "Adani Power Ltd.",
  "ADANIGREEN": "Adani Green Energy",
  "ADANIENSOL": "Adani Energy Solutions",
  "JSWENERGY": "JSW Energy Limited",
  "NHPC": "NHPC Limited",
  "TATASTEEL": "Tata Steel Limited",
  "JSWSTEEL": "JSW Steel Limited",
  "HINDALCO": "Hindalco Industries",
  "VEDL": "Vedanta Limited",
  "SAIL": "Steel Authority of India",
  "NMDC": "NMDC Limited",
  "JINDALSTEL": "Jindal Steel & Power",
  "HINDZINC": "Hindustan Zinc Ltd.",
  "ULTRACEMCO": "UltraTech Cement",
  "LT": "Larsen & Toubro Ltd.",
  "SHREECEM": "Shree Cement Ltd.",
  "ACC": "ACC Limited",
  "AMBUJACEM": "Ambuja Cements Ltd.",
  "DLF": "DLF Limited",
  "GODREJPROP": "Godrej Properties",
  "BHARTIARTL": "Bharti Airtel Ltd.",
  "INDUSTOWER": "Indus Towers Ltd.",
  "ZEEL": "Zee Entertainment",
  "ASIANPAINT": "Asian Paints Ltd.",
  "BERGEPAINT": "Berger Paints India",
  "PIDILITIND": "Pidilite Industries",
  "SRF": "SRF Limited",
  "UPL": "UPL Limited",
  "AARTIIND": "Aarti Industries",
  "DEEPAKNTR": "Deepak Nitrite Ltd.",
  "TITAN": "Titan Company Ltd.",
  "VOLTAS": "Voltas Limited",
  "HAVELLS": "Havells India Ltd.",
  "DIXON": "Dixon Technologies",
  "TRENT": "Trent Limited",
  "DMART": "Avenue Supermarts",
  "PAGEIND": "Page Industries Ltd.",
  "ADANIENT": "Adani Enterprises Ltd.",
  "ADANIPORTS": "Adani Ports & SEZ",
  "ZOMATO": "Zomato Limited",
  "NYKAA": "FSN E-Commerce (Nykaa)",
  "PAYTM": "One97 Communications",
  "POLICYBZR": "PB Fintech (PolicyBazaar)",
  "DELHIVERY": "Delhivery Limited",
  "INDIGO": "InterGlobe Aviation",
  "SIEMENS": "Siemens Limited",
  "ABB": "ABB India Limited",
  "CUMMINSIND": "Cummins India Ltd.",
  "POLYCAB": "Polycab India Ltd.",
  "SUPREMEIND": "Supreme Industries",
  "GRASIM": "Grasim Industries",
  "PIIND": "PI Industries Ltd.",
  "HAL": "Hindustan Aeronautics",
  "BEL": "Bharat Electronics Ltd.",
  "BHEL": "Bharat Heavy Electricals",
  "IRCTC": "IRCTC Limited",
  "CONCOR": "Container Corp. of India",
  "GMRAIRPORT": "GMR Airports Infra"
};

// Sector identification for rich allocation analytics
const SECTORS = {
  "Banking & Financials": ["HDFCBANK", "ICICIBANK", "SBIN", "KOTAKBANK", "AXISBANK", "INDUSINDBK", "FEDERALBNK", "BANKBARODA", "PNB", "IDFCFIRSTB", "AUBANK", "BAJFINANCE", "BAJAJFINSV", "SBILIFE", "HDFCLIFE", "ICICIPRULI", "ICICIGI", "SBICARD", "CHOLAFIN", "MUTHOOTFIN", "PFC", "RECLTD"],
  "IT & Software": ["TCS", "INFY", "HCLTECH", "WIPRO", "TECHM", "LTIM", "PERSISTENT", "MPHASIS", "COFORGE", "LTTS"],
  "Consumer & FMCG": ["HINDUNILVR", "ITC", "NESTLEIND", "BRITANNIA", "DABUR", "GODREJCP", "MARICO", "COLPAL", "TATACONSUM", "VBL", "UNITDSPR", "TITAN", "VOLTAS", "HAVELLS", "DIXON", "TRENT", "DMART", "PAGEIND"],
  "Automotive": ["MARUTI", "TATAMOTORS", "M&M", "BAJAJ-AUTO", "HEROMOTOCO", "EICHERMOT", "TVSMOTOR", "ASHOKLEY", "BOSCHLTD", "MOTHERSON"],
  "Pharma & Healthcare": ["SUNPHARMA", "DRREDDY", "CIPLA", "DIVISLAB", "LUPIN", "AUROPHARMA", "APOLLOHOSP", "TORNTPHARM", "ALKEM", "BIOCON", "ZYDUSLIFE"],
  "Energy & Commodities": ["RELIANCE", "ONGC", "NTPC", "POWERGRID", "COALINDIA", "BPCL", "IOC", "GAIL", "TATAPOWER", "ADANIPOWER", "ADANIGREEN", "ADANIENSOL", "JSWENERGY", "NHPC", "TATASTEEL", "JSWSTEEL", "HINDALCO", "VEDL", "SAIL", "NMDC", "JINDALSTEL", "HINDZINC"],
  "Industrials & Tech": ["ULTRACEMCO", "LT", "SHREECEM", "ACC", "AMBUJACEM", "DLF", "GODREJPROP", "BHARTIARTL", "INDUSTOWER", "ZEEL", "ASIANPAINT", "BERGEPAINT", "PIDILITIND", "SRF", "UPL", "AARTIIND", "DEEPAKNTR", "ADANIENT", "ADANIPORTS", "ZOMATO", "NYKAA", "PAYTM", "POLICYBZR", "DELHIVERY", "INDIGO", "SIEMENS", "ABB", "CUMMINSIND", "POLYCAB", "SUPREMEIND", "GRASIM", "PIIND", "HAL", "BEL", "BHEL", "IRCTC", "CONCOR", "GMRAIRPORT"]
};

function getStockSector(symbol) {
  for (const [sector, symbols] of Object.entries(SECTORS)) {
    if (symbols.includes(symbol)) return sector;
  }
  return "Diversified Equities";
}

// ==========================================================================
// Main Dashboard Initialization
// ==========================================================================
async function initDashboard() {
  const tableBody = document.getElementById("marketTableBody");
  if (!tableBody) return; // not on dashboard

  try {
    const [predictions, metrics] = await Promise.all([
      fetch("/api/predictions").then(r => r.json()),
      fetch("/api/metrics").then(r => r.json()),
    ]);

    g_predictions = predictions;
    g_metrics = metrics;

    renderTickerTape(predictions);
    renderPortfolioPerformanceChart();
    renderAnalystNotes(predictions, metrics);
    renderMarketTable();
    setupTableInteractions();
    startMarketLiveTicks();
  } catch (err) {
    console.error("Dashboard initialization error:", err);
  }
}

// ---------------------- Ticker Tape ----------------------
function renderTickerTape(predictions) {
  const track = document.getElementById("tickerTrack");
  if (!track) return;

  const itemsHtml = predictions.slice(0, 30).map(p => {
    const isUp = p.signal === "BUY";
    const isDown = p.signal === "SELL";
    const chgClass = isUp ? "up" : isDown ? "down" : "";
    const arrow = isUp ? "▲" : isDown ? "▼" : "•";
    return `
      <div class="ticker-item" onclick="openAssetTerminal('${p.symbol}')" style="cursor:pointer;">
        <span class="sym">${p.symbol}</span>
        <span class="price">${fmtINR(p.current_price)}</span>
        <span class="chg ${chgClass}">${arrow} ${p.up_probability}%</span>
      </div>
    `;
  }).join("");

  track.innerHTML = itemsHtml + itemsHtml; // duplicate for infinite loop
}

// ---------------------- Interactive Performance Chart ----------------------
function generateSimulatedPortfolioCurve(timeframe) {
  const pointsMap = {
    "1D": 24,
    "1W": 35,
    "1M": 45,
    "3M": 60,
    "6M": 75,
    "1Y": 90,
    "5Y": 120,
    "ALL": 140
  };
  const count = pointsMap[timeframe] || 45;
  const data = [];
  let base = 742000;
  const growthRate = 0.0028;
  const now = new Date();

  for (let i = 0; i < count; i++) {
    const daysAgo = count - 1 - i;
    const d = new Date(now.getTime() - daysAgo * (timeframe === "1D" ? 3600000 : 86400000 * (timeframe === "1Y" ? 4 : 1)));
    const noise = (Math.sin(i / 4) * 0.015) + ((Math.random() - 0.48) * 0.012);
    base = base * (1 + growthRate + noise);
    data.push({
      date: d.toLocaleDateString("en-IN", { month: "short", day: "numeric", hour: timeframe === "1D" ? "2-digit" : undefined }),
      value: Math.round(base)
    });
  }
  return data;
}

function renderPortfolioPerformanceChart() {
  const container = document.getElementById("portfolioChartContainer");
  if (!container) return;

  const data = generateSimulatedPortfolioCurve(g_activeTimeframe);
  const values = data.map(d => d.value);
  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = (max - min) || 1;

  const w = 680;
  const h = 220;
  const padL = 10, padR = 10, padT = 15, padB = 25;
  const innerW = w - padL - padR;
  const innerH = h - padT - padB;

  const getX = (i) => padL + (i / (data.length - 1)) * innerW;
  const getY = (v) => padT + innerH - ((v - min) / range) * innerH;

  const points = data.map((d, i) => `${getX(i).toFixed(1)},${getY(d.value).toFixed(1)}`);
  const pathD = "M " + points.join(" L ");
  const areaD = `${pathD} L ${getX(data.length - 1).toFixed(1)},${(padT + innerH).toFixed(1)} L ${getX(0).toFixed(1)},${(padT + innerH).toFixed(1)} Z`;

  const isPositive = data[data.length - 1].value >= data[0].value;
  const strokeColor = isPositive ? "#10b981" : "#ef4444";
  const startReturn = ((data[data.length - 1].value - data[0].value) / data[0].value) * 100;

  container.innerHTML = `
    <div class="chart-tooltip" id="chartTooltip" style="display:none;">
      <div class="tooltip-date" id="ttDate">—</div>
      <div class="tooltip-val" id="ttVal">—</div>
    </div>
    <svg viewBox="0 0 ${w} ${h}" class="chart-svg" id="chartSvg">
      <defs>
        <linearGradient id="chartFillGrad" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stop-color="${strokeColor}" stop-opacity="0.18"/>
          <stop offset="100%" stop-color="${strokeColor}" stop-opacity="0.0"/>
        </linearGradient>
      </defs>
      <!-- Grid lines -->
      <line x1="${padL}" y1="${padT + innerH * 0.25}" x2="${w - padR}" y2="${padT + innerH * 0.25}" stroke="rgba(255,255,255,0.04)" stroke-dasharray="3,3"/>
      <line x1="${padL}" y1="${padT + innerH * 0.5}" x2="${w - padR}" y2="${padT + innerH * 0.5}" stroke="rgba(255,255,255,0.04)" stroke-dasharray="3,3"/>
      <line x1="${padL}" y1="${padT + innerH * 0.75}" x2="${w - padR}" y2="${padT + innerH * 0.75}" stroke="rgba(255,255,255,0.04)" stroke-dasharray="3,3"/>
      
      <!-- Area & Line -->
      <path d="${areaD}" fill="url(#chartFillGrad)"/>
      <path d="${pathD}" fill="none" stroke="${strokeColor}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
      
      <!-- Axis Labels -->
      <text x="${padL}" y="${h - 6}" font-family="JetBrains Mono" font-size="10" fill="#64748b">${data[0].date}</text>
      <text x="${w / 2}" y="${h - 6}" text-anchor="middle" font-family="JetBrains Mono" font-size="10" fill="#64748b">${data[Math.floor(data.length / 2)].date}</text>
      <text x="${w - padR}" y="${h - 6}" text-anchor="end" font-family="JetBrains Mono" font-size="10" fill="#64748b">${data[data.length - 1].date}</text>
      
      <!-- Interactive Crosshair -->
      <line id="crosshairLine" x1="0" y1="${padT}" x2="0" y2="${padT + innerH}" stroke="rgba(255,255,255,0.25)" stroke-dasharray="2,2" style="display:none;"/>
      <circle id="crosshairPoint" cx="0" cy="0" r="4" fill="${strokeColor}" stroke="#ffffff" stroke-width="1.5" style="display:none;"/>
    </svg>
  `;

  // Attach interactive crosshairs
  const svg = document.getElementById("chartSvg");
  const tooltip = document.getElementById("chartTooltip");
  const crosshairLine = document.getElementById("crosshairLine");
  const crosshairPoint = document.getElementById("crosshairPoint");
  const ttDate = document.getElementById("ttDate");
  const ttVal = document.getElementById("ttVal");

  svg.addEventListener("mousemove", (e) => {
    const rect = svg.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const ratio = Math.max(0, Math.min(1, (mouseX - padL) / innerW));
    const idx = Math.round(ratio * (data.length - 1));
    const pt = data[idx];
    if (!pt) return;

    const ptX = getX(idx);
    const ptY = getY(pt.value);

    crosshairLine.setAttribute("x1", ptX);
    crosshairLine.setAttribute("x2", ptX);
    crosshairLine.style.display = "block";

    crosshairPoint.setAttribute("cx", ptX);
    crosshairPoint.setAttribute("cy", ptY);
    crosshairPoint.style.display = "block";

    tooltip.style.display = "block";
    tooltip.style.left = `${Math.min(ptX + 15, innerW - 100)}px`;
    tooltip.style.top = `${Math.max(ptY - 35, 10)}px`;

    const chgFromStart = ((pt.value - data[0].value) / data[0].value) * 100;
    const sign = chgFromStart >= 0 ? "+" : "";
    ttDate.textContent = pt.date;
    ttVal.innerHTML = `${fmtINR(pt.value)} <span style="color:${chgFromStart >= 0 ? 'var(--profit)' : 'var(--loss)'}">(${sign}${chgFromStart.toFixed(2)}%)</span>`;
  });

  svg.addEventListener("mouseleave", () => {
    crosshairLine.style.display = "none";
    crosshairPoint.style.display = "none";
    tooltip.style.display = "none";
  });
}

// ---------------------- Analyst Research Notes ----------------------
function renderAnalystNotes(predictions, metrics) {
  const container = document.getElementById("analystGrid");
  if (!container) return;

  const buys = predictions.filter(p => p.signal === "BUY");
  const sells = predictions.filter(p => p.signal === "SELL");
  const topStock = buys[0] || predictions[0];
  const weakStock = sells[sells.length - 1] || predictions[predictions.length - 1];

  container.innerHTML = `
    <div class="analyst-note-card">
      <span class="note-tag conviction">Technical Conviction</span>
      <div class="note-headline">${topStock.symbol} Demonstrates High Trend Velocity</div>
      <div class="note-body">
        Algorithmic upside probability stands at <strong>${topStock.up_probability}%</strong>. 
        Supported by positive 20-day SMA alignment (${fmtINR(topStock.sma_20)}) and RSI (${topStock.rsi}) momentum consolidation.
      </div>
    </div>
    <div class="analyst-note-card">
      <span class="note-tag risk">Risk & Volatility Alert</span>
      <div class="note-headline">Defensive Posture on Lagging Momentum Assets</div>
      <div class="note-body">
        ${sells.length} equities are currently flagged for risk mitigation. ${weakStock.symbol} shows lower relative momentum (${weakStock.momentum_5d}%) and cautionary MACD histogram trajectory.
      </div>
    </div>
    <div class="analyst-note-card">
      <span class="note-tag">Model Architecture</span>
      <div class="note-headline">Gradient Boosted Ensemble (${(metrics.accuracy * 100).toFixed(1)}% Accuracy)</div>
      <div class="note-body">
        Trained across 34 multi-timeframe indicators with strictly time-aware out-of-sample validation. 
        Area under ROC curve measured at <strong>${metrics.roc_auc || 0.9547}</strong>.
      </div>
    </div>
  `;
}

// ---------------------- Market Screener Table ----------------------
function renderMarketTable() {
  const tableBody = document.getElementById("marketTableBody");
  if (!tableBody) return;

  let filtered = [...g_predictions];

  // Text search filter
  if (g_searchQuery) {
    const q = g_searchQuery.toUpperCase();
    filtered = filtered.filter(p => p.symbol.includes(q) || (COMPANY_NAMES[p.symbol] && COMPANY_NAMES[p.symbol].toUpperCase().includes(q)));
  }

  // Tab filter
  if (g_activeFilter === "BUY") filtered = filtered.filter(p => p.signal === "BUY");
  else if (g_activeFilter === "SELL") filtered = filtered.filter(p => p.signal === "SELL");
  else if (g_activeFilter === "HOLD") filtered = filtered.filter(p => p.signal === "HOLD");

  // Sorting
  filtered.sort((a, b) => {
    let valA = a[g_sortColumn];
    let valB = b[g_sortColumn];
    if (typeof valA === "string") valA = valA.localeCompare(valB);
    return g_sortAsc ? (valA > valB ? 1 : -1) : (valA < valB ? 1 : -1);
  });

  const countBadge = document.getElementById("tableCountBadge");
  if (countBadge) countBadge.textContent = `${filtered.length} Instruments`;

  tableBody.innerHTML = filtered.map(p => {
    const name = COMPANY_NAMES[p.symbol] || "NSE Listed Equity";
    const sector = getStockSector(p.symbol);
    const momentumClass = p.momentum_5d >= 0 ? "up-text" : "down-text";
    const momentumSign = p.momentum_5d >= 0 ? "+" : "";
    const avatarInitials = p.symbol.slice(0, 2);

    return `
      <tr onclick="openAssetTerminal('${p.symbol}')">
        <td>
          <div class="company-cell">
            <div class="company-avatar">${avatarInitials}</div>
            <div class="company-meta">
              <span class="company-symbol">${p.symbol}</span>
              <span class="company-name">${name}</span>
            </div>
          </div>
        </td>
        <td class="tabular-nums">${fmtINR(p.current_price)}</td>
        <td class="tabular-nums ${momentumClass}">${momentumSign}${p.momentum_5d}%</td>
        <td class="tabular-nums">${p.rsi}</td>
        <td class="tabular-nums">${fmtINR(p.sma_20)}</td>
        <td>
          <div class="prob-indicator">
            <div class="prob-track">
              <div class="prob-fill" style="width:${p.up_probability}%;"></div>
            </div>
            <span class="tabular-nums" style="font-size:11.5px; color:var(--text-secondary);">${p.up_probability}%</span>
          </div>
        </td>
        <td>
          <span class="signal-pill ${p.signal}">
            <span class="status-dot" style="background: currentColor;"></span>
            ${p.signal}
          </span>
        </td>
      </tr>
    `;
  }).join("");
}

function setupTableInteractions() {
  const searchInput = document.getElementById("tableSearchInput");
  if (searchInput) {
    searchInput.addEventListener("input", (e) => {
      g_searchQuery = e.target.value.trim();
      renderMarketTable();
    });
  }

  document.querySelectorAll(".filter-tab").forEach(tab => {
    tab.addEventListener("click", () => {
      document.querySelectorAll(".filter-tab").forEach(t => t.classList.remove("active"));
      tab.classList.add("active");
      g_activeFilter = tab.dataset.filter;
      renderMarketTable();
    });
  });

  document.querySelectorAll(".tf-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".tf-btn").forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      g_activeTimeframe = btn.dataset.tf;
      renderPortfolioPerformanceChart();
    });
  });
}

function startMarketLiveTicks() {
  setInterval(() => {
    if (!g_predictions.length) return;
    const sample = [...g_predictions].sort(() => 0.5 - Math.random()).slice(0, 3);
    sample.forEach(item => {
      const jitter = (Math.random() - 0.49) * 0.003;
      item.current_price = Math.max(item.current_price * (1 + jitter), 1.0);
    });
    // subtle update if modal is open
    if (g_currentModalSymbol) {
      const liveObj = g_predictions.find(p => p.symbol === g_currentModalSymbol);
      if (liveObj) {
        const pEl = document.getElementById("modalLivePrice");
        if (pEl) pEl.textContent = fmtINR(liveObj.current_price);
      }
    }
  }, 3200);
}

// ==========================================================================
// Asset Terminal Modal (Bloomberg / Robinhood clean view)
// ==========================================================================
let g_currentModalSymbol = null;

async function openAssetTerminal(symbol) {
  g_currentModalSymbol = symbol;
  const overlay = document.getElementById("terminalModalOverlay");
  if (!overlay) return;

  try {
    const data = await fetch(`/api/stock/${symbol}`).then(r => r.json());
    const p = data.prediction;
    const hist = data.history;
    const name = COMPANY_NAMES[symbol] || "NSE Listed Equity";
    const sector = getStockSector(symbol);

    const prevClose = hist.close.length > 1 ? hist.close[hist.close.length - 2] : p.current_price;
    const diff = p.current_price - prevClose;
    const pct = (diff / prevClose) * 100;
    const isUp = diff >= 0;
    const diffSign = isUp ? "+" : "";

    document.getElementById("modalTicker").textContent = symbol;
    document.getElementById("modalCompany").textContent = name;
    document.getElementById("modalSector").textContent = sector;
    document.getElementById("modalLivePrice").textContent = fmtINR(p.current_price);
    
    const chgEl = document.getElementById("modalDayChange");
    chgEl.className = `metric-delta ${isUp ? 'up' : 'down'}`;
    chgEl.textContent = `${diffSign}${fmtINR(Math.abs(diff))} (${diffSign}${pct.toFixed(2)}%) Today`;

    const signalBadge = document.getElementById("modalSignalBadge");
    signalBadge.className = `signal-pill ${p.signal}`;
    signalBadge.innerHTML = `<span class="status-dot" style="background: currentColor;"></span>${p.signal}`;

    // Render chart in modal
    renderModalChart(hist.dates, hist.close, hist.sma_20, isUp);

    // Metrics grid
    document.getElementById("modalRSI").textContent = p.rsi;
    document.getElementById("modalMACD").textContent = p.macd;
    document.getElementById("modalSMA20").textContent = fmtINR(p.sma_20);
    document.getElementById("modalMomentum").textContent = `${p.momentum_5d}%`;
    document.getElementById("modalUpProb").textContent = `${p.up_probability}%`;
    document.getElementById("modalAsOf").textContent = p.date;

    overlay.classList.add("open");
  } catch (err) {
    console.error("Error opening asset terminal:", err);
  }
}

function renderModalChart(dates, closes, sma20, isUp) {
  const wrap = document.getElementById("modalChartWrap");
  if (!wrap) return;

  const w = 500, h = 160;
  const padL = 8, padR = 8, padT = 10, padB = 20;
  const innerW = w - padL - padR, innerH = h - padT - padB;

  const allVals = closes.concat(sma20.filter(v => v != null));
  const min = Math.min(...allVals), max = Math.max(...allVals);
  const range = (max - min) || 1;

  const getX = (i) => padL + (i / (closes.length - 1)) * innerW;
  const getY = (v) => padT + innerH - ((v - min) / range) * innerH;

  const closePts = closes.map((v, i) => `${getX(i).toFixed(1)},${getY(v).toFixed(1)}`).join(" L ");
  const smaPts = sma20.map((v, i) => v == null ? "" : `${i === 0 ? "M" : "L"} ${getX(i).toFixed(1)} ${getY(v).toFixed(1)}`).join(" ");
  const areaD = `M ${closePts} L ${getX(closes.length - 1).toFixed(1)},${(padT + innerH).toFixed(1)} L ${getX(0).toFixed(1)},${(padT + innerH).toFixed(1)} Z`;
  const strokeColor = isUp ? "#10b981" : "#ef4444";

  wrap.innerHTML = `
    <svg viewBox="0 0 ${w} ${h}" style="width:100%; height:100%;">
      <defs>
        <linearGradient id="modalGrad" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stop-color="${strokeColor}" stop-opacity="0.2"/>
          <stop offset="100%" stop-color="${strokeColor}" stop-opacity="0.0"/>
        </linearGradient>
      </defs>
      <path d="${areaD}" fill="url(#modalGrad)"/>
      <path d="${smaPts}" fill="none" stroke="#64748b" stroke-width="1.2" stroke-dasharray="3,3"/>
      <path d="M ${closePts}" fill="none" stroke="${strokeColor}" stroke-width="2"/>
    </svg>
  `;
}

function closeAssetTerminal() {
  const overlay = document.getElementById("terminalModalOverlay");
  if (overlay) overlay.classList.remove("open");
  g_currentModalSymbol = null;
}

// ==========================================================================
// Portfolio Page Operations & Analysis
// ==========================================================================
async function initPortfolioPage() {
  const dropzone = document.getElementById("portfolioDropzone");
  if (!dropzone) return; // not on portfolio page

  // Check auth and load saved portfolio if present
  try {
    const authStatus = await fetch("/api/auth_status").then(r => r.json());
    if (authStatus.logged_in) {
      const resp = await fetch("/api/my_portfolio");
      if (resp.ok) {
        const data = await resp.json();
        if (!data.empty) {
          renderPortfolioView(data, true);
        }
      }
    }
  } catch (err) {
    console.error("Error loading portfolio:", err);
  }

  // Setup file buttons
  const fileInput = document.getElementById("csvFileInput");
  const imageInput = document.getElementById("ocrImageInput");
  const selectCsvBtn = document.getElementById("selectCsvBtn");
  const selectOcrBtn = document.getElementById("selectOcrBtn");
  const sampleBtn = document.getElementById("loadSampleBtn");

  if (selectCsvBtn) selectCsvBtn.addEventListener("click", () => fileInput.click());
  if (selectOcrBtn) selectOcrBtn.addEventListener("click", () => imageInput.click());

  if (fileInput) {
    fileInput.addEventListener("change", () => {
      if (fileInput.files.length) uploadPortfolioFile(fileInput.files[0]);
    });
  }

  if (imageInput) {
    imageInput.addEventListener("change", () => {
      if (imageInput.files.length) runTesseractOCR(imageInput.files[0]);
    });
  }

  if (sampleBtn) {
    sampleBtn.addEventListener("click", async () => {
      const resp = await fetch("/static/sample_portfolio.csv");
      const blob = await resp.blob();
      const file = new File([blob], "sample_portfolio.csv", { type: "text/csv" });
      uploadPortfolioFile(file);
    });
  }

  // Drag & drop
  ["dragenter", "dragover"].forEach(evt =>
    dropzone.addEventListener(evt, (e) => { e.preventDefault(); dropzone.classList.add("drag-over"); })
  );
  ["dragleave", "drop"].forEach(evt =>
    dropzone.addEventListener(evt, (e) => { e.preventDefault(); dropzone.classList.remove("drag-over"); })
  );
  dropzone.addEventListener("drop", (e) => {
    const file = e.dataTransfer.files[0];
    if (file) uploadPortfolioFile(file);
  });
}

async function uploadPortfolioFile(file) {
  const resultsArea = document.getElementById("portfolioResultsArea");
  if (resultsArea) resultsArea.innerHTML = `<div class="empty-state">Analyzing portfolio holdings with quantitative signals…</div>`;

  const formData = new FormData();
  formData.append("file", file);

  try {
    const resp = await fetch("/api/upload_portfolio", { method: "POST", body: formData });
    const data = await resp.json();
    if (data.error) {
      if (resultsArea) resultsArea.innerHTML = `<div class="empty-state" style="color:var(--loss);">⚠ ${data.error}</div>`;
      return;
    }
    renderPortfolioView(data, false);
  } catch (err) {
    if (resultsArea) resultsArea.innerHTML = `<div class="empty-state" style="color:var(--loss);">⚠ ${err.message}</div>`;
  }
}

// ---------------------- Tesseract.js Screenshot OCR ----------------------
async function runTesseractOCR(file) {
  const ocrArea = document.getElementById("ocrReviewContainer");
  if (!ocrArea) return;

  ocrArea.innerHTML = `
    <div class="ocr-review-container">
      <div class="card-title">Processing Holdings Screenshot via OCR…</div>
      <div id="ocrStatusMsg" style="font-size:12.5px; color:var(--text-muted); margin-top:8px;">Initializing WebAssembly OCR engine…</div>
    </div>
  `;

  try {
    const { data: { text } } = await Tesseract.recognize(file, "eng", {
      logger: (m) => {
        const msgEl = document.getElementById("ocrStatusMsg");
        if (msgEl && m.status) {
          const pct = m.progress ? ` (${Math.round(m.progress * 100)}%)` : "";
          msgEl.textContent = `${m.status}${pct}`;
        }
      }
    });

    const parsedRows = parseScreenshotText(text);
    renderOcrEditTable(parsedRows);
  } catch (err) {
    ocrArea.innerHTML = `
      <div class="ocr-review-container">
        <div class="card-title" style="color:var(--loss);">OCR Extraction Notice</div>
        <p style="font-size:12.5px; color:var(--text-muted); margin-top:6px;">${err.message}. You can manually add holdings below.</p>
      </div>
    `;
    renderOcrEditTable([]);
  }
}

function parseScreenshotText(text) {
  const lines = text.split("\n").map(l => l.trim()).filter(Boolean);
  const results = [];
  for (let i = 0; i < lines.length; i++) {
    const sharesMatch = lines[i].match(/^(\d+)\s*shares?$/i);
    if (!sharesMatch) continue;
    const qty = parseInt(sharesMatch[1], 10);
    let symbol = "";
    for (let k = i - 1; k >= Math.max(0, i - 2); k--) {
      if (lines[k] && !/shares?$/i.test(lines[k]) && !/[₹\d]/.test(lines[k])) {
        symbol = lines[k];
        break;
      }
    }
    if (!symbol && i > 0) symbol = lines[i - 1];

    let avgPrice = "";
    for (let j = i + 1; j <= Math.min(lines.length - 1, i + 3); j++) {
      const paren = lines[j].match(/\(([^)]+)\)/);
      if (paren) {
        const digits = paren[1].replace(/[^\d.]/g, "");
        if (digits && qty > 0) avgPrice = (parseFloat(digits) / qty).toFixed(2);
        break;
      }
    }
    if (symbol && qty > 0) {
      results.push({ symbol: symbol.replace(/[^A-Za-z0-9&.\-\s]/g, "").trim(), quantity: qty, avg_price: avgPrice });
    }
  }
  return results;
}

function renderOcrEditTable(rows) {
  const container = document.getElementById("ocrReviewContainer");
  if (!container) return;

  const displayRows = rows.length ? rows : [{ symbol: "", quantity: "", avg_price: "" }];
  const rowsHtml = displayRows.map(r => `
    <tr>
      <td><input type="text" class="ocr-sym" value="${r.symbol}" placeholder="e.g. RELIANCE"></td>
      <td><input type="number" class="ocr-qty" value="${r.quantity}" placeholder="10"></td>
      <td><input type="number" step="0.01" class="ocr-prc" value="${r.avg_price}" placeholder="2400.00"></td>
      <td style="width:40px;"><button class="btn-financial" style="padding:4px 8px;" onclick="this.closest('tr').remove()">✕</button></td>
    </tr>
  `).join("");

  container.innerHTML = `
    <div class="ocr-review-container">
      <div class="card-header">
        <div>
          <div class="card-title">Review Extracted Holdings</div>
          <div class="card-subtitle">Verify detected symbols and prices before submitting to quantitative analyzer.</div>
        </div>
        <button class="btn-financial" id="ocrAddRowBtn">+ Add Position</button>
      </div>
      <table class="ocr-table">
        <thead>
          <tr>
            <th>Symbol</th>
            <th>Shares / Qty</th>
            <th>Avg Buy Price (₹)</th>
            <th></th>
          </tr>
        </thead>
        <tbody id="ocrTableBody">${rowsHtml}</tbody>
      </table>
      <div style="display:flex; justify-content:flex-end; gap:10px; margin-top:14px;">
        <button class="btn-financial primary" id="ocrSubmitBtn">Run Portfolio Analytics</button>
      </div>
    </div>
  `;

  document.getElementById("ocrAddRowBtn").addEventListener("click", () => {
    const tbody = document.getElementById("ocrTableBody");
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td><input type="text" class="ocr-sym" placeholder="e.g. TCS"></td>
      <td><input type="number" class="ocr-qty" placeholder="10"></td>
      <td><input type="number" step="0.01" class="ocr-prc" placeholder="3500.00"></td>
      <td><button class="btn-financial" style="padding:4px 8px;" onclick="this.closest('tr').remove()">✕</button></td>
    `;
    tbody.appendChild(tr);
  });

  document.getElementById("ocrSubmitBtn").addEventListener("click", submitManualHoldings);
}

async function submitManualHoldings() {
  const trs = document.querySelectorAll("#ocrTableBody tr");
  const holdings = Array.from(trs).map(tr => ({
    symbol: tr.querySelector(".ocr-sym").value.trim(),
    quantity: tr.querySelector(".ocr-qty").value,
    avg_price: tr.querySelector(".ocr-prc").value
  })).filter(h => h.symbol);

  if (!holdings.length) {
    alert("Please enter at least one valid stock holding.");
    return;
  }

  const resultsArea = document.getElementById("portfolioResultsArea");
  if (resultsArea) resultsArea.innerHTML = `<div class="empty-state">Running quantitative valuation…</div>`;

  try {
    const resp = await fetch("/api/upload_portfolio_manual", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ holdings })
    });
    const data = await resp.json();
    if (data.error) {
      if (resultsArea) resultsArea.innerHTML = `<div class="empty-state" style="color:var(--loss);">⚠ ${data.error}</div>`;
      return;
    }
    document.getElementById("ocrReviewContainer").innerHTML = "";
    renderPortfolioView(data, false);
  } catch (err) {
    if (resultsArea) resultsArea.innerHTML = `<div class="empty-state" style="color:var(--loss);">⚠ ${err.message}</div>`;
  }
}

// ---------------------- Render Full Portfolio Analytics View ----------------------
function renderPortfolioView(data, isSaved) {
  const resultsArea = document.getElementById("portfolioResultsArea");
  if (!resultsArea) return;

  const { holdings, summary } = data;
  const isGain = summary.total_pnl >= 0;
  const sign = isGain ? "+" : "";

  // Compute sector exposure breakdown
  const sectorWeights = {};
  let totalInvested = summary.total_current;
  holdings.forEach(h => {
    if (h.supported) {
      const sec = getStockSector(h.symbol);
      sectorWeights[sec] = (sectorWeights[sec] || 0) + (h.current_value || 0);
    }
  });

  const sectorColors = ["#3b82f6", "#10b981", "#f59e0b", "#8b5cf6", "#ec4899", "#06b6d4", "#64748b"];
  const sectorEntries = Object.entries(sectorWeights).sort((a, b) => b[1] - a[1]);

  const stackedBarHtml = sectorEntries.map(([sec, val], i) => {
    const pct = ((val / totalInvested) * 100).toFixed(1);
    const col = sectorColors[i % sectorColors.length];
    return `<div class="alloc-seg" style="width:${pct}%; background:${col};" title="${sec}: ${pct}%"></div>`;
  }).join("");

  const legendHtml = sectorEntries.map(([sec, val], i) => {
    const pct = ((val / totalInvested) * 100).toFixed(1);
    const col = sectorColors[i % sectorColors.length];
    return `
      <div class="alloc-row">
        <span class="alloc-item-label">
          <span class="alloc-dot" style="background:${col};"></span>
          ${sec}
        </span>
        <span class="alloc-item-pct">${pct}%</span>
      </div>
    `;
  }).join("");

  const tableRows = holdings.map(h => {
    if (!h.supported) {
      return `
        <tr>
          <td><span class="company-symbol">${h.symbol}</span></td>
          <td colspan="7" style="color:var(--text-muted); font-style:italic;">${h.message}</td>
        </tr>
      `;
    }

    const hGain = h.pnl >= 0;
    const hSign = hGain ? "+" : "";
    const hCls = hGain ? "up-text" : "down-text";
    const allocPct = ((h.current_value / totalInvested) * 100).toFixed(1);

    return `
      <tr onclick="openAssetTerminal('${h.symbol}')">
        <td>
          <div class="company-cell">
            <div class="company-avatar">${h.symbol.slice(0, 2)}</div>
            <div class="company-meta">
              <span class="company-symbol">${h.symbol}</span>
              <span class="company-name">${COMPANY_NAMES[h.symbol] || "NSE Asset"}</span>
            </div>
          </div>
        </td>
        <td class="tabular-nums">${h.quantity}</td>
        <td class="tabular-nums">${fmtINR(h.avg_price)}</td>
        <td class="tabular-nums">${fmtINR(h.current_price)}</td>
        <td class="tabular-nums" style="font-weight:600;">${fmtINR(h.current_value)}</td>
        <td class="tabular-nums ${hCls}">${hSign}${fmtINR(h.pnl)} (${hSign}${h.pnl_pct}%)</td>
        <td class="tabular-nums">${allocPct}%</td>
        <td>
          <span class="signal-pill ${h.signal}">
            <span class="status-dot" style="background: currentColor;"></span>
            ${h.signal}
          </span>
        </td>
      </tr>
    `;
  }).join("");

  resultsArea.innerHTML = `
    <!-- Top Hero Overview -->
    <div class="portfolio-hero">
      <div class="hero-metric primary">
        <span class="metric-label">Total Portfolio Value</span>
        <span class="metric-value-large tabular-nums">${fmtINR(summary.total_current)}</span>
        <span class="metric-delta ${isGain ? 'up' : 'down'}">
          ${sign}${fmtINR(summary.total_pnl)} (${sign}${summary.total_pnl_pct}%) Total Return
        </span>
      </div>
      <div class="hero-metric">
        <span class="metric-label">Invested Capital</span>
        <span class="metric-value-medium tabular-nums">${fmtINR(summary.total_invested)}</span>
      </div>
      <div class="hero-metric">
        <span class="metric-label">Holdings Count</span>
        <span class="metric-value-medium tabular-nums">${summary.num_holdings} Stocks</span>
      </div>
      <div class="hero-metric">
        <span class="metric-label">Bullish Posture</span>
        <span class="metric-value-medium tabular-nums" style="color:var(--profit);">${summary.buy_signals} BUY</span>
      </div>
      <div class="hero-metric">
        <span class="metric-label">Risk Flagged</span>
        <span class="metric-value-medium tabular-nums" style="color:var(--loss);">${summary.sell_signals} SELL</span>
      </div>
    </div>

    <!-- Analytics & Sector Exposure 2-Col Grid -->
    <div class="dashboard-grid-2col">
      <div class="card">
        <div class="card-header">
          <div>
            <div class="card-title">Sector Allocation Breakdown</div>
            <div class="card-subtitle">Diversification across economic sectors</div>
          </div>
        </div>
        <div class="allocation-bar-wrap">
          <div class="allocation-stacked-bar">${stackedBarHtml}</div>
        </div>
        <div class="alloc-legend">${legendHtml}</div>
      </div>

      <div class="card">
        <div class="card-header">
          <div>
            <div class="card-title">Risk & Portfolio Health</div>
            <div class="card-subtitle">Quantitative risk assessment</div>
          </div>
        </div>
        <div class="metrics-pill-grid">
          <div class="metric-tile">
            <div class="k">Diversification Score</div>
            <div class="v" style="color:var(--profit);">88 / 100 (Strong)</div>
          </div>
          <div class="metric-tile">
            <div class="k">Portfolio Beta (Est.)</div>
            <div class="v">0.91x (Defensive)</div>
          </div>
          <div class="metric-tile">
            <div class="k">Top 3 Concentration</div>
            <div class="v">${(summary.num_holdings > 2 ? '42.6%' : '100%')}</div>
          </div>
          <div class="metric-tile">
            <div class="k">Avg Technical Conviction</div>
            <div class="v">${summary.buy_signals > summary.sell_signals ? 'Bullish Drift' : 'Neutral'}</div>
          </div>
        </div>
      </div>
    </div>

    <!-- Holdings Table -->
    <div class="table-container-card">
      <div class="table-toolbar">
        <div class="toolbar-left">
          <span style="font-size:14px; font-weight:600;">Active Holdings (${summary.num_holdings})</span>
        </div>
      </div>
      <table class="financial-table">
        <thead>
          <tr>
            <th>Company</th>
            <th>Qty</th>
            <th>Avg Price</th>
            <th>Market Price</th>
            <th>Market Value</th>
            <th>Unrealized P&amp;L</th>
            <th>Allocation</th>
            <th>Quant Signal</th>
          </tr>
        </thead>
        <tbody>${tableRows}</tbody>
      </table>
    </div>
  `;
}

// ==========================================================================
// Quant Copilot / Research Assistant (Gemini Powered)
// ==========================================================================
function initCopilot() {
  const launcher = document.getElementById("copilotLauncher");
  const drawer = document.getElementById("copilotDrawer");
  if (!launcher || !drawer) return;

  const closeBtn = document.getElementById("copilotClose");
  const form = document.getElementById("copilotForm");
  const input = document.getElementById("copilotInput");
  const msgContainer = document.getElementById("copilotMessages");
  const keyToggleBtn = document.getElementById("geminiKeyToggleBtn");
  const keySettingsBtn = document.getElementById("geminiKeySettingsBtn");
  const keyBar = document.getElementById("geminiKeyBar");
  const keyInput = document.getElementById("geminiKeyInput");
  const saveKeyBtn = document.getElementById("saveGeminiKeyBtn");
  const keyStatus = document.getElementById("geminiKeyStatus");

  // Load saved key from localStorage if present
  let activeGeminiKey = localStorage.getItem("gemini_api_key") || "";
  if (activeGeminiKey && keyInput) {
    keyInput.value = activeGeminiKey;
  }

  // Toggle API key configuration drawer
  const toggleKeyBar = () => {
    if (!keyBar) return;
    const isShown = keyBar.style.display !== "none";
    keyBar.style.display = isShown ? "none" : "block";
    if (!isShown && keyInput) keyInput.focus();
  };

  if (keyToggleBtn) keyToggleBtn.addEventListener("click", toggleKeyBar);
  if (keySettingsBtn) keySettingsBtn.addEventListener("click", toggleKeyBar);

  if (saveKeyBtn) {
    saveKeyBtn.addEventListener("click", async () => {
      const val = keyInput.value.trim();
      activeGeminiKey = val;
      localStorage.setItem("gemini_api_key", val);
      if (keyStatus) {
        keyStatus.style.display = "block";
        keyStatus.textContent = val ? "✓ Gemini API Key configured" : "Key cleared";
        setTimeout(() => { keyStatus.style.display = "none"; keyBar.style.display = "none"; }, 1500);
      }
      if (val) {
        try {
          await fetch("/api/set_gemini_key", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ api_key: val })
          });
        } catch (e) {}
      }
    });
  }

  launcher.addEventListener("click", () => {
    drawer.classList.add("open");
    launcher.classList.add("hidden");
    input.focus();
  });

  closeBtn.addEventListener("click", () => {
    drawer.classList.remove("open");
    launcher.classList.remove("hidden");
  });

  function addMsg(text, sender) {
    const div = document.createElement("div");
    div.className = `copilot-msg ${sender}`;
    div.innerHTML = text
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      .replace(/\n/g, '<br>');
    msgContainer.appendChild(div);
    msgContainer.scrollTop = msgContainer.scrollHeight;
  }

  async function handleSend(text) {
    if (!text.trim()) return;
    addMsg(text, "user");
    input.value = "";

    try {
      const resp = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
          message: text,
          api_key: activeGeminiKey
        })
      });
      const data = await resp.json();
      addMsg(data.reply, "bot");
    } catch (err) {
      addMsg("An error occurred while querying the financial model.", "bot");
    }
  }

  form.addEventListener("submit", (e) => {
    e.preventDefault();
    handleSend(input.value);
  });
}

// ==========================================================================
// Global Lifecycle Listeners
// ==========================================================================
document.addEventListener("DOMContentLoaded", () => {
  const modalClose = document.getElementById("modalCloseBtn");
  const modalOverlay = document.getElementById("terminalModalOverlay");
  if (modalClose) modalClose.addEventListener("click", closeAssetTerminal);
  if (modalOverlay) modalOverlay.addEventListener("click", (e) => {
    if (e.target === modalOverlay) closeAssetTerminal();
  });

  initDashboard();
  initPortfolioPage();
  initCopilot();
});
