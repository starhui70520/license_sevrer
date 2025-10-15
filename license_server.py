#!/usr/bin/env python3
"""
License Server - A simple license management system
Generates and validates software licenses using JWT tokens
"""

import os
import json
import datetime
from flask import Flask, request, jsonify
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend
import jwt

app = Flask(__name__)

# Configuration
PRIVATE_KEY_FILE = 'private_key.pem'
PUBLIC_KEY_FILE = 'public_key.pem'
LICENSES_FILE = 'licenses.json'

# Storage for licenses
licenses_db = {}


def generate_key_pair():
    """Generate RSA key pair for signing licenses"""
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )
    
    # Save private key
    with open(PRIVATE_KEY_FILE, 'wb') as f:
        f.write(private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ))
    
    # Save public key
    public_key = private_key.public_key()
    with open(PUBLIC_KEY_FILE, 'wb') as f:
        f.write(public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ))
    
    return private_key, public_key


def load_private_key():
    """Load private key from file"""
    if not os.path.exists(PRIVATE_KEY_FILE):
        return None
    
    with open(PRIVATE_KEY_FILE, 'rb') as f:
        return serialization.load_pem_private_key(
            f.read(),
            password=None,
            backend=default_backend()
        )


def load_public_key():
    """Load public key from file"""
    if not os.path.exists(PUBLIC_KEY_FILE):
        return None
    
    with open(PUBLIC_KEY_FILE, 'rb') as f:
        return serialization.load_pem_public_key(
            f.read(),
            backend=default_backend()
        )


def load_licenses():
    """Load licenses from file"""
    global licenses_db
    if os.path.exists(LICENSES_FILE):
        with open(LICENSES_FILE, 'r') as f:
            licenses_db = json.load(f)
    else:
        licenses_db = {}


def save_licenses():
    """Save licenses to file"""
    with open(LICENSES_FILE, 'w') as f:
        json.dump(licenses_db, f, indent=2)


def generate_license(customer_name, product, expiry_days=365, features=None):
    """Generate a new license"""
    private_key = load_private_key()
    if not private_key:
        raise ValueError("Private key not found. Please initialize the server first.")
    
    # Load existing licenses
    load_licenses()
    
    # Create license data
    now = datetime.datetime.now(datetime.timezone.utc)
    expiry = now + datetime.timedelta(days=expiry_days)
    
    license_data = {
        'customer': customer_name,
        'product': product,
        'issued_at': now.isoformat(),
        'expires_at': expiry.isoformat(),
        'features': features or []
    }
    
    # Sign license with private key
    private_key_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    
    token = jwt.encode(
        license_data,
        private_key_pem,
        algorithm='RS256'
    )
    
    # Store license
    license_id = f"{customer_name}_{product}_{now.timestamp()}"
    licenses_db[license_id] = {
        'token': token,
        'data': license_data
    }
    save_licenses()
    
    return token, license_id


def validate_license(token):
    """Validate a license token"""
    public_key = load_public_key()
    if not public_key:
        raise ValueError("Public key not found. Please initialize the server first.")
    
    public_key_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    
    try:
        # Decode and verify token
        decoded = jwt.decode(
            token,
            public_key_pem,
            algorithms=['RS256']
        )
        
        # Check expiry
        expires_at = datetime.datetime.fromisoformat(decoded['expires_at'])
        now = datetime.datetime.now(datetime.timezone.utc)
        # Make expires_at timezone-aware if it isn't already
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=datetime.timezone.utc)
        if now > expires_at:
            return False, "License expired", None
        
        return True, "License valid", decoded
    except jwt.ExpiredSignatureError:
        return False, "License expired", None
    except jwt.InvalidTokenError as e:
        return False, f"Invalid license: {str(e)}", None


# API Endpoints

@app.route('/')
def index():
    """Health check endpoint"""
    return jsonify({
        'status': 'running',
        'service': 'License Server',
        'version': '1.0.0'
    })


@app.route('/initialize', methods=['POST'])
def initialize():
    """Initialize the server by generating key pairs"""
    try:
        if os.path.exists(PRIVATE_KEY_FILE) and os.path.exists(PUBLIC_KEY_FILE):
            return jsonify({
                'error': 'Server already initialized. Delete key files to reinitialize.'
            }), 400
        
        generate_key_pair()
        return jsonify({
            'message': 'Server initialized successfully',
            'public_key_file': PUBLIC_KEY_FILE,
            'private_key_file': PRIVATE_KEY_FILE
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/license/generate', methods=['POST'])
def api_generate_license():
    """Generate a new license"""
    try:
        data = request.get_json()
        
        if not data or 'customer' not in data or 'product' not in data:
            return jsonify({
                'error': 'Missing required fields: customer and product'
            }), 400
        
        customer = data['customer']
        product = data['product']
        expiry_days = data.get('expiry_days', 365)
        features = data.get('features', [])
        
        token, license_id = generate_license(customer, product, expiry_days, features)
        
        return jsonify({
            'message': 'License generated successfully',
            'license_id': license_id,
            'token': token,
            'customer': customer,
            'product': product,
            'expiry_days': expiry_days,
            'features': features
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/license/validate', methods=['POST'])
def api_validate_license():
    """Validate a license token"""
    try:
        data = request.get_json()
        
        if not data or 'token' not in data:
            return jsonify({
                'error': 'Missing required field: token'
            }), 400
        
        token = data['token']
        is_valid, message, decoded = validate_license(token)
        
        response = {
            'valid': is_valid,
            'message': message
        }
        
        if decoded:
            response['license_data'] = decoded
        
        return jsonify(response)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/licenses', methods=['GET'])
def list_licenses():
    """List all generated licenses"""
    return jsonify({
        'count': len(licenses_db),
        'licenses': [
            {
                'id': lid,
                'customer': data['data']['customer'],
                'product': data['data']['product'],
                'issued_at': data['data']['issued_at'],
                'expires_at': data['data']['expires_at']
            }
            for lid, data in licenses_db.items()
        ]
    })


@app.route('/public-key', methods=['GET'])
def get_public_key():
    """Get the public key for client-side validation"""
    try:
        if not os.path.exists(PUBLIC_KEY_FILE):
            return jsonify({
                'error': 'Server not initialized. Please initialize first.'
            }), 404
        
        with open(PUBLIC_KEY_FILE, 'r') as f:
            public_key = f.read()
        
        return jsonify({
            'public_key': public_key
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def main():
    """Main entry point"""
    load_licenses()
    
    print("=" * 60)
    print("License Server Starting...")
    print("=" * 60)
    
    if not os.path.exists(PRIVATE_KEY_FILE) or not os.path.exists(PUBLIC_KEY_FILE):
        print("\n⚠️  WARNING: Server not initialized!")
        print("Please call POST /initialize to generate key pairs")
    else:
        print("\n✓ Server initialized and ready")
    
    print("\nAPI Endpoints:")
    print("  GET  /              - Health check")
    print("  POST /initialize    - Initialize server (generate keys)")
    print("  POST /license/generate - Generate new license")
    print("  POST /license/validate - Validate license")
    print("  GET  /licenses      - List all licenses")
    print("  GET  /public-key    - Get public key")
    print("\n" + "=" * 60)
    
    # Get debug mode from environment variable (default: False for security)
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    if not debug_mode:
        print("\n⚠️  NOTE: Running in production mode. Set FLASK_DEBUG=True for debug mode.")
    
    app.run(host='0.0.0.0', port=5000, debug=debug_mode)


if __name__ == '__main__':
    main()
