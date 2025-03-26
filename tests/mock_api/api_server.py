"""
Mock API server for testing
"""
from flask import Flask, jsonify, request
import time
from typing import Dict, List
import random
from functools import wraps

app = Flask(__name__)

# Load test data
from tests.config.test_config import (
    TEST_PROPERTIES,
    TEST_TAX_RECORDS,
    TEST_PERMITS,
    TEST_UTILITIES,
    TEST_API_KEYS
)

# Rate limiting configuration
RATE_LIMITS = {
    'property_api': {'calls': 0, 'reset_time': time.time(), 'limit': 100},
    'tax_api': {'calls': 0, 'reset_time': time.time(), 'limit': 50},
    'permit_api': {'calls': 0, 'reset_time': time.time(), 'limit': 30},
    'utility_api': {'calls': 0, 'reset_time': time.time(), 'limit': 20}
}

def require_api_key(api_name: str):
    """
    Decorator to check API key
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            api_key = request.headers.get('X-API-Key')
            if not api_key:
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 401,
                        'message': 'API key required'
                    }
                }), 401

            if api_key != TEST_API_KEYS[api_name]:
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 401,
                        'message': 'Invalid API key'
                    }
                }), 401

            return func(*args, **kwargs)
        return wrapper
    return decorator

def check_rate_limit(api_name: str):
    """
    Decorator to check rate limits
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            current_time = time.time()
            rate_limit = RATE_LIMITS[api_name]

            # Reset counter if time window has passed
            if current_time - rate_limit['reset_time'] > 3600:
                rate_limit['calls'] = 0
                rate_limit['reset_time'] = current_time

            # Check rate limit
            if rate_limit['calls'] >= rate_limit['limit']:
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 429,
                        'message': 'Rate limit exceeded'
                    }
                }), 429

            rate_limit['calls'] += 1
            return func(*args, **kwargs)
        return wrapper
    return decorator

def simulate_latency():
    """
    Simulate random API latency
    """
    time.sleep(random.uniform(0.1, 0.5))

def simulate_error(probability: float = 0.1) -> bool:
    """
    Randomly simulate API errors
    """
    return random.random() < probability

@app.route('/properties', methods=['GET'])
@require_api_key('property_api')
@check_rate_limit('property_api')
def get_properties():
    """
    Mock property API endpoint
    """
    simulate_latency()
    
    if simulate_error():
        return jsonify({
            'success': False,
            'error': {
                'code': 500,
                'message': 'Internal server error'
            }
        }), 500

    # Get query parameters
    address = request.args.get('address')
    property_type = request.args.get('type')

    # Filter properties
    properties = TEST_PROPERTIES
    if address:
        properties = [p for p in properties if address.lower() in p['address'].lower()]
    if property_type:
        properties = [p for p in properties if p['property_type'] == property_type]

    return jsonify({
        'success': True,
        'data': properties,
        'metadata': {
            'total': len(properties),
            'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S%z')
        }
    })

@app.route('/tax', methods=['GET'])
@require_api_key('tax_api')
@check_rate_limit('tax_api')
def get_tax_records():
    """
    Mock tax API endpoint
    """
    simulate_latency()
    
    if simulate_error():
        return jsonify({
            'success': False,
            'error': {
                'code': 500,
                'message': 'Internal server error'
            }
        }), 500

    # Get query parameters
    address = request.args.get('address')
    parcel_id = request.args.get('parcel_id')

    # Filter records
    records = TEST_TAX_RECORDS
    if address:
        records = [r for r in records if address.lower() in r['address'].lower()]
    if parcel_id:
        records = [r for r in records if r['parcel_id'] == parcel_id]

    return jsonify({
        'success': True,
        'data': records,
        'metadata': {
            'total': len(records),
            'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S%z')
        }
    })

@app.route('/permits', methods=['GET'])
@require_api_key('permit_api')
@check_rate_limit('permit_api')
def get_permits():
    """
    Mock permit API endpoint
    """
    simulate_latency()
    
    if simulate_error():
        return jsonify({
            'success': False,
            'error': {
                'code': 500,
                'message': 'Internal server error'
            }
        }), 500

    # Get query parameters
    address = request.args.get('address')
    permit_type = request.args.get('type')
    status = request.args.get('status')

    # Filter permits
    permits = TEST_PERMITS
    if address:
        permits = [p for p in permits if address.lower() in p['address'].lower()]
    if permit_type:
        permits = [p for p in permits if p['type'] == permit_type]
    if status:
        permits = [p for p in permits if p['status'] == status]

    return jsonify({
        'success': True,
        'data': permits,
        'metadata': {
            'total': len(permits),
            'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S%z')
        }
    })

@app.route('/utilities', methods=['GET'])
@require_api_key('utility_api')
@check_rate_limit('utility_api')
def get_utilities():
    """
    Mock utility API endpoint
    """
    simulate_latency()
    
    if simulate_error():
        return jsonify({
            'success': False,
            'error': {
                'code': 500,
                'message': 'Internal server error'
            }
        }), 500

    # Get query parameters
    address = request.args.get('address')
    property_id = request.args.get('property_id')

    # Filter utilities
    utilities = TEST_UTILITIES
    if address:
        utilities = [u for u in utilities if address.lower() in u['address'].lower()]
    if property_id:
        utilities = [u for u in utilities if u['property_id'] == property_id]

    return jsonify({
        'success': True,
        'data': utilities,
        'metadata': {
            'total': len(utilities),
            'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S%z')
        }
    })

@app.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint
    """
    return jsonify({
        'status': 'healthy',
        'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S%z'),
        'rate_limits': {
            name: {
                'calls': info['calls'],
                'limit': info['limit'],
                'reset_time': time.strftime(
                    '%Y-%m-%dT%H:%M:%S%z',
                    time.localtime(info['reset_time'])
                )
            }
            for name, info in RATE_LIMITS.items()
        }
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
