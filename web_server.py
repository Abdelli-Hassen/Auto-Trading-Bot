"""
Web Frontend Server for Trading Bot
Serves the design UI components and provides API endpoints
"""

import os
import json
import logging
from pathlib import Path
from datetime import datetime
from threading import Thread
import time

try:
    from flask import Flask, render_template, jsonify, request
    from flask_cors import CORS
except ImportError:
    print("ERROR: Flask not installed!")
    print("Install it with: pip install flask flask-cors")
    exit(1)

# Setup
app = Flask(__name__)
CORS(app)
logger = logging.getLogger(__name__)

# Get project root
PROJECT_ROOT = Path(__file__).parent
DESIGN_REPLICA_PATH = PROJECT_ROOT / "design_replica"

# Pages mapping
PAGES = {
    'dashboard': 'executive_dashboard/code.html',
    'positions': 'positions_order_book/code.html',
    'analytics': 'strategy_analytics/code.html',
    'config': 'configuration_settings/code.html',
    'logs': 'system_logs_monitoring/code.html',
    'design': 'technical_trading_interface/DESIGN.md',
}


@app.route('/')
def index():
    """Serve main dashboard"""
    html_file = DESIGN_REPLICA_PATH / PAGES['dashboard']
    if html_file.exists():
        with open(html_file, 'r', encoding='utf-8') as f:
            return f.read()
    return "<h1>Dashboard</h1><p>Design files not found</p>", 404


@app.route('/dashboard')
def dashboard():
    """Executive dashboard"""
    html_file = DESIGN_REPLICA_PATH / PAGES['dashboard']
    if html_file.exists():
        with open(html_file, 'r', encoding='utf-8') as f:
            return f.read()
    return "<h1>Dashboard</h1>", 404


@app.route('/positions')
def positions():
    """Positions and order book"""
    html_file = DESIGN_REPLICA_PATH / PAGES['positions']
    if html_file.exists():
        with open(html_file, 'r', encoding='utf-8') as f:
            return f.read()
    return "<h1>Positions</h1>", 404


@app.route('/analytics')
def analytics():
    """Strategy analytics"""
    html_file = DESIGN_REPLICA_PATH / PAGES['analytics']
    if html_file.exists():
        with open(html_file, 'r', encoding='utf-8') as f:
            return f.read()
    return "<h1>Analytics</h1>", 404


@app.route('/configuration')
def configuration():
    """System configuration"""
    html_file = DESIGN_REPLICA_PATH / PAGES['config']
    if html_file.exists():
        with open(html_file, 'r', encoding='utf-8') as f:
            return f.read()
    return "<h1>Configuration</h1>", 404


@app.route('/logs')
def logs():
    """System logs and monitoring"""
    html_file = DESIGN_REPLICA_PATH / PAGES['logs']
    if html_file.exists():
        with open(html_file, 'r', encoding='utf-8') as f:
            return f.read()
    return "<h1>System Logs</h1>", 404


@app.route('/api/status')
def api_status():
    """Get system status"""
    return jsonify({
        'status': 'online',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0',
        'mode': 'development',
    })


@app.route('/api/bot-status')
def api_bot_status():
    """Get trading bot status"""
    return jsonify({
        'running': True,
        'mode': 'testnet',
        'positions': 0,
        'balance': 10000.00,
        'equity': 10000.00,
        'pnl': 0.00,
        'timestamp': datetime.now().isoformat(),
    })


@app.route('/api/design-spec')
def api_design_spec():
    """Get design specifications"""
    try:
        design_file = DESIGN_REPLICA_PATH / 'technical_trading_interface' / 'DESIGN.md'
        if design_file.exists():
            with open(design_file, 'r', encoding='utf-8') as f:
                content = f.read()
                # Return first 1000 chars as summary
                return jsonify({
                    'name': 'Technical Trading Interface',
                    'description': 'Professional trading dashboard design system',
                    'content_preview': content[:1000],
                    'full_path': str(design_file),
                })
    except Exception as e:
        logger.error(f"Error reading design spec: {e}")
    
    return jsonify({'error': 'Design spec not found'}), 404


@app.route('/api/components')
def api_components():
    """List available design components"""
    components = []
    for name, path in PAGES.items():
        component_path = DESIGN_REPLICA_PATH / path
        components.append({
            'name': name,
            'path': path,
            'exists': component_path.exists(),
            'url': f'/{name}' if name != 'design' else '/api/design-spec'
        })
    
    return jsonify(components)


@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy'}), 200


@app.errorhandler(404)
def not_found(error):
    """404 handler"""
    return jsonify({'error': 'Not found'}), 404


@app.errorhandler(500)
def server_error(error):
    """500 handler"""
    return jsonify({'error': 'Internal server error'}), 500


def run_web_server(host='127.0.0.1', port=5000):
    """
    Run the Flask web server
    
    Args:
        host: Server host (default: localhost)
        port: Server port (default: 5000)
    """
    print("\n" + "="*60)
    print("TRADING BOT - WEB FRONTEND")
    print("="*60)
    print("\nWeb Server Starting")
    print(f"  URL: http://{host}:{port}")
    print(f"  Dashboard: http://{host}:{port}/dashboard")
    print(f"  Positions: http://{host}:{port}/positions")
    print(f"  Analytics: http://{host}:{port}/analytics")
    print(f"  Config: http://{host}:{port}/configuration")
    print(f"  Logs: http://{host}:{port}/logs")
    print(f"\n  API Status: http://{host}:{port}/api/status")
    print(f"  API Components: http://{host}:{port}/api/components")
    print(f"\nPress Ctrl+C to stop the server\n")
    print("="*60 + "\n")
    
    try:
        app.run(host=host, port=port, debug=False, threaded=True)
    except KeyboardInterrupt:
        print("\n\nWeb server stopped by user")
    except Exception as e:
        print(f"\nError running web server: {e}")
        logger.error(f"Web server error: {e}")


if __name__ == '__main__':
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    run_web_server()
