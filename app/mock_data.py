"""
mock_data.py
------------
Generates realistic, deterministic-ish demo data for the SOC Dashboard.

This is used automatically whenever real AWS calls fail or are unavailable
(no credentials, service not enabled in the account/region, sandbox with no
network access, etc.) so the dashboard is always demonstrable.
"""

import random
import uuid
from datetime import datetime, timedelta

random.seed(42)  # reproducible demo data

SEVERITIES = ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFORMATIONAL"]
SEVERITY_WEIGHTS = [5, 15, 35, 35, 10]

REGIONS = ["us-east-1", "us-west-2", "eu-west-1"]


def _rand_time(days_back=14):
    delta = timedelta(
        days=random.randint(0, days_back),
        hours=random.randint(0, 23),
        minutes=random.randint(0, 59),
    )
    return (datetime.utcnow() - delta).isoformat() + "Z"


def _weighted_severity():
    return random.choices(SEVERITIES, weights=SEVERITY_WEIGHTS, k=1)[0]


SECURITYHUB_TITLES = [
    "S3 bucket is publicly accessible",
    "IAM user has console access without MFA",
    "Security group allows unrestricted SSH access (0.0.0.0/0)",
    "EBS volume is not encrypted",
    "CloudTrail is not enabled in all regions",
    "Root account has active access keys",
    "RDS instance is publicly accessible",
    "IAM policy grants full administrative privileges",
    "VPC flow logging is not enabled",
    "Password policy does not require minimum complexity",
]

GUARDDUTY_TITLES = [
    "UnauthorizedAccess:EC2/SSHBruteForce",
    "Recon:EC2/PortProbeUnprotectedPort",
    "CryptoCurrency:EC2/BitcoinTool.B!DNS",
    "UnauthorizedAccess:IAMUser/InstanceCredentialExfiltration",
    "Trojan:EC2/DNSDataExfiltration",
    "Backdoor:EC2/C&CActivity.B!DNS",
    "PrivilegeEscalation:IAMUser/AdministrativePermissions",
    "Impact:EC2/WinRMBruteForce",
    "Stealth:IAMUser/CloudTrailLoggingDisabled",
    "Persistence:IAMUser/NetworkPermissions",
]

INSPECTOR_TITLES = [
    "CVE-2023-44487 - HTTP/2 Rapid Reset vulnerability",
    "CVE-2022-3602 - OpenSSL buffer overflow",
    "CVE-2021-44228 - Log4Shell remote code execution",
    "CVE-2023-38545 - curl SOCKS5 heap overflow",
    "CVE-2020-1971 - OpenSSL GENERAL_NAME_cmp denial of service",
    "Outdated Amazon Linux AMI kernel package",
    "Vulnerable version of OpenSSH detected",
    "Container image contains vulnerable glibc package",
]

CLOUDTRAIL_EVENTS = [
    "ConsoleLogin",
    "CreateUser",
    "DeleteTrail",
    "PutBucketPolicy",
    "AuthorizeSecurityGroupIngress",
    "StopLogging",
    "CreateAccessKey",
    "AttachUserPolicy",
    "TerminateInstances",
    "AssumeRole",
]


def get_securityhub_findings(count=18):
    findings = []
    for _ in range(count):
        sev = _weighted_severity()
        findings.append({
            "id": str(uuid.uuid4()),
            "title": random.choice(SECURITYHUB_TITLES),
            "severity": sev,
            "resource_type": random.choice(["AwsS3Bucket", "AwsEc2SecurityGroup", "AwsIamUser", "AwsEc2Volume", "AwsRdsDbInstance"]),
            "region": random.choice(REGIONS),
            "account_id": "123456789012",
            "created_at": _rand_time(),
            "workflow_state": random.choice(["NEW", "NOTIFIED", "RESOLVED"]),
            "compliance_status": random.choice(["FAILED", "PASSED", "WARNING"]),
        })
    return findings


def get_guardduty_findings(count=14):
    findings = []
    for _ in range(count):
        sev = _weighted_severity()
        findings.append({
            "id": str(uuid.uuid4()),
            "title": random.choice(GUARDDUTY_TITLES),
            "severity": sev,
            "type": "Threat Detection",
            "region": random.choice(REGIONS),
            "resource": random.choice(["EC2 Instance i-0a1b2c3d", "IAM User dev-user", "S3 Bucket app-logs"]),
            "created_at": _rand_time(),
            "count": random.randint(1, 40),
        })
    return findings


def get_inspector_findings(count=12):
    findings = []
    for _ in range(count):
        sev = _weighted_severity()
        findings.append({
            "id": str(uuid.uuid4()),
            "title": random.choice(INSPECTOR_TITLES),
            "severity": sev,
            "resource_type": random.choice(["AWS_EC2_INSTANCE", "AWS_ECR_CONTAINER_IMAGE", "AWS_LAMBDA_FUNCTION"]),
            "region": random.choice(REGIONS),
            "created_at": _rand_time(),
            "fix_available": random.choice(["YES", "NO", "PARTIAL"]),
        })
    return findings


def get_cloudtrail_events(count=25):
    events = []
    for _ in range(count):
        events.append({
            "id": str(uuid.uuid4()),
            "event_name": random.choice(CLOUDTRAIL_EVENTS),
            "event_source": random.choice(["iam.amazonaws.com", "s3.amazonaws.com", "ec2.amazonaws.com", "signin.amazonaws.com"]),
            "username": random.choice(["admin", "dev-user", "ci-cd-role", "root", "security-audit"]),
            "source_ip": f"{random.randint(1,223)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(0,255)}",
            "region": random.choice(REGIONS),
            "event_time": _rand_time(days_back=7),
            "read_only": random.choice([True, False]),
        })
    return sorted(events, key=lambda e: e["event_time"], reverse=True)
