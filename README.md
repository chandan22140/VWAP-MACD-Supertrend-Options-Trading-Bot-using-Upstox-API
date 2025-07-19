
# VWAP-MACD-Supertrend-Options-Trading-Bot-using-Upstox-API

A professional-grade intraday options trading algorithm built on the **Brahmastra Strategy**, leveraging Supertrend, MACD, and VWAP indicators for high-confidence entries. The bot connects to the **Upstox Open API** and trades ATM options on NIFTY or BANKNIFTY based on triple confirmation logic.

---

##  Features

-  **Triple Confirmation Strategy** (Supertrend + MACD + VWAP)
-  Real-time data fetching from **Upstox API**
-  Auto-execution of ATM option trades (CE/PE) based on signal alignment
-  Built-in stop-loss and target levels
-  Accurate indicator calculations with:
  -  Correct Supertrend (with ATR smoothing)
  -  Clean VWAP using cumulative typical price
  -  Standard MACD (fast/slow EMA + signal + histogram)

---

##  Strategy Rules (Brahmastra Logic)

**Enter Trade Only When All Three Conditions Align:**

1.  **Supertrend Signal**: A trend flip (uptrend/downtrend)
2.  **MACD Crossover**: MACD line crosses Signal line
3.  **Price Near VWAP**: Ensures mean-reversion entry

**Exit Conditions:**

- Partial exit when MACD gives an opposite signal
- Full exit when Supertrend flips again
- Optional: Hard target and stop-loss levels (e.g., 100 pt target, 50 pt SL)

---

##  Project Structure

```

VWAP-MACD-Supertrend-Options-Trading-Bot-using-Upstox-API/

├── brahmastra.py
├── requirements.txt
└── README.md

````

---

## ⚙️ Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/brahmastra-algo.git
cd brahmastra-algo
````

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure API Credentials

Update your Upstox credentials in `main.py`:

```python
API_KEY = "YOUR_UPSTOX_API_KEY"
API_SECRET = "YOUR_UPSTOX_API_SECRET"
REDIRECT_URI = "YOUR_REDIRECT_URI"
ACCESS_TOKEN = "YOUR_ACCESS_TOKEN"
```

Follow the [Upstox OAuth Flow](https://upstox.com/developer/api-documentation/open-api/#section/Authentication) to generate an access token.

---

##  Indicator Math Highlights

###  VWAP

Cumulative version based on:

```
VWAP = sum(typical_price * volume) / sum(volume)
```

###  MACD

```
MACD = EMA(close, fast) - EMA(close, slow)
Signal = EMA(MACD, signal_period)
Histogram = MACD - Signal
```

###  Supertrend

Built using ATR with Wilder’s smoothing and dynamic band tightening for trend continuity.
