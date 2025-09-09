#!/usr/bin/env python3
"""
WHOOP webhook server example.
Receives real-time updates from WHOOP API.
"""

import os
import sys
import json
import hmac
import hashlib
from datetime import datetime
from flask import Flask, request, jsonify
from werkzeug.exceptions import BadRequest

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.config import WhoopConfig
from src.models import WhoopWebhookEvent


app = Flask(__name__)


def verify_webhook_signature(payload, signature, secret):
    """Verify webhook signature for security."""
    if not secret:
        return True  # Skip verification if no secret provided
    
    expected_signature = hmac.new(
        secret.encode('utf-8'),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(signature, expected_signature)


@app.route('/webhook', methods=['POST'])
def webhook_handler():
    """Handle incoming webhook events."""
    try:
        # Get signature from headers
        signature = request.headers.get('X-WHOOP-Signature')
        if not signature:
            return jsonify({'error': 'Missing signature'}), 400
        
        # Get raw payload
        payload = request.get_data()
        
        # Verify signature
        config = WhoopConfig.from_env()
        if not verify_webhook_signature(payload, signature, config.webhook_secret):
            return jsonify({'error': 'Invalid signature'}), 401
        
        # Parse JSON payload
        try:
            data = request.get_json()
        except Exception:
            return jsonify({'error': 'Invalid JSON'}), 400
        
        # Process webhook event
        event = WhoopWebhookEvent(**data)
        
        print(f"Received webhook event: {event.event_type}")
        print(f"User ID: {event.user_id}")
        print(f"Resource ID: {event.resource_id}")
        print(f"Timestamp: {event.timestamp}")
        
        # Handle different event types
        if event.event_type == 'cycle.created':
            handle_cycle_created(event)
        elif event.event_type == 'sleep.created':
            handle_sleep_created(event)
        elif event.event_type == 'recovery.created':
            handle_recovery_created(event)
        elif event.event_type == 'workout.created':
            handle_workout_created(event)
        else:
            print(f"Unknown event type: {event.event_type}")
        
        return jsonify({'status': 'success'}), 200
        
    except Exception as e:
        print(f"Webhook error: {e}")
        return jsonify({'error': 'Internal server error'}), 500


def handle_cycle_created(event):
    """Handle cycle created event."""
    print(f"  New cycle created for user {event.user_id}")
    if event.data:
        print(f"  Cycle data: {json.dumps(event.data, indent=2)}")


def handle_sleep_created(event):
    """Handle sleep created event."""
    print(f"  New sleep record created for user {event.user_id}")
    if event.data:
        print(f"  Sleep data: {json.dumps(event.data, indent=2)}")


def handle_recovery_created(event):
    """Handle recovery created event."""
    print(f"  New recovery record created for user {event.user_id}")
    if event.data:
        print(f"  Recovery data: {json.dumps(event.data, indent=2)}")


def handle_workout_created(event):
    """Handle workout created event."""
    print(f"  New workout created for user {event.user_id}")
    if event.data:
        print(f"  Workout data: {json.dumps(event.data, indent=2)}")


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat()
    }), 200


@app.route('/', methods=['GET'])
def index():
    """Root endpoint with instructions."""
    return jsonify({
        'message': 'WHOOP Webhook Server',
        'endpoints': {
            'webhook': '/webhook (POST)',
            'health': '/health (GET)'
        },
        'instructions': [
            '1. Configure this URL in your WHOOP app settings',
            '2. Set WEBHOOK_SECRET in your environment',
            '3. Start receiving real-time updates'
        ]
    }), 200


def main():
    """Main function to run the webhook server."""
    print("WHOOP Webhook Server")
    print("=" * 20)
    
    # Load configuration
    try:
        config = WhoopConfig.from_env()
        print("✓ Configuration loaded successfully")
    except Exception as e:
        print(f"✗ Configuration error: {e}")
        print("Please ensure you have a .env file with WHOOP credentials")
        return
    
    if not config.webhook_secret:
        print("⚠️  Warning: No webhook secret configured. Webhooks will not be verified.")
        print("   Set WEBHOOK_SECRET in your environment for security.")
    
    print(f"\nWebhook server starting on port {config.webhook_port}")
    print(f"Webhook URL: http://localhost:{config.webhook_port}/webhook")
    print(f"Health check: http://localhost:{config.webhook_port}/health")
    print("\nTo configure webhooks in WHOOP:")
    print("1. Go to your WHOOP Developer Dashboard")
    print("2. Edit your app settings")
    print("3. Set webhook URL to: http://your-domain.com/webhook")
    print("4. Set webhook secret to match WEBHOOK_SECRET")
    print("\nPress Ctrl+C to stop the server")
    
    try:
        app.run(
            host='0.0.0.0',
            port=config.webhook_port,
            debug=False
        )
    except KeyboardInterrupt:
        print("\n✓ Webhook server stopped")


if __name__ == "__main__":
    main()
