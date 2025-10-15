#!/usr/bin/env python3
"""
Basic tests for license server functionality
"""

import os
import sys
import json
import datetime
import tempfile
import shutil
from unittest.mock import patch

# Import the license server module
import license_server


def test_key_generation():
    """Test RSA key pair generation"""
    print("Testing key pair generation...")
    
    # Create a temporary directory for test files
    test_dir = tempfile.mkdtemp()
    original_dir = os.getcwd()
    
    try:
        os.chdir(test_dir)
        
        # Generate keys
        private_key, public_key = license_server.generate_key_pair()
        
        # Check files were created
        assert os.path.exists('private_key.pem'), "Private key file not created"
        assert os.path.exists('public_key.pem'), "Public key file not created"
        
        # Verify keys can be loaded
        loaded_private = license_server.load_private_key()
        loaded_public = license_server.load_public_key()
        
        assert loaded_private is not None, "Failed to load private key"
        assert loaded_public is not None, "Failed to load public key"
        
        print("✓ Key generation test passed")
        return True
        
    finally:
        os.chdir(original_dir)
        shutil.rmtree(test_dir)


def test_license_generation_and_validation():
    """Test license generation and validation"""
    print("Testing license generation and validation...")
    
    # Create a temporary directory for test files
    test_dir = tempfile.mkdtemp()
    original_dir = os.getcwd()
    
    try:
        os.chdir(test_dir)
        
        # Generate keys first
        license_server.generate_key_pair()
        
        # Generate a license
        customer = "Test Company"
        product = "Test Product"
        expiry_days = 30
        features = ["feature1", "feature2"]
        
        token, license_id = license_server.generate_license(
            customer, product, expiry_days, features
        )
        
        assert token is not None, "Token not generated"
        assert license_id is not None, "License ID not generated"
        
        # Validate the license
        is_valid, message, decoded = license_server.validate_license(token)
        
        assert is_valid, f"License validation failed: {message}"
        assert decoded is not None, "No decoded data returned"
        assert decoded['customer'] == customer, "Customer name mismatch"
        assert decoded['product'] == product, "Product name mismatch"
        assert decoded['features'] == features, "Features mismatch"
        
        print("✓ License generation and validation test passed")
        return True
        
    finally:
        os.chdir(original_dir)
        shutil.rmtree(test_dir)


def test_expired_license():
    """Test that expired licenses are detected"""
    print("Testing expired license detection...")
    
    # Create a temporary directory for test files
    test_dir = tempfile.mkdtemp()
    original_dir = os.getcwd()
    
    try:
        os.chdir(test_dir)
        
        # Generate keys first
        license_server.generate_key_pair()
        
        # Generate a license with negative expiry (already expired)
        token, license_id = license_server.generate_license(
            "Test Company", "Test Product", expiry_days=-1
        )
        
        # Try to validate the expired license
        is_valid, message, decoded = license_server.validate_license(token)
        
        assert not is_valid, "Expired license was marked as valid"
        assert "expired" in message.lower(), "Error message doesn't mention expiration"
        
        print("✓ Expired license detection test passed")
        return True
        
    finally:
        os.chdir(original_dir)
        shutil.rmtree(test_dir)


def test_invalid_token():
    """Test that invalid tokens are rejected"""
    print("Testing invalid token rejection...")
    
    # Create a temporary directory for test files
    test_dir = tempfile.mkdtemp()
    original_dir = os.getcwd()
    
    try:
        os.chdir(test_dir)
        
        # Generate keys first
        license_server.generate_key_pair()
        
        # Try to validate an invalid token
        invalid_token = "invalid.token.here"
        is_valid, message, decoded = license_server.validate_license(invalid_token)
        
        assert not is_valid, "Invalid token was marked as valid"
        assert decoded is None, "Decoded data returned for invalid token"
        
        print("✓ Invalid token rejection test passed")
        return True
        
    finally:
        os.chdir(original_dir)
        shutil.rmtree(test_dir)


def test_license_persistence():
    """Test that licenses are persisted to file"""
    print("Testing license persistence...")
    
    # Create a temporary directory for test files
    test_dir = tempfile.mkdtemp()
    original_dir = os.getcwd()
    
    try:
        os.chdir(test_dir)
        
        # Generate keys first
        license_server.generate_key_pair()
        
        # Generate a license
        token1, license_id1 = license_server.generate_license(
            "Company1", "Product1", 365
        )
        
        # Check that licenses.json was created
        assert os.path.exists('licenses.json'), "Licenses file not created"
        
        # Load licenses from file
        with open('licenses.json', 'r') as f:
            licenses_data = json.load(f)
        
        assert license_id1 in licenses_data, "Generated license not in file"
        assert licenses_data[license_id1]['token'] == token1, "Token mismatch in file"
        
        # Generate another license
        token2, license_id2 = license_server.generate_license(
            "Company2", "Product2", 365
        )
        
        # Reload and verify both licenses exist
        with open('licenses.json', 'r') as f:
            licenses_data = json.load(f)
        
        assert len(licenses_data) == 2, "Expected 2 licenses in database"
        assert license_id1 in licenses_data, "First license missing"
        assert license_id2 in licenses_data, "Second license missing"
        
        print("✓ License persistence test passed")
        return True
        
    finally:
        os.chdir(original_dir)
        shutil.rmtree(test_dir)


def main():
    """Run all tests"""
    print("=" * 60)
    print("License Server Test Suite")
    print("=" * 60 + "\n")
    
    tests = [
        test_key_generation,
        test_license_generation_and_validation,
        test_expired_license,
        test_invalid_token,
        test_license_persistence,
    ]
    
    passed = 0
    failed = 0
    
    for test_func in tests:
        try:
            if test_func():
                passed += 1
        except AssertionError as e:
            print(f"✗ Test failed: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ Test error: {e}")
            failed += 1
        print()
    
    print("=" * 60)
    print(f"Tests completed: {passed} passed, {failed} failed")
    print("=" * 60)
    
    return failed == 0


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
