# Known Limitations and Future Enhancements

This document tracks known limitations, incomplete features (TODOs), and planned enhancements for the Revenue Context Engine.

---

## 🔴 High Priority Limitations

### 1. Salesforce Token Refresh Not Implemented

**File**: `app/integrations/salesforce_task.py:42`

**Current Behavior**:
```python
# TODO: Refresh token and retry
```

**Impact**: 
- Salesforce API calls will fail after access token expires (typically 2 hours)
- Requires manual re-authentication

**Workaround**:
- Monitor token expiration
- Re-authenticate manually when needed
- Set up alerts for authentication failures

**Planned Fix**: Q2 2026
- Implement automatic token refresh using refresh_token
- Add token expiration tracking
- Retry failed requests with new token

---

## 🟡 Medium Priority Limitations

### 2. API Key Validation Not Fully Implemented

**File**: `app/auth/api.py:16`

**Current Behavior**:
```python
# TODO: Validate api_key and tenant_id
```

**Impact**:
- API key authentication endpoint exists but validation is placeholder
- JWT authentication is fully functional and should be used instead

**Workaround**:
- Use JWT authentication (fully implemented)
- API key endpoint is for future use

**Planned Fix**: Q3 2026
- Implement API key storage and validation
- Add API key rotation
- Add rate limiting per API key

---

### 3. Account ID Mapping Uses External ID Directly

**File**: `app/integrations/salesforce_task.py:27`

**Current Behavior**:
```python
account_id = account_external_id  # TODO: lookup mapping
```

**Impact**:
- Assumes Salesforce external ID matches internal account ID
- May cause issues if IDs don't align

**Workaround**:
- Ensure Salesforce external IDs match internal account IDs
- Or manually maintain ID mapping

**Planned Fix**: Q3 2026
- Implement account ID mapping table
- Add automatic ID resolution
- Support multiple ID formats

---

## 🟢 Low Priority / Deprecated

### 4. Generic CRM Webhook Handler Incomplete

**File**: `app/integrations/crm_webhook.py:13`

**Current Behavior**:
```python
# TODO: Validate, transform, enqueue event
```

**Impact**:
- Generic webhook endpoint not functional
- Salesforce-specific webhook works perfectly

**Workaround**:
- Use Salesforce-specific webhook endpoint: `/api/integrations/salesforce/webhook`
- This is fully implemented and production-ready

**Planned Fix**: Q4 2026
- Implement generic webhook handler for other CRMs
- Add support for HubSpot, Pipedrive, etc.

---

### 5. Legacy Audit Logger Not Persisting

**File**: `app/compliance/audit.py:16`

**Current Behavior**:
```python
# TODO: Persist to Postgres
```

**Impact**: None - this is deprecated code

**Workaround**:
- Use new audit logger: `app/compliance/audit_logger.py`
- Fully functional with partitioned tables and query functions

**Planned Fix**: Remove in next version
- Delete deprecated `audit.py` file
- Migrate any remaining references

---

## ✅ Completed Features

### Email Generation with AI
- ✅ Migrated from OpenAI to Gemini API
- ✅ Async generation with proper error handling
- ✅ Confidence scoring and metrics tracking

### Security
- ✅ JWT authentication with validation
- ✅ Encryption key rotation support
- ✅ Security headers middleware
- ✅ Rate limiting with Redis
- ✅ CORS configuration

### Monitoring
- ✅ Prometheus metrics
- ✅ Health check endpoints
- ✅ Request ID tracing
- ✅ Audit logging with partitioned tables

### Database
- ✅ Alembic migrations
- ✅ Async PostgreSQL support
- ✅ Connection pooling
- ✅ Proper indexes and partitioning

---

## 📋 Future Enhancements (Not Blocking Deployment)

### Performance
- [ ] Add Redis caching for frequently accessed data
- [ ] Implement database query optimization
- [ ] Enable response compression
- [ ] Add connection pooling for external APIs

### Security
- [ ] Automated API key rotation
- [ ] IP whitelisting for admin endpoints
- [ ] Webhook signature verification
- [ ] Audit log encryption for sensitive data

### Reliability
- [ ] Enhanced circuit breakers for all external APIs
- [ ] Retry logic with exponential backoff
- [ ] Improved dead letter queue processing
- [ ] Health check for external service dependencies

### Developer Experience
- [ ] Pre-commit hooks for linting
- [ ] CI/CD pipeline automation
- [ ] OpenAPI/Swagger documentation
- [ ] Docker Compose for local development

### Monitoring
- [ ] Sentry integration for error tracking
- [ ] Grafana dashboards
- [ ] Automated alerting
- [ ] Log aggregation and analysis

---

## 🚀 Deployment Impact Assessment

### Can Deploy Now ✅
All critical features are functional:
- Authentication (JWT)
- Email generation (Gemini API)
- Salesforce webhook integration
- Audit logging
- Health checks
- Security middleware

### Known Limitations in Production
1. **Salesforce tokens** - Will need manual refresh every 2 hours
2. **API key auth** - Not available (use JWT instead)
3. **Generic webhooks** - Not available (use Salesforce webhook)

### Mitigation Strategies
1. **Token Refresh**: Set up monitoring alerts for auth failures
2. **API Key Auth**: Document JWT as the primary authentication method
3. **Generic Webhooks**: Document Salesforce as the supported CRM

---

## 📞 Support and Questions

For questions about these limitations or to request prioritization changes:
- Create an issue in the repository
- Contact the development team
- Review the implementation plan for detailed timelines

---

**Last Updated**: 2026-02-03  
**Next Review**: 2026-03-01
