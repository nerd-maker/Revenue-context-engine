# Billing Integration Plan

## Overview
- **Goal**: Track per-tenant usage and enable metered billing (future Stripe integration)

## Usage Tracking
- All API calls and workflow events are logged with `tenant_id`
- Usage dashboard exposes per-tenant metrics (signals, tasks, emails, enrichment, experiments)
- Quotas and rate limits enforced via Redis

## Billing Events
- Export usage data to S3 for billing pipeline
- (Planned) Integrate with Stripe for invoicing and payment

## Stripe Integration (Future)
- Create Stripe customer for each tenant
- Sync usage data to Stripe metered billing API
- Webhook for payment status, failed payments

## Security/Compliance
- No sensitive payment data stored in platform DB
- PCI compliance handled by Stripe

## Runbook
1. Export usage data from dashboard or S3
2. (Future) Sync to Stripe for invoicing
3. Monitor payment status and alert on failures
