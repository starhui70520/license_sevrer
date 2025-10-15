#!/bin/bash

echo "Starting License Server Integration Test"
echo "=========================================="

# Start the server in the background
python license_server.py &
SERVER_PID=$!

# Wait for server to start
echo "Waiting for server to start..."
sleep 3

# Test health endpoint
echo ""
echo "Testing health endpoint..."
curl -s http://localhost:5000/ | python -m json.tool

# Initialize the server
echo ""
echo "Initializing server..."
curl -s -X POST http://localhost:5000/initialize | python -m json.tool

# Generate a license
echo ""
echo "Generating a license..."
curl -s -X POST http://localhost:5000/license/generate \
  -H "Content-Type: application/json" \
  -d '{
    "customer": "Test Company",
    "product": "Test Product",
    "expiry_days": 365,
    "features": ["feature1", "feature2"]
  }' | python -m json.tool > /tmp/license_response.json

cat /tmp/license_response.json

# Extract the token
TOKEN=$(python -c "import json; data=json.load(open('/tmp/license_response.json')); print(data.get('token', ''))")

# Validate the license
echo ""
echo "Validating the license..."
curl -s -X POST http://localhost:5000/license/validate \
  -H "Content-Type: application/json" \
  -d "{\"token\": \"$TOKEN\"}" | python -m json.tool

# List all licenses
echo ""
echo "Listing all licenses..."
curl -s http://localhost:5000/licenses | python -m json.tool

# Get public key
echo ""
echo "Getting public key..."
curl -s http://localhost:5000/public-key | python -m json.tool | head -5

# Stop the server
echo ""
echo "Stopping server..."
kill $SERVER_PID
wait $SERVER_PID 2>/dev/null

echo ""
echo "Integration test completed!"
echo "=========================================="
