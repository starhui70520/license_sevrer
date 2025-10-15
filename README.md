# License Server

A simple, lightweight license management system for software applications. This server provides REST API endpoints for generating, validating, and managing software licenses using JWT tokens and RSA encryption.

## Features

- **Secure License Generation**: Uses RSA-2048 encryption to sign licenses
- **JWT-Based Tokens**: Industry-standard JSON Web Tokens for license distribution
- **Expiration Management**: Set custom expiration dates for licenses
- **Feature Flags**: Support for feature-based licensing
- **REST API**: Easy-to-use HTTP endpoints
- **Client Validation**: Distribute public key for offline validation

## Installation

### Prerequisites

- Python 3.7 or higher
- pip package manager

### Setup

1. Clone the repository:
```bash
git clone https://github.com/starhui70520/license_sevrer.git
cd license_sevrer
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Starting the Server

Run the license server:

```bash
python license_server.py
```

The server will start on `http://localhost:5000`

For development with debug mode enabled:

```bash
FLASK_DEBUG=True python license_server.py
```

### Initialize the Server

Before generating licenses, initialize the server to create RSA key pairs:

```bash
curl -X POST http://localhost:5000/initialize
```

This creates:
- `private_key.pem` - Used for signing licenses (keep secure!)
- `public_key.pem` - Used for validating licenses (can be distributed)

### API Endpoints

#### 1. Health Check
```bash
GET /
```

**Response:**
```json
{
  "status": "running",
  "service": "License Server",
  "version": "1.0.0"
}
```

#### 2. Initialize Server
```bash
POST /initialize
```

**Response:**
```json
{
  "message": "Server initialized successfully",
  "public_key_file": "public_key.pem",
  "private_key_file": "private_key.pem"
}
```

#### 3. Generate License
```bash
POST /license/generate
Content-Type: application/json

{
  "customer": "Acme Corporation",
  "product": "Enterprise Suite",
  "expiry_days": 365,
  "features": ["feature1", "feature2", "premium"]
}
```

**Response:**
```json
{
  "message": "License generated successfully",
  "license_id": "Acme Corporation_Enterprise Suite_1697384400.123",
  "token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "customer": "Acme Corporation",
  "product": "Enterprise Suite",
  "expiry_days": 365,
  "features": ["feature1", "feature2", "premium"]
}
```

#### 4. Validate License
```bash
POST /license/validate
Content-Type: application/json

{
  "token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Response:**
```json
{
  "valid": true,
  "message": "License valid",
  "license_data": {
    "customer": "Acme Corporation",
    "product": "Enterprise Suite",
    "issued_at": "2023-10-15T12:00:00",
    "expires_at": "2024-10-15T12:00:00",
    "features": ["feature1", "feature2", "premium"]
  }
}
```

#### 5. List All Licenses
```bash
GET /licenses
```

**Response:**
```json
{
  "count": 1,
  "licenses": [
    {
      "id": "Acme Corporation_Enterprise Suite_1697384400.123",
      "customer": "Acme Corporation",
      "product": "Enterprise Suite",
      "issued_at": "2023-10-15T12:00:00",
      "expires_at": "2024-10-15T12:00:00"
    }
  ]
}
```

#### 6. Get Public Key
```bash
GET /public-key
```

**Response:**
```json
{
  "public_key": "-----BEGIN PUBLIC KEY-----\nMIIBIjANBgkq..."
}
```

## Client Example

A complete client example is provided in `client_example.py`:

```bash
python client_example.py
```

This demonstrates:
- Server initialization
- License generation
- License validation
- Listing licenses
- Retrieving the public key

## Integration Example

### Python Client Integration

```python
import requests
import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend

# Get the public key from the server
response = requests.get('http://localhost:5000/public-key')
public_key_pem = response.json()['public_key']

# Load the public key
public_key = serialization.load_pem_public_key(
    public_key_pem.encode(),
    backend=default_backend()
)

# Validate a license token
def validate_license_offline(token):
    try:
        decoded = jwt.decode(
            token,
            public_key,
            algorithms=['RS256']
        )
        return True, decoded
    except jwt.InvalidTokenError:
        return False, None

# Use in your application
is_valid, license_data = validate_license_offline(token)
if is_valid:
    print(f"Licensed to: {license_data['customer']}")
    print(f"Features: {license_data['features']}")
else:
    print("Invalid license!")
```

## Security Considerations

1. **Private Key Protection**: Keep `private_key.pem` secure and never distribute it
2. **HTTPS**: Use HTTPS in production to protect API communications
3. **Authentication**: Add API authentication for production deployments
4. **Access Control**: Restrict access to license generation endpoints
5. **Key Rotation**: Implement key rotation policies for long-term deployments
6. **Debug Mode**: Disable debug mode in production by setting `FLASK_DEBUG=False` environment variable
7. **Production Server**: Use a production WSGI server (e.g., Gunicorn, uWSGI) instead of Flask's development server

## File Structure

```
license_sevrer/
├── README.md                 # This file
├── requirements.txt          # Python dependencies
├── license_server.py         # Main server application
├── client_example.py         # Example client usage
├── .gitignore               # Git ignore rules
├── private_key.pem          # Generated private key (not in git)
├── public_key.pem           # Generated public key (not in git)
└── licenses.json            # License database (not in git)
```

## Development

### Running Tests

```bash
# Install test dependencies
pip install pytest requests

# Run tests
pytest
```

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is open source and available under the MIT License.

## Support

For issues, questions, or contributions, please visit:
https://github.com/starhui70520/license_sevrer

## Changelog

### Version 1.0.0
- Initial release
- JWT-based license generation
- RSA-2048 encryption
- REST API endpoints
- Feature-based licensing
- License expiration management