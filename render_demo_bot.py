import requests
import json
import time
from binance.client import Client
from binance.exceptions import BinanceAPIException
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from datetime import datetime

# ===== BINANCE TESTNET CONFIG =====
TESTNET_API_KEY = "3hHNdquTkoDws8sZkudSbG0GXSD2B53JjQJhrH83gJuWwQ9GrP4K1OkujyfSn1Ss"
TESTNET_API_SECRET = "iVUTAIQWT9lYNoEINehGwPYOxoeZECAh8FnnagHhcY14iNStom9ojhcKiqbumxT9"

# Use Binance Testnet URL
TESTNET_URL = "https://testnet.binance.vision/api"

# ===== SIGNAL SOURCES =====
SIGNAL_SOURCES = [
    {
        'name': 'TradingView Top Crypto',
        'url': 'https://www.tradingview.com/markets/cryptocurrencies/ideas/',
        'type': 'scrape'
    },
    {
        'name': 'CoinMarketCap Gainers',
        'url': 'https://api.coinmarketcap.com/data-api/v3/cryptocurrency/listing?start=1&limit=100&sortBy=percent_change_24h&sortType=desc',
        'type': 'api'
    },
    {
        'name': 'Binance Top Volume',
        'url': 'https://api.binance.com/api/v3/ticker/24hr',
        'type': 'api'
    }
]

class RealBinanceTrader:
    def __init__(self, api_key, api_secret, testnet=True):
        self.client = Client(api_key, api_secret, testnet=testnet)
        self.testnet = testnet
        self.test_connection()
        
    def test_connection(self):
        try:
            print("🔗 Testing Binance Testnet connection...")
            account = self.client.get_account()
            print(f"✅ Testnet connected! Account: {account['accountType']}")
            
            # Get testnet balance
            balances = [bal for bal in account['balances'] if float(bal['free']) > 0]
            print("💰 Testnet Balances:")
            for bal in balances[:5]:  # Show top 5
                print(f"   {bal['asset']}: {bal['free']}")
                
        except Exception as e:
            print(f"❌ Testnet connection failed: {e}")
    
    def get_symbol_info(self, symbol):
        """Get symbol precision and limits"""
        try:
            info = self.client.get_symbol_info(symbol)
            if info:
                lot_size = next((f for f in info['filters'] if f['filterType'] == 'LOT_SIZE'), None)
                min_qty = float(lot_size['minQty']) if lot_size else 0.001
                step_size = float(lot_size['stepSize']) if lot_size else 0.001
                return min_qty, step_size
        except:
            pass
        return 0.001, 0.001  # Default values
    
    def execute_real_demo_trade(self, symbol, side, quantity, order_type=Client.ORDER_TYPE_MARKET):
        """Execute REAL order on Binance Testnet"""
        try:
            print(f"🎯 Executing REAL TESTNET ORDER: {side} {quantity} {symbol}")
            
            # Validate symbol exists
            try:
                self.client.get_symbol_ticker(symbol=symbol)
            except:
                print(f"❌ Symbol {symbol} not found on Binance")
                return None
            
            # Get symbol precision
            min_qty, step_size = self.get_symbol_info(symbol)
            
            # Adjust quantity to meet precision requirements
            quantity = max(quantity, min_qty)
            quantity = round(quantity / step_size) * step_size
            
            print(f"📊 Order details: {side} {quantity} {symbol} (Type: {order_type})")
            
            # EXECUTE REAL TESTNET ORDER
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
            
            return order
            
        except BinanceAPIException as e:
            print(f"❌ Binance API Error: {e.code} - {e.message}")
            return None
        except Exception as e:
            print(f"❌ Trade execution failed: {e}")
            return None

class LiveSignalScraper:
    def __init__(self):
        self.setup_browser()
    
    def setup_browser(self):
        """Setup headless Firefox for scraping"""
        print("🌐 Setting up Firefox for live scraping...")
        firefox_options = Options()
        firefox_options.add_argument('--headless')
        firefox_options.add_argument('--no-sandbox')
        firefox_options.add_argument('--disable-dev-shm-usage')
        firefox_options.add_argument('--user-agent=Mozilla/5.0 (X11; Linux x86_64; rv:91.0) Gecko/20100101 Firefox/91.0')
        
        try:
            self.driver = webdriver.Firefox(options=firefox_options)
            print("✅ Firefox setup complete")
        except Exception as e:
            print(f"❌ Firefox setup failed: {e}")
            self.driver = None
    
    def scrape_tradingview_live(self):
        """Scrape live signals from TradingView"""
        signals = []
        if not self.driver:
            return signals
            
        try:
            print("📊 Scraping LIVE TradingView signals...")
            url = "https://www.tradingview.com/markets/cryptocurrencies/ideas/"
            self.driver.get(url)
            time.sleep(8)  # Wait for page load
            
            # Get page source and parse
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            # Find trading ideas
            ideas = soup.find_all('div', class_='tv-widget-idea')[:15]
            
            for idea in ideas:
                try:
                    title_elem = idea.find('div', class_='tv-widget-idea__title')
                    if title_elem:
                        title = title_elem.text.strip().upper()
                        
                        # Extract symbol from title
                        symbol = self.extract_symbol(title)
                        if symbol:
                            # Determine signal type from title
                            signal_type = self.analyze_sentiment(title)
                            
                            signals.append({
                                'symbol': symbol + 'USDT',
                                'source': 'TradingView',
                                'type': signal_type,
                                'confidence': 0.75,
                                'reason': title[:80],
                                'timestamp': datetime.now()
                            })
                except Exception as e:
                    continue
                    
            print(f"✅ Scraped {len(signals)} signals from TradingView")
            return signals
            
        except Exception as e:
            print(f"❌ TradingView scrape failed: {e}")
            return []
    
    def get_binance_top_volume(self):
        """Get top volume coins from Binance API"""
        try:
            print("📈 Getting Binance top volume signals...")
            response = requests.get('https://api.binance.com/api/v3/ticker/24hr', timeout=10)
            data = response.json()
            
            # Filter USDT pairs and sort by volume
            usdt_pairs = [ticker for ticker in data if ticker['symbol'].endswith('USDT')]
            
            # Manual sorting without pandas
            def get_volume(ticker):
                return float(ticker['volume'])
            
            usdt_pairs.sort(key=get_volume, reverse=True)
            top_volume = usdt_pairs[:10]
            
            signals = []
            for ticker in top_volume:
                price_change = float(ticker['priceChangePercent'])
                
                # Generate signal based on volume and price change
                if price_change > 2.0:  # Only if price is moving
                    signal_type = 'BUY' if price_change > 0 else 'SELL'
                    
                    signals.append({
                        'symbol': ticker['symbol'],
                        'source': 'BinanceVolume',
                        'type': signal_type,
                        'confidence': min(0.8, abs(price_change) / 10 + 0.3),
                        'reason': f"Volume: {float(ticker['volume']):.0f}, Change: {price_change:.1f}%",
                        'timestamp': datetime.now()
                    })
            
            return signals
            
        except Exception as e:
            print(f"❌ Binance volume data failed: {e}")
            return []
    
    def get_market_movers(self):
        """Get top market movers"""
        try:
            print("🎯 Analyzing market movers...")
            response = requests.get('https://api.binance.com/api/v3/ticker/24hr', timeout=10)
            data = response.json()
            
            # Get top gainers and losers
            usdt_pairs = [t for t in data if t['symbol'].endswith('USDT') and float(t['volume']) > 1000]
            
            # Manual sorting without pandas
            def get_price_change(ticker):
                return float(ticker['priceChangePercent'])
            
            # Sort gainers (descending)
            gainers = sorted(usdt_pairs, key=get_price_change, reverse=True)[:5]
            # Sort losers (ascending)
            losers = sorted(usdt_pairs, key=get_price_change)[:5]
            
            signals = []
            
            # Add top gainers as BUY signals
            for gainer in gainers:
                change = float(gainer['priceChangePercent'])
                if change > 5.0:  # Significant movement
                    signals.append({
                        'symbol': gainer['symbol'],
                        'source': 'MarketMovers',
                        'type': 'BUY',
                        'confidence': min(0.85, change / 15),
                        'reason': f"Top gainer: {change:.1f}%",
                        'timestamp': datetime.now()
                    })
            
            # Add top losers as SELL signals
            for loser in losers:
                change = float(loser['priceChangePercent'])
                if change < -3.0:  # Significant drop
                    signals.append({
                        'symbol': loser['symbol'],
                        'source': 'MarketMovers',
                        'type': 'SELL', 
                        'confidence': min(0.75, abs(change) / 12),
                        'reason': f"Top loser: {change:.1f}%",
                        'timestamp': datetime.now()
                    })
            
            return signals
            
        except Exception as e:
            print(f"❌ Market movers analysis failed: {e}")
            return []
    
    def extract_symbol(self, title):
        """Extract cryptocurrency symbol from title"""
        crypto_symbols = [
            'BTC', 'ETH', 'BNB', 'ADA', 'DOT', 'LINK', 'LTC', 'BCH', 'XRP', 
            'EOS', 'TRX', 'XLM', 'ATOM', 'XTZ', 'VET', 'THETA', 'FIL', 'DOGE',
            'SOL', 'MATIC', 'AVAX', 'ALGO', 'NEAR', 'FTM', 'SAND', 'MANA'
        ]
        
        for symbol in crypto_symbols:
            if symbol in title:
                return symbol
        return None
    
    def analyze_sentiment(self, title):
        """Analyze sentiment from title text"""
        title_lower = title.lower()
        
        buy_words = ['buy', 'bull', 'long', 'up', 'rally', 'surge', 'breakout', 'pump']
        sell_words = ['sell', 'bear', 'short', 'down', 'drop', 'crash', 'dump']
        
        buy_count = sum(1 for word in buy_words if word in title_lower)
        sell_count = sum(1 for word in sell_words if word in title_lower)
        
        if buy_count > sell_count:
            return 'BUY'
        elif sell_count > buy_count:
            return 'SELL'
        else:
            return 'BUY'  # Default to buy for neutral

class SignalExecutor:
    def __init__(self, trader):
        self.trader = trader
        self.scraper = LiveSignalScraper()
        self.trade_history = []
    
    def collect_all_signals(self):
        """Collect signals from all sources"""
        print("\n📡 Collecting LIVE signals from all sources...")
        
        all_signals = []
        all_signals.extend(self.scraper.scrape_tradingview_live())
        all_signals.extend(self.scraper.get_binance_top_volume())
        all_signals.extend(self.scraper.get_market_movers())
        
        print(f"📊 Total signals collected: {len(all_signals)}")
        return all_signals
    
    def analyze_and_execute(self):
        """Analyze signals and execute best ones"""
        signals = self.collect_all_signals()
        
        if not signals:
            print("❌ No signals collected, skipping cycle")
            return
        
        # Group by symbol and calculate consensus (same logic as original, no pandas)
        symbol_data = {}
        for signal in signals:
            symbol = signal['symbol']
            if symbol not in symbol_data:
                symbol_data[symbol] = {'buy': 0, 'sell': 0, 'confidence_sum': 0, 'sources': [], 'count': 0}
            
            if signal['type'] == 'BUY':
                symbol_data[symbol]['buy'] += 1
            else:
                symbol_data[symbol]['sell'] += 1
            
            symbol_data[symbol]['confidence_sum'] += signal['confidence']
            symbol_data[symbol]['sources'].append(signal['source'])
            symbol_data[symbol]['count'] += 1
        
        # Rank symbols by signal strength (same logic as original)
        ranked_symbols = []
        for symbol, data in symbol_data.items():
            total_signals = data['count']
            buy_ratio = data['buy'] / total_signals
            avg_confidence = data['confidence_sum'] / total_signals
            
            # Calculate final score
            score = avg_confidence * (1 + (abs(buy_ratio - 0.5) * 2))  # Reward consensus
            
            action = 'BUY' if buy_ratio >= 0.5 else 'SELL'
            consensus = max(buy_ratio, 1 - buy_ratio)  # How much agreement
            
            ranked_symbols.append({
                'symbol': symbol,
                'action': action,
                'score': score,
                'consensus': consensus,
                'confidence': avg_confidence,
                'total_signals': total_signals,
                'sources': list(set(data['sources']))
            })
        
        # Sort by score (manual sorting without pandas)
        def get_score(signal):
            return signal['score']
        
        ranked_symbols.sort(key=get_score, reverse=True)
        
        # Execute top signals
        print(f"\n🎯 Top ranked signals:")
        for i, signal in enumerate(ranked_symbols[:5]):
            print(f"{i+1}. {signal['symbol']} - {signal['action']} "
                  f"(Score: {signal['score']:.2f}, Consensus: {signal['consensus']:.1%})")
        
        # Execute top 1-2 signals
        for signal in ranked_symbols[:2]:
            if signal['score'] > 0.6:  # Minimum quality threshold
                self.execute_signal(signal)
    
    def execute_signal(self, signal):
        """Execute a trading signal"""
        try:
            symbol = signal['symbol']
            action = signal['action']
            
            print(f"\n🚀 EXECUTING: {action} {symbol}")
            print(f"   Confidence: {signal['confidence']:.2f}")
            print(f"   Consensus: {signal['consensus']:.1%}")
            print(f"   Sources: {', '.join(signal['sources'])}")
            
            # Determine position size (small for demo)
            quantity = self.calculate_position_size(symbol)
            
            if quantity > 0:
                # EXECUTE REAL TESTNET ORDER
                order = self.trader.execute_real_demo_trade(
                    symbol=symbol,
                    side=action,
                    quantity=quantity
                )
                
                if order:
                    self.trade_history.append({
                        'timestamp': datetime.now(),
                        'symbol': symbol,
                        'action': action,
                        'quantity': quantity,
                        'order_id': order['orderId'],
                        'status': order['status']
                    })
                    print(f"✅ Successfully executed REAL TESTNET order!")
                else:
                    print(f"❌ Order execution failed")
            else:
                print(f"❌ Invalid position size for {symbol}")
                
        except Exception as e:
            print(f"❌ Signal execution failed: {e}")
    
    def calculate_position_size(self, symbol):
        """Calculate appropriate position size"""
        # Small fixed sizes for demo
        size_map = {
            'BTCUSDT': 0.0005,   # ~$20
            'ETHUSDT': 0.003,    # ~$10
            'BNBUSDT': 0.02,     # ~$5
        }
        
        # Default size for other coins
        default_size = 1.0 if any(x in symbol for x in ['USDT', 'BUSD']) else 10.0
        
        # Get base asset
        base_asset = symbol.replace('USDT', '')
        
        if base_asset in ['BTC', 'ETH', 'BNB']:
            return size_map.get(symbol, 0.01)
        else:
            return 5.0  # $5 worth for altcoins

def main():
    print("""
    🚀 BINANCE TESTNET LIVE TRADING BOT
    ===================================
    🔥 REAL ORDERS on Binance Testnet
    📊 Live Signal Scraping (Firefox)
    ⚡ Instant Execution
    💰 DEMO MONEY ONLY - NO REAL RISK
    ===================================
    """)
    
    # Initialize real testnet trader
    trader = RealBinanceTrader(TESTNET_API_KEY, TESTNET_API_SECRET, testnet=True)
    executor = SignalExecutor(trader)
    
    cycle_count = 0
    while True:
        try:
            cycle_count += 1
            print(f"\n{'='*60}")
            print(f"🔄 CYCLE {cycle_count} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"{'='*60}")
            
            # Run signal collection and execution
            executor.analyze_and_execute()
            
            # Show recent trade history
            if executor.trade_history:
                print(f"\n📈 Recent Trades (Last 5):")
                for trade in executor.trade_history[-5:]:
                    print(f"   {trade['timestamp'].strftime('%H:%M')} - "
                          f"{trade['action']} {trade['quantity']} {trade['symbol']} "
                          f"(ID: {trade['order_id']})")
            
            print(f"\n💤 Waiting 3 minutes for next cycle...")
            time.sleep(180)  # 3 minutes between cycles
            
        except KeyboardInterrupt:
            print(f"\n🛑 Bot stopped by user after {cycle_count} cycles")
            break
        except Exception as e:
            print(f"❌ Error in main loop: {e}")
            print("💤 Retrying in 60 seconds...")
            time.sleep(60)

if __name__ == "__main__":
    main()
