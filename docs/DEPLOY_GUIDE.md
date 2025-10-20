# Q-Storm Platform - Deployment Guide (Render.com)

Complete step-by-step guide for deploying Q-Storm Platform to Render.com.

**Version**: 1.0.0
**Last Updated**: 2025-10-20
**Platform**: Render.com (Free Tier)
**Target Audience**: DevOps, Developers, System Administrators

---

## Table of Contents

1. [Pre-Deployment Checklist](#pre-deployment-checklist)
2. [Render.com Setup](#rendercom-setup)
3. [Repository Configuration](#repository-configuration)
4. [Service Deployment](#service-deployment)
5. [Environment Configuration](#environment-configuration)
6. [Post-Deployment Verification](#post-deployment-verification)
7. [Monitoring & Maintenance](#monitoring--maintenance)
8. [Troubleshooting](#troubleshooting)
9. [Rollback Procedures](#rollback-procedures)
10. [Upgrade Path](#upgrade-path)

---

## Pre-Deployment Checklist

### Prerequisites

**Required**:
- [ ] GitHub/GitLab repository with Q-Storm Platform code
- [ ] Render.com account (free tier available)
- [ ] Git repository with `render.yaml` configuration
- [ ] Understanding of environment variables (see `ENV_SETUP.md`)
- [ ] Basic Flask application knowledge

**Recommended**:
- [ ] Backup of local development database
- [ ] Documentation of current configuration
- [ ] Test data for post-deployment verification
- [ ] Monitoring/alerting setup plan

### Code Verification

**Run Local Tests**:
```bash
# Verify application starts successfully
python app_improved.py

# Check health endpoint
curl http://localhost:5000/health

# Validate configuration
python3 -c "from config import validate_env_config; validate_env_config()"

# Run test suite (if available)
pytest tests/
```

**Expected Output**:
```
✅ Configuration valid
✅ Database initialized
✅ Flask application running on http://localhost:5000
✅ Health check: {"status": "healthy"}
```

### Repository Preparation

**1. Verify Essential Files**:
```bash
# Check required files exist
ls -la render.yaml requirements.txt app_improved.py config.py auth.py db_manager.py

# Verify .gitignore excludes sensitive files
cat .gitignore | grep -E "(\.env|__pycache__|\.db$)"
```

**2. Update `.gitignore`**:
```gitignore
# Environment variables
.env
.env.local
.env.production

# Database
*.db
*.sqlite
*.sqlite3
data/*.db

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python

# Uploads and outputs
uploads/*
!uploads/.gitkeep
outputs/*
!outputs/.gitkeep

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db
```

**3. Commit and Push**:
```bash
# Ensure all changes are committed
git status
git add render.yaml docs/ENV_SETUP.md docs/DEPLOY_GUIDE.md
git commit -m "Add deployment configuration for Render.com

- Add render.yaml with free tier configuration
- Add /health endpoint for deployment verification
- Add comprehensive environment setup documentation
- Add deployment guide with troubleshooting

🤖 Generated with Claude Code
Co-Authored-By: Claude <noreply@anthropic.com>"

# Push to main branch
git push origin main
```

---

## Render.com Setup

### Account Creation

**1. Sign Up**:
- Navigate to https://render.com
- Click "Get Started" or "Sign Up"
- Choose sign-up method:
  - GitHub (recommended for automatic repo access)
  - GitLab
  - Email

**2. Authorize Repository Access**:
- Select "GitHub" as authentication provider
- Click "Authorize Render"
- Grant access to Q-Storm Platform repository

### Dashboard Overview

**Key Sections**:
- **Services**: Your deployed applications
- **Environment Groups**: Shared environment variables
- **Billing**: Usage and plan details
- **Account Settings**: API keys and security

---

## Repository Configuration

### Connect Repository

**Step 1: New Web Service**
1. Click "New +" button in dashboard
2. Select "Blueprint" (for `render.yaml` deployment)
3. Choose "GitHub" or "GitLab"
4. Search for your repository: `Q-Sorm-Project-α`
5. Click "Connect"

**Step 2: Blueprint Configuration**
- Render detects `render.yaml` automatically
- Review configuration preview
- Verify:
  - Service name: `qstorm-platform`
  - Environment: `python`
  - Plan: `free`
  - Build command: `pip install -r requirements.txt`
  - Start command: `python app_improved.py`

**Step 3: Approve Blueprint**
- Click "Apply Blueprint"
- Render creates service based on `render.yaml`
- Initial build starts automatically

---

## Service Deployment

### Initial Deployment

**Build Process** (5-10 minutes):

```
1. Clone repository → 30 seconds
2. Install dependencies → 2-5 minutes
3. Run build command → 1-2 minutes
4. Start application → 30 seconds
5. Health check verification → 30 seconds
```

**Monitor Build Logs**:
- Navigate to service dashboard
- Click "Logs" tab
- Watch for:
  - `Successfully installed Flask-2.3.0 pandas-2.0.0 ...`
  - `Configuration valid`
  - `Running on http://0.0.0.0:10000`
  - `Health check passed`

**Build Status Indicators**:
- 🟢 **Live**: Deployment successful, service running
- 🟡 **Building**: Installation in progress
- 🔴 **Failed**: Error occurred (check logs)
- ⚪ **Sleeping**: Free tier idle state (after 15 min)

### Deployment Stages

**Stage 1: Repository Clone**
```
Cloning repository from GitHub...
✅ Repository cloned successfully
```

**Stage 2: Environment Setup**
```
Python 3.10 detected
Creating virtual environment...
✅ Virtual environment created
```

**Stage 3: Dependency Installation**
```
Installing dependencies from requirements.txt...
Collecting Flask==2.3.0
Collecting pandas==2.0.0
...
✅ Successfully installed 11 packages
```

**Stage 4: Application Start**
```
Executing: python app_improved.py
✅ Configuration valid
✅ Database initialized at /opt/render/project/src/data/qstorm.db
✅ Flask application running
```

**Stage 5: Health Check**
```
Health check: GET /health
✅ Status 200 OK
Service marked as Live
```

---

## Environment Configuration

### Configure Environment Variables

**Access Environment Settings**:
1. Go to service dashboard
2. Click "Environment" tab
3. Review auto-configured variables from `render.yaml`

### Required Variables Setup

**1. Generate API Key**:
```bash
# Run locally to generate secure key
python3 -c "from auth import generate_api_key; print(generate_api_key())"

# Example output:
# Xa7K9mP3nQ2vR8tY5wZ1aB4cD6eF0gH2
```

**2. Update QSTORM_API_KEY**:
- Find `QSTORM_API_KEY` in environment variables list
- Click "Edit" button
- Replace auto-generated value with your secure key
- Click "Save Changes"

**3. Verify All Variables**:
```yaml
✅ FLASK_ENV = production
✅ QSTORM_API_KEY = Xa7K9mP3nQ2vR8tY5wZ1aB4cD6eF0gH2
✅ MAX_FILE_SIZE_MB = 200
✅ DATABASE_PATH = /opt/render/project/src/data/qstorm.db
✅ UPLOAD_FOLDER = /opt/render/project/src/uploads
✅ PYTHONUNBUFFERED = 1
✅ FLASK_APP = app_improved.py
```

**4. Trigger Redeploy**:
- Render automatically redeploys when environment changes
- Or click "Manual Deploy" → "Deploy latest commit"
- Wait for build to complete (5-10 minutes)

### Optional: Environment Groups

For managing variables across multiple services:

1. Navigate to "Environment Groups"
2. Click "New Environment Group"
3. Name: `qstorm-shared-config`
4. Add common variables
5. Link to service in service settings

---

## Post-Deployment Verification

### 1. Health Check Verification

**Test Health Endpoint**:
```bash
# Replace with your actual Render URL
curl https://qstorm-platform.onrender.com/health
```

**Expected Response**:
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

**Failure Response**:
```json
{
  "status": "unhealthy",
  "error": "Service unavailable",
  "timestamp": "2025-10-20T10:30:00.000Z"
}
```
→ Check logs for detailed error messages

### 2. API Authentication Test

**Test with Invalid Key** (should fail):
```bash
curl -X POST https://qstorm-platform.onrender.com/api/v1/analysis/timeseries \
  -H "X-API-Key: invalid-key" \
  -H "Content-Type: application/json" \
  -d '{"session_id": "test-session"}'
```

**Expected Response** (403 Forbidden):
```json
{
  "success": false,
  "error": "Invalid API key",
  "code": "AUTH_INVALID_API_KEY"
}
```

**Test with Valid Key** (should succeed):
```bash
curl -X POST https://qstorm-platform.onrender.com/api/v1/analysis/timeseries \
  -H "X-API-Key: Xa7K9mP3nQ2vR8tY5wZ1aB4cD6eF0gH2" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test-session",
    "data": [[1, 100], [2, 200]],
    "metric": "売上金額",
    "time_unit": "月"
  }'
```

**Expected Response** (200 OK):
```json
{
  "success": true,
  "data": {
    "chart_type": "timeseries",
    "analysis_id": 1,
    "session_id": "test-session"
  }
}
```

### 3. Database Persistence Test

**Create Test Data**:
```bash
# Create analysis via API
curl -X POST https://qstorm-platform.onrender.com/api/v1/analysis/timeseries \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"session_id": "persistence-test", "data": [[1,100]]}'
```

**Verify Persistence After Restart**:
```bash
# Trigger manual deploy (restart service)
# Then retrieve history

curl https://qstorm-platform.onrender.com/api/v1/history/recent \
  -H "X-API-Key: YOUR_API_KEY"
```

**Expected**: Previous analysis should still be retrievable

### 4. File Upload Test

**Test File Upload Endpoint** (if implemented):
```bash
curl -X POST https://qstorm-platform.onrender.com/api/v1/upload \
  -H "X-API-Key: YOUR_API_KEY" \
  -F "file=@sample_data.csv"
```

**Verify**:
- Upload succeeds
- File size limits enforced (MAX_FILE_SIZE_MB)
- Files stored correctly

### 5. Performance Baseline

**Measure Response Times**:
```bash
# Health check (should be <100ms)
time curl https://qstorm-platform.onrender.com/health

# API endpoint (should be <500ms for simple queries)
time curl -X POST https://qstorm-platform.onrender.com/api/v1/analysis/timeseries \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"session_id": "perf-test", "data": [[1,100]]}'
```

**Free Tier Expectations**:
- Health check: 50-200ms (warm) / 30-60s (cold start)
- Simple API calls: 200-1000ms
- Complex analysis: 1-5 seconds

---

## Monitoring & Maintenance

### Built-in Monitoring

**Render Dashboard Metrics**:
- **Status**: Service health (Live/Building/Failed)
- **CPU Usage**: Current CPU utilization
- **Memory Usage**: RAM consumption
- **Request Count**: HTTP request volume
- **Response Times**: Average latency

**Access Logs**:
1. Navigate to service dashboard
2. Click "Logs" tab
3. Filter by:
   - Time range
   - Log level (INFO/WARNING/ERROR)
   - Search keywords

**Log Retention**:
- Free tier: 7 days
- Paid tiers: 30+ days

### Health Monitoring

**Setup External Monitoring** (recommended):
- [UptimeRobot](https://uptimerobot.com/) - Free tier: 50 monitors
- [Pingdom](https://www.pingdom.com/) - Free trial available
- [StatusCake](https://www.statuscake.com/) - Free tier: 10 uptime tests

**Configuration Example** (UptimeRobot):
```
Monitor Type: HTTP(s)
URL: https://qstorm-platform.onrender.com/health
Interval: 5 minutes
Timeout: 30 seconds
Alert: Email when down
```

### Maintenance Windows

**Free Tier Sleep Behavior**:
- Service sleeps after 15 minutes of inactivity
- First request after sleep: 30-60 second cold start
- No automatic keep-alive on free tier

**Keep-Alive Strategy** (optional, not recommended for free tier):
```bash
# External cron job to ping every 14 minutes
*/14 * * * * curl https://qstorm-platform.onrender.com/health
```

**Scheduled Maintenance**:
- Render performs platform maintenance with notice
- Check Render status page: https://status.render.com
- Subscribe to status updates

### Database Backups

**Manual Backup Procedure**:

Since SQLite is file-based, backups require manual download:

1. **Access Shell** (paid plans only):
   ```bash
   render shell qstorm-platform
   sqlite3 /opt/render/project/src/data/qstorm.db .dump > backup.sql
   ```

2. **Alternative**: Implement backup API endpoint:
   ```python
   @app.route('/admin/backup', methods=['GET'])
   @require_api_key
   def backup_database():
       # Return database dump
       # Add authentication and access control!
   ```

3. **Best Practice**:
   - Upgrade to paid plan for shell access
   - Implement automated backup to cloud storage (S3, Google Cloud Storage)
   - Schedule weekly backups

**Backup Schedule Recommendation**:
- Daily: Last 7 days
- Weekly: Last 4 weeks
- Monthly: Last 12 months

---

## Troubleshooting

### Common Deployment Issues

#### Issue 1: Build Fails - Missing Dependencies

**Symptom**:
```
ERROR: Could not find a version that satisfies the requirement Flask==2.3.0
```

**Solution**:
```bash
# Verify requirements.txt is committed
git ls-files | grep requirements.txt

# Check file contents
cat requirements.txt

# Ensure Python version compatibility
# Update render.yaml if needed:
pythonVersion: "3.10"
```

#### Issue 2: Health Check Fails

**Symptom**:
```
Health check failed: Connection refused
```

**Solutions**:
1. **Verify `/health` endpoint exists**:
   ```bash
   grep -n "/health" app_improved.py
   ```

2. **Check Flask is binding to 0.0.0.0**:
   ```python
   # app_improved.py should have:
   if __name__ == '__main__':
       app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
   ```

3. **Review startup logs**:
   - Check Render dashboard → Logs
   - Look for errors during application start

#### Issue 3: Authentication Failures

**Symptom**:
```json
{
  "success": false,
  "error": "API key required",
  "code": "AUTH_MISSING_API_KEY"
}
```

**Solutions**:
1. **Verify API key is set**:
   - Check Environment tab in Render dashboard
   - Ensure QSTORM_API_KEY is not empty

2. **Validate request headers**:
   ```bash
   # Correct header name
   -H "X-API-Key: YOUR_KEY"

   # NOT:
   -H "Authorization: Bearer YOUR_KEY"
   ```

3. **Check environment**:
   ```bash
   # Verify FLASK_ENV=production
   # If set to development, auth is skipped
   ```

#### Issue 4: Database Errors

**Symptom**:
```
sqlite3.OperationalError: unable to open database file
```

**Solutions**:
1. **Verify persistent disk configuration**:
   ```yaml
   # render.yaml should have:
   disk:
     name: qstorm-data
     mountPath: /opt/render/project/src/data
     sizeGB: 1
   ```

2. **Check DATABASE_PATH**:
   ```bash
   # Must match disk mountPath
   DATABASE_PATH=/opt/render/project/src/data/qstorm.db
   ```

3. **Verify permissions**:
   - Render should auto-create directories
   - Check logs for permission errors

#### Issue 5: File Upload Fails

**Symptom**:
```
413 Request Entity Too Large
```

**Solutions**:
1. **Check MAX_FILE_SIZE_MB**:
   ```bash
   # Environment variable
   MAX_FILE_SIZE_MB=200
   ```

2. **Verify Flask configuration**:
   ```python
   # app_improved.py
   app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE_MB * 1024 * 1024
   ```

3. **Render proxy limits**:
   - Free tier: 100MB request size limit
   - Paid tiers: 500MB+
   - Consider upgrading for larger files

#### Issue 6: Cold Start Performance

**Symptom**:
- First request after 15 minutes takes 30-60 seconds
- Users experience timeout errors

**Solutions**:
1. **Accept as free tier limitation**:
   - Expected behavior on free tier
   - Service sleeps after inactivity

2. **Implement client-side retry**:
   ```javascript
   // Retry with exponential backoff
   fetch(url, { timeout: 60000 })
     .catch(() => fetch(url, { timeout: 60000 }))
   ```

3. **Upgrade to paid plan**:
   - Starter plan ($7/month): No sleep
   - Instant response times

### Debug Mode

**Enable Verbose Logging** (temporary, for troubleshooting only):

```yaml
# Add to environment variables
FLASK_DEBUG=1  # ⚠️ NEVER in production long-term

# Or in code
import logging
logging.basicConfig(level=logging.DEBUG)
```

**Review Detailed Logs**:
```bash
# Access via Render dashboard
# Look for:
# - Configuration values (sanitized)
# - Request/response details
# - Stack traces
```

**Disable After Debugging**:
```bash
# Remove FLASK_DEBUG or set to 0
FLASK_DEBUG=0
```

---

## Rollback Procedures

### Automatic Rollback

Render does not auto-rollback failed deployments. Manual intervention required.

### Manual Rollback Steps

**Option 1: Redeploy Previous Commit**

1. **Find Previous Working Commit**:
   ```bash
   git log --oneline
   # Find commit hash before breaking change
   ```

2. **Revert in Git**:
   ```bash
   # Option A: Revert commit (creates new commit)
   git revert <bad-commit-hash>
   git push origin main

   # Option B: Reset to previous state (destructive)
   git reset --hard <good-commit-hash>
   git push --force origin main
   ```

3. **Trigger Redeploy**:
   - Render auto-deploys on push
   - Or click "Manual Deploy" in dashboard

**Option 2: Use Render Manual Deploy**

1. Go to service dashboard
2. Click "Manual Deploy"
3. Select "Deploy specific commit"
4. Choose previous working commit hash
5. Click "Deploy"

**Option 3: Suspend Service** (emergency)

1. Go to service dashboard
2. Click "Suspend Service"
3. Fix issues locally
4. Resume service once fixed

### Rollback Verification

**After Rollback**:
1. Check health endpoint: `/health`
2. Verify API functionality
3. Test critical user flows
4. Review logs for errors
5. Monitor performance metrics

---

## Upgrade Path

### Free Tier → Starter Plan

**Benefits**:
- No sleep (always-on)
- 1GB RAM (vs 512MB)
- 1 CPU (vs 0.5 CPU)
- Faster response times
- Better for production use

**Cost**: $7/month per service

**Upgrade Steps**:
1. Go to service dashboard
2. Click "Upgrade Plan"
3. Select "Starter"
4. Confirm payment method
5. Service upgrades immediately (no downtime)

### Starter → Standard Plan

**Benefits**:
- 2GB RAM
- 2 CPU
- Background workers support
- Priority support
- Better for high-traffic applications

**Cost**: $25/month per service

### When to Upgrade

**Consider upgrading when**:
- Cold start delays affect user experience (Free → Starter)
- Memory usage consistently >80% (Starter → Standard)
- CPU usage consistently >70% (Starter → Standard)
- Concurrent users >50 (Free → Starter)
- Need background job processing (Starter → Standard)
- Require shell access for debugging (Any paid plan)

---

## Production Best Practices

### Security Checklist

- [ ] Strong API key generated and stored securely
- [ ] HTTPS enforced (automatic on Render)
- [ ] API rate limiting configured (Flask-Limiter)
- [ ] CORS origins updated for production domain
- [ ] Debug mode disabled (FLASK_ENV=production)
- [ ] Error messages sanitized (no stack traces exposed)
- [ ] Database not publicly accessible (Render default)
- [ ] Regular security updates scheduled

### Performance Optimization

- [ ] Database indexes created for common queries
- [ ] Response caching implemented where appropriate
- [ ] File upload size limits enforced
- [ ] Rate limiting configured per endpoint
- [ ] Logging level set to WARNING or ERROR in production
- [ ] Static assets served efficiently
- [ ] Database connection pooling considered

### Operational Readiness

- [ ] Monitoring and alerting configured
- [ ] Health check endpoint tested
- [ ] Backup strategy documented and tested
- [ ] Rollback procedure documented
- [ ] API key rotation schedule established
- [ ] Incident response plan created
- [ ] Deployment runbook maintained
- [ ] Team access permissions configured

---

## Support & Resources

### Render.com Resources

- **Documentation**: https://render.com/docs
- **Status Page**: https://status.render.com
- **Community Forum**: https://community.render.com
- **Support**: help@render.com (paid plans have priority)

### Q-Storm Platform Resources

- **Environment Setup**: `docs/ENV_SETUP.md`
- **Architecture Spec**: `SYSTEM_ARCHITECTURE_SPECIFICATION.md`
- **Implementation Workflow**: `IMPLEMENTATION_WORKFLOW.md`

### Emergency Contacts

**Service Down**:
1. Check Render status page
2. Review service logs
3. Verify environment configuration
4. Contact Render support (if paid plan)

**Security Incident**:
1. Rotate API keys immediately
2. Review access logs
3. Suspend service if necessary
4. Document incident for post-mortem

---

## Deployment Checklist

### Pre-Deployment
- [ ] Code tested locally
- [ ] All tests passing
- [ ] `render.yaml` configured
- [ ] `.gitignore` updated
- [ ] Changes committed and pushed

### Deployment
- [ ] Repository connected to Render
- [ ] Blueprint applied successfully
- [ ] Build completed without errors
- [ ] Environment variables configured
- [ ] API key generated and set

### Post-Deployment
- [ ] Health check passing
- [ ] API authentication working
- [ ] Database persistence verified
- [ ] Performance acceptable
- [ ] Monitoring configured

### Production Readiness
- [ ] Security checklist completed
- [ ] Documentation updated
- [ ] Team trained on deployment process
- [ ] Rollback procedure tested
- [ ] Backup strategy implemented

---

**Deployment Complete!** 🎉

Your Q-Storm Platform is now live on Render.com. Access your service at:
`https://qstorm-platform.onrender.com`

For ongoing support, refer to this guide and related documentation.
