#!/usr/bin/env python3
"""
License Client Example - Demonstrates how to use the license server
"""

import requests
import json

# Server configuration
SERVER_URL = "http://localhost:5000"


def initialize_server():
    """Initialize the license server"""
    print("Initializing server...")
    response = requests.post(f"{SERVER_URL}/initialize")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}\n")
    return response.json()


def generate_license(customer, product, expiry_days=365, features=None):
    """Generate a new license"""
    print(f"Generating license for {customer} - {product}...")
    data = {
        'customer': customer,
        'product': product,
        'expiry_days': expiry_days,
        'features': features or []
    }
    response = requests.post(f"{SERVER_URL}/license/generate", json=data)
    print(f"Status: {response.status_code}")
    result = response.json()
    print(f"Response: {json.dumps(result, indent=2)}\n")
    return result


def validate_license(token):
    """Validate a license token"""
    print(f"Validating license...")
    data = {'token': token}
    response = requests.post(f"{SERVER_URL}/license/validate", json=data)
    print(f"Status: {response.status_code}")
    result = response.json()
    print(f"Response: {json.dumps(result, indent=2)}\n")
    return result


def list_licenses():
    """List all licenses"""
    print("Listing all licenses...")
    response = requests.get(f"{SERVER_URL}/licenses")
    print(f"Status: {response.status_code}")
    result = response.json()
    print(f"Response: {json.dumps(result, indent=2)}\n")
    return result


def get_public_key():
    """Get the public key"""
    print("Getting public key...")
    response = requests.get(f"{SERVER_URL}/public-key")
    print(f"Status: {response.status_code}")
    result = response.json()
    print(f"Response: {json.dumps(result, indent=2)}\n")
    return result


def main():
    """Main example flow"""
    print("=" * 60)
    print("License Server Client Example")
    print("=" * 60 + "\n")
    
    try:
        # Check server health
        print("Checking server health...")
        response = requests.get(f"{SERVER_URL}/")
        print(f"Server Status: {response.json()}\n")
        
        # Initialize server (only needed once)
        try:
            initialize_server()
        except Exception as e:
            print(f"Note: {e} (Server may already be initialized)\n")
        
        # Generate a license
        license_result = generate_license(
            customer="Acme Corporation",
            product="Enterprise Suite",
            expiry_days=365,
            features=["feature1", "feature2", "premium"]
        )
        
        # Extract token
        token = license_result.get('token')
        
        if token:
            # Validate the license
            validate_license(token)
            
            # List all licenses
            list_licenses()
            
            # Get public key
            get_public_key()
        
        print("=" * 60)
        print("Example completed successfully!")
        print("=" * 60)
        
    except requests.exceptions.ConnectionError:
        print("ERROR: Cannot connect to server. Please make sure the server is running.")
        print("Start the server with: python license_server.py")
    except Exception as e:
        print(f"ERROR: {e}")


if __name__ == '__main__':
    main()
