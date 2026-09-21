"""
aws_client.py
-------------
Thin wrappers around boto3 for Security Hub, GuardDuty, Inspector2, and
CloudTrail. Every function tries a real AWS call first; if it fails for
ANY reason (no credentials, service not enabled, no network, permissions
error, throttling, etc.) it transparently falls back to demo data from
mock_data.py so the dashboard never breaks.
"""

import os
import logging
import boto3
from botocore.exceptions import BotoCoreError, ClientError, NoCredentialsError

from app import mock_data

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("soc-dashboard")

REGION = os.getenv("AWS_REGION", "us-east-1")
FORCE_DEMO = os.getenv("FORCE_DEMO_MODE", "false").lower() == "true"


def _session():
    return boto3.session.Session(region_name=REGION)


def _demo_mode_active():
    if FORCE_DEMO:
        return True
    return False


# ---------------------------------------------------------------------------
# Security Hub
# ---------------------------------------------------------------------------
def get_securityhub_findings():
    if _demo_mode_active():
        return mock_data.get_securityhub_findings(), True
    try:
        client = _session().client("securityhub")
        resp = client.get_findings(MaxResults=50)
        findings = []
        for f in resp.get("Findings", []):
            findings.append({
                "id": f.get("Id"),
                "title": f.get("Title"),
                "severity": f.get("Severity", {}).get("Label", "INFORMATIONAL"),
                "resource_type": (f.get("Resources") or [{}])[0].get("Type", "Unknown"),
                "region": f.get("Region", REGION),
                "account_id": f.get("AwsAccountId", "unknown"),
                "created_at": f.get("CreatedAt"),
                "workflow_state": f.get("Workflow", {}).get("Status", "NEW"),
                "compliance_status": f.get("Compliance", {}).get("Status", "UNKNOWN"),
            })
        if not findings:
            raise ValueError("No findings returned (service may not be enabled)")
        return findings, False
    except (BotoCoreError, ClientError, NoCredentialsError, ValueError) as e:
        logger.warning(f"[SecurityHub] Falling back to demo data: {e}")
        return mock_data.get_securityhub_findings(), True


# ---------------------------------------------------------------------------
# GuardDuty
# ---------------------------------------------------------------------------
def get_guardduty_findings():
    if _demo_mode_active():
        return mock_data.get_guardduty_findings(), True
    try:
        client = _session().client("guardduty")
        detectors = client.list_detectors().get("DetectorIds", [])
        if not detectors:
            raise ValueError("No GuardDuty detector configured in this region")

        detector_id = detectors[0]
        finding_ids = client.list_findings(DetectorId=detector_id, MaxResults=50).get("FindingIds", [])
        if not finding_ids:
            raise ValueError("No GuardDuty findings returned")

        details = client.get_findings(DetectorId=detector_id, FindingIds=finding_ids).get("Findings", [])
        findings = []
        for f in details:
            findings.append({
                "id": f.get("Id"),
                "title": f.get("Title"),
                "severity": _gd_severity_label(f.get("Severity", 0)),
                "type": f.get("Type"),
                "region": f.get("Region", REGION),
                "resource": f.get("Resource", {}).get("ResourceType", "Unknown"),
                "created_at": f.get("CreatedAt"),
                "count": f.get("Service", {}).get("Count", 1),
            })
        return findings, False
    except (BotoCoreError, ClientError, NoCredentialsError, ValueError) as e:
        logger.warning(f"[GuardDuty] Falling back to demo data: {e}")
        return mock_data.get_guardduty_findings(), True


def _gd_severity_label(score):
    if score >= 7:
        return "HIGH"
    if score >= 4:
        return "MEDIUM"
    return "LOW"


# ---------------------------------------------------------------------------
# Inspector (Inspector2)
# ---------------------------------------------------------------------------
def get_inspector_findings():
    if _demo_mode_active():
        return mock_data.get_inspector_findings(), True
    try:
        client = _session().client("inspector2")
        resp = client.list_findings(maxResults=50)
        findings = []
        for f in resp.get("findings", []):
            findings.append({
                "id": f.get("findingArn"),
                "title": f.get("title", "Unknown finding"),
                "severity": f.get("severity", "INFORMATIONAL"),
                "resource_type": (f.get("resources") or [{}])[0].get("type", "Unknown"),
                "region": REGION,
                "created_at": str(f.get("firstObservedAt", "")),
                "fix_available": f.get("fixAvailable", "NO"),
            })
        if not findings:
            raise ValueError("No Inspector findings returned (service may not be enabled)")
        return findings, False
    except (BotoCoreError, ClientError, NoCredentialsError, ValueError) as e:
        logger.warning(f"[Inspector] Falling back to demo data: {e}")
        return mock_data.get_inspector_findings(), True


# ---------------------------------------------------------------------------
# CloudTrail
# ---------------------------------------------------------------------------
def get_cloudtrail_events():
    if _demo_mode_active():
        return mock_data.get_cloudtrail_events(), True
    try:
        client = _session().client("cloudtrail")
        resp = client.lookup_events(MaxResults=50)
        events = []
        for e in resp.get("Events", []):
            events.append({
                "id": e.get("EventId"),
                "event_name": e.get("EventName"),
                "event_source": e.get("EventSource"),
                "username": e.get("Username", "unknown"),
                "source_ip": _extract_source_ip(e),
                "region": REGION,
                "event_time": str(e.get("EventTime", "")),
                "read_only": e.get("ReadOnly", "true") == "true",
            })
        if not events:
            raise ValueError("No CloudTrail events returned")
        return events, False
    except (BotoCoreError, ClientError, NoCredentialsError, ValueError) as e:
        logger.warning(f"[CloudTrail] Falling back to demo data: {e}")
        return mock_data.get_cloudtrail_events(), True


def _extract_source_ip(event):
    try:
        import json
        raw = json.loads(event.get("CloudTrailEvent", "{}"))
        return raw.get("sourceIPAddress", "unknown")
    except Exception:
        return "unknown"
