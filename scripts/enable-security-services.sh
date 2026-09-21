#!/usr/bin/env bash
# OPTIONAL: Enables Security Hub, GuardDuty, and Inspector2 in your AWS
# account/region so the dashboard can pull REAL findings instead of demo data.
#
# Requires: AWS CLI v2 installed and configured (aws configure)
# Usage:    ./enable-security-services.sh [region]

set -e
REGION="${1:-us-east-1}"

echo "Enabling AWS security services in region: $REGION"

echo "1) Enabling Security Hub..."
aws securityhub enable-security-hub --region "$REGION" || echo "  (already enabled or insufficient permissions)"

echo "2) Enabling GuardDuty..."
aws guardduty create-detector --enable --region "$REGION" || echo "  (already enabled or insufficient permissions)"

echo "3) Enabling Inspector2 (EC2, ECR, Lambda scanning)..."
aws inspector2 enable --resource-types EC2 ECR LAMBDA --region "$REGION" || echo "  (already enabled or insufficient permissions)"

echo "4) Checking CloudTrail trails..."
TRAILS=$(aws cloudtrail describe-trails --region "$REGION" --query 'trailList[].Name' --output text)
if [ -z "$TRAILS" ]; then
  echo "  No trail found. Creating a basic trail 'soc-dashboard-trail' (requires an S3 bucket)."
  echo "  Skipping auto-creation - CloudTrail needs an S3 bucket ARN. Create manually, e.g.:"
  echo "    aws cloudtrail create-trail --name soc-dashboard-trail --s3-bucket-name <your-bucket> --region $REGION"
  echo "    aws cloudtrail start-logging --name soc-dashboard-trail --region $REGION"
else
  echo "  Existing trail(s) found: $TRAILS"
fi

echo ""
echo "Done. It can take several minutes to hours for findings to start appearing."
echo "Until then (or if you skip this script entirely), the dashboard runs on demo data."
