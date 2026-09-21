"""
streamlit_app.py
-----------------
Streamlit version of the AWS SOC Dashboard. Reuses the exact same
aws_client.py / mock_data.py logic as the Flask app - only the UI layer
is different.

Run with:
    streamlit run streamlit_app.py
"""

import os
from collections import Counter

import pandas as pd
import plotly.express as px
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="AWS Security Operations Center",
    page_icon="🛡️",
    layout="wide",
)

# When deployed on Streamlit Community Cloud, there is no local .env file.
# Credentials are instead configured via Streamlit's "Secrets" UI, which
# populates st.secrets. Copy any matching keys into os.environ so the
# existing aws_client.py (which reads via os.getenv) works unchanged both
# locally (.env) and when deployed (Secrets). Locally, with no secrets.toml
# file at all, st.secrets raises FileNotFoundError just from being touched -
# so this whole block is wrapped in a try/except and simply does nothing
# in that case, leaving the .env values already loaded above untouched.
try:
    for _key in ("AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_SESSION_TOKEN",
                 "AWS_REGION", "FORCE_DEMO_MODE"):
        if _key in st.secrets:
            os.environ[_key] = str(st.secrets[_key])
except Exception:
    pass  # No secrets.toml present (normal for local runs) - use .env instead

from app import aws_client  # noqa: E402

SEVERITY_ORDER = ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFORMATIONAL"]
SEVERITY_COLORS = {
    "CRITICAL": "#ff4d5e",
    "HIGH": "#ff9f43",
    "MEDIUM": "#ffd43b",
    "LOW": "#51cf66",
    "INFORMATIONAL": "#74c0fc",
}


@st.cache_data(ttl=60, show_spinner=False)
def load_all_data():
    sh, sh_demo = aws_client.get_securityhub_findings()
    gd, gd_demo = aws_client.get_guardduty_findings()
    insp, insp_demo = aws_client.get_inspector_findings()
    ct, ct_demo = aws_client.get_cloudtrail_events()
    return {
        "securityhub": (sh, sh_demo),
        "guardduty": (gd, gd_demo),
        "inspector": (insp, insp_demo),
        "cloudtrail": (ct, ct_demo),
    }


# --- Header -----------------------------------------------------------
col_title, col_refresh = st.columns([6, 1])
with col_title:
    st.title("🛡️ AWS Security Operations Center")
with col_refresh:
    st.write("")
    if st.button("🔄 Refresh", use_container_width=True):
        st.cache_data.clear()

data = load_all_data()
sh, sh_demo = data["securityhub"]
gd, gd_demo = data["guardduty"]
insp, insp_demo = data["inspector"]
ct, ct_demo = data["cloudtrail"]

any_demo = any([sh_demo, gd_demo, insp_demo, ct_demo])
if any_demo:
    demo_sources = [n for n, d in [("Security Hub", sh_demo), ("GuardDuty", gd_demo),
                                    ("Inspector", insp_demo), ("CloudTrail", ct_demo)] if d]
    st.warning(f"⚠️ DEMO DATA MODE for: {', '.join(demo_sources)} "
               f"(live AWS call unavailable — showing realistic sample data instead)")

# --- KPIs ---------------------------------------------------------------
all_findings = sh + gd + insp
severity_counts = Counter(f["severity"].upper() for f in all_findings)

k1, k2, k3, k4 = st.columns(4)
k1.metric("Total Findings", len(all_findings))
k2.metric("Critical", severity_counts.get("CRITICAL", 0))
k3.metric("High", severity_counts.get("HIGH", 0))
k4.metric("CloudTrail Events (7d)", len(ct))

st.divider()

# --- Charts ---------------------------------------------------------------
chart_col1, chart_col2 = st.columns(2)

with chart_col1:
    st.subheader("Findings by Severity")
    sev_df = pd.DataFrame(
        [{"severity": s, "count": severity_counts.get(s, 0)} for s in SEVERITY_ORDER]
    )
    sev_df = sev_df[sev_df["count"] > 0]
    if not sev_df.empty:
        fig = px.pie(
            sev_df, names="severity", values="count", hole=0.55,
            color="severity", color_discrete_map=SEVERITY_COLORS,
        )
        fig.update_layout(margin=dict(t=10, b=10, l=10, r=10), height=350)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No findings to chart.")

with chart_col2:
    st.subheader("Findings by Source")
    source_df = pd.DataFrame([
        {"source": "SecurityHub", "count": len(sh)},
        {"source": "GuardDuty", "count": len(gd)},
        {"source": "Inspector", "count": len(insp)},
    ])
    fig2 = px.bar(source_df, x="source", y="count", color="source")
    fig2.update_layout(showlegend=False, margin=dict(t=10, b=10, l=10, r=10), height=350)
    st.plotly_chart(fig2, use_container_width=True)

st.divider()

# --- Tabs with tables -----------------------------------------------------
tab1, tab2, tab3, tab4 = st.tabs(["Security Hub", "GuardDuty", "Inspector", "CloudTrail"])

with tab1:
    if sh:
        df = pd.DataFrame(sh)[["severity", "title", "resource_type", "region",
                                "workflow_state", "created_at"]]
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No Security Hub findings.")

with tab2:
    if gd:
        df = pd.DataFrame(gd)[["severity", "title", "resource", "region", "count", "created_at"]]
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No GuardDuty findings.")

with tab3:
    if insp:
        df = pd.DataFrame(insp)[["severity", "title", "resource_type", "fix_available", "created_at"]]
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No Inspector findings.")

with tab4:
    if ct:
        df = pd.DataFrame(ct)[["event_name", "event_source", "username", "source_ip",
                                "region", "event_time"]]
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No CloudTrail events.")

st.caption("AWS SOC Dashboard — Class Project | Integrates Security Hub, GuardDuty, Inspector & CloudTrail")
