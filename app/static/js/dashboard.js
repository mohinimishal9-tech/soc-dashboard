const SEVERITY_COLORS = {
  CRITICAL: "#ff4d5e",
  HIGH: "#ff9f43",
  MEDIUM: "#ffd43b",
  LOW: "#51cf66",
  INFORMATIONAL: "#74c0fc",
};

let severityChart, sourceChart;

async function fetchJSON(url) {
  const res = await fetch(url);
  return res.json();
}

function sevPill(sev) {
  const s = (sev || "INFORMATIONAL").toUpperCase();
  return `<span class="sev-pill sev-${s}">${s}</span>`;
}

function fmtTime(t) {
  if (!t) return "--";
  try {
    return new Date(t).toLocaleString();
  } catch {
    return t;
  }
}

function renderTable(bodyId, rows, rowFn) {
  const tbody = document.getElementById(bodyId);
  tbody.innerHTML = rows.map(rowFn).join("");
}

function renderSeverityChart(counts) {
  const ctx = document.getElementById("severityChart");
  const labels = Object.keys(counts);
  const data = Object.values(counts);
  const colors = labels.map(l => SEVERITY_COLORS[l] || "#888");

  if (severityChart) severityChart.destroy();
  severityChart = new Chart(ctx, {
    type: "doughnut",
    data: { labels, datasets: [{ data, backgroundColor: colors, borderWidth: 0 }] },
    options: {
      plugins: { legend: { position: "bottom", labels: { color: "#e6ebf5" } } },
    },
  });
}

function renderSourceChart(bySource) {
  const ctx = document.getElementById("sourceChart");
  const labels = Object.keys(bySource);
  const data = Object.values(bySource);

  if (sourceChart) sourceChart.destroy();
  sourceChart = new Chart(ctx, {
    type: "bar",
    data: {
      labels,
      datasets: [{ label: "Findings", data, backgroundColor: "#4f8cff", borderRadius: 6 }],
    },
    options: {
      plugins: { legend: { display: false } },
      scales: {
        x: { ticks: { color: "#8b95ab" }, grid: { color: "#2a3350" } },
        y: { ticks: { color: "#8b95ab" }, grid: { color: "#2a3350" }, beginAtZero: true },
      },
    },
  });
}

async function loadSummary() {
  const summary = await fetchJSON("/api/findings/summary");
  document.getElementById("kpiTotalFindings").textContent = summary.total_findings;
  document.getElementById("kpiCritical").textContent = summary.severity_counts.CRITICAL || 0;
  document.getElementById("kpiHigh").textContent = summary.severity_counts.HIGH || 0;
  document.getElementById("kpiEvents").textContent = summary.total_cloudtrail_events;

  renderSeverityChart(summary.severity_counts);
  renderSourceChart(summary.by_source);

  const badge = document.getElementById("demoBadge");
  badge.classList.toggle("hidden", !summary.demo_mode);

  document.getElementById("lastUpdated").textContent = "Updated " + new Date().toLocaleTimeString();
}

async function loadSecurityHub() {
  const data = await fetchJSON("/api/findings/securityhub");
  renderTable("securityhubBody", data.findings, f => `
    <tr>
      <td>${sevPill(f.severity)}</td>
      <td>${f.title}</td>
      <td>${f.resource_type}</td>
      <td>${f.region}</td>
      <td>${f.workflow_state}</td>
      <td>${fmtTime(f.created_at)}</td>
    </tr>`);
}

async function loadGuardDuty() {
  const data = await fetchJSON("/api/findings/guardduty");
  renderTable("guarddutyBody", data.findings, f => `
    <tr>
      <td>${sevPill(f.severity)}</td>
      <td>${f.title}</td>
      <td>${f.resource}</td>
      <td>${f.region}</td>
      <td>${f.count}</td>
      <td>${fmtTime(f.created_at)}</td>
    </tr>`);
}

async function loadInspector() {
  const data = await fetchJSON("/api/findings/inspector");
  renderTable("inspectorBody", data.findings, f => `
    <tr>
      <td>${sevPill(f.severity)}</td>
      <td>${f.title}</td>
      <td>${f.resource_type}</td>
      <td>${f.fix_available}</td>
      <td>${fmtTime(f.created_at)}</td>
    </tr>`);
}

async function loadCloudTrail() {
  const data = await fetchJSON("/api/events/cloudtrail");
  renderTable("cloudtrailBody", data.events, e => `
    <tr>
      <td>${e.event_name}</td>
      <td>${e.event_source}</td>
      <td>${e.username}</td>
      <td>${e.source_ip}</td>
      <td>${e.region}</td>
      <td>${fmtTime(e.event_time)}</td>
    </tr>`);
}

async function loadAll() {
  await Promise.all([
    loadSummary(),
    loadSecurityHub(),
    loadGuardDuty(),
    loadInspector(),
    loadCloudTrail(),
  ]);
}

function setupTabs() {
  document.querySelectorAll(".tab-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
      document.querySelectorAll(".tab-content").forEach(c => c.classList.remove("active"));
      btn.classList.add("active");
      document.getElementById("tab-" + btn.dataset.tab).classList.add("active");
    });
  });
}

document.getElementById("refreshBtn").addEventListener("click", loadAll);
setupTabs();
loadAll();
setInterval(loadAll, 60000); // auto-refresh every 60s
