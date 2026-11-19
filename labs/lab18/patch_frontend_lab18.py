"""
Patch Threat Analysis frontend app.js to include Lab 18:
Comparative Capstone Benchmark (MongoDB vs Cassandra vs Neo4j)
"""

import os

app_js_path = r"c:\Users\aryap\OneDrive\Desktop\lab 7\frontend\js\app.js"

with open(app_js_path, "r", encoding="utf-8") as f:
    code = f.read()

# 1. Update switchTab to handle lab18
if "else if (tabName === 'lab18') loadLab18();" not in code:
    code = code.replace(
        "else if (tabName === 'lab17') loadLab17();",
        "else if (tabName === 'lab17') loadLab17();\n  else if (tabName === 'lab18') loadLab18();"
    )

lab18_js = r'''

// ══════════════════════════════════════════════════════════════════════════
// LAB 18: COMPARATIVE CAPSTONE BENCHMARK & POLYGLOT PERSISTENCE
// MongoDB (Measured) vs Apache Cassandra (Estimated) vs Neo4j (Estimated)
// Student: K. Pranav Reddy (24BTRCL098)
// ══════════════════════════════════════════════════════════════════════════

let currentLab18SubTab = 'benchmark';
let lab18CachedData = null;

async function loadLab18() {
  const container = document.getElementById('lab18-content');
  if (!container) return;
  container.innerHTML = '<div style="text-align:center;padding:50px;color:var(--text-muted);"><div class="spinner" style="margin:0 auto 16px;"></div>Loading Comparative Capstone Benchmark Studio...</div>';

  try {
    const [overviewRes, benchRes, archRes, ringsRes] = await Promise.all([
      fetch(`${API_BASE}/api/labs/lab18/overview`),
      fetch(`${API_BASE}/api/labs/lab18/benchmark`),
      fetch(`${API_BASE}/api/labs/lab18/architecture_comparison`),
      fetch(`${API_BASE}/api/labs/lab18/fraud_rings`)
    ]);

    const overview = await overviewRes.json();
    const benchData = await benchRes.json();
    const archData = await archRes.json();
    const ringsData = await ringsRes.json();

    lab18CachedData = { overview, benchData, archData, ringsData };
    renderLab18View(overview, benchData, archData, ringsData);
  } catch (err) {
    container.innerHTML = `<div class="section-panel" style="border-color:var(--red);color:var(--red);">Failed to load Lab 18 data: ${esc(err.message)}</div>`;
  }
}

function renderLab18View(overview, benchData, archData, ringsData) {
  const container = document.getElementById('lab18-content');
  if (!container) return;

  const html = `
    <!-- Lab 18 Banner -->
    <div class="lab-banner" style="background:linear-gradient(135deg, rgba(6, 182, 212, 0.12) 0%, rgba(139, 92, 246, 0.12) 100%);border:1px solid rgba(6, 182, 212, 0.35);border-radius:var(--radius-md);padding:24px;margin-bottom:24px;">
      <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:16px;">
        <div>
          <div style="display:flex;align-items:center;gap:10px;margin-bottom:8px;">
            <span class="badge" style="background:rgba(6, 182, 212, 0.2);color:var(--cyan);border:1px solid var(--cyan);font-weight:700;">LAB 18</span>
            <span class="badge" style="background:rgba(16, 185, 129, 0.2);color:var(--green);border:1px solid var(--green);">CAPSTONE BENCHMARK</span>
            <span class="badge" style="background:rgba(139, 92, 246, 0.2);color:var(--purple);border:1px solid var(--purple);">POLYGLOT ARCHITECTURE</span>
            <span class="badge" style="background:rgba(234, 179, 8, 0.2);color:#eab308;border:1px solid #eab308;">STUDENT: 24BTRCL098</span>
          </div>
          <h1 style="font-size:22px;color:var(--heading);font-weight:800;margin:0 0 8px 0;">Comparative Capstone: NoSQL Database Benchmarking</h1>
          <p style="font-size:13px;color:var(--text-muted);margin:0;max-width:880px;line-height:1.6;">
            Empirical benchmarking of <strong>MongoDB v7.0 (Measured)</strong> against architectural cost models for <strong>Apache Cassandra</strong> and <strong>Neo4j</strong> across a 10,000 synthetic financial transaction fraud detection workload (~2.0% ground-truth fraud rate).
          </p>
        </div>
        <div style="display:flex;gap:10px;align-items:center;">
          <a href="https://hub.docker.com/r/aryapranav1024/nosql-lab18" target="_blank" class="btn btn-secondary" style="display:flex;align-items:center;gap:8px;font-size:12px;background:rgba(255,255,255,0.05);border:1px solid var(--border-card);color:var(--text-primary);padding:8px 12px;border-radius:var(--radius-sm);text-decoration:none;">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="7" width="20" height="14" rx="2" ry="2"/><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/></svg>
            Docker Hub Image
          </a>
          <button class="btn btn-primary" onclick="runLiveLab18Benchmark()" id="btn-run-bench" style="background:var(--cyan);border-color:var(--cyan);display:flex;align-items:center;gap:8px;">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="5 3 19 12 5 21 5 3"/></svg>
            Run Live Benchmark
          </button>
        </div>
      </div>
    </div>

    <!-- Telemetry Status Pills -->
    <div style="display:grid;grid-template-columns:repeat(auto-fit, minmax(220px, 1fr));gap:16px;margin-bottom:24px;">
      <div class="card" style="padding:16px;border-left:4px solid var(--green);">
        <div style="font-size:11px;color:var(--text-muted);text-transform:uppercase;font-weight:600;">Primary Target</div>
        <div style="font-size:18px;font-weight:700;color:var(--heading);margin:4px 0;">MongoDB 7.0</div>
        <div style="font-size:12px;color:var(--green);font-weight:600;">[MEASURED] Live WiredTiger</div>
      </div>
      <div class="card" style="padding:16px;border-left:4px solid var(--orange);">
        <div style="font-size:11px;color:var(--text-muted);text-transform:uppercase;font-weight:600;">Baseline Ingestion</div>
        <div style="font-size:18px;font-weight:700;color:var(--heading);margin:4px 0;">Apache Cassandra</div>
        <div style="font-size:12px;color:var(--orange);font-weight:600;">[ESTIMATED] LSM-Tree Model</div>
      </div>
      <div class="card" style="padding:16px;border-left:4px solid var(--purple);">
        <div style="font-size:11px;color:var(--text-muted);text-transform:uppercase;font-weight:600;">Baseline Graph</div>
        <div style="font-size:18px;font-weight:700;color:var(--heading);margin:4px 0;">Neo4j Graph Engine</div>
        <div style="font-size:12px;color:var(--purple);font-weight:600;">[ESTIMATED] Index-Free Adjacency</div>
      </div>
      <div class="card" style="padding:16px;border-left:4px solid var(--cyan);">
        <div style="font-size:11px;color:var(--text-muted);text-transform:uppercase;font-weight:600;">Ground-Truth Dataset</div>
        <div style="font-size:18px;font-weight:700;color:var(--heading);margin:4px 0;">10,000 Txns</div>
        <div style="font-size:12px;color:var(--cyan);font-weight:600;">2.0% Calibrated Fraud Rate</div>
      </div>
    </div>

    <!-- Subtab Navigation -->
    <div style="display:flex;gap:8px;margin-bottom:20px;border-bottom:1px solid var(--border-card);padding-bottom:12px;flex-wrap:wrap;">
      <button class="btn ${currentLab18SubTab === 'benchmark' ? 'btn-primary' : ''}" onclick="switchLab18SubTab('benchmark')" style="${currentLab18SubTab === 'benchmark' ? 'background:var(--cyan);border-color:var(--cyan);' : ''}">
        Activity 1: Benchmark Matrix
      </button>
      <button class="btn ${currentLab18SubTab === 'rings' ? 'btn-primary' : ''}" onclick="switchLab18SubTab('rings')" style="${currentLab18SubTab === 'rings' ? 'background:var(--purple);border-color:var(--purple);' : ''}">
        Q5: Syndicate Fraud Rings (Graph)
      </button>
      <button class="btn ${currentLab18SubTab === 'ledger' ? 'btn-primary' : ''}" onclick="switchLab18SubTab('ledger')" style="${currentLab18SubTab === 'ledger' ? 'background:var(--green);border-color:var(--green);' : ''}">
        Transaction Ledger (10k Dataset)
      </button>
      <button class="btn ${currentLab18SubTab === 'architecture' ? 'btn-primary' : ''}" onclick="switchLab18SubTab('architecture')" style="${currentLab18SubTab === 'architecture' ? 'background:var(--orange);border-color:var(--orange);' : ''}">
        Activity 2: Polyglot Blueprint
      </button>
    </div>

    <!-- Subtab Content Container -->
    <div id="lab18-subtab-container">
      ${renderLab18SubTabContent(benchData, archData, ringsData)}
    </div>
  `;

  container.innerHTML = html;
}

function switchLab18SubTab(subTab) {
  currentLab18SubTab = subTab;
  if (!lab18CachedData) return;
  const container = document.getElementById('lab18-subtab-container');
  if (container) {
    container.innerHTML = renderLab18SubTabContent(lab18CachedData.benchData, lab18CachedData.archData, lab18CachedData.ringsData);
    if (subTab === 'ledger') loadLab18Transactions();
  }
  // Update button active states
  renderLab18View(lab18CachedData.overview, lab18CachedData.benchData, lab18CachedData.archData, lab18CachedData.ringsData);
}

function renderLab18SubTabContent(benchData, archData, ringsData) {
  if (currentLab18SubTab === 'benchmark') {
    return renderLab18BenchmarkTab(benchData);
  } else if (currentLab18SubTab === 'rings') {
    return renderLab18FraudRingsTab(ringsData);
  } else if (currentLab18SubTab === 'ledger') {
    return renderLab18TransactionsTab();
  } else if (currentLab18SubTab === 'architecture') {
    return renderLab18ArchitectureTab(archData);
  }
  return '';
}

function renderLab18BenchmarkTab(benchData) {
  const matrix = benchData.matrix || [];

  let rowsHtml = '';
  matrix.forEach(row => {
    let mongoMetric = '';
    let cassMetric = '';
    let neoMetric = '';

    if (row.query_id === 'Q4') {
      mongoMetric = `<div style="font-weight:700;color:var(--green);font-size:15px;">${row.mongodb_measured.throughput_ops_sec?.toLocaleString()} ops/s</div><div style="font-size:11px;color:var(--text-muted);">${row.mongodb_measured.latency_ms} ms/op</div>`;
      cassMetric = `<div style="font-weight:700;color:var(--orange);font-size:15px;">22,000 - 35,000 ops/s</div><div style="font-size:11px;color:var(--text-muted);">0.035 ms/op (MemTable)</div>`;
      neoMetric = `<div style="font-weight:700;color:var(--purple);font-size:15px;">1,100 - 2,200 ops/s</div><div style="font-size:11px;color:var(--text-muted);">0.650 ms/op (ACID)</div>`;
    } else {
      mongoMetric = `<div style="font-weight:700;color:var(--green);font-size:15px;">${row.mongodb_measured.latency_ms} ms</div><div style="font-size:11px;color:var(--text-muted);">P95: ${row.mongodb_measured.p95_ms} ms</div>`;
      cassMetric = `<div style="font-weight:700;color:var(--orange);font-size:15px;">${row.cassandra_estimated.latency_range}</div><div style="font-size:11px;color:var(--text-muted);">${row.cassandra_estimated.latency_ms ? row.cassandra_estimated.latency_ms + ' ms est.' : 'N/A in CQL'}</div>`;
      neoMetric = `<div style="font-weight:700;color:var(--purple);font-size:15px;">${row.neo4j_estimated.latency_range}</div><div style="font-size:11px;color:var(--text-muted);">${row.neo4j_estimated.latency_ms} ms est.</div>`;
    }

    rowsHtml += `
      <tr style="border-bottom:1px solid var(--border-card);">
        <td style="padding:14px;">
          <div style="font-weight:700;color:var(--heading);font-size:14px;">${esc(row.query_id)}: ${esc(row.name)}</div>
          <div style="font-size:11px;color:var(--cyan);margin-top:2px;">${esc(row.access_pattern)}</div>
        </td>
        <td style="padding:14px;background:rgba(16, 185, 129, 0.04);">
          ${mongoMetric}
          <div style="font-size:11px;color:var(--text-muted);margin-top:4px;">${esc(row.mongodb_measured.mechanism)}</div>
        </td>
        <td style="padding:14px;background:rgba(249, 115, 22, 0.04);">
          ${cassMetric}
          <div style="font-size:11px;color:var(--text-muted);margin-top:4px;">${esc(row.cassandra_estimated.mechanism)}</div>
        </td>
        <td style="padding:14px;background:rgba(139, 92, 246, 0.04);">
          ${neoMetric}
          <div style="font-size:11px;color:var(--text-muted);margin-top:4px;">${esc(row.neo4j_estimated.mechanism)}</div>
        </td>
        <td style="padding:14px;">
          <span class="badge" style="background:rgba(6, 182, 212, 0.15);color:var(--cyan);border:1px solid var(--cyan);font-weight:700;">${esc(row.winner)}</span>
          <div style="font-size:11px;color:var(--text-muted);margin-top:6px;line-height:1.4;">${esc(row.summary)}</div>
        </td>
      </tr>
    `;
  });

  return `
    <div class="card" style="padding:20px;margin-bottom:24px;">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;">
        <div>
          <h3 style="font-size:16px;color:var(--heading);margin:0 0 4px 0;">Empirical Performance Comparison Matrix</h3>
          <p style="font-size:12px;color:var(--text-muted);margin:0;">
            Strict separation: <strong>[MEASURED]</strong> reflects live WiredTiger B-Tree benchmark runs; <strong>[ESTIMATED]</strong> reflects architectural distributed cost models.
          </p>
        </div>
        <span class="badge" style="background:rgba(16, 185, 129, 0.15);color:var(--green);border:1px solid var(--green);">
          ${esc(benchData.telemetry_source || 'MEASURED LIVE')}
        </span>
      </div>

      <div class="table-container" style="overflow-x:auto;">
        <table class="table" style="width:100%;border-collapse:collapse;font-size:13px;">
          <thead>
            <tr style="border-bottom:2px solid var(--border-card);text-align:left;">
              <th style="padding:12px;color:var(--text-muted);font-weight:600;">Query Access Pattern</th>
              <th style="padding:12px;color:var(--green);font-weight:700;">MongoDB 7.0<br><span style="font-size:10px;font-weight:normal;color:var(--text-muted);">[MEASURED LIVE]</span></th>
              <th style="padding:12px;color:var(--orange);font-weight:700;">Apache Cassandra<br><span style="font-size:10px;font-weight:normal;color:var(--text-muted);">[ESTIMATED]</span></th>
              <th style="padding:12px;color:var(--purple);font-weight:700;">Neo4j Graph<br><span style="font-size:10px;font-weight:normal;color:var(--text-muted);">[ESTIMATED]</span></th>
              <th style="padding:12px;color:var(--cyan);font-weight:700;">Winning Architecture</th>
            </tr>
          </thead>
          <tbody>
            ${rowsHtml}
          </tbody>
        </table>
      </div>
    </div>

    <!-- Core Takeaways Cards -->
    <div style="display:grid;grid-template-columns:repeat(auto-fit, minmax(300px, 1fr));gap:16px;">
      <div class="card" style="padding:18px;">
        <h4 style="color:var(--green);font-size:14px;margin:0 0 8px 0;display:flex;align-items:center;gap:6px;">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
          MongoDB: The Operational Engine
        </h4>
        <p style="font-size:12px;color:var(--text-muted);line-height:1.5;margin:0;">
          Delivers consistent single-digit millisecond response across user point lookups (1.92 ms), ad-hoc risk score filtering (5.67 ms), and multi-stage category aggregation pipelines (31.02 ms). Ideal for stateful screening and rule evaluation.
        </p>
      </div>

      <div class="card" style="padding:18px;">
        <h4 style="color:var(--orange);font-size:14px;margin:0 0 8px 0;display:flex;align-items:center;gap:6px;">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>
          Cassandra: The High-Velocity Ledger
        </h4>
        <p style="font-size:12px;color:var(--text-muted);line-height:1.5;margin:0;">
          LSM-Tree write buffering yields unrivaled write ingestion (>25,000 ops/s). However, lack of secondary range scans across partition tokens forces heavy denormalization and makes multi-partition analytics unviable without Spark.
        </p>
      </div>

      <div class="card" style="padding:18px;">
        <h4 style="color:var(--purple);font-size:14px;margin:0 0 8px 0;display:flex;align-items:center;gap:6px;">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><line x1="8.59" y1="13.51" x2="15.42" y2="17.49"/><line x1="15.41" y1="6.51" x2="8.59" y2="10.49"/></svg>
          Neo4j: The Syndicate Fraud Detector
        </h4>
        <p style="font-size:12px;color:var(--text-muted);line-height:1.5;margin:0;">
          Index-Free Adjacency traverses shared devices and multi-hop account rings in 1.8 ms (vs 62.8 ms in MongoDB $lookup). While unmatched for entity graphs, transactional pointer locks severely limit primary transaction ledger throughput.
        </p>
      </div>
    </div>
  `;
}

function renderLab18FraudRingsTab(ringsData) {
  const rings = ringsData.rings || [];
  let ringsHtml = '';

  rings.forEach((r, idx) => {
    const fraudUsers = (r.fraud_users || []).map(u => `<span class="badge" style="background:rgba(239, 68, 68, 0.15);color:var(--red);border:1px solid var(--red);margin:2px;">${esc(u)}</span>`).join('');
    const connectedUsers = (r.connected_users || []).slice(0, 8).map(u => `<span class="badge" style="background:rgba(255,255,255,0.05);color:var(--text-primary);border:1px solid var(--border-card);margin:2px;">${esc(u)}</span>`).join('');
    const locs = (r.sample_locations || []).join(', ');

    ringsHtml += `
      <div class="card" style="padding:16px;margin-bottom:12px;border-left:4px solid var(--purple);">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
          <div style="font-size:15px;font-weight:700;color:var(--heading);display:flex;align-items:center;gap:8px;">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--purple)" stroke-width="2"><rect x="5" y="2" width="14" height="20" rx="2" ry="2"/><line x1="12" y1="18" x2="12.01" y2="18"/></svg>
            Compromised Device: <span style="color:var(--purple);font-family:monospace;">${esc(r.device_id)}</span>
          </div>
          <span class="badge" style="background:rgba(139, 92, 246, 0.2);color:var(--purple);font-weight:700;">
            ${r.connected_users_count} Associated Accounts
          </span>
        </div>
        <div style="font-size:12px;margin-bottom:6px;">
          <strong style="color:var(--red);">Confirmed Fraudulent Users:</strong> ${fraudUsers}
        </div>
        <div style="font-size:12px;margin-bottom:6px;">
          <strong style="color:var(--text-muted);">Associated Accounts on Same Device:</strong> ${connectedUsers} ${r.connected_users_count > 8 ? `<em>+${r.connected_users_count - 8} more</em>` : ''}
        </div>
        <div style="font-size:11px;color:var(--text-muted);">
          Geographic Footprint: <strong>${esc(locs || 'Multiple Cities')}</strong>
        </div>
      </div>
    `;
  });

  return `
    <div class="card" style="padding:20px;margin-bottom:20px;">
      <h3 style="font-size:16px;color:var(--heading);margin:0 0 6px 0;">Query 5: Shared Device Syndicate Fraud Rings</h3>
      <p style="font-size:12px;color:var(--text-muted);margin:0 0 16px 0;line-height:1.5;">
        Identified fraud rings where confirmed compromised user accounts share physical hardware devices (<code>device_id</code>) with other active accounts. In MongoDB, this requires multi-stage <code>$lookup</code> joins (~62 ms). In Neo4j, direct RAM pointer dereferencing resolves the entire syndicate subgraph in <strong>1.8 ms</strong>.
      </p>
      ${ringsHtml}
    </div>
  `;
}

function renderLab18TransactionsTab() {
  return `
    <div class="card" style="padding:20px;">
      <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px;margin-bottom:16px;">
        <div>
          <h3 style="font-size:16px;color:var(--heading);margin:0 0 4px 0;">Synthetic Transaction Ledger (10,000 Records)</h3>
          <p style="font-size:12px;color:var(--text-muted);margin:0;">Calibrated ground-truth fraud rate: ~2.0% with realistic merchant, geo, and device metadata.</p>
        </div>
        <div style="display:flex;gap:10px;align-items:center;">
          <label style="font-size:12px;display:flex;align-items:center;gap:6px;cursor:pointer;">
            <input type="checkbox" id="lab18-filter-fraud" onchange="loadLab18Transactions()" checked>
            <span style="color:var(--red);font-weight:600;">Only Fraudulent (is_fraud=true)</span>
          </label>
          <select id="lab18-filter-category" onchange="loadLab18Transactions()" class="input" style="font-size:12px;padding:6px 10px;">
            <option value="all">All Merchant Categories</option>
            <option value="Cryptocurrency">Cryptocurrency</option>
            <option value="Wire Transfer">Wire Transfer</option>
            <option value="Electronics">Electronics</option>
            <option value="Retail">Retail</option>
            <option value="Travel">Travel</option>
            <option value="Dining">Dining</option>
            <option value="Digital Goods">Digital Goods</option>
            <option value="ATM Withdrawal">ATM Withdrawal</option>
          </select>
        </div>
      </div>

      <div id="lab18-transactions-table-container">
        <div style="text-align:center;padding:30px;color:var(--text-muted);"><div class="spinner" style="margin:0 auto 12px;"></div>Loading transactions...</div>
      </div>
    </div>
  `;
}

async function loadLab18Transactions() {
  const container = document.getElementById('lab18-transactions-table-container');
  if (!container) return;

  const onlyFraud = document.getElementById('lab18-filter-fraud')?.checked ?? true;
  const category = document.getElementById('lab18-filter-category')?.value ?? 'all';

  try {
    const res = await fetch(`${API_BASE}/api/labs/lab18/transactions?only_fraud=${onlyFraud}&category=${encodeURIComponent(category)}&limit=25`);
    const data = await res.json();
    const items = data.items || [];

    if (items.length === 0) {
      container.innerHTML = '<div style="text-align:center;padding:30px;color:var(--text-muted);">No transactions matching criteria.</div>';
      return;
    }

    let rowsHtml = '';
    items.forEach(t => {
      const isFraud = t.is_fraud;
      const riskColor = t.risk_score >= 80 ? 'var(--red)' : t.risk_score >= 50 ? 'var(--orange)' : 'var(--green)';
      const statusBadge = isFraud 
        ? `<span class="badge" style="background:rgba(239, 68, 68, 0.15);color:var(--red);border:1px solid var(--red);font-weight:700;">FRAUD</span>`
        : `<span class="badge" style="background:rgba(16, 185, 129, 0.15);color:var(--green);border:1px solid var(--green);">LEGIT</span>`;

      rowsHtml += `
        <tr style="border-bottom:1px solid var(--border-card);">
          <td style="padding:10px;font-family:monospace;font-weight:600;">${esc(t.transaction_id)}</td>
          <td style="padding:10px;font-family:monospace;color:var(--cyan);">${esc(t.user_id)}</td>
          <td style="padding:10px;font-weight:700;color:var(--heading);">$${Number(t.amount).toFixed(2)}</td>
          <td style="padding:10px;">${esc(t.merchant)} <span style="font-size:11px;color:var(--text-muted);">(${esc(t.category)})</span></td>
          <td style="padding:10px;font-family:monospace;color:var(--purple);">${esc(t.device_id)}</td>
          <td style="padding:10px;font-weight:700;color:${riskColor};">${Number(t.risk_score).toFixed(1)}</td>
          <td style="padding:10px;">${statusBadge}</td>
          <td style="padding:10px;font-size:11px;color:var(--text-muted);">${esc(t.location?.city || '')}, ${esc(t.location?.country || '')}</td>
        </tr>
      `;
    });

    container.innerHTML = `
      <div style="font-size:12px;color:var(--text-muted);margin-bottom:8px;">Displaying <strong>${items.length}</strong> of <strong>${data.total}</strong> matching records:</div>
      <div class="table-container" style="overflow-x:auto;">
        <table class="table" style="width:100%;border-collapse:collapse;font-size:12px;">
          <thead>
            <tr style="border-bottom:2px solid var(--border-card);text-align:left;">
              <th style="padding:10px;color:var(--text-muted);">Txn ID</th>
              <th style="padding:10px;color:var(--text-muted);">User ID</th>
              <th style="padding:10px;color:var(--text-muted);">Amount</th>
              <th style="padding:10px;color:var(--text-muted);">Merchant / Category</th>
              <th style="padding:10px;color:var(--text-muted);">Device ID</th>
              <th style="padding:10px;color:var(--text-muted);">Risk Score</th>
              <th style="padding:10px;color:var(--text-muted);">Status</th>
              <th style="padding:10px;color:var(--text-muted);">Location</th>
            </tr>
          </thead>
          <tbody>
            ${rowsHtml}
          </tbody>
        </table>
      </div>
    `;
  } catch (err) {
    container.innerHTML = `<div style="color:var(--red);padding:20px;">Failed to load transactions: ${esc(err.message)}</div>`;
  }
}

function renderLab18ArchitectureTab(archData) {
  const poly = archData.polyglot_architecture || {};
  const dims = archData.dimensions || [];

  let dimRows = '';
  dims.forEach(d => {
    dimRows += `
      <tr style="border-bottom:1px solid var(--border-card);">
        <td style="padding:12px;font-weight:600;color:var(--heading);">${esc(d.attribute)}</td>
        <td style="padding:12px;color:var(--green);">${esc(d.mongodb)}</td>
        <td style="padding:12px;color:var(--orange);">${esc(d.cassandra)}</td>
        <td style="padding:12px;color:var(--purple);">${esc(d.neo4j)}</td>
      </tr>
    `;
  });

  return `
    <!-- Polyglot Diagram Card -->
    <div class="card" style="padding:22px;margin-bottom:24px;border:1px solid rgba(6, 182, 212, 0.3);">
      <h3 style="font-size:16px;color:var(--heading);margin:0 0 8px 0;display:flex;align-items:center;gap:8px;">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="var(--cyan)" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 9h18M9 21V9"/></svg>
        Tri-Tier Polyglot Persistence Architecture (Final Recommendation)
      </h3>
      <p style="font-size:13px;color:var(--text-muted);margin:0 0 16px 0;line-height:1.6;">
        No single database satisfies point queries, ad-hoc rule scoring, high-velocity ingestion, and syndicate graph traversal without unacceptable compromises. Production architectures route workloads to specialized engines:
      </p>

      <div style="display:grid;grid-template-columns:repeat(auto-fit, minmax(280px, 1fr));gap:16px;margin-bottom:16px;">
        <div class="card" style="padding:16px;background:rgba(249, 115, 22, 0.05);border-left:4px solid var(--orange);">
          <div style="font-size:11px;color:var(--orange);font-weight:700;text-transform:uppercase;">Tier 1: Ingestion Buffer</div>
          <h4 style="font-size:16px;color:var(--heading);margin:4px 0 8px 0;">${esc(poly.tier1_ingestion?.database || 'Apache Cassandra')}</h4>
          <p style="font-size:12px;color:var(--text-muted);line-height:1.5;margin:0 0 8px 0;">
            <strong>Role:</strong> ${esc(poly.tier1_ingestion?.responsibility || '')}
          </p>
          <div style="font-size:11px;color:var(--orange);font-weight:600;">
            ✓ ${esc(poly.tier1_ingestion?.benefit || '')}
          </div>
        </div>

        <div class="card" style="padding:16px;background:rgba(16, 185, 129, 0.05);border-left:4px solid var(--green);">
          <div style="font-size:11px;color:var(--green);font-weight:700;text-transform:uppercase;">Tier 2: Operational Engine</div>
          <h4 style="font-size:16px;color:var(--heading);margin:4px 0 8px 0;">${esc(poly.tier2_operational?.database || 'MongoDB 7.0')}</h4>
          <p style="font-size:12px;color:var(--text-muted);line-height:1.5;margin:0 0 8px 0;">
            <strong>Role:</strong> ${esc(poly.tier2_operational?.responsibility || '')}
          </p>
          <div style="font-size:11px;color:var(--green);font-weight:600;">
            ✓ ${esc(poly.tier2_operational?.benefit || '')}
          </div>
        </div>

        <div class="card" style="padding:16px;background:rgba(139, 92, 246, 0.05);border-left:4px solid var(--purple);">
          <div style="font-size:11px;color:var(--purple);font-weight:700;text-transform:uppercase;">Tier 3: Syndicate Discovery</div>
          <h4 style="font-size:16px;color:var(--heading);margin:4px 0 8px 0;">${esc(poly.tier3_syndicate?.database || 'Neo4j Graph')}</h4>
          <p style="font-size:12px;color:var(--text-muted);line-height:1.5;margin:0 0 8px 0;">
            <strong>Role:</strong> ${esc(poly.tier3_syndicate?.responsibility || '')}
          </p>
          <div style="font-size:11px;color:var(--purple);font-weight:600;">
            ✓ ${esc(poly.tier3_syndicate?.benefit || '')}
          </div>
        </div>
      </div>
    </div>

    <!-- Architectural Dimensions Matrix -->
    <div class="card" style="padding:20px;">
      <h3 style="font-size:16px;color:var(--heading);margin:0 0 14px 0;">Architectural Dimensions & CAP Tradeoffs</h3>
      <div class="table-container" style="overflow-x:auto;">
        <table class="table" style="width:100%;border-collapse:collapse;font-size:12px;">
          <thead>
            <tr style="border-bottom:2px solid var(--border-card);text-align:left;">
              <th style="padding:10px;color:var(--text-muted);">Dimension</th>
              <th style="padding:10px;color:var(--green);">MongoDB 7.0</th>
              <th style="padding:10px;color:var(--orange);">Apache Cassandra</th>
              <th style="padding:10px;color:var(--purple);">Neo4j Graph</th>
            </tr>
          </thead>
          <tbody>
            ${dimRows}
          </tbody>
        </table>
      </div>
    </div>
  `;
}

async function runLiveLab18Benchmark() {
  const btn = document.getElementById('btn-run-bench');
  if (btn) {
    btn.disabled = true;
    btn.innerHTML = '<div class="spinner" style="width:14px;height:14px;"></div> Benchmarking...';
  }

  showToast('Executing live MongoDB capstone benchmark (15 iterations)...');

  try {
    const res = await fetch(`${API_BASE}/api/labs/lab18/run_benchmark`, { method: 'POST' });
    if (!res.ok) throw new Error('Benchmark failed');
    showToast('Live benchmark completed successfully!');
    await loadLab18();
  } catch (err) {
    showToast('Benchmark run failed: ' + err.message);
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="5 3 19 12 5 21 5 3"/></svg> Run Live Benchmark';
    }
  }
}
'''

with open(app_js_path, "w", encoding="utf-8") as f:
    f.write(code + "\n" + lab18_js)

print(f"[SUCCESS] Patched {app_js_path} with Lab 18 functions.")
