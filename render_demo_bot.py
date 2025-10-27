import requests
import json
import time
from binance.client import Client
from binance.exceptions import BinanceAPIException
from datetime import datetime

# ===== BINANCE TESTNET CONFIG =====
# ⚠️ REPLACE WITH YOUR NEW API KEYS!
TESTNET_API_KEY = "3hHNdquTkoDws8sZkudSbG0GXSD2B53JjQJhrH83gJuWwQ9GrP4K1OkujyfSn1Ss"
TESTNET_API_SECRET = "iVUTAIQWT9lYNoEINehGwPYOxoeZECAh8FnnagHhcY14iNStom9ojhcKiqbumxT9"

import requests
import json
import time
from binance.client import Client
from binance.exceptions import BinanceAPIException
from datetime import datetime

# ===== BINANCE TESTNET CONFIG =====
TESTNET_API_KEY = "3hHNdquTkoDws8sZkudSbG0GXSD2B53JjQJhrH83gJuWwQ9GrP4K1OkujyfSn1Ss"
TESTNET_API_SECRET = "iVUTAIQWT9lYNoEINehGwPYOxoeZECAh8FnnagHhcY14iNStom9ojhcKiqbumxT9"
BASE_URL = "https://testnet.binance.vision"


class RealBinanceTrader:
    def __init__(self, api_key, api_secret, testnet=True):
        self.client = Client(api_key, api_secret, testnet=testnet)
        self.api_key = api_key
        self.api_secret = api_secret
        self.testnet = testnet
        self.test_connection()

    def test_connection(self):
        try:
            print("🔗 Testing Binance Testnet connection...")
            account = self.client.get_account()
            print(f"✅ Testnet connected! Account: {account['accountType']}")

            self.show_balances()

        except Exception as e:
            print(f"❌ Testnet connection failed: {e}")

    def show_balances(self):
        """Print all non-zero balances"""
        try:
            account = self.client.get_account()
            balances = [bal for bal in account['balances'] if float(bal['free']) > 0]
            print("💰 Balances:")
            for bal in balances:
                print(f"   {bal['asset']}: {bal['free']}")
        except Exception as e:
            print(f"⚠️ Could not fetch balances: {e}")

    def get_server_time(self):
        """Use Binance server time for signed requests"""
        r = requests.get(f"{BASE_URL}/api/v3/time")
        return r.json()["serverTime"]

    def get_trade_history(self, symbol):
        """Fetch trade history using raw signed endpoint"""
        try:
            timestamp = self.get_server_time()
            params = f"symbol={symbol}&timestamp={timestamp}&recvWindow=5000"

            import hmac, hashlib
            signature = hmac.new(
                self.api_secret.encode("utf-8"),
                params.encode("utf-8"),
                hashlib.sha256
            ).hexdigest()

            headers = {"X-MBX-APIKEY": self.api_key}
            url = f"{BASE_URL}/api/v3/myTrades?{params}&signature={signature}"

            response = requests.get(url, headers=headers)
            trades = response.json()
            return trades if isinstance(trades, list) else []
        except Exception as e:
            print(f"⚠️ Error fetching trade history: {e}")
            return []

    def get_symbol_info(self, symbol):
        """Get symbol precision and limits"""
        try:
            info = self.client.get_symbol_info(symbol)
            if info:
                lot_size = next((f for f in info["filters"] if f["filterType"] == "LOT_SIZE"), None)
                min_qty = float(lot_size["minQty"]) if lot_size else 0.001
                step_size = float(lot_size["stepSize"]) if lot_size else 0.001
                return min_qty, step_size
        except:
            pass
        return 0.001, 0.001

    def execute_real_demo_trade(self, symbol, side, order_type=Client.ORDER_TYPE_MARKET):
        """Execute REAL order on Binance Testnet with proper sizing"""
        try:
            print(f"🎯 Executing REAL TESTNET ORDER: {side} {symbol}")

            # Get current price first
            ticker = self.client.get_symbol_ticker(symbol=symbol)
            current_price = float(ticker["price"])
            print(f"💰 Current price: ${current_price:.4f}")

            # Calculate proper quantity for $25 order
            target_usd_value = 25.0
            quantity = target_usd_value / current_price

            # Get symbol precision
            min_qty, step_size = self.get_symbol_info(symbol)
            quantity = max(quantity, min_qty)
            quantity = round(quantity / step_size) * step_size

            final_value = quantity * current_price
            print(f"📊 Order details: {side} {quantity:.4f} {symbol} = ${final_value:.2f}")

            # Execute REAL TESTNET ORDER
            order = self.client.create_order(
                symbol=symbol,
                side=side,
                type=order_type,
                quantity=quantity
            )

            print(f"✅ REAL TESTNET ORDER EXECUTED!")
            print(f"   Order ID: {order['orderId']}")
            print(f"   Status: {order['status']}")
            print(f"   Executed Qty: {order['executedQty']}")

            # === NEW: Fetch latest trades & calculate P/L ===
            time.sleep(1)
            trades = self.get_trade_history(symbol)
            if trades:
                last_trade = trades[-1]
                entry_price = float(last_trade["price"])
                print(f"📈 Entry price: ${entry_price:.4f}")

                # Current market value
                new_ticker = self.client.get_symbol_ticker(symbol=symbol)
                current_market_price = float(new_ticker["price"])
                pnl = (current_market_price - entry_price) / entry_price * 100

                print(f"📊 Current market price: ${current_market_price:.4f}")
                print(f"💹 P/L: {pnl:+.2f}%")

            # === Show balances after trade ===
            self.show_balances()

            return order

        except BinanceAPIException as e:
            print(f"❌ Binance API Error: {e.code} - {e.message}")
            return None
        except Exception as e:
            print(f"❌ Trade execution failed: {e}")
            return None


# === Rest of your code (SignalFinder, SignalExecutor, main) stays the same ===
# Just replace your RealBinanceTrader class with this upgraded one.

class SmartSignalFinder:
    def __init__(self):
        self.major_coins = [
            'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT', 'DOTUSDT',
            'LINKUSDT', 'LTCUSDT', 'BCHUSDT', 'XRPUSDT', 'EOSUSDT',
            'TRXUSDT', 'XLMUSDT', 'ATOMUSDT', 'XTZUSDT', 'VETUSDT',
            'THETAUSDT', 'FILUSDT', 'DOGEUSDT', 'SOLUSDT', 'MATICUSDT',
            'AVAXUSDT', 'ALGOUSDT', 'NEARUSDT', 'FTMUSDT', 'SANDUSDT',
            'MANAUSDT', 'AAVEUSDT', 'UNIUSDT', 'MKRUSDT', 'COMPUSDT'
        ]

    def get_binance_signals_with_retry(self):
        """Get signals from Binance API with retry logic"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                print(f"📈 Getting Binance signals (attempt {attempt + 1})...")
                response = requests.get('https://api.binance.com/api/v3/ticker/24hr', timeout=15)
                data = response.json()
                return self.process_binance_data(data)
            except Exception as e:
                print(f"❌ Attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2)

        print("❌ All Binance API attempts failed")
        return self.get_fallback_signals()

    def process_binance_data(self, data):
        """Process Binance data into trading signals"""
        signals = []

        # Filter for major coins only
        major_data = [t for t in data if t['symbol'] in self.major_coins and float(t['volume']) > 100000]

        if not major_data:
            return self.get_fallback_signals()

        # Strategy 1: Top volume with positive momentum
        volume_signals = self.get_volume_signals(major_data)
        signals.extend(volume_signals)

        # Strategy 2: Biggest gainers
        gainer_signals = self.get_gainer_signals(major_data)
        signals.extend(gainer_signals)

        # Strategy 3: Oversold bounce candidates
        oversold_signals = self.get_oversold_signals(major_data)
        signals.extend(oversold_signals)

        return signals

    def get_volume_signals(self, data):
        """Signals based on high volume and momentum"""
        # Sort by volume (descending)
        high_volume = sorted(data, key=lambda x: float(x['volume']), reverse=True)[:10]

        signals = []
        for ticker in high_volume:
            change = float(ticker['priceChangePercent'])
            if change > 2.0:  # Positive momentum
                signals.append({
                    'symbol': ticker['symbol'],
                    'source': 'VolumeMomentum',
                    'type': 'BUY',
                    'confidence': min(0.8, change / 12 + 0.4),
                    'reason': f"High volume +{change:.1f}%",
                    'score': float(ticker['volume']) * (1 + change/100)
                })

        return signals[:3]  # Top 3 volume signals

    def get_gainer_signals(self, data):
        """Signals from top gainers"""
        # Sort by price change (descending)
        gainers = sorted(data, key=lambda x: float(x['priceChangePercent']), reverse=True)[:5]

        signals = []
        for ticker in gainers:
            change = float(ticker['priceChangePercent'])
            if change > 4.0:  # Significant gain
                signals.append({
                    'symbol': ticker['symbol'],
                    'source': 'TopGainer',
                    'type': 'BUY',
                    'confidence': min(0.85, change / 15),
                    'reason': f"Top gainer: +{change:.1f}%",
                    'score': change
                })

        return signals[:2]  # Top 2 gainers

    def get_oversold_signals(self, data):
        """Signals for potential bounce from oversold conditions"""
        # Sort by price change (ascending - biggest losers)
        losers = sorted(data, key=lambda x: float(x['priceChangePercent']))[:5]

        signals = []
        for ticker in losers:
            change = float(ticker['priceChangePercent'])
            volume = float(ticker['volume'])

            # Look for high volume losers (potential capitulation)
            if change < -5.0 and volume > 500000:
                signals.append({
                    'symbol': ticker['symbol'],
                    'source': 'OversoldBounce',
                    'type': 'BUY',
                    'confidence': 0.65,
                    'reason': f"Oversold: {change:.1f}% with high volume",
                    'score': abs(change) * volume / 1000000
                })

        return signals[:2]  # Top 2 oversold candidates

    def get_fallback_signals(self):
        """Fallback signals when API fails"""
        print("⚠️ Using fallback signals...")

        # Simple rotation strategy
        fallback_coins = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT', 'DOTUSDT']

        signals = []
        for symbol in fallback_coins[:3]:
            signals.append({
                'symbol': symbol,
                'source': 'Fallback',
                'type': 'BUY',
                'confidence': 0.7,
                'reason': "Fallback rotation",
                'score': 0.7
            })

        return signals

class SignalExecutor:
    def __init__(self, trader):
        self.trader = trader
        self.signal_finder = SmartSignalFinder()
        self.trade_history = []
        self.last_trade_time = None

    def collect_signals(self):
        """Collect and process signals"""
        print("\n📡 Collecting trading signals...")

        signals = self.signal_finder.get_binance_signals_with_retry()

        # Remove duplicates and sort by score
        unique_signals = {}
        for signal in signals:
            symbol = signal['symbol']
            if symbol not in unique_signals or signal['score'] > unique_signals[symbol]['score']:
                unique_signals[symbol] = signal

        sorted_signals = sorted(unique_signals.values(), key=lambda x: x['score'], reverse=True)

        print(f"📊 Found {len(sorted_signals)} qualified signals")
        return sorted_signals

    def execute_best_signal(self):
        """Execute the single best signal"""
        signals = self.collect_signals()

        if not signals:
            print("❌ No qualified signals found")
            return

        # Show top 3 signals
        print(f"\n🎯 Top signals:")
        for i, signal in enumerate(signals[:3]):
            print(f"   {i+1}. {signal['symbol']} - {signal['type']} "
                  f"(Score: {signal['score']:.1f}, Conf: {signal['confidence']:.2f})")

        best_signal = signals[0]

        # Only trade if confidence is good
        if best_signal['confidence'] > 0.6:
            print(f"\n🚀 EXECUTING BEST SIGNAL: {best_signal['type']} {best_signal['symbol']}")
            print(f"   Reason: {best_signal['reason']}")
            print(f"   Confidence: {best_signal['confidence']:.2f}")

            # Execute trade
            order = self.trader.execute_real_demo_trade(
                symbol=best_signal['symbol'],
                side=best_signal['type']
            )

            if order:
                self.trade_history.append({
                    'timestamp': datetime.now(),
                    'symbol': best_signal['symbol'],
                    'action': best_signal['type'],
                    'order_id': order['orderId'],
                    'status': order['status']
                })
                self.last_trade_time = datetime.now()
                print(f"✅ Trade executed successfully!")
            else:
                print(f"❌ Trade execution failed")
        else:
            print(f"⏸️ Skipping trade - confidence too low: {best_signal['confidence']:.2f}")

def main():
    print("""
    🚀 BINANCE TESTNET TRADING BOT
    ==============================
    🔥 REAL Testnet Orders
    📊 Smart Signal Detection
    💰 Proper Order Sizing ($25+)
    ⚡ No Browser Dependencies
    ==============================
    """)

    # Initialize trader
    trader = RealBinanceTrader(TESTNET_API_KEY, TESTNET_API_SECRET, testnet=True)
    executor = SignalExecutor(trader)

    cycle_count = 0
    while True:
        try:
            cycle_count += 1
            print(f"\n{'='*50}")
            print(f"🔄 CYCLE {cycle_count} - {datetime.now().strftime('%H:%M:%S')}")
            print(f"{'='*50}")

            # Execute trading logic
            executor.execute_best_signal()

            # Show recent activity
            if executor.trade_history:
                print(f"\n📈 Recent Trades:")
                for trade in executor.trade_history[-3:]:
                    print(f"   {trade['timestamp'].strftime('%H:%M')} - "
                          f"{trade['action']} {trade['symbol']} "
                          f"(ID: {trade['order_id']})")

            print(f"\n💤 Waiting 5 minutes for next cycle...")
            time.sleep(300)  # 5 minutes

        except KeyboardInterrupt:
            print(f"\n🛑 Bot stopped after {cycle_count} cycles")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            print("💤 Retrying in 2 minutes...")
            time.sleep(120)

if __name__ == "__main__":
    main()
