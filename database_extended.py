"""دیتابیس پیشرفته با پشتیبانی از سیگنالهای جدید"""

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta

Base = declarative_base()

class CryptoPrice(Base):
    __tablename__ = 'crypto_prices'
    id = Column(Integer, primary_key=True)
    symbol = Column(String(20), index=True)
    price = Column(Float)
    open_price = Column(Float)
    high_price = Column(Float)
    low_price = Column(Float)
    close_price = Column(Float)
    volume = Column(Float)
    quote_volume = Column(Float)
    price_change = Column(Float)
    price_change_percent = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    timeframe = Column(String(10), default='1m')

class SignalRecord(Base):
    __tablename__ = 'signal_records'
    id = Column(Integer, primary_key=True)
    symbol = Column(String(20), index=True)
    signal_type = Column(String(10))
    signal_source = Column(String(50))
    signal_category = Column(String(30))  # BASIC, ADVANCED, PUMP_DUMP
    strength = Column(Float)
    reason = Column(Text)
    entry_price = Column(Float)
    target_percent = Column(Float, default=2.0)
    stop_percent = Column(Float, default=1.0)
    target_price = Column(Float)
    stop_price = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    validated_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime)
    status = Column(String(20), default='pending')
    result = Column(String(20), default='unknown')
    exit_price = Column(Float, nullable=True)
    profit_percent = Column(Float, nullable=True)
    max_profit_percent = Column(Float, nullable=True)
    max_loss_percent = Column(Float, nullable=True)
    validation_note = Column(Text, nullable=True)
    timeframe = Column(String(10), default='1m')
    # فیلدهای جدید برای سیگنالهای پیشرفته
    is_smart_money = Column(Boolean, default=False)
    is_order_block = Column(Boolean, default=False)
    is_liquidity_hunt = Column(Boolean, default=False)
    is_divergence = Column(Boolean, default=False)
    is_whale = Column(Boolean, default=False)
    is_pump_dump = Column(Boolean, default=False)
    rsi_value = Column(Float, nullable=True)
    volume_zscore = Column(Float, nullable=True)

class PumpDumpRecord(Base):
    __tablename__ = 'pump_dump_records'
    id = Column(Integer, primary_key=True)
    symbol = Column(String(20), index=True)
    alert_type = Column(String(20))
    price_at_alert = Column(Float)
    price_change_percent = Column(Float)
    volume_change_percent = Column(Float)
    momentum = Column(Integer, nullable=True)
    time_period = Column(String(20))
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    validated_at = Column(DateTime, nullable=True)
    price_after_5min = Column(Float, nullable=True)
    price_after_15min = Column(Float, nullable=True)
    price_after_30min = Column(Float, nullable=True)
    continued = Column(Boolean, nullable=True)
    reversal_percent = Column(Float, nullable=True)
    max_continuation = Column(Float, nullable=True)
    status = Column(String(20), default='pending')
    result = Column(String(20), default='unknown')

class AdvancedSignalRecord(Base):
    """جدول مخصوص سیگنالهای پیشرفته"""
    __tablename__ = 'advanced_signals'
    id = Column(Integer, primary_key=True)
    symbol = Column(String(20), index=True)
    signal_type = Column(String(50))  # SMART_MONEY, ORDER_BLOCK, etc.
    direction = Column(String(10))  # BUY, SELL
    strength = Column(Float)
    reason = Column(Text)
    price = Column(Float)
    stop_loss = Column(Float, nullable=True)
    take_profit = Column(Float, nullable=True)
    volume_zscore = Column(Float, nullable=True)
    rsi = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    status = Column(String(20), default='pending')
    result = Column(String(20), default='unknown')
    profit_percent = Column(Float, nullable=True)
    validated_at = Column(DateTime, nullable=True)

class SignalAccuracy(Base):
    __tablename__ = 'signal_accuracy'
    id = Column(Integer, primary_key=True)
    period = Column(String(20))
    period_start = Column(DateTime, index=True)
    period_end = Column(DateTime)
    total_signals = Column(Integer, default=0)
    successful_signals = Column(Integer, default=0)
    failed_signals = Column(Integer, default=0)
    pending_signals = Column(Integer, default=0)
    success_rate = Column(Float, default=0.0)
    # آمار پیشرفته
    smart_money_total = Column(Integer, default=0)
    smart_money_success = Column(Integer, default=0)
    order_block_total = Column(Integer, default=0)
    order_block_success = Column(Integer, default=0)
    liquidity_total = Column(Integer, default=0)
    liquidity_success = Column(Integer, default=0)
    divergence_total = Column(Integer, default=0)
    divergence_success = Column(Integer, default=0)
    whale_total = Column(Integer, default=0)
    whale_success = Column(Integer, default=0)
    avg_profit_percent = Column(Float, default=0.0)
    calculated_at = Column(DateTime, default=datetime.utcnow)

class Database:
    def __init__(self, db_url='sqlite:///crypto_futures.db'):
        self.engine = create_engine(db_url, echo=False)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
    
    def get_session(self):
        return self.Session()
    
    def save_price(self, data):
        session = self.Session()
        try:
            price = CryptoPrice(**data)
            session.add(price)
            session.commit()
            return price.id
        except Exception as e:
            session.rollback()
        finally:
            session.close()
    
    def save_signal(self, signal_data):
        session = self.Session()
        try:
            entry_price = signal_data.get('price', 0)
            target_pct = signal_data.get('target_percent', 2.0)
            stop_pct = signal_data.get('stop_percent', 1.0)
            
            if signal_data.get('signal_type') == 'BUY' or signal_data.get('signal') == 'BUY':
                target_price = entry_price * (1 + target_pct / 100)
                stop_price = entry_price * (1 - stop_pct / 100)
                sig_type = 'BUY'
            else:
                target_price = entry_price * (1 - target_pct / 100)
                stop_price = entry_price * (1 + stop_pct / 100)
                sig_type = 'SELL'
            
            sig_source = signal_data.get('signal_source', signal_data.get('type', 'MIXED'))
            
            record = SignalRecord(
                symbol=signal_data.get('symbol'),
                signal_type=sig_type,
                signal_source=sig_source,
                signal_category=self._get_category(sig_source),
                strength=signal_data.get('strength', 50),
                reason=signal_data.get('reason', ''),
                entry_price=entry_price,
                target_percent=target_pct,
                stop_percent=stop_pct,
                target_price=target_price,
                stop_price=stop_price,
                expires_at=datetime.utcnow() + timedelta(hours=1),
                is_smart_money='SMART_MONEY' in sig_source,
                is_order_block='ORDER_BLOCK' in sig_source,
                is_liquidity_hunt='LIQUIDITY' in sig_source,
                is_divergence='DIVERGENCE' in sig_source,
                is_whale='WHALE' in sig_source,
                is_pump_dump='PUMP' in sig_source or 'DUMP' in sig_source,
                rsi_value=signal_data.get('rsi'),
                volume_zscore=signal_data.get('volume_zscore')
            )
            
            session.add(record)
            session.commit()
            return record.id
        except Exception as e:
            session.rollback()
            print(f"خطا در ذخیره سیگنال: {e}")
        finally:
            session.close()
    
    def save_advanced_signal(self, signal_data):
        session = self.Session()
        try:
            record = AdvancedSignalRecord(
                symbol=signal_data.get('symbol'),
                signal_type=signal_data.get('type', ''),
                direction=signal_data.get('signal', ''),
                strength=signal_data.get('strength', 50),
                reason=signal_data.get('reason', ''),
                price=signal_data.get('price', 0),
                stop_loss=signal_data.get('stop_loss'),
                take_profit=signal_data.get('take_profit'),
                volume_zscore=signal_data.get('volume_zscore'),
                rsi=signal_data.get('rsi')
            )
            session.add(record)
            session.commit()
            return record.id
        except Exception as e:
            session.rollback()
        finally:
            session.close()
    
    def save_pump_dump(self, alert_data):
        session = self.Session()
        try:
            record = PumpDumpRecord(
                symbol=alert_data.get('symbol'),
                alert_type=alert_data.get('alert_type'),
                price_at_alert=alert_data.get('price'),
                price_change_percent=alert_data.get('price_change'),
                volume_change_percent=alert_data.get('volume_change'),
                momentum=alert_data.get('momentum'),
                time_period=alert_data.get('time_period', '15m')
            )
            session.add(record)
            session.commit()
            return record.id
        except Exception as e:
            session.rollback()
        finally:
            session.close()
    
    def _get_category(self, source):
        if any(x in source for x in ['SMART_MONEY', 'ORDER_BLOCK', 'LIQUIDITY', 'DIVERGENCE', 'WHALE']):
            return 'ADVANCED'
        elif any(x in source for x in ['PUMP', 'DUMP']):
            return 'PUMP_DUMP'
        return 'BASIC'
    
    def get_pending_signals(self, min_age_minutes=3):
        session = self.Session()
        try:
            cutoff = datetime.utcnow() - timedelta(minutes=min_age_minutes)
            signals = session.query(SignalRecord).filter(
                SignalRecord.status == 'pending',
                SignalRecord.created_at <= cutoff,
                SignalRecord.expires_at > datetime.utcnow()
            ).all()
            return signals
        finally:
            session.close()
    
    def get_pending_pump_dumps(self, min_age_minutes=5):
        session = self.Session()
        try:
            cutoff = datetime.utcnow() - timedelta(minutes=min_age_minutes)
            alerts = session.query(PumpDumpRecord).filter(
                PumpDumpRecord.status == 'pending',
                PumpDumpRecord.created_at <= cutoff
            ).all()
            return alerts
        finally:
            session.close()
    
    def update_signal_result(self, signal_id, result_data):
        session = self.Session()
        try:
            signal = session.query(SignalRecord).filter(SignalRecord.id == signal_id).first()
            if signal:
                signal.status = result_data.get('status', 'validated')
                signal.result = result_data.get('result', 'unknown')
                signal.exit_price = result_data.get('exit_price')
                signal.profit_percent = result_data.get('profit_percent')
                signal.max_profit_percent = result_data.get('max_profit')
                signal.max_loss_percent = result_data.get('max_loss')
                signal.validated_at = datetime.utcnow()
                signal.validation_note = result_data.get('note', '')
                session.commit()
        finally:
            session.close()
    
    def update_pump_dump_result(self, alert_id, result_data):
        session = self.Session()
        try:
            alert = session.query(PumpDumpRecord).filter(PumpDumpRecord.id == alert_id).first()
            if alert:
                for key, value in result_data.items():
                    if hasattr(alert, key):
                        setattr(alert, key, value)
                alert.validated_at = datetime.utcnow()
                session.commit()
        finally:
            session.close()
    
    def get_accuracy_stats(self, hours=24):
        session = self.Session()
        try:
            from sqlalchemy import func
            cutoff = datetime.utcnow() - timedelta(hours=hours)
            
            total = session.query(SignalRecord).filter(SignalRecord.created_at >= cutoff).count()
            successful = session.query(SignalRecord).filter(
                SignalRecord.created_at >= cutoff,
                SignalRecord.result == 'success'
            ).count()
            failed = session.query(SignalRecord).filter(
                SignalRecord.created_at >= cutoff,
                SignalRecord.result == 'failure'
            ).count()
            pending = session.query(SignalRecord).filter(
                SignalRecord.created_at >= cutoff,
                SignalRecord.status == 'pending'
            ).count()
            
            # آمار پیشرفته
            advanced_stats = {}
            for field, name in [
                ('is_smart_money', 'smart_money'),
                ('is_order_block', 'order_block'),
                ('is_liquidity_hunt', 'liquidity'),
                ('is_divergence', 'divergence'),
                ('is_whale', 'whale')
            ]:
                field_total = session.query(SignalRecord).filter(
                    SignalRecord.created_at >= cutoff,
                    getattr(SignalRecord, field) == True
                ).count()
                field_success = session.query(SignalRecord).filter(
                    SignalRecord.created_at >= cutoff,
                    getattr(SignalRecord, field) == True,
                    SignalRecord.result == 'success'
                ).count()
                advanced_stats[name] = {
                    'total': field_total,
                    'success': field_success,
                    'rate': round((field_success / field_total * 100) if field_total > 0 else 0, 2)
                }
            
            avg_profit = session.query(func.avg(SignalRecord.profit_percent)).filter(
                SignalRecord.created_at >= cutoff,
                SignalRecord.result == 'success'
            ).scalar() or 0
            
            return {
                'period_hours': hours,
                'total_signals': total,
                'successful': successful,
                'failed': failed,
                'pending': pending,
                'success_rate': round((successful / total * 100) if total > 0 else 0, 2),
                'failure_rate': round((failed / total * 100) if total > 0 else 0, 2),
                'advanced': advanced_stats,
                'avg_profit': round(avg_profit, 2),
                'calculated_at': datetime.utcnow().isoformat()
            }
        finally:
            session.close()
    
    def get_signal_history(self, limit=100, symbol=None, category=None):
        session = self.Session()
        try:
            query = session.query(SignalRecord)
            if symbol:
                query = query.filter(SignalRecord.symbol == symbol)
            if category:
                query = query.filter(SignalRecord.signal_category == category)
            
            signals = query.order_by(SignalRecord.created_at.desc()).limit(limit).all()
            
            return [{
                'id': s.id,
                'symbol': s.symbol,
                'signal_type': s.signal_type,
                'signal_source': s.signal_source,
                'category': s.signal_category,
                'strength': s.strength,
                'reason': s.reason,
                'entry_price': s.entry_price,
                'exit_price': s.exit_price,
                'profit_percent': s.profit_percent,
                'status': s.status,
                'result': s.result,
                'created_at': s.created_at.isoformat() if s.created_at else None,
                'is_advanced': s.signal_category == 'ADVANCED'
            } for s in signals]
        finally:
            session.close()
    
    def get_pump_dump_history(self, limit=50):
        session = self.Session()
        try:
            alerts = session.query(PumpDumpRecord).order_by(
                PumpDumpRecord.created_at.desc()
            ).limit(limit).all()
            
            return [{
                'id': a.id,
                'symbol': a.symbol,
                'alert_type': a.alert_type,
                'price_at_alert': a.price_at_alert,
                'price_change': a.price_change_percent,
                'volume_change': a.volume_change_percent,
                'momentum': a.momentum,
                'continued': a.continued,
                'status': a.status,
                'result': a.result,
                'created_at': a.created_at.isoformat() if a.created_at else None
            } for a in alerts]
        finally:
            session.close()
    
    def get_latest_prices(self, limit=250):
        session = self.Session()
        try:
            from sqlalchemy import func
            subquery = session.query(
                CryptoPrice.symbol,
                func.max(CryptoPrice.id).label('max_id')
            ).group_by(CryptoPrice.symbol).subquery()
            
            prices = session.query(CryptoPrice).join(
                subquery,
                (CryptoPrice.symbol == subquery.c.symbol) & 
                (CryptoPrice.id == subquery.c.max_id)
            ).limit(limit).all()
            
            return [{
                'symbol': p.symbol,
                'price': p.price,
                'price_change_percent': p.price_change_percent,
                'volume': p.volume,
                'quote_volume': p.quote_volume
            } for p in prices]
        finally:
            session.close()

db = Database()
