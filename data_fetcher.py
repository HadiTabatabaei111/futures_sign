import ccxt
import pandas as pd
from datetime import datetime

class DataFetcher:
    SOURCES = {
        'kucoin': 'کوکوین ⭐',
        'bybit': 'بایبیت',
        'okx': 'OKX',
        'mexc': 'MEXC',
        'gateio': 'Gate.io'
    }
    
    def __init__(self, source='kucoin'):
        self.source = source
        self.exchange = None
        self._init_exchange()
    
    def _init_exchange(self):
        try:
            exchanges = {
                'kucoin': lambda: ccxt.kucoinfutures({'enableRateLimit': True, 'options': {'defaultType': 'swap'}}),
                'bybit': lambda: ccxt.bybit({'enableRateLimit': True, 'options': {'defaultType': 'linear'}}),
                'okx': lambda: ccxt.okx({'enableRateLimit': True, 'options': {'defaultType': 'swap'}}),
                'mexc': lambda: ccxt.mexc({'enableRateLimit': True, 'options': {'defaultType': 'swap'}}),
                'gateio': lambda: ccxt.gateio({'enableRateLimit': True, 'options': {'defaultType': 'swap'}})
            }
            self.exchange = exchanges.get(self.source, exchanges['kucoin'])()
        except Exception as e:
            print(f"خطا: {e}")
    
    def get_futures_symbols(self, limit=250):
        try:
            self.exchange.load_markets()
            symbols = [s for s, m in self.exchange.markets.items() 
                      if (m.get('swap') or m.get('future') or m.get('linear')) 
                      and 'USDT' in s and m.get('active', True)]
            return symbols[:limit]
        except:
            return []
    
    def get_ticker(self, symbol):
        try:
            ticker = self.exchange.fetch_ticker(symbol)
            return {
                'symbol': symbol.replace('/', '').replace(':USDT', '').replace('-', ''),
                'price': ticker.get('last', 0),
                'open_price': ticker.get('open', ticker.get('last', 0)),
                'high_price': ticker.get('high', ticker.get('last', 0)),
                'low_price': ticker.get('low', ticker.get('last', 0)),
                'close_price': ticker.get('last', 0),
                'volume': ticker.get('baseVolume', 0) or 0,
                'quote_volume': ticker.get('quoteVolume', 0) or 0,
                'price_change': ticker.get('change', 0) or 0,
                'price_change_percent': ticker.get('percentage', 0) or 0,
                'timestamp': datetime.utcnow()
            }
        except:
            return None
    
    def get_all_tickers(self):
        try:
            tickers = self.exchange.fetch_tickers()
            results = []
            for symbol, ticker in tickers.items():
                if 'USDT' in symbol and (ticker.get('last') or 0) > 0:
                    results.append({
                        'symbol': symbol.replace('/', '').replace(':USDT', '').replace('-', ''),
                        'price': ticker['last'],
                        'open_price': ticker.get('open', ticker['last']) or ticker['last'],
                        'high_price': ticker.get('high', ticker['last']) or ticker['last'],
                        'low_price': ticker.get('low', ticker['last']) or ticker['last'],
                        'close_price': ticker['last'],
                        'volume': ticker.get('baseVolume', 0) or 0,
                        'quote_volume': ticker.get('quoteVolume', 0) or 0,
                        'price_change': ticker.get('change', 0) or 0,
                        'price_change_percent': ticker.get('percentage', 0) or 0,
                        'timestamp': datetime.utcnow()
                    })
            results.sort(key=lambda x: x.get('quote_volume', 0) or 0, reverse=True)
            return results[:250]
        except:
            return []
    
    def get_ohlcv(self, symbol, timeframe='1m', limit=500):
        try:
            ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            if not ohlcv:
                return pd.DataFrame()
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df['symbol'] = symbol.replace('/', '').replace(':USDT', '').replace('-', '')
            return df
        except:
            return pd.DataFrame()
    
    def switch_source(self, new_source):
        if new_source in self.SOURCES:
            self.source = new_source
            self._init_exchange()
            return True
        return False
    
    def test_connection(self):
        try:
            self.exchange.load_markets()
            return True
        except:
            return False
