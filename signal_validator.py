from datetime import datetime, timedelta
from database_extended import db, SignalRecord, PumpDumpRecord

class SignalValidator:
    def __init__(self, fetcher):
        self.fetcher = fetcher
    
    def validate_pending_signals(self):
        print(f"[{datetime.now()}] 🔍 اعتبارسنجی سیگنالها...")
        pending_signals = db.get_pending_signals(min_age_minutes=3)
        results = {'validated': 0, 'success': 0, 'failure': 0, 'details': []}
        for signal in pending_signals:
            try:
                result = self._validate_single_signal(signal)
                if result.get('status') != 'pending':
                    results['validated'] += 1
                    if result.get('result') == 'success':
                        results['success'] += 1
                    elif result.get('result') == 'failure':
                        results['failure'] += 1
                    results['details'].append(result)
            except Exception as e:
                print(f"  خطا در بررسی {signal.symbol}: {e}")
        print(f"  ✅ بررسی: {results['validated']} | موفق: {results['success']} | ناموفق: {results['failure']}")
        return results
    
    def _validate_single_signal(self, signal):
        current_price = self._get_current_price(signal.symbol)
        if not current_price:
            return {'status': 'pending', 'message': 'قیمت دریافت نشد'}
        entry_price = signal.entry_price
        if signal.signal_type == 'BUY':
            profit_percent = ((current_price - entry_price) / entry_price) * 100
        else:
            profit_percent = ((entry_price - current_price) / entry_price) * 100
        result = 'unknown'
        status = 'validated'
        note = ''
        if profit_percent >= signal.target_percent:
            result = 'success'
            note = f'🎯 تارگت! سود: {profit_percent:.2f}%'
        elif profit_percent <= -signal.stop_percent:
            result = 'failure'
            note = f'❌ استاپ! ضرر: {profit_percent:.2f}%'
        elif datetime.utcnow() > signal.expires_at:
            status = 'expired'
            if profit_percent > 0:
                result = 'success'
                note = f'⏰ منقضی با سود {profit_percent:.2f}%'
            elif profit_percent < -0.5:
                result = 'failure'
                note = f'⏰ منقضی با ضرر {profit_percent:.2f}%'
            else:
                result = 'breakeven'
                note = '⏰ منقضی - سربهسر'
        else:
            return {'status': 'pending', 'profit_percent': profit_percent}
        db.update_signal_result(signal.id, {
            'status': status, 'result': result, 'exit_price': current_price,
            'profit_percent': round(profit_percent, 2), 'note': note
        })
        return {
            'signal_id': signal.id, 'symbol': signal.symbol, 'signal_type': signal.signal_type,
            'profit_percent': round(profit_percent, 2), 'status': status, 'result': result, 'note': note
        }
    
    def validate_pump_dumps(self):
        pending = db.get_pending_pump_dumps(min_age_minutes=5)
        results = {'validated': 0, 'continued': 0, 'reversed': 0}
        for alert in pending:
            try:
                result = self._validate_pump_dump(alert)
                results['validated'] += 1
                if result.get('continued'):
                    results['continued'] += 1
                else:
                    results['reversed'] += 1
            except:
                pass
        return results
    
    def _validate_pump_dump(self, alert):
        current_price = self._get_current_price(alert.symbol)
        if not current_price:
            return {'status': 'error'}
        initial_price = alert.price_at_alert
        price_change = ((current_price - initial_price) / initial_price) * 100
        continued = (alert.alert_type == 'PUMP' and price_change > 0) or \
                   (alert.alert_type == 'DUMP' and price_change < 0)
        result = 'success' if continued else 'failure'
        db.update_pump_dump_result(alert.id, {
            'status': 'validated', 'result': result, 'continued': continued,
            'reversal_percent': round(price_change, 2) if not continued else None,
            'max_continuation': round(price_change, 2) if continued else None
        })
        return {'alert_id': alert.id, 'continued': continued, 'result': result}
    
    def _get_current_price(self, symbol):
        try:
            symbols = self.fetcher.get_futures_symbols(300)
            full_symbol = None
            for s in symbols:
                if symbol.upper() in s.upper().replace('/', '').replace(':USDT', '').replace('-', ''):
                    full_symbol = s
                    break
            if not full_symbol:
                return None
            ticker = self.fetcher.get_ticker(full_symbol)
            return ticker.get('price') if ticker else None
        except:
            return None
    
    def get_realtime_stats(self):
        return {
            'last_hour': db.get_accuracy_stats(hours=1),
            'last_24h': db.get_accuracy_stats(hours=24),
            'last_7d': db.get_accuracy_stats(hours=168)
        }

validator = None

def init_validator(fetcher):
    global validator
    validator = SignalValidator(fetcher)

def run_validation():
    if validator:
        try:
            signal_results = validator.validate_pending_signals()
            pump_results = validator.validate_pump_dumps()
            return {'signals': signal_results, 'pump_dumps': pump_results, 'timestamp': datetime.utcnow().isoformat()}
        except Exception as e:
            print(f"خطا: {e}")
    return None
