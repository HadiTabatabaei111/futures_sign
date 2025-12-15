import pandas as pd
import numpy as np
from ta.trend import MACD, EMAIndicator, SMAIndicator
from ta.momentum import RSIIndicator, StochasticOscillator
from ta.volatility import BollingerBands, AverageTrueRange

class TechnicalIndicators:
    @staticmethod
    def calculate_all(df):
        if len(df) < 100:
            return df
        df = df.copy()
        df['ma_7'] = SMAIndicator(df['close'], window=7).sma_indicator()
        df['ma_25'] = SMAIndicator(df['close'], window=25).sma_indicator()
        df['ma_99'] = SMAIndicator(df['close'], window=99).sma_indicator()
        df['ema_7'] = EMAIndicator(df['close'], window=7).ema_indicator()
        df['ema_25'] = EMAIndicator(df['close'], window=25).ema_indicator()
        df['ema_99'] = EMAIndicator(df['close'], window=99).ema_indicator()
        df['rsi'] = RSIIndicator(df['close'], window=14).rsi()
        macd = MACD(df['close'])
        df['macd'] = macd.macd()
        df['macd_signal'] = macd.macd_signal()
        df['macd_histogram'] = macd.macd_diff()
        bb = BollingerBands(df['close'], window=20)
        df['bb_upper'] = bb.bollinger_hband()
        df['bb_middle'] = bb.bollinger_mavg()
        df['bb_lower'] = bb.bollinger_lband()
        df['atr'] = AverageTrueRange(df['high'], df['low'], df['close'], window=14).average_true_range()
        df['volume_sma'] = SMAIndicator(df['volume'], window=20).sma_indicator()
        stoch = StochasticOscillator(df['high'], df['low'], df['close'])
        df['stoch_k'] = stoch.stoch()
        df['stoch_d'] = stoch.stoch_signal()
        return df
    
    @staticmethod
    def calculate_ut_bot(df, key_value=1, atr_period=10):
        if len(df) < atr_period + 5:
            return df
        df = df.copy()
        df['xATR'] = AverageTrueRange(df['high'], df['low'], df['close'], window=atr_period).average_true_range()
        df['nLoss'] = key_value * df['xATR']
        df['xATRTrailingStop'] = 0.0
        for i in range(1, len(df)):
            close_now = df['close'].iloc[i]
            close_prev = df['close'].iloc[i-1]
            atr_stop_prev = df['xATRTrailingStop'].iloc[i-1]
            n_loss = df['nLoss'].iloc[i]
            if close_now > atr_stop_prev and close_prev > atr_stop_prev:
                df.iloc[i, df.columns.get_loc('xATRTrailingStop')] = max(atr_stop_prev, close_now - n_loss)
            elif close_now < atr_stop_prev and close_prev < atr_stop_prev:
                df.iloc[i, df.columns.get_loc('xATRTrailingStop')] = min(atr_stop_prev, close_now + n_loss)
            elif close_now > atr_stop_prev:
                df.iloc[i, df.columns.get_loc('xATRTrailingStop')] = close_now - n_loss
            else:
                df.iloc[i, df.columns.get_loc('xATRTrailingStop')] = close_now + n_loss
        df['pos'] = 0
        for i in range(1, len(df)):
            close_now = df['close'].iloc[i]
            close_prev = df['close'].iloc[i-1]
            atr_stop_prev = df['xATRTrailingStop'].iloc[i-1]
            if close_prev < atr_stop_prev and close_now > atr_stop_prev:
                df.iloc[i, df.columns.get_loc('pos')] = 1
            elif close_prev > atr_stop_prev and close_now < atr_stop_prev:
                df.iloc[i, df.columns.get_loc('pos')] = -1
            else:
                df.iloc[i, df.columns.get_loc('pos')] = df['pos'].iloc[i-1]
        df['ut_buy'] = (df['pos'] == 1) & (df['pos'].shift(1) != 1)
        df['ut_sell'] = (df['pos'] == -1) & (df['pos'].shift(1) != -1)
        return df
    
    @staticmethod
    def find_ma_crossovers(df):
        crossovers = []
        if 'ma_7' not in df.columns or 'ma_25' not in df.columns:
            return crossovers
        for i in range(1, len(df)):
            if df['ma_7'].iloc[i-1] < df['ma_25'].iloc[i-1] and df['ma_7'].iloc[i] > df['ma_25'].iloc[i]:
                crossovers.append({'index': i, 'type': 'MA_GOLDEN', 'signal': 'BUY', 'price': df['close'].iloc[i]})
            if df['ma_7'].iloc[i-1] > df['ma_25'].iloc[i-1] and df['ma_7'].iloc[i] < df['ma_25'].iloc[i]:
                crossovers.append({'index': i, 'type': 'MA_DEATH', 'signal': 'SELL', 'price': df['close'].iloc[i]})
        return crossovers
    
    @staticmethod
    def find_ema_crossovers(df):
        crossovers = []
        if 'ema_7' not in df.columns or 'ema_25' not in df.columns:
            return crossovers
        for i in range(1, len(df)):
            if df['ema_7'].iloc[i-1] < df['ema_25'].iloc[i-1] and df['ema_7'].iloc[i] > df['ema_25'].iloc[i]:
                crossovers.append({'index': i, 'type': 'EMA_GOLDEN', 'signal': 'BUY', 'price': df['close'].iloc[i]})
            if df['ema_7'].iloc[i-1] > df['ema_25'].iloc[i-1] and df['ema_7'].iloc[i] < df['ema_25'].iloc[i]:
                crossovers.append({'index': i, 'type': 'EMA_DEATH', 'signal': 'SELL', 'price': df['close'].iloc[i]})
        return crossovers
