# Q-Storm Platform - Environment Setup Guide

Complete guide for configuring environment variables for Q-Storm Platform deployment.

**Version**: 1.0.0
**Last Updated**: 2025-10-20
**Target**: Production & Development Environments

---

## Table of Contents

1. [Environment Variables Overview](#environment-variables-overview)
2. [Required Variables](#required-variables)
3. [Optional Variables](#optional-variables)
4. [Environment-Specific Configuration](#environment-specific-configuration)
5. [API Key Management](#api-key-management)
6. [Configuration Validation](#configuration-validation)
7. [Troubleshooting](#troubleshooting)

---

## Environment Variables Overview

### Variable Categories

| Category | Variables | Purpose |
|----------|-----------|---------|
| **Application** | `FLASK_ENV`, `FLASK_APP` | Runtime environment control |
| **Authentication** | `QSTORM_API_KEY` | API security (production only) |
| **File Upload** | `MAX_FILE_SIZE_MB`, `UPLOAD_FOLDER` | File processing limits |
| **Database** | `DATABASE_PATH` | SQLite database location |
| **External APIs** | `OPENAI_API_KEY` | Optional third-party integrations |

---

## Required Variables

### 1. FLASK_ENV

**Purpose**: Controls application environment and authentication requirements

**Values**: `development` | `production`

**Default**: `development`

**Impact**:
- `development`: No authentication required, debug mode enabled
- `production`: API key authentication required, debug mode disabled

```bash
# Development
export FLASK_ENV=development

# Production (Render.com)
FLASK_ENV=production
```

### 2. QSTORM_API_KEY

**Purpose**: API authentication key (required in production)

**Format**: 32-character URL-safe random string

**Requirements**:
- Minimum length: 20 characters
- Generated using cryptographically secure random generator
- Required when `FLASK_ENV=production`
- Optional when `FLASK_ENV=development`

**Generation**:
```bash
# Generate secure API key
python3 -c "from auth import generate_api_key; print(generate_api_key())"

# Example output
Xa7K9mP3nQ2vR8tY5wZ1aB4cD6eF0gH2
```

**Usage in Requests**:
```bash
# Include in HTTP headers
curl -X POST https://your-app.onrender.com/api/v1/analysis/timeseries \
  -H "X-API-Key: Xa7K9mP3nQ2vR8tY5wZ1aB4cD6eF0gH2" \
  -H "Content-Type: application/json" \
  -d '{"session_id": "test-session"}'
```

### 3. MAX_FILE_SIZE_MB

**Purpose**: Maximum file upload size limit

**Format**: Integer (1-1000)

**Default**: `200`

**Validation**: Must be between 1 and 1000 MB

```bash
# Standard configuration
export MAX_FILE_SIZE_MB=200

# Low-resource environment
export MAX_FILE_SIZE_MB=50

# High-capacity environment
export MAX_FILE_SIZE_MB=500
```

### 4. DATABASE_PATH

**Purpose**: SQLite database file location

**Format**: Absolute file path

**Default**: `data/qstorm.db`

**Render.com Configuration**:
```bash
# Use persistent disk mount path
DATABASE_PATH=/opt/render/project/src/data/qstorm.db
```

**Local Development**:
```bash
# Relative path from project root
DATABASE_PATH=data/qstorm.db
```

### 5. UPLOAD_FOLDER

**Purpose**: Directory for temporary file uploads

**Format**: Absolute directory path

**Default**: `uploads`

**Render.com Configuration**:
```bash
# Temporary disk location
UPLOAD_FOLDER=/opt/render/project/src/uploads
```

**Local Development**:
```bash
# Relative path from project root
UPLOAD_FOLDER=uploads
```

---

## Optional Variables

### 1. OPENAI_API_KEY

**Purpose**: OpenAI API integration (future features)

**Format**: `sk-` prefixed string

**Status**: Not currently used in Phase 1

**Validation**: Must start with `sk-` if provided

```bash
# Optional - for future AI features
export OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### 2. FLASK_APP

**Purpose**: Flask application entry point

**Default**: `app_improved.py`

```bash
export FLASK_APP=app_improved.py
```

### 3. PYTHONUNBUFFERED

**Purpose**: Force Python stdout/stderr to be unbuffered

**Value**: `1`

**Benefit**: Real-time log output in deployment environments

```bash
export PYTHONUNBUFFERED=1
```

---

## Environment-Specific Configuration

### Development Environment

**File**: `.env` (create in project root)

```bash
# Development Environment Configuration
FLASK_ENV=development
MAX_FILE_SIZE_MB=200
DATABASE_PATH=data/qstorm.db
UPLOAD_FOLDER=uploads

# Optional: Authentication (not enforced in development)
# QSTORM_API_KEY=dev-test-key-12345678

# Optional: External APIs
# OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxx
```

**Load in Python**:
```python
# Option 1: Manual loading with python-dotenv
from dotenv import load_dotenv
load_dotenv()

# Option 2: Export before running
source .env && python app_improved.py
```

### Production Environment (Render.com)

**Configuration Location**: Render Dashboard → Environment Tab

**Required Variables**:
```yaml
FLASK_ENV=production
QSTORM_API_KEY=<GENERATE_SECURE_KEY>
MAX_FILE_SIZE_MB=200
DATABASE_PATH=/opt/render/project/src/data/qstorm.db
UPLOAD_FOLDER=/opt/render/project/src/uploads
PYTHONUNBUFFERED=1
FLASK_APP=app_improved.py
```

**Setup Steps**:
1. Navigate to Render Dashboard
2. Select your web service
3. Click "Environment" tab
4. Add each variable with appropriate value
5. Click "Save Changes"
6. Service will auto-redeploy with new configuration

---

## API Key Management

### Generation Best Practices

**Security Requirements**:
- Use `secrets.token_urlsafe()` for cryptographic security
- Minimum 32 bytes of entropy (43 characters)
- Never commit API keys to version control
- Rotate keys periodically (every 90 days recommended)

**Generation Methods**:

```bash
# Method 1: Using auth module (recommended)
python3 -c "from auth import generate_api_key; print(generate_api_key())"

# Method 2: Using Python secrets directly
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# Method 3: Using openssl
openssl rand -base64 32 | tr -d "=+/" | cut -c1-43
```

### Key Storage

**Development**:
- Store in `.env` file (gitignored)
- Share securely with team via password manager
- Document key owner and generation date

**Production**:
- Store in Render.com environment variables
- Enable secret sync across services if needed
- Document in secure internal wiki or password manager

**Never**:
- ❌ Commit to Git repository
- ❌ Share via email or Slack
- ❌ Hardcode in application code
- ❌ Log to console or files

### Key Rotation

**Rotation Steps**:
1. Generate new API key using approved method
2. Update Render.com environment variable
3. Update all API clients with new key
4. Monitor logs for authentication failures
5. Document rotation date and reason

**Rotation Schedule**:
- **Routine**: Every 90 days
- **Incident**: Immediately if key compromised
- **Personnel**: When team members leave
- **Audit**: After security audits or penetration tests

---

## Configuration Validation

### Automated Validation

The application automatically validates configuration on startup:

```python
# config.py validates on import
from config import validate_env_config

try:
    validate_env_config()
    print("✅ Configuration valid")
except ValueError as e:
    print(f"❌ Configuration error: {e}")
    exit(1)
```

### Manual Validation

**Test Configuration**:
```bash
# Validate environment variables
python3 -c "
from config import validate_env_config
try:
    validate_env_config()
    print('✅ All environment variables valid')
except ValueError as e:
    print(f'❌ Validation failed: {e}')
"
```

**Expected Output (Success)**:
```
✅ All environment variables valid
```

**Expected Output (Failure)**:
```
❌ Validation failed: QSTORM_API_KEY is required in production environment
```

### Validation Rules

**MAX_FILE_SIZE_MB**:
- ✅ Must be integer
- ✅ Must be between 1 and 1000
- ❌ Cannot be string or float
- ❌ Cannot be negative or zero

**QSTORM_API_KEY** (production only):
- ✅ Must be set when `FLASK_ENV=production`
- ✅ Must be at least 20 characters
- ✅ Should be cryptographically random
- ❌ Cannot be empty string
- ❌ Cannot be weak (e.g., "password", "test123")

**OPENAI_API_KEY** (if provided):
- ✅ Must start with `sk-`
- ✅ Must be valid string format
- ❌ Cannot be malformed or incorrect prefix

**DATABASE_PATH**:
- ✅ Parent directory must exist or be creatable
- ✅ Must have write permissions
- ❌ Cannot be read-only filesystem
- ❌ Cannot contain invalid path characters

---

## Troubleshooting

### Common Issues

#### 1. Authentication Failures

**Symptom**:
```json
{
  "success": false,
  "error": "API key required",
  "code": "AUTH_MISSING_API_KEY"
}
```

**Solutions**:
- Verify `X-API-Key` header is included in request
- Check API key matches `QSTORM_API_KEY` environment variable
- Ensure `FLASK_ENV=production` if authentication is required
- Validate key has not been truncated or modified

#### 2. Configuration Validation Errors

**Symptom**:
```
[ERROR] Environment configuration invalid: MAX_FILE_SIZE_MB must be 1-1000, got 0
```

**Solutions**:
- Check environment variable types (string vs integer)
- Verify values are within valid ranges
- Ensure required variables are set for production
- Review `.env` file syntax (no quotes needed for most values)

#### 3. Database Connection Failures

**Symptom**:
```json
{
  "status": "unhealthy",
  "error": "Service unavailable"
}
```

**Solutions**:
- Verify `DATABASE_PATH` directory exists
- Check write permissions on database file
- Ensure persistent disk is mounted (Render.com)
- Validate SQLite version compatibility

#### 4. File Upload Errors

**Symptom**:
```json
{
  "success": false,
  "error": "File too large"
}
```

**Solutions**:
- Verify `MAX_FILE_SIZE_MB` is set appropriately
- Check `UPLOAD_FOLDER` exists and is writable
- Ensure sufficient disk space available
- Review Nginx/proxy upload size limits (Render.com)

### Health Check Verification

**Test Health Endpoint**:
```bash
# Local development
curl http://localhost:5000/health

# Production (Render.com)
curl https://your-app.onrender.com/health
```

**Expected Response (Healthy)**:
```json
{
  "status": "healthy",
  "service": "qstorm-platform",
  "version": "1.0.0",
  "timestamp": "2025-10-20T10:30:00.000Z",
  "checks": {
    "database": "ok",
    "filesystem": "ok"
  }
}
```

**Response (Unhealthy)**:
```json
{
  "status": "unhealthy",
  "error": "Required directory missing: data",
  "timestamp": "2025-10-20T10:30:00.000Z"
}
```

### Debug Mode

**Enable Detailed Logging**:
```bash
# Development only - never in production
export FLASK_ENV=development
export FLASK_DEBUG=1

python app_improved.py
```

**View Configuration at Runtime**:
```python
import config
print(f"Environment: {config.FLASK_ENV}")
print(f"Auth Required: {config.REQUIRE_AUTH}")
print(f"Max File Size: {config.MAX_FILE_SIZE_MB}MB")
print(f"Database: {config.BASE_DIR / 'data' / 'qstorm.db'}")
```

---

## Security Best Practices

### Environment Variable Security

**DO**:
- ✅ Use `.env` files for local development (gitignored)
- ✅ Use platform environment variables for production (Render.com)
- ✅ Rotate API keys regularly (every 90 days)
- ✅ Use cryptographically secure random generation
- ✅ Limit access to environment variables to necessary personnel
- ✅ Audit access logs periodically

**DON'T**:
- ❌ Commit `.env` files to Git
- ❌ Share API keys via insecure channels (email, Slack, etc.)
- ❌ Use weak or predictable API keys
- ❌ Reuse API keys across environments
- ❌ Log API keys in application logs
- ❌ Expose API keys in error messages or stack traces

### Production Checklist

Before deploying to production:

- [ ] Generate secure `QSTORM_API_KEY` using approved method
- [ ] Set `FLASK_ENV=production`
- [ ] Configure all required environment variables in Render.com
- [ ] Verify database persistent disk is configured
- [ ] Test health check endpoint responds correctly
- [ ] Validate authentication works with test API call
- [ ] Review CORS origins and update for production domain
- [ ] Enable HTTPS (automatic on Render.com)
- [ ] Document API key storage location securely
- [ ] Set up monitoring and alerting

---

## Support & References

### Documentation
- [Render.com Environment Variables](https://render.com/docs/environment-variables)
- [Flask Configuration Handling](https://flask.palletsprojects.com/en/2.3.x/config/)
- [Python Secrets Module](https://docs.python.org/3/library/secrets.html)

### Related Files
- `config.py`: Configuration validation logic
- `auth.py`: API key authentication implementation
- `render.yaml`: Render.com deployment configuration
- `DEPLOY_GUIDE.md`: Deployment instructions

### Contact
For environment configuration issues:
1. Check this guide's troubleshooting section
2. Review application logs in Render Dashboard
3. Verify health check endpoint status
4. Consult DEPLOY_GUIDE.md for deployment-specific issues
