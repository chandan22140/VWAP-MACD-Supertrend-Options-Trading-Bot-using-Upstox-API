import time
import pandas as pd
from upstox_api.api import Upstox, LiveFeedType, OHLCInterval
import pandas as pd
import numpy as np
API_KEY = ""
API_SECRET = ""
REDIRECT_URI = ""
ACCESS_TOKEN = ""  # generated via OAuth flow

SYMBOL = "NIFTY 50"              # underlying
OPTION_STRIKE = 0                  # 0 for ATM
OPTION_TYPE = "CE"               # "CE" or "PE"
TIMEFRAME = OHLCInterval.Minute_5 # 5-minute candles
VWAP_PERIOD = None                 # VWAP uses entire session
MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9
SUPERTREND_PERIOD = 10
SUPERTREND_FACTOR = 3

STOP_LOSS_POINTS = 50
TARGET_POINTS = 100

# === UTILITY FUNCTIONS ===

def fetch_ohlc(u: Upstox, symbol, interval, count=100):
    """Fetch historical OHLC data."""
    bars = u.get_ohlc(exchange="NSE_OPTION", symbol=symbol, interval=interval, count=count)
    df = pd.DataFrame(bars)
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.set_index('timestamp', inplace=True)
    return df


# def calculate_vwap(df):
#     """Volume Weighted Average Price."""
#     vwap = (df['close'] * df['volume']).cumsum() / df['volume'].cumsum()
#     return vwap


# def calculate_macd(df):
#     """Returns MACD line, signal line, histogram."""
#     fast_ema = df['close'].ewm(span=MACD_FAST, adjust=False).mean()
#     slow_ema = df['close'].ewm(span=MACD_SLOW, adjust=False).mean()
#     macd = fast_ema - slow_ema
#     signal = macd.ewm(span=MACD_SIGNAL, adjust=False).mean()
#     hist = macd - signal
#     return macd, signal, hist


# def calculate_supertrend(df, period, factor):
#     """Returns Supertrend series."""
#     hl2 = (df['high'] + df['low']) / 2
#     atr = df['high'].combine(df['low'], max) - df['high'].combine(df['low'], min)
#     atr = atr.rolling(period).mean()
#     upperband = hl2 + (factor * atr)
#     lowerband = hl2 - (factor * atr)
#     supertrend = [True] * len(df)
#     for i in range(1, len(df)):
#         curr_close = df['close'].iloc[i]
#         prev_st = supertrend[i-1]
#         if curr_close > upperband.iloc[i-1]:
#             supertrend[i] = True
#         elif curr_close < lowerband.iloc[i-1]:
#             supertrend[i] = False
#         else:
#             supertrend[i] = prev_st
#         # adjust bands
#         if supertrend[i] and lowerband.iloc[i] < lowerband.iloc[i-1]:
#             lowerband.iloc[i] = lowerband.iloc[i-1]
#         if not supertrend[i] and upperband.iloc[i] > upperband.iloc[i-1]:
#             upperband.iloc[i] = upperband.iloc[i-1]
#     return pd.Series(supertrend, index=df.index)




# --- Corrected VWAP ---
def calculate_vwap(df):
    """
    Calculates the continuous Volume Weighted Average Price (VWAP).
    
    Note: Standard VWAP is typically reset daily for intraday analysis. 
    This implementation is a continuous, cumulative version.
    """
    # Standard VWAP uses the "typical price"
    typical_price = (df['high'] + df['low'] + df['close']) / 3
    
    # Calculate cumulative values
    cumulative_price_volume = (typical_price * df['volume']).cumsum()
    cumulative_volume = df['volume'].cumsum()
    
    # Handle potential division by zero at the start
    vwap = cumulative_price_volume / cumulative_volume
    vwap.fillna(method='ffill', inplace=True) # Forward fill any initial NaNs
    
    return vwap

# --- Improved MACD ---
def calculate_macd(df, fast_period=12, slow_period=26, signal_period=9):
    """
    Calculates the Moving Average Convergence Divergence (MACD).
    
    Returns a tuple containing three pandas Series:
    (MACD Line, Signal Line, Histogram)
    """
    # Calculate Fast and Slow EMAs
    fast_ema = df['close'].ewm(span=fast_period, adjust=False).mean()
    slow_ema = df['close'].ewm(span=slow_period, adjust=False).mean()
    
    # Calculate MACD Line
    macd_line = fast_ema - slow_ema
    
    # Calculate Signal Line
    signal_line = macd_line.ewm(span=signal_period, adjust=False).mean()
    
    # Calculate MACD Histogram
    histogram = macd_line - signal_line
    
    return macd_line, signal_line, histogram

# --- Corrected Supertrend ---
def calculate_supertrend(df, period=7, factor=3.0):
    """
    Calculates the Supertrend indicator.
    
    Returns a pandas Series with the Supertrend line.
    """
    # 1. Calculate ATR (Average True Range) correctly
    hl2 = (df['high'] + df['low']) / 2
    prev_close = df['close'].shift(1)
    
    tr1 = pd.DataFrame(df['high'] - df['low'])
    tr2 = pd.DataFrame(abs(df['high'] - prev_close))
    tr3 = pd.DataFrame(abs(df['low'] - prev_close))
    
    frames = [tr1, tr2, tr3]
    true_range = pd.concat(frames, axis=1, join='inner').max(axis=1)
    
    # Using RMA (Wilder's smoothing) for ATR, which is common
    # This is equivalent to an EMA with alpha = 1 / period
    atr = true_range.ewm(alpha=1/period, adjust=False).mean()
    
    # 2. Calculate Upper and Lower Bands
    upper_band = hl2 + (factor * atr)
    lower_band = hl2 - (factor * atr)
    
    # 3. Initialize Supertrend and Direction
    supertrend = pd.Series([np.nan] * len(df), index=df.index)
    direction = pd.Series([1] * len(df), index=df.index) # 1 for uptrend, -1 for downtrend
    
    # 4. Main loop to calculate Supertrend
    for i in range(1, len(df)):
        # If the current close breaks above the previous upper band, it's an uptrend
        if df['close'].iloc[i] > upper_band.iloc[i-1]:
            direction.iloc[i] = 1
        # If the current close breaks below the previous lower band, it's a downtrend
        elif df['close'].iloc[i] < lower_band.iloc[i-1]:
            direction.iloc[i] = -1
        # Otherwise, the trend continues
        else:
            direction.iloc[i] = direction.iloc[i-1]
            # Adjust bands to "stick" to the price during a trend
            if direction.iloc[i] == 1 and lower_band.iloc[i] < lower_band.iloc[i-1]:
                lower_band.iloc[i] = lower_band.iloc[i-1]
            if direction.iloc[i] == -1 and upper_band.iloc[i] > upper_band.iloc[i-1]:
                upper_band.iloc[i] = upper_band.iloc[i-1]

    # 5. Determine the Supertrend line value
    for i in range(len(df)):
        if direction.iloc[i] == 1:
            supertrend.iloc[i] = lower_band.iloc[i]
        else:
            supertrend.iloc[i] = upper_band.iloc[i]
            
    return supertrend

# === MAIN ALGO ===

def main():
    # Initialize Upstox session
    u = Upstox(API_KEY, ACCESS_TOKEN)
    u.set_redirect_uri(REDIRECT_URI)
    u.get_master_contract(exchange="NSE")

    # Determine the ATM option symbol
    def get_atm_option_symbol():
        # Fetch nearest strike and construct symbol
        # Placeholder: user must implement logic
        return "NIFTY21JUN20000CE"

    option_symbol = get_atm_option_symbol()

    # Fetch initial data
    df = fetch_ohlc(u, option_symbol, TIMEFRAME)
    df['vwap'] = calculate_vwap(df)
    df['macd'], df['signal'], df['hist'] = calculate_macd(df)
    df['supertrend'] = calculate_supertrend(df, SUPERTREND_PERIOD, SUPERTREND_FACTOR)

    position = None

    while True:
        # Update with latest candle
        new_df = fetch_ohlc(u, option_symbol, TIMEFRAME, count=1)
        if new_df.index[-1] not in df.index:
            # Append and recalc indicators
            df = df.append(new_df)
            df['vwap'] = calculate_vwap(df)
            df['macd'], df['signal'], df['hist'] = calculate_macd(df)
            df['supertrend'] = calculate_supertrend(df, SUPERTREND_PERIOD, SUPERTREND_FACTOR)

            # Check last two candles
            last = df.iloc[-1]
            prev = df.iloc[-2]

            # Triple confirmation
            st_change = last['supertrend'] != prev['supertrend']
            macd_cross = (prev['macd'] < prev['signal'] and last['macd'] > last['signal']) or \
                         (prev['macd'] > prev['signal'] and last['macd'] < last['signal'])
            price_near_vwap = abs(last['close'] - last['vwap']) < (last['vwap'] * 0.002)

            if not position and st_change and macd_cross and price_near_vwap:
                # Determine direction
                direction = "BUY" if last['supertrend'] else "SELL"
                # Place order
                qty = 1
                sl = last['close'] - STOP_LOSS_POINTS if direction == "BUY" else last['close'] + STOP_LOSS_POINTS
                tgt = last['close'] + TARGET_POINTS if direction == "BUY" else last['close'] - TARGET_POINTS
                order = u.place_order(exchange="NSE_OPTION", symbol=option_symbol,
                                      transaction_type=direction,
                                      quantity=qty,
                                      order_type="SL-M",
                                      product="INTRADAY",
                                      price=None,
                                      trigger_price=sl,
                                      stop_loss=sl,
                                      square_off=tgt)
                position = {
                    'direction': direction,
                    'qty': qty,
                    'sl': sl,
                    'tgt': tgt,
                    'order_id': order.order_id
                }
                print(f"Opened {direction} position on {option_symbol} at {last['close']}")

        # Sleep until next candle
        time.sleep(30)

if __name__ == "__main__":
    main()
