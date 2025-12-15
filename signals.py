import pandas as pd
from datetime import datetime

class SignalGenerator:
    @staticmethod
    def analyze_for_signals(df, symbol):
        signals = []
        if len(df) < 100:
            return signals
        latest = df.iloc[-1]
        prev = df.iloc[-2]
        strength = 0
        reasons = []
        signal_type = None
        
        rsi = latest.get('rsi', 50)
        if rsi < 30:
            strength += 25
            reasons.append(f'RSI Oversold ({rsi:.1f})')
            signal_type = 'BUY'
        elif rsi > 70:
            strength += 25
            reasons.append(f'RSI Overbought ({rsi:.1f})')
            signal_type = 'SELL'
        
        macd = latest.get('macd', 0)
        macd_signal = latest.get('macd_signal', 0)
        prev_macd = prev.get('macd', 0)
        prev_macd_signal = prev.get('macd_signal', 0)
        if prev_macd < prev_macd_signal and macd > macd_signal:
            strength += 30
            reasons.append('MACD Bullish Cross')
            if signal_type != 'SELL':
                signal_type = 'BUY'
        elif prev_macd > prev_macd_signal and macd < macd_signal:
            strength += 30
            reasons.append('MACD Bearish Cross')
            if signal_type != 'BUY':
                signal_type = 'SELL'
        
        ma_7 = latest.get('ma_7', 0)
        ma_25 = latest.get('ma_25', 0)
        prev_ma_7 = prev.get('ma_7', 0)
        prev_ma_25 = prev.get('ma_25', 0)
        if prev_ma_7 < prev_ma_25 and ma_7 > ma_25:
            strength += 25
            reasons.append('MA Golden Cross')
            if signal_type != 'SELL':
                signal_type = 'BUY'
        elif prev_ma_7 > prev_ma_25 and ma_7 < ma_25:
            strength += 25
            reasons.append('MA Death Cross')
            if signal_type != 'BUY':
                signal_type = 'SELL'
        
        ema_7 = latest.get('ema_7', 0)
        ema_25 = latest.get('ema_25', 0)
        prev_ema_7 = prev.get('ema_7', 0)
        prev_ema_25 = prev.get('ema_25', 0)
        if prev_ema_7 < prev_ema_25 and ema_7 > ema_25:
            strength += 25
            reasons.append('EMA Golden Cross')
            if signal_type != 'SELL':
                signal_type = 'BUY'
        elif prev_ema_7 > prev_ema_25 and ema_7 < ema_25:
            strength += 25
            reasons.append('EMA Death Cross')
            if signal_type != 'BUY':
                signal_type = 'SELL'
        
        close = latest.get('close', 0)
        bb_lower = latest.get('bb_lower', 0)
        bb_upper = latest.get('bb_upper', 0)
        if bb_lower > 0 and close < bb_lower:
            strength += 15
            reasons.append('Below Bollinger Lower')
            if signal_type != 'SELL':
                signal_type = 'BUY'
        elif bb_upper > 0 and close > bb_upper:
            strength += 15
            reasons.append('Above Bollinger Upper')
            if signal_type != 'BUY':
                signal_type = 'SELL'
        
        volume = latest.get('volume', 0)
        volume_sma = latest.get('volume_sma', 0)
        if volume_sma > 0 and volume > volume_sma * 2:
            strength += 10
            reasons.append('High Volume')
        
        if strength >= 35 and signal_type:
            signals.append({
                'symbol': symbol,
                'signal_type': signal_type,
                'signal_source': 'BASIC_ANALYSIS',
                'strength': min(strength, 100),
                'price': close,
                'reason': ' | '.join(reasons),
                'rsi_value': rsi,
                'timestamp': datetime.utcnow()
            })
        return signals
    
    @staticmethod
    def generate_ut_bot_signals(df, symbol):
        signals = []
        if len(df) < 10:
            return signals
        latest = df.iloc[-1]
        if latest.get('ut_buy', False):
            signals.append({
                'symbol': symbol,
                'signal_type': 'BUY',
                'signal_source': 'UT_BOT',
                'strength': 85,
                'price': latest['close'],
                'reason': '🤖 UT Bot Alert - BUY Signal',
                'timestamp': datetime.utcnow()
            })
        if latest.get('ut_sell', False):
            signals.append({
                'symbol': symbol,
                'signal_type': 'SELL',
                'signal_source': 'UT_BOT',
                'strength': 85,
                'price': latest['close'],
                'reason': '🤖 UT Bot Alert - SELL Signal',
                'timestamp': datetime.utcnow()
            })
        return signals
    
    @staticmethod
    def detect_pump_dump(df, symbol, threshold_percent=5, time_window=15):
        alerts = []
        if len(df) < time_window:
            return alerts
        recent = df.tail(time_window)
        start_price = recent['close'].iloc[0]
        end_price = recent['close'].iloc[-1]
        price_change = ((end_price - start_price) / start_price) * 100
        avg_volume = df['volume'].tail(100).mean()
        recent_volume = recent['volume'].mean()
        volume_change = ((recent_volume - avg_volume) / avg_volume) * 100 if avg_volume > 0 else 0
        if price_change >= threshold_percent and volume_change > 50:
            alerts.append({
                'symbol': symbol,
                'alert_type': 'PUMP',
                'price_change': round(price_change, 2),
                'volume_change': round(volume_change, 2),
                'time_period': f'{time_window}m',
                'price': end_price,
                'timestamp': datetime.utcnow()
            })
        elif price_change <= -threshold_percent and volume_change > 50:
            alerts.append({
                'symbol': symbol,
                'alert_type': 'DUMP',
                'price_change': round(price_change, 2),
                'volume_change': round(volume_change, 2),
                'time_period': f'{time_window}m',
                'price': end_price,
                'timestamp': datetime.utcnow()
            })
        return alerts
