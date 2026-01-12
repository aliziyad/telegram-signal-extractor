from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_cors import CORS
from functools import wraps
from datetime import datetime, timedelta
from sqlalchemy import func, desc
from app.database.connection import SessionLocal, init_db
from app.database.models import (
    TelegramChannel, ParsedSignal, ExtractionLog, ParsingError, SignalStats
)
from config.settings import settings
import logging

logger = logging.getLogger(__name__)

def create_app():
    app = Flask(__name__, template_folder='app/dashboard/templates', static_folder='app/dashboard/static')
    app.config['SECRET_KEY'] = settings.SECRET_KEY
    CORS(app)
    
    # Initialize database on startup
    init_db()
    
    def login_required(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user' not in session:
                return redirect(url_for('login'))
            return f(*args, **kwargs)
        return decorated_function
    
    # ==================== Authentication Routes ====================
    
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')
            
            if username == settings.ADMIN_USERNAME and password == settings.ADMIN_PASSWORD:
                session['user'] = username
                return redirect(url_for('dashboard'))
            else:
                return render_template('login.html', error='Invalid credentials'), 401
        
        return render_template('login.html')
    
    @app.route('/logout')
    def logout():
        session.clear()
        return redirect(url_for('login'))
    
    # ==================== Dashboard Routes ====================
    
    @app.route('/')
    @login_required
    def dashboard():
        return render_template('dashboard.html')
    
    # ==================== API Routes ====================
    
    @app.route('/api/stats', methods=['GET'])
    @login_required
    def get_stats():
        """Get overall system statistics"""
        db = SessionLocal()
        try:
            total_signals = db.query(ParsedSignal).count()
            sent_signals = db.query(ParsedSignal).filter(
                ParsedSignal.sent_to_supabase == True
            ).count()
            pending_signals = db.query(ParsedSignal).filter(
                ParsedSignal.status == "pending"
            ).count()
            failed_signals = db.query(ParsedSignal).filter(
                ParsedSignal.status == "failed"
            ).count()
            
            # Channel stats
            active_channels = db.query(TelegramChannel).filter(
                TelegramChannel.is_active == True
            ).count()
            
            # Parsing method breakdown
            parsing_methods = db.query(
                ParsedSignal.parsing_method,
                func.count(ParsedSignal.id)
            ).group_by(ParsedSignal.parsing_method).all()
            
            # Last 24 hours
            yesterday = datetime.utcnow() - timedelta(hours=24)
            signals_24h = db.query(ParsedSignal).filter(
                ParsedSignal.extracted_at >= yesterday
            ).count()
            
            return jsonify({
                "total_signals": total_signals,
                "sent_signals": sent_signals,
                "pending_signals": pending_signals,
                "failed_signals": failed_signals,
                "active_channels": active_channels,
                "signals_24h": signals_24h,
                "success_rate": round((sent_signals / total_signals * 100) if total_signals > 0 else 0, 2),
                "parsing_methods": [
                    {"method": m[0], "count": m[1]} for m in parsing_methods
                ]
            })
        finally:
            db.close()
    
    @app.route('/api/channels', methods=['GET'])
    @login_required
    def get_channels():
        """Get all channels with their stats"""
        db = SessionLocal()
        try:
            channels = db.query(TelegramChannel).all()
            
            result = []
            for channel in channels:
                stats = db.query(ParsedSignal).filter(
                    ParsedSignal.channel_id == channel.channel_id
                )
                
                result.append({
                    "id": channel.id,
                    "channel_id": channel.channel_id,
                    "channel_name": channel.channel_name,
                    "channel_username": channel.channel_username,
                    "is_active": channel.is_active,
                    "total_signals": stats.count(),
                    "sent_signals": stats.filter(ParsedSignal.sent_to_supabase == True).count(),
                    "pending_signals": stats.filter(ParsedSignal.status == "pending").count(),
                    "failed_signals": stats.filter(ParsedSignal.status == "failed").count(),
                    "created_at": channel.created_at.isoformat(),
                    "updated_at": channel.updated_at.isoformat()
                })
            
            return jsonify(result)
        finally:
            db.close()
    
    @app.route('/api/channels', methods=['POST'])
    @login_required
    def add_channel():
        """Add a new channel to monitor"""
        data = request.json
        db = SessionLocal()
        try:
            channel = TelegramChannel(
                channel_id=data.get('channel_id'),
                channel_name=data.get('channel_name'),
                channel_username=data.get('channel_username'),
                is_active=True
            )
            db.add(channel)
            db.commit()
            
            logger.info(f"Channel added: {data.get('channel_name')}")
            
            return jsonify({
                "success": True,
                "message": f"Channel {data.get('channel_name')} added successfully"
            }), 201
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to add channel: {e}")
            return jsonify({"success": False, "error": str(e)}), 400
        finally:
            db.close()
    
    @app.route('/api/channels/<channel_id>', methods=['PUT'])
    @login_required
    def update_channel(channel_id):
        """Toggle channel active status"""
        data = request.json
        db = SessionLocal()
        try:
            channel = db.query(TelegramChannel).filter(
                TelegramChannel.channel_id == channel_id
            ).first()
            
            if not channel:
                return jsonify({"success": False, "error": "Channel not found"}), 404
            
            channel.is_active = data.get('is_active', channel.is_active)
            db.commit()
            
            logger.info(f"Channel updated: {channel.channel_name} - Active: {channel.is_active}")
            
            return jsonify({"success": True, "message": "Channel updated"})
        except Exception as e:
            db.rollback()
            return jsonify({"success": False, "error": str(e)}), 400
        finally:
            db.close()
    
    @app.route('/api/channels/<channel_id>', methods=['DELETE'])
    @login_required
    def delete_channel(channel_id):
        """Delete a channel"""
        db = SessionLocal()
        try:
            channel = db.query(TelegramChannel).filter(
                TelegramChannel.channel_id == channel_id
            ).first()
            
            if not channel:
                return jsonify({"success": False, "error": "Channel not found"}), 404
            
            channel_name = channel.channel_name
            db.delete(channel)
            db.commit()
            
            logger.info(f"Channel deleted: {channel_name}")
            
            return jsonify({"success": True, "message": f"Channel {channel_name} deleted"})
        except Exception as e:
            db.rollback()
            return jsonify({"success": False, "error": str(e)}), 400
        finally:
            db.close()
    
    @app.route('/api/signals', methods=['GET'])
    @login_required
    def get_signals():
        """Get recent signals with pagination"""
        db = SessionLocal()
        try:
            page = request.args.get('page', 1, type=int)
            limit = request.args.get('limit', 50, type=int)
            status = request.args.get('status')
            
            query = db.query(ParsedSignal).order_by(desc(ParsedSignal.extracted_at))
            
            if status:
                query = query.filter(ParsedSignal.status == status)
            
            total = query.count()
            offset = (page - 1) * limit
            signals = query.limit(limit).offset(offset).all()
            
            result = []
            for signal in signals:
                result.append({
                    "id": signal.id,
                    "channel_id": signal.channel_id,
                    "symbol": signal.symbol,
                    "direction": signal.direction,
                    "entry_price": signal.entry_price,
                    "stop_loss": signal.stop_loss,
                    "take_profit_1": signal.take_profit_1,
                    "take_profit_2": signal.take_profit_2,
                    "take_profit_3": signal.take_profit_3,
                    "parsing_method": signal.parsing_method,
                    "confidence_score": signal.confidence_score,
                    "status": signal.status,
                    "sent_to_supabase": signal.sent_to_supabase,
                    "extracted_at": signal.extracted_at.isoformat(),
                    "message_timestamp": signal.message_timestamp.isoformat() if signal.message_timestamp else None
                })
            
            return jsonify({
                "signals": result,
                "total": total,
                "page": page,
                "limit": limit,
                "pages": (total + limit - 1) // limit
            })
        finally:
            db.close()
    
    @app.route('/api/logs', methods=['GET'])
    @login_required
    def get_logs():
        """Get recent logs"""
        db = SessionLocal()
        try:
            limit = request.args.get('limit', 100, type=int)
            log_type = request.args.get('type')
            
            query = db.query(ExtractionLog).order_by(desc(ExtractionLog.created_at))
            
            if log_type:
                query = query.filter(ExtractionLog.log_type == log_type)
            
            logs = query.limit(limit).all()
            
            result = []
            for log in logs:
                result.append({
                    "id": log.id,
                    "channel_id": log.channel_id,
                    "log_type": log.log_type,
                    "message": log.message,
                    "metadata": log.log_metadata,
                    "created_at": log.created_at.isoformat()
                })
            
            return jsonify(result)
        finally:
            db.close()
    
    @app.route('/api/errors', methods=['GET'])
    @login_required
    def get_parsing_errors():
        """Get parsing errors"""
        db = SessionLocal()
        try:
            errors = db.query(ParsingError).filter(
                ParsingError.resolved == False
            ).order_by(desc(ParsingError.created_at)).limit(50).all()
            
            result = []
            for error in errors:
                result.append({
                    "id": error.id,
                    "channel_id": error.channel_id,
                    "parsing_method": error.parsing_method,
                    "raw_message": error.raw_message[:200],
                    "error_message": error.error_message,
                    "created_at": error.created_at.isoformat()
                })
            
            return jsonify(result)
        finally:
            db.close()
    
    @app.route('/api/health', methods=['GET'])
    def health_check():
        """Health check endpoint"""
        return jsonify({
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat()
        })
    
    return app
