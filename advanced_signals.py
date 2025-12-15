"""
🔥 سیستم سیگنالدهی پیشرفته
شامل: Smart Money, Order Blocks, Liquidity Hunt, Divergence, Whale Detection
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from ta.trend import EMAIndicator, SMAIndicator
from ta.momentum import RSIIndicator
from ta.volatility import AverageTrueRange

class AdvancedSignalEngine:
    """موتور سیگنالدهی پیشرفته"""
    
    @staticmethod
    def detect_smart_money(df, volume_threshold=2.0):
        """تشخیص ورود و خروج پول هوشمند"""
        if len(df) < 30:
            return []
        
        df = df.copy()
        df['volume_sma'] = df['volume'].rolling(20).mean()
        df['volume_ratio'] = df['volume'] / df['volume_sma']
        df['price_change'] = df['close'].pct_change() * 100
        
        signals = []
        
        for i in range(20, len(df)):
            vol_ratio = df['volume_ratio'].iloc[i]
            price_change = abs(df['price_change'].iloc[i])
            
            if pd.isna(vol_ratio):
                continue
            
            # جمعآوری: حجم بالا، تغییر قیمت کم
            if vol_ratio > volume_threshold and price_change < 0.5:
                signals.append({
                    'index': i,
                    'type': 'SMART_MONEY_ACCUMULATION',
                    'signal': 'BUY',
                    'strength': min(vol_ratio * 30, 95),
                    'reason': f'💰 Smart Money Accumulation (Vol: {vol_ratio:.1f}x)',
                    'price': df['close'].iloc[i],
                    'timestamp': df['timestamp'].iloc[i] if 'timestamp' in df.columns else None
                })
            
            # توزیع: حجم بالا، قیمت بالا رفته
            elif vol_ratio > volume_threshold and price_change > 2:
                if df['close'].iloc[i] > df['close'].iloc[i-1]:
                    signals.append({
                        'index': i,
                        'type': 'SMART_MONEY_DISTRIBUTION',
                        'signal': 'SELL',
                        'strength': min(vol_ratio * 25, 90),
                        'reason': f'💰 Smart Money Distribution (Vol: {vol_ratio:.1f}x)',
                        'price': df['close'].iloc[i],
                        'timestamp': df['timestamp'].iloc[i] if 'timestamp' in df.columns else None
                    })
        
        return signals[-5:] if signals else []
    
    @staticmethod
    def find_order_blocks(df, lookback=50):
        """یافتن Order Blocks"""
        if len(df) < 10:
            return []
        
        df = df.copy()
        order_blocks = []
        
        for i in range(3, len(df) - 1):
            try:
                # Bullish Order Block
                if (df['close'].iloc[i-1] < df['open'].iloc[i-1] and
                    df['close'].iloc[i] > df['open'].iloc[i] and
                    df['close'].iloc[i] > df['high'].iloc[i-1]):
                    
                    move_strength = ((df['close'].iloc[i] - df['low'].iloc[i-1]) / 
                                    df['low'].iloc[i-1]) * 100
                    
                    if move_strength > 0.5:
                        order_blocks.append({
                            'index': i,
                            'type': 'BULLISH_ORDER_BLOCK',
                            'signal': 'BUY',
                            'top': df['high'].iloc[i-1],
                            'bottom': df['low'].iloc[i-1],
                            'strength': min(move_strength * 20, 90),
                            'reason': f'📦 Bullish Order Block ({move_strength:.1f}% move)',
                            'price': df['close'].iloc[i],
                            'timestamp': df['timestamp'].iloc[i] if 'timestamp' in df.columns else None
                        })
                
                # Bearish Order Block
                if (df['close'].iloc[i-1] > df['open'].iloc[i-1] and
                    df['close'].iloc[i] < df['open'].iloc[i] and
                    df['close'].iloc[i] < df['low'].iloc[i-1]):
                    
                    move_strength = ((df['high'].iloc[i-1] - df['close'].iloc[i]) / 
                                    df['high'].iloc[i-1]) * 100
                    
                    if move_strength > 0.5:
                        order_blocks.append({
                            'index': i,
                            'type': 'BEARISH_ORDER_BLOCK',
                            'signal': 'SELL',
                            'top': df['high'].iloc[i-1],
                            'bottom': df['low'].iloc[i-1],
                            'strength': min(move_strength * 20, 90),
                            'reason': f'📦 Bearish Order Block ({move_strength:.1f}% move)',
                            'price': df['close'].iloc[i],
                            'timestamp': df['timestamp'].iloc[i] if 'timestamp' in df.columns else None
                        })
            except:
                continue
        
        return order_blocks[-5:] if order_blocks else []
    
    @staticmethod
    def detect_liquidity_hunt(df, lookback=20):
        """تشخیص شکار نقدینگی - بهترین نقطه ورود!"""
        if len(df) < lookback + 5:
            return []
        
        df = df.copy()
        signals = []
        
        for i in range(lookback, len(df)):
            try:
                window = df.iloc[i-lookback:i]
                current = df.iloc[i]
                
                prev_high = window['high'].max()
                prev_low = window['low'].min()
                
                # شکار نقدینگی پایین (Long Signal)
                if (current['low'] < prev_low and 
                    current['close'] > prev_low and
                    current['close'] > current['open']):
                    
                    hunt_depth = ((prev_low - current['low']) / prev_low) * 100
                    
                    signals.append({
                        'index': i,
                        'type': 'LIQUIDITY_GRAB_LOW',
                        'signal': 'BUY',
                        'strength': min(75 + hunt_depth * 10, 95),
                        'reason': f'🎯 Liquidity Hunt Below Support ({hunt_depth:.2f}%)',
                        'price': current['close'],
                        'stop_loss': current['low'] * 0.995,
                        'timestamp': df['timestamp'].iloc[i] if 'timestamp' in df.columns else None
                    })
                
                # شکار نقدینگی بالا (Short Signal)
                if (current['high'] > prev_high and 
                    current['close'] < prev_high and
                    current['close'] < current['open']):
                    
                    hunt_depth = ((current['high'] - prev_high) / prev_high) * 100
                    
                    signals.append({
                        'index': i,
                        'type': 'LIQUIDITY_GRAB_HIGH',
                        'signal': 'SELL',
                        'strength': min(75 + hunt_depth * 10, 95),
                        'reason': f'🎯 Liquidity Hunt Above Resistance ({hunt_depth:.2f}%)',
                        'price': current['close'],
                        'stop_loss': current['high'] * 1.005,
                        'timestamp': df['timestamp'].iloc[i] if 'timestamp' in df.columns else None
                    })
            except:
                continue
        
        return signals[-5:] if signals else []
    
    @staticmethod
    def find_divergences(df):
        """یافتن واگراییها"""
        if len(df) < 30:
            return []
        
        df = df.copy()
        df['rsi'] = RSIIndicator(df['close'], window=14).rsi()
        
        divergences = []
        lookback = 5
        
        for i in range(lookback * 2, len(df)):
            try:
                # واگرایی صعودی
                if (df['close'].iloc[i] < df['close'].iloc[i-lookback] and
                    df['rsi'].iloc[i] > df['rsi'].iloc[i-lookback] and
                    df['rsi'].iloc[i] < 40):
                    
                    divergences.append({
                        'index': i,
                        'type': 'BULLISH_DIVERGENCE',
                        'signal': 'BUY',
                        'strength': 85,
                        'reason': f'📈 RSI Bullish Divergence (RSI: {df["rsi"].iloc[i]:.1f})',
                        'price': df['close'].iloc[i],
                        'rsi': df['rsi'].iloc[i],
                        'timestamp': df['timestamp'].iloc[i] if 'timestamp' in df.columns else None
                    })
                
                # واگرایی نزولی
                if (df['close'].iloc[i] > df['close'].iloc[i-lookback] and
                    df['rsi'].iloc[i] < df['rsi'].iloc[i-lookback] and
                    df['rsi'].iloc[i] > 60):
                    
                    divergences.append({
                        'index': i,
                        'type': 'BEARISH_DIVERGENCE',
                        'signal': 'SELL',
                        'strength': 85,
                        'reason': f'📉 RSI Bearish Divergence (RSI: {df["rsi"].iloc[i]:.1f})',
                        'price': df['close'].iloc[i],
                        'rsi': df['rsi'].iloc[i],
                        'timestamp': df['timestamp'].iloc[i] if 'timestamp' in df.columns else None
                    })
            except:
                continue
        
        return divergences[-5:] if divergences else []
    
    @staticmethod
    def detect_whale_activity(df, std_multiplier=2.5):
        """تشخیص فعالیت نهنگها"""
        if len(df) < 60:
            return []
        
        df = df.copy()
        df['volume_mean'] = df['volume'].rolling(50).mean()
        df['volume_std'] = df['volume'].rolling(50).std()
        
        whale_signals = []
        
        for i in range(50, len(df)):
            try:
                if df['volume_std'].iloc[i] == 0 or pd.isna(df['volume_std'].iloc[i]):
                    continue
                
                zscore = (df['volume'].iloc[i] - df['volume_mean'].iloc[i]) / df['volume_std'].iloc[i]
                
                if zscore > std_multiplier:
                    price_change = ((df['close'].iloc[i] - df['open'].iloc[i]) / 
                                   df['open'].iloc[i]) * 100
                    
                    if price_change > 0.3:
                        whale_signals.append({
                            'index': i,
                            'type': 'WHALE_BUYING',
                            'signal': 'BUY',
                            'strength': min(65 + zscore * 8, 95),
                            'reason': f'🐋 Whale Buying Detected (Vol Z: {zscore:.1f})',
                            'price': df['close'].iloc[i],
                            'volume_zscore': round(zscore, 2),
                            'timestamp': df['timestamp'].iloc[i] if 'timestamp' in df.columns else None
                        })
                    elif price_change < -0.3:
                        whale_signals.append({
                            'index': i,
                            'type': 'WHALE_SELLING',
                            'signal': 'SELL',
                            'strength': min(65 + zscore * 8, 95),
                            'reason': f'🐋 Whale Selling Detected (Vol Z: {zscore:.1f})',
                            'price': df['close'].iloc[i],
                            'volume_zscore': round(zscore, 2),
                            'timestamp': df['timestamp'].iloc[i] if 'timestamp' in df.columns else None
                        })
            except:
                continue
        
        return whale_signals[-5:] if whale_signals else []


class AdvancedPumpDumpDetector:
    """تشخیص پیشرفته پامپ و دامپ"""
    
    @staticmethod
    def detect_pump_starting(df, symbol):
        """تشخیص شروع پامپ"""
        if len(df) < 100:
            return []
        
        alerts = []
        
        try:
            recent_30 = df.tail(30)
            older_30 = df.tail(60).head(30)
            
            recent_volatility = recent_30['close'].std() / recent_30['close'].mean()
            older_volatility = older_30['close'].std() / older_30['close'].mean()
            
            recent_volume = recent_30['volume'].mean()
            older_volume = older_30['volume'].mean()
            
            # جمعآوری = نوسان کم + حجم کمی بیشتر
            if older_volatility > 0 and recent_volatility < older_volatility * 0.7:
                if older_volume > 0 and recent_volume > older_volume * 1.2:
                    
                    last_5 = df.tail(5)
                    resistance = df.tail(50)['high'].quantile(0.9)
                    
                    if last_5['close'].iloc[-1] > resistance:
                        avg_vol = df['volume'].tail(20).mean()
                        if avg_vol > 0:
                            volume_spike = last_5['volume'].iloc[-1] / avg_vol
                            
                            if volume_spike > 1.5:
                                alerts.append({
                                    'symbol': symbol,
                                    'alert_type': 'PUMP_STARTING',
                                    'signal': 'BUY',
                                    'confidence': min(70 + volume_spike * 5, 95),
                                    'strength': min(70 + volume_spike * 5, 95),
                                    'price': df['close'].iloc[-1],
                                    'resistance_broken': resistance,
                                    'volume_spike': round(volume_spike, 2),
                                    'reason': f'🚀 Pump Starting! Vol Spike: {volume_spike:.1f}x',
                                    'timestamp': datetime.utcnow()
                                })
        except:
            pass
        
        return alerts
    
    @staticmethod
    def detect_dump_warning(df, symbol):
        """هشدار دامپ"""
        if len(df) < 50:
            return []
        
        alerts = []
        
        try:
            df = df.copy()
            df['rsi'] = RSIIndicator(df['close'], window=14).rsi()
            
            latest = df.iloc[-1]
            conditions_met = 0
            reasons = []
            
            # RSI بالا
            if latest['rsi'] > 75:
                conditions_met += 1
                reasons.append(f"RSI: {latest['rsi']:.1f}")
            
            # سایه بالای بلند
            upper_wick = latest['high'] - max(latest['open'], latest['close'])
            body = abs(latest['close'] - latest['open'])
            
            if body > 0 and upper_wick > body * 2:
                conditions_met += 1
                reasons.append("Long Upper Wick")
            
            # حجم بالا با کندل نزولی
            volume_avg = df['volume'].tail(20).mean()
            if volume_avg > 0 and latest['volume'] > volume_avg * 1.5:
                if latest['close'] < latest['open']:
                    conditions_met += 1
                    reasons.append("High Vol Selling")
            
            if conditions_met >= 2:
                alerts.append({
                    'symbol': symbol,
                    'alert_type': 'DUMP_WARNING',
                    'signal': 'SELL',
                    'confidence': min(40 + conditions_met * 20, 90),
                    'strength': min(40 + conditions_met * 20, 90),
                    'price': latest['close'],
                    'rsi': latest['rsi'],
                    'reason': f'⚠️ Dump Warning! {" | ".join(reasons)}',
                    'timestamp': datetime.utcnow()
                })
        except:
            pass
        
        return alerts
    
    @staticmethod
    def detect_advanced_pump_dump(df, symbol, threshold=5, window=15):
        """تشخیص پامپ و دامپ پیشرفته"""
        if len(df) < window + 10:
            return []
        
        alerts = []
        
        try:
            recent = df.tail(window)
            
            start_price = recent['close'].iloc[0]
            end_price = recent['close'].iloc[-1]
            price_change = ((end_price - start_price) / start_price) * 100
            
            avg_volume = df['volume'].tail(100).mean()
            recent_volume = recent['volume'].mean()
            volume_change = ((recent_volume - avg_volume) / avg_volume) * 100 if avg_volume > 0 else 0
            
            # بررسی مومنتوم
            momentum = 0
            for i in range(1, len(recent)):
                if recent['close'].iloc[i] > recent['close'].iloc[i-1]:
                    momentum += 1
                else:
                    momentum -= 1
            
            # پامپ قوی
            if price_change >= threshold and volume_change > 50 and momentum > window * 0.5:
                alerts.append({
                    'symbol': symbol,
                    'alert_type': 'STRONG_PUMP',
                    'signal': 'BUY',
                    'price_change': round(price_change, 2),
                    'volume_change': round(volume_change, 2),
                    'momentum': momentum,
                    'strength': min(70 + price_change * 3, 95),
                    'price': end_price,
                    'reason': f'🚀 STRONG PUMP! +{price_change:.1f}% | Vol +{volume_change:.0f}%',
                    'timestamp': datetime.utcnow()
                })
            
            # دامپ قوی
            elif price_change <= -threshold and volume_change > 50 and momentum < -window * 0.5:
                alerts.append({
                    'symbol': symbol,
                    'alert_type': 'STRONG_DUMP',
                    'signal': 'SELL',
                    'price_change': round(price_change, 2),
                    'volume_change': round(volume_change, 2),
                    'momentum': momentum,
                    'strength': min(70 + abs(price_change) * 3, 95),
                    'price': end_price,
                    'reason': f'📉 STRONG DUMP! {price_change:.1f}% | Vol +{volume_change:.0f}%',
                    'timestamp': datetime.utcnow()
                })
        except:
            pass
        
        return alerts


class UltimateSignalGenerator:
    """ترکیب همه روشها برای بهترین سیگنال"""
    
    def __init__(self):
        self.engine = AdvancedSignalEngine()
        self.pump_dump = AdvancedPumpDumpDetector()
    
    def analyze(self, df, symbol):
        """تحلیل کامل و تولید سیگنال نهایی"""
        all_signals = []
        
        try:
            # جمعآوری همه سیگنالها
            smart_money = self.engine.detect_smart_money(df)
            order_blocks = self.engine.find_order_blocks(df)
            liquidity = self.engine.detect_liquidity_hunt(df)
            divergence = self.engine.find_divergences(df)
            whale = self.engine.detect_whale_activity(df)
            pump = self.pump_dump.detect_pump_starting(df, symbol)
            dump = self.pump_dump.detect_dump_warning(df, symbol)
            pump_dump = self.pump_dump.detect_advanced_pump_dump(df, symbol)
            
            # اضافه کردن symbol به همه
            for sig_list in [smart_money, order_blocks, liquidity, divergence, whale]:
                for sig in sig_list:
                    sig['symbol'] = symbol
                    all_signals.append(sig)
            
            all_signals.extend(pump)
            all_signals.extend(dump)
            all_signals.extend(pump_dump)
            
        except Exception as e:
            print(f"خطا در تحلیل {symbol}: {e}")
        
        return all_signals
    
    def get_best_signals(self, df, symbol, top_n=3):
        """بهترین سیگنالها"""
        all_signals = self.analyze(df, symbol)
        
        # مرتبسازی بر اساس قدرت
        all_signals.sort(key=lambda x: x.get('strength', 0), reverse=True)
        
        return all_signals[:top_n]
    
    def get_combined_score(self, df, symbol):
        """امتیاز ترکیبی"""
        signals = self.analyze(df, symbol)
        
        buy_score = 0
        sell_score = 0
        buy_reasons = []
        sell_reasons = []
        
        weights = {
            'LIQUIDITY_GRAB': 1.5,
            'SMART_MONEY': 1.4,
            'DIVERGENCE': 1.3,
            'WHALE': 1.2,
            'ORDER_BLOCK': 1.1,
            'PUMP': 1.0,
            'DUMP': 1.0
        }
        
        for sig in signals:
            sig_type = sig.get('type', '')
            strength = sig.get('strength', 50)
            
            weight = 1.0
            for key, w in weights.items():
                if key in sig_type:
                    weight = w
                    break
            
            if sig.get('signal') == 'BUY':
                buy_score += strength * weight
                buy_reasons.append(sig.get('reason', sig_type))
            elif sig.get('signal') == 'SELL':
                sell_score += strength * weight
                sell_reasons.append(sig.get('reason', sig_type))
        
        if buy_score > sell_score and buy_score > 80:
            return {
                'symbol': symbol,
                'recommendation': 'STRONG_BUY',
                'score': round(buy_score, 1),
                'confidence': min(buy_score / 3, 95),
                'reasons': buy_reasons[:5],
                'price': df['close'].iloc[-1] if len(df) > 0 else 0
            }
        elif sell_score > buy_score and sell_score > 80:
            return {
                'symbol': symbol,
                'recommendation': 'STRONG_SELL',
                'score': round(sell_score, 1),
                'confidence': min(sell_score / 3, 95),
                'reasons': sell_reasons[:5],
                'price': df['close'].iloc[-1] if len(df) > 0 else 0
            }
        else:
            return {
                'symbol': symbol,
                'recommendation': 'NEUTRAL',
                'buy_score': round(buy_score, 1),
                'sell_score': round(sell_score, 1)
            }

# نمونه گلوبال
ultimate_generator = UltimateSignalGenerator()
