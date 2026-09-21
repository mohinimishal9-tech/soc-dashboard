# Architecture

```
                        ┌─────────────────────────────┐
                        │        AWS Account          │
                        │                              │
                        │  ┌──────────────┐            │
                        │  │ Security Hub │            │
                        │  └──────┬───────┘            │
                        │         │ findings           │
                        │  ┌──────▼───────┐            │
                        │  │  GuardDuty   │            │
                        │  └──────┬───────┘            │
                        │         │ findings            │
                        │  ┌──────▼───────┐            │
                        │  │  Inspector   │            │
                        │  └──────┬───────┘            │
                        │         │ findings            │
                        │  ┌──────▼───────┐            │
                        │  │ CloudTrail   │            │
                        │  └──────┬───────┘            │
                        │         │ events              │
                        └─────────┼────────────────────┘
                                  │ boto3 (read-only IAM role)
                          ┌───────▼────────┐
                          │  Flask backend  │
                          │  (aws_client.py)│
                          │  - normalizes   │
                          │  - aggregates   │
                          │  - falls back   │
                          │    to demo data │
                          └───────┬────────┘
                                  │ REST/JSON API
                          ┌───────▼────────┐
                          │  Browser UI     │
                          │  (Chart.js +    │
                          │   HTML tables)  │
                          └────────────────┘
```

## Components

1. **Security Hub** — central aggregator for AWS config/compliance findings
   (CIS/AWS Foundational Security Best Practices checks).
2. **GuardDuty** — continuous threat detection (recon, credential misuse,
   malware/crypto-mining behavior, etc.) using VPC Flow Logs, DNS logs, and
   CloudTrail management events.
3. **Inspector** — automated vulnerability scanning (CVEs) for EC2, ECR
   container images, and Lambda functions.
4. **CloudTrail** — audit log of all API calls/management events across the
   account, used for forensic timeline and anomaly review.
5. **Flask backend (`app/aws_client.py`, `app/app.py`)** — pulls findings via
   `boto3`, normalizes each service's schema into a common shape
   (`severity`, `title`, `resource`, `region`, `created_at`), and exposes a
   small REST API. If AWS calls fail for any reason it transparently serves
   realistic demo data (`app/mock_data.py`) so the system is always
   demonstrable.
6. **Dashboard UI (`templates/index.html`, `static/js/dashboard.js`)** — single
   page app with KPI cards, a severity-distribution donut chart, a
   findings-by-source bar chart, and tabbed tables per service, auto-refreshing
   every 60 seconds.

## Data flow

`Browser -> Flask REST API -> aws_client.py -> boto3 -> AWS Security Services`
(falls back to `mock_data.py` on any failure)

## Why the demo-data fallback matters

Class environments often don't have a live AWS account with these services
enabled (GuardDuty/Inspector/Security Hub have costs and take time to
populate findings). The fallback design lets you:
- Demo/grade the **full working UI and API** with zero AWS setup.
- Swap to **real AWS data** at any time by adding credentials to `.env` and
  optionally running `scripts/enable-security-services.sh` — no code changes
  needed.
