"""
app.py
------
Flask entry point for the AWS SOC Dashboard.

Routes:
  GET /                          -> dashboard UI
  GET /api/findings/summary      -> aggregated counts across all 4 sources
  GET /api/findings/securityhub  -> Security Hub findings
  GET /api/findings/guardduty    -> GuardDuty findings
  GET /api/findings/inspector    -> Inspector findings
  GET /api/events/cloudtrail     -> CloudTrail events
"""

import os
from collections import Counter
from flask import Flask, jsonify, render_template
from dotenv import load_dotenv

load_dotenv()

from app import aws_client  # noqa: E402

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/findings/securityhub")
def api_securityhub():
    findings, demo = aws_client.get_securityhub_findings()
    return jsonify({"source": "SecurityHub", "demo_mode": demo, "count": len(findings), "findings": findings})


@app.route("/api/findings/guardduty")
def api_guardduty():
    findings, demo = aws_client.get_guardduty_findings()
    return jsonify({"source": "GuardDuty", "demo_mode": demo, "count": len(findings), "findings": findings})


@app.route("/api/findings/inspector")
def api_inspector():
    findings, demo = aws_client.get_inspector_findings()
    return jsonify({"source": "Inspector", "demo_mode": demo, "count": len(findings), "findings": findings})


@app.route("/api/events/cloudtrail")
def api_cloudtrail():
    events, demo = aws_client.get_cloudtrail_events()
    return jsonify({"source": "CloudTrail", "demo_mode": demo, "count": len(events), "events": events})


@app.route("/api/findings/summary")
def api_summary():
    sh, sh_demo = aws_client.get_securityhub_findings()
    gd, gd_demo = aws_client.get_guardduty_findings()
    insp, insp_demo = aws_client.get_inspector_findings()
    ct, ct_demo = aws_client.get_cloudtrail_events()

    all_findings = sh + gd + insp
    severity_counts = Counter(f["severity"].upper() for f in all_findings)

    by_source = {
        "SecurityHub": len(sh),
        "GuardDuty": len(gd),
        "Inspector": len(insp),
    }

    order = ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFORMATIONAL"]
    severity_ordered = {k: severity_counts.get(k, 0) for k in order}

    return jsonify({
        "demo_mode": any([sh_demo, gd_demo, insp_demo, ct_demo]),
        "total_findings": len(all_findings),
        "total_cloudtrail_events": len(ct),
        "severity_counts": severity_ordered,
        "by_source": by_source,
    })


if __name__ == "__main__":
    port = int(os.getenv("FLASK_PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
