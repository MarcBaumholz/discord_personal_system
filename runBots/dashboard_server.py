#!/usr/bin/env python3
"""
Discord Bot Dashboard Server
Flask-based web dashboard for monitoring Discord bot status in real-time
"""

import os
import json
import time
import threading
from datetime import datetime
from flask import Flask, render_template, jsonify, Response
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configuration
STATUS_FILE = '/app/data/bot_status.json'
UPDATE_INTERVAL = 5  # seconds

def get_bot_status():
    """Get current bot status from JSON file"""
    try:
        if os.path.exists(STATUS_FILE):
            with open(STATUS_FILE, 'r') as f:
                return json.load(f)
        else:
            # Return default status if file doesn't exist
            return {
                "timestamp": datetime.now().isoformat(),
                "system_start_time": datetime.now().isoformat(),
                "system_uptime": "Starting...",
                "total_bots": 12,
                "running_count": 0,
                "stopped_count": 0,
                "failed_count": 12,
                "bots": []
            }
    except Exception as e:
        logger.error(f"Error reading status file: {e}")
        return {
            "timestamp": datetime.now().isoformat(),
            "error": str(e),
            "total_bots": 12,
            "running_count": 0,
            "stopped_count": 0,
            "failed_count": 12,
            "bots": []
        }

@app.route('/')
def dashboard():
    """Main dashboard page"""
    return render_template('dashboard.html')

@app.route('/api/status')
def api_status():
    """API endpoint for current bot status"""
    return jsonify(get_bot_status())

@app.route('/api/events')
def events():
    """Server-Sent Events endpoint for real-time updates"""
    def generate():
        while True:
            try:
                status = get_bot_status()
                yield f"data: {json.dumps(status)}\n\n"
                time.sleep(UPDATE_INTERVAL)
            except Exception as e:
                logger.error(f"Error in SSE stream: {e}")
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
                time.sleep(UPDATE_INTERVAL)
    
    return Response(generate(), mimetype='text/plain')

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "dashboard": "running"
    })

if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    os.makedirs('/app/runBots/templates', exist_ok=True)
    
    logger.info("🌐 Starting Discord Bot Dashboard Server...")
    logger.info("📊 Dashboard will be available at: http://localhost:8080")
    
    # Run Flask app
    app.run(
        host='0.0.0.0',
        port=8080,
        debug=False,
        threaded=True
    ) 