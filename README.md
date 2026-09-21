# AWS-Based Security Operations Center (SOC) Dashboard

A centralized web dashboard that integrates **AWS Security Hub**,
**GuardDuty**, **Inspector**, and **CloudTrail** into one place, so a
security analyst can see findings, threats, vulnerabilities, and audit
events without switching between four different AWS console pages.

Runs immediately out of the box in **demo data mode** (no AWS account
needed to grade/demo it), and switches automatically to **live AWS data**
the moment valid credentials are provided.

---

## 1. Quick Start (just run it)

### Linux / macOS
```bash
unzip soc-dashboard.zip
cd soc-dashboard
chmod +x run.sh
./run.sh
```

### Windows
```
unzip soc-dashboard.zip
cd soc-dashboard
run.bat
```

Then open **http://localhost:5000** in your browser.

That's it — the script creates a virtual environment, installs
dependencies, and starts the Flask server. Since no AWS credentials are
configured by default, it automatically displays realistic **demo data**
(clearly labeled with a "DEMO DATA MODE" badge in the UI) so the full
dashboard is functional immediately.

Requires: **Python 3.9+** installed and on your PATH.

---

## 1b. Running the Streamlit Version Instead

This project also includes a Streamlit version of the same dashboard
(`streamlit_app.py`) — same data, same AWS integration, different UI
framework. Useful if your class specifically wants a Streamlit app.

```powershell
python -m pip install -r requirements.txt
streamlit run streamlit_app.py
```

It will automatically open in your browser (usually at
`http://localhost:8501`). It uses the same `.env` file and the same
`app/aws_client.py` / `app/mock_data.py` logic as the Flask version, so
demo-data fallback and real AWS credentials work identically — no extra
setup beyond what's already in `.env`.

You can run the Flask app and the Streamlit app at the same time (they
use different ports, 5000 vs 8501) if you want to compare both.

---

## 2. Using Real AWS Data (optional)

1. Copy `.env.example` to `.env` (the run script does this for you
   automatically on first run).
2. Fill in your AWS credentials in `.env`:
   ```
   AWS_ACCESS_KEY_ID=...
   AWS_SECRET_ACCESS_KEY=...
   AWS_REGION=us-east-1
   ```
   (An IAM user/role with the read-only permissions in
   `scripts/iam-readonly-policy.json` is sufficient.)
3. Make sure the security services are actually enabled in your account.
   Either:
   - Run the helper script: `bash scripts/enable-security-services.sh us-east-1`, or
   - Deploy `scripts/soc-infrastructure.yaml` via CloudFormation:
     ```bash
     aws cloudformation deploy \
       --template-file scripts/soc-infrastructure.yaml \
       --stack-name soc-dashboard-infra \
       --parameter-overrides TrailBucketName=my-unique-trail-bucket-name \
       --capabilities CAPABILITY_NAMED_IAM
     ```
4. Restart the app (`./run.sh` / `run.bat`). It will now show real findings.
   If any individual service has no findings yet or isn't reachable, that
   service alone falls back to demo data — the app never crashes.

---

## 3. Project Structure

```
soc-dashboard/
├── run.sh / run.bat            # one-command setup + launch
├── requirements.txt
├── .env.example
├── app/
│   ├── app.py                  # Flask routes / REST API
│   ├── aws_client.py           # boto3 calls + auto fallback to demo data
│   ├── mock_data.py            # realistic demo data generator
│   ├── templates/index.html    # dashboard UI
│   └── static/
│       ├── css/style.css
│       └── js/dashboard.js     # Chart.js + fetch logic
├── scripts/
│   ├── enable-security-services.sh   # AWS CLI: turn on the 4 services
│   ├── soc-infrastructure.yaml       # CloudFormation: trail, GuardDuty, IAM role
│   └── iam-readonly-policy.json      # minimal IAM policy for the app
└── docs/
    └── architecture.md         # diagram + design notes
```

---

## 4. How It Works

- **Backend (`app/aws_client.py`)** calls the AWS SDK (`boto3`) for each
  service's findings API (`securityhub.get_findings`,
  `guardduty.get_findings`, `inspector2.list_findings`,
  `cloudtrail.lookup_events`), normalizes them into a common schema, and
  serves them as JSON via Flask routes.
- **Resilience**: every AWS call is wrapped in a try/except. If credentials
  are missing, a service isn't enabled, or there's simply no network access
  (e.g., in a sandboxed grading environment), that call transparently falls
  back to demo data — so the dashboard is always usable.
- **Frontend** polls the REST API and renders:
  - 4 KPI cards (total findings, critical count, high count, CloudTrail
    event count)
  - A severity-distribution donut chart
  - A findings-by-source bar chart
  - Tabbed, sortable-by-eye tables for each of the 4 services
  - Auto-refresh every 60 seconds + manual refresh button

---

## 5. Project Write-Up (for report / submission)

**Objective**: Build a centralized monitoring dashboard that aggregates
security signal from multiple native AWS security services into a single
pane of glass, reducing the need for analysts to context-switch between
consoles.

**Services integrated**:
| Service | Purpose |
|---|---|
| Security Hub | Aggregated compliance & configuration findings (CIS/AWS FSBP) |
| GuardDuty | ML/threat-intel-based intrusion & anomaly detection |
| Inspector | Automated CVE/vulnerability scanning for EC2, ECR, Lambda |
| CloudTrail | Full audit trail of account API activity |

**Implementation**: Python/Flask backend using `boto3` for AWS API
integration; vanilla JS + Chart.js frontend; IAM least-privilege read-only
role; optional CloudFormation stack for supporting infrastructure
(S3 log bucket, CloudTrail trail, GuardDuty detector, IAM role).

**Result**: A working, demoable dashboard that functions identically
whether backed by live AWS findings or (in the absence of a provisioned
AWS environment) realistic simulated data — useful both for coursework
evaluation and as a template for a real deployment.

**Possible extensions**: persist findings history in a database for
trend-over-time analysis, add SNS/email alerting on new CRITICAL findings,
add authentication (Cognito) in front of the dashboard, deploy the Flask
app itself on AWS (App Runner / ECS / Elastic Beanstalk) behind an ALB.

---

## 6. Troubleshooting

- **"python3: command not found"** — install Python 3.9+ from python.org.
- **Port 5000 already in use** — change `FLASK_PORT` in `.env`.
- **Real AWS data not showing** — check `.env` credentials, confirm the
  IAM identity has the permissions in `scripts/iam-readonly-policy.json`,
  and confirm the services are enabled in the region set by `AWS_REGION`.
- **Everything shows "DEMO DATA MODE" even with credentials set** — check
  the terminal logs; each failed AWS call logs a warning explaining why it
  fell back (e.g., "No GuardDuty detector configured in this region").
