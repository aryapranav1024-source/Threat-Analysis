import os
import re

app_js_path = r"..\lab 7\frontend\js\app.js"

with open(app_js_path, "r", encoding="utf-8") as f:
    code = f.read()

# 1. Update tabTitles
if "'lab16':" not in code:
    code = code.replace(
        "  lab15: 'Lab 15: Multi-Tenant SaaS Architecture & Zero-Downtime Migration',",
        "  lab15: 'Lab 15: Multi-Tenant SaaS Architecture & Zero-Downtime Migration',\n  lab16: 'Lab 16: Polyglot Data Modeling & Hybrid Query Service',"
    )

# 2. Update switchTab
if "tabName === 'lab16'" not in code:
    code = code.replace(
        "  else if (tabName === 'lab15') loadLab15();",
        "  else if (tabName === 'lab15') loadLab15();\n  else if (tabName === 'lab16') loadLab16();"
    )

# 3. Append Lab 16 JavaScript UI Logic
lab16_js = '''

// ══════════════════════════════════════════════════════════════════════════
// LAB 16: POLYGLOT DATA MODELING & HYBRID QUERY SERVICE
// ══════════════════════════════════════════════════════════════════════════

let lab16CachedData = null;
let currentLab16SubTab = 'router';

async function loadLab16() {
  const container = document.getElementById('lab16-content');
  if (!container) return;
  container.innerHTML = '<div style="text-align:center;padding:50px;color:var(--text-muted);"><div class="spinner" style="margin:0 auto 16px;"></div>Loading Polyglot Persistence Architecture & Hybrid Query Service...</div>';

  try {
    const [schemasRes, casesRes, topoRes, benchRes] = await Promise.all([
      fetch(`${API_BASE}/api/labs/lab16/schemas`),
      fetch(`${API_BASE}/api/labs/lab16/cases`),
      fetch(`${API_BASE}/api/labs/lab16/topology`),
      fetch(`${API_BASE}/api/labs/lab16/benchmarks`)
    ]);
    const schemasData = await schemasRes.json();
    const casesData = await casesRes.json();
    const topoData = await topoRes.json();
    const benchData = await benchRes.json();

    lab16CachedData = { schemasData, casesData, topoData, benchData };
    renderLab16View(schemasData, casesData, topoData, benchData);
  } catch (err) {
    container.innerHTML = `<div class="section-panel" style="border-color:var(--red);color:var(--red);">Failed to load Lab 16 data: ${esc(err.message)}</div>`;
  }
}

function renderLab16View(schemasData, casesData, topoData, benchData) {
  const container = document.getElementById('lab16-content');
  if (!container) return;

  const html = `
    <!-- Lab 16 Header Banner -->
    <div class="lab-banner" style="background:linear-gradient(135deg, rgba(139, 92, 246, 0.12) 0%, rgba(6, 182, 212, 0.12) 100%);border:1px solid rgba(139, 92, 246, 0.35);border-radius:var(--radius-md);padding:24px;margin-bottom:24px;">
      <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:16px;">
        <div>
          <div style="display:flex;align-items:center;gap:10px;margin-bottom:8px;">
            <span class="badge" style="background:rgba(139, 92, 246, 0.2);color:var(--purple);border:1px solid var(--purple);font-weight:700;">LAB 16</span>
            <span class="badge" style="background:rgba(6, 182, 212, 0.2);color:var(--cyan);border:1px solid var(--cyan);">POLYGLOT PERSISTENCE</span>
            <span class="badge" style="background:rgba(16, 185, 129, 0.2);color:var(--green);border:1px solid var(--green);">DYNAMIC QUERY ROUTING</span>
          </div>
          <h1 style="font-size:22px;color:var(--heading);font-weight:800;margin:0 0 8px 0;">Polyglot Data Modeling & Hybrid Query Service</h1>
          <p style="font-size:13px;color:var(--text-muted);margin:0;max-width:860px;line-height:1.6;">
            A real-world financial fraud intelligence platform leveraging the complementary architectural biases of three database families: 
            <strong>MongoDB</strong> for flexible document point lookups and attribute range filtering, <strong>Apache Cassandra</strong> for partition-clustered high-velocity time-series writes, and <strong>Neo4j / Graph Engine</strong> for native recursive multi-hop fraud ring traversal.
          </p>
        </div>
        <div style="display:flex;gap:10px;">
          <button class="btn btn-primary" onclick="seedLab16Data()" style="background:var(--purple);border-color:var(--purple);display:flex;align-items:center;gap:8px;">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21.5 2v6h-6M21.34 15.57a10 10 0 1 1-.57-8.38l5.67-5.67"/></svg>
            Reset & Re-seed Data
          </button>
        </div>
      </div>

      <!-- Quick Metrics Strip -->
      <div style="display:grid;grid-template-columns:repeat(auto-fit, minmax(200px, 1fr));gap:14px;margin-top:20px;">
        <div style="background:var(--bg-card);border:1px solid var(--border-card);border-radius:var(--radius-sm);padding:14px;">
          <div style="font-size:11px;color:var(--text-dim);text-transform:uppercase;letter-spacing:0.05em;margin-bottom:4px;">Document Store</div>
          <div style="font-size:16px;font-weight:700;color:var(--cyan);display:flex;align-items:center;gap:6px;">
            MongoDB v8.3
            <span style="font-size:11px;padding:2px 6px;border-radius:4px;background:rgba(6,182,212,0.15);color:var(--cyan);">${casesData.count || 6} Cases</span>
          </div>
          <div style="font-size:11px;color:var(--text-muted);margin-top:4px;">Atomic reads & compound filters</div>
        </div>

        <div style="background:var(--bg-card);border:1px solid var(--border-card);border-radius:var(--radius-sm);padding:14px;">
          <div style="font-size:11px;color:var(--text-dim);text-transform:uppercase;letter-spacing:0.05em;margin-bottom:4px;">Wide-Column Store</div>
          <div style="font-size:16px;font-weight:700;color:var(--orange);display:flex;align-items:center;gap:6px;">
            Apache Cassandra
            <span style="font-size:11px;padding:2px 6px;border-radius:4px;background:rgba(249,115,22,0.15);color:var(--orange);">CQL Table</span>
          </div>
          <div style="font-size:11px;color:var(--text-muted);margin-top:4px;">Partition ((suspect), time DESC)</div>
        </div>

        <div style="background:var(--bg-card);border:1px solid var(--border-card);border-radius:var(--radius-sm);padding:14px;">
          <div style="font-size:11px;color:var(--text-dim);text-transform:uppercase;letter-spacing:0.05em;margin-bottom:4px;">Graph Engine</div>
          <div style="font-size:16px;font-weight:700;color:var(--purple);display:flex;align-items:center;gap:6px;">
            Neo4j / In-Memory
            <span style="font-size:11px;padding:2px 6px;border-radius:4px;background:rgba(139,92,246,0.15);color:var(--purple);">${topoData.suspect_count || 6} Suspects</span>
          </div>
          <div style="font-size:11px;color:var(--text-muted);margin-top:4px;">Index-free pointer traversal</div>
        </div>

        <div style="background:var(--bg-card);border:1px solid var(--border-card);border-radius:var(--radius-sm);padding:14px;">
          <div style="font-size:11px;color:var(--text-dim);text-transform:uppercase;letter-spacing:0.05em;margin-bottom:4px;">Fraud Ring Status</div>
          <div style="font-size:16px;font-weight:700;color:var(--red);display:flex;align-items:center;gap:6px;">
            Ring Detected
            <span style="font-size:11px;padding:2px 6px;border-radius:4px;background:rgba(239,68,68,0.15);color:var(--red);">4 Connected</span>
          </div>
          <div style="font-size:11px;color:var(--text-muted);margin-top:4px;">Via DEV-500 & DEV-777</div>
        </div>
      </div>
    </div>

    <!-- Sub-tabs Navigation -->
    <div style="display:flex;gap:10px;border-bottom:1px solid var(--border-card);margin-bottom:20px;padding-bottom:10px;flex-wrap:wrap;">
      <button class="btn ${currentLab16SubTab === 'router' ? 'btn-primary' : 'btn-outline'}" onclick="switchLab16SubTab('router')" style="font-size:13px;background:${currentLab16SubTab === 'router' ? 'var(--purple)' : 'transparent'};border-color:var(--purple);">
        ⚡ Interactive Hybrid Query Router
      </button>
      <button class="btn ${currentLab16SubTab === 'schemas' ? 'btn-primary' : 'btn-outline'}" onclick="switchLab16SubTab('schemas')" style="font-size:13px;background:${currentLab16SubTab === 'schemas' ? 'var(--purple)' : 'transparent'};border-color:var(--purple);">
        📑 Three-Way Schema Comparison
      </button>
      <button class="btn ${currentLab16SubTab === 'topology' ? 'btn-primary' : 'btn-outline'}" onclick="switchLab16SubTab('topology')" style="font-size:13px;background:${currentLab16SubTab === 'topology' ? 'var(--purple)' : 'transparent'};border-color:var(--purple);">
        🕸️ Device-Sharing Graph Topology
      </button>
      <button class="btn ${currentLab16SubTab === 'benchmarks' ? 'btn-primary' : 'btn-outline'}" onclick="switchLab16SubTab('benchmarks')" style="font-size:13px;background:${currentLab16SubTab === 'benchmarks' ? 'var(--purple)' : 'transparent'};border-color:var(--purple);">
        📊 Decision Matrix & Complexity Benchmarks
      </button>
    </div>

    <!-- Sub-tab Containers -->
    <div id="lab16-subtab-router" style="display:${currentLab16SubTab === 'router' ? 'block' : 'none'};">
      ${buildLab16RouterHtml(casesData)}
    </div>

    <div id="lab16-subtab-schemas" style="display:${currentLab16SubTab === 'schemas' ? 'block' : 'none'};">
      ${buildLab16SchemasHtml(schemasData)}
    </div>

    <div id="lab16-subtab-topology" style="display:${currentLab16SubTab === 'topology' ? 'block' : 'none'};">
      ${buildLab16TopologyHtml(topoData)}
    </div>

    <div id="lab16-subtab-benchmarks" style="display:${currentLab16SubTab === 'benchmarks' ? 'block' : 'none'};">
      ${buildLab16BenchmarksHtml(benchData)}
    </div>
  `;

  container.innerHTML = html;

  // If on topology tab, render SVG
  if (currentLab16SubTab === 'topology') {
    setTimeout(() => renderTopologySvg(topoData.nodes, topoData.edges), 60);
  }
}

function switchLab16SubTab(subTab) {
  currentLab16SubTab = subTab;
  if (lab16CachedData) {
    renderLab16View(lab16CachedData.schemasData, lab16CachedData.casesData, lab16CachedData.topoData, lab16CachedData.benchData);
  }
}

// ─── Sub-Tab 1: Hybrid Query Router ───
function buildLab16RouterHtml(casesData) {
  return `
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-bottom:24px;">
      <!-- Query Dispatcher Controls -->
      <div class="section-panel" style="padding:20px;background:var(--bg-card);border:1px solid var(--border-card);border-radius:var(--radius-md);">
        <h3 style="font-size:15px;color:var(--heading);margin-bottom:14px;display:flex;align-items:center;gap:8px;">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="color:var(--cyan);"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>
          Smart Query Dispatcher & Execution
        </h3>
        <p style="font-size:12px;color:var(--text-muted);margin-bottom:16px;">
          Choose an access pattern or run one of the canonical lab queries. The service inspects the query type and mechanically routes it to the optimal storage engine.
        </p>

        <!-- Quick Preset Buttons -->
        <div style="margin-bottom:18px;">
          <label style="font-size:11px;font-weight:700;color:var(--text-dim);text-transform:uppercase;display:block;margin-bottom:8px;">Canonical Lab 16 Queries:</label>
          <div style="display:flex;flex-direction:column;gap:8px;">
            <button class="btn btn-outline" onclick="runLab16HybridQuery('point_lookup', {case_id:'FC-001'})" style="text-align:left;font-size:12px;padding:8px 12px;display:flex;justify-content:space-between;align-items:center;">
              <span><strong>Query 1:</strong> Point Lookup <code>case_id='FC-001'</code></span>
              <span class="badge" style="background:rgba(6,182,212,0.15);color:var(--cyan);font-size:10px;">➔ MongoDB</span>
            </button>
            <button class="btn btn-outline" onclick="runLab16HybridQuery('attribute_filter', {risk_threshold:0.80})" style="text-align:left;font-size:12px;padding:8px 12px;display:flex;justify-content:space-between;align-items:center;">
              <span><strong>Query 2:</strong> Attribute Range Filter <code>risk_score &gt; 0.80</code></span>
              <span class="badge" style="background:rgba(6,182,212,0.15);color:var(--cyan);font-size:10px;">➔ MongoDB</span>
            </button>
            <button class="btn btn-outline" onclick="runLab16HybridQuery('graph_traversal', {suspect_id:'U-101', max_hops:3})" style="text-align:left;font-size:12px;padding:8px 12px;display:flex;justify-content:space-between;align-items:center;">
              <span><strong>Query 3:</strong> Multi-Hop Device Sharing <code>U-101 (3 Hops)</code></span>
              <span class="badge" style="background:rgba(139,92,246,0.15);color:var(--purple);font-size:10px;">➔ Graph Engine</span>
            </button>
          </div>
        </div>

        <div style="border-top:1px solid var(--border-card);padding-top:14px;margin-bottom:14px;">
          <label style="font-size:11px;font-weight:700;color:var(--text-dim);text-transform:uppercase;display:block;margin-bottom:8px;">Custom Query Builder:</label>
          
          <div style="margin-bottom:12px;">
            <label style="font-size:12px;color:var(--text-muted);display:block;margin-bottom:4px;">Query Intent:</label>
            <select id="lab16-query-type" class="search-input" style="width:100%;padding:8px;background:var(--bg-input);border:1px solid var(--border-card);border-radius:var(--radius-sm);color:var(--text);" onchange="toggleLab16QueryInputs()">
              <option value="point_lookup">Point Lookup by Case ID (Document Key)</option>
              <option value="attribute_filter">Attribute Range Filter (Risk Score Threshold)</option>
              <option value="graph_traversal">Multi-Hop Traversal (Device Sharing Ring)</option>
            </select>
          </div>

          <!-- Input for Point Lookup -->
          <div id="lab16-input-point" style="margin-bottom:12px;">
            <label style="font-size:12px;color:var(--text-muted);display:block;margin-bottom:4px;">Select Case ID:</label>
            <select id="lab16-case-id" class="search-input" style="width:100%;padding:8px;background:var(--bg-input);border:1px solid var(--border-card);border-radius:var(--radius-sm);color:var(--text);">
              <option value="FC-001">FC-001 (Arjun - ₹50,000 - FakeStore - Risk: 0.92)</option>
              <option value="FC-002">FC-002 (Sneha - ₹2,200 - QuickPay - Risk: 0.41)</option>
              <option value="FC-003">FC-003 (Rahul - ₹71,000 - CryptoBridge - Risk: 0.88)</option>
              <option value="FC-004">FC-004 (Priya - ₹500 - CoffeeShop - Risk: 0.12)</option>
              <option value="FC-005">FC-005 (Vikram - ₹42,000 - ElectronicsHub - Risk: 0.84)</option>
              <option value="FC-006">FC-006 (Ananya - ₹1,500 - AppStore - Risk: 0.25)</option>
            </select>
          </div>

          <!-- Input for Attribute Filter -->
          <div id="lab16-input-filter" style="margin-bottom:12px;display:none;">
            <label style="font-size:12px;color:var(--text-muted);display:flex;justify-content:space-between;margin-bottom:4px;">
              <span>Minimum Risk Score:</span>
              <span id="lab16-risk-val" style="font-weight:700;color:var(--cyan);">0.80</span>
            </label>
            <input type="range" id="lab16-risk-slider" min="0.10" max="0.95" step="0.05" value="0.80" style="width:100%;" oninput="document.getElementById('lab16-risk-val').textContent = parseFloat(this.value).toFixed(2)">
          </div>

          <!-- Input for Graph Traversal -->
          <div id="lab16-input-graph" style="margin-bottom:12px;display:none;">
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;">
              <div>
                <label style="font-size:12px;color:var(--text-muted);display:block;margin-bottom:4px;">Starting Suspect:</label>
                <select id="lab16-suspect-id" class="search-input" style="width:100%;padding:8px;background:var(--bg-input);border:1px solid var(--border-card);border-radius:var(--radius-sm);color:var(--text);">
                  <option value="U-101">U-101 (Arjun Sharma)</option>
                  <option value="U-102">U-102 (Sneha Roy)</option>
                  <option value="U-103">U-103 (Rahul Verma)</option>
                  <option value="U-104">U-104 (Priya Nair)</option>
                  <option value="U-105">U-105 (Vikram Patel)</option>
                  <option value="U-106">U-106 (Ananya Das)</option>
                </select>
              </div>
              <div>
                <label style="font-size:12px;color:var(--text-muted);display:block;margin-bottom:4px;">Max Degrees / Hops:</label>
                <select id="lab16-max-hops" class="search-input" style="width:100%;padding:8px;background:var(--bg-input);border:1px solid var(--border-card);border-radius:var(--radius-sm);color:var(--text);">
                  <option value="1">1 Hop (Direct Neighbors)</option>
                  <option value="2">2 Hops</option>
                  <option value="3" selected>3 Hops (Deep Ring Traversal)</option>
                  <option value="4">4 Hops</option>
                </select>
              </div>
            </div>
          </div>

          <button class="btn btn-primary" onclick="submitCustomLab16Query()" style="width:100%;background:var(--cyan);border-color:var(--cyan);font-weight:700;">
            🚀 Dispatch Query to Polyglot Engine
          </button>
        </div>
      </div>

      <!-- Live Execution Telemetry & Result -->
      <div id="lab16-result-card" class="section-panel" style="padding:20px;background:var(--bg-card);border:1px solid var(--border-card);border-radius:var(--radius-md);">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px;">
          <h3 style="font-size:15px;color:var(--heading);margin:0;display:flex;align-items:center;gap:8px;">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="color:var(--green);"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>
            Routing Decision & Execution Output
          </h3>
          <span id="lab16-exec-time" class="badge" style="background:rgba(16,185,129,0.15);color:var(--green);display:none;">0.00 ms</span>
        </div>

        <div id="lab16-result-body">
          <div style="text-align:center;padding:50px 20px;color:var(--text-dim);border:1px dashed var(--border-card);border-radius:var(--radius-sm);">
            <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" style="margin-bottom:10px;opacity:0.5;"><circle cx="12" cy="12" r="10"/><path d="m4.93 4.93 4.24 4.24M14.83 9.17l4.24-4.24M14.83 14.83l4.24 4.24M9.17 14.83l-4.24 4.24"/></svg>
            <p style="margin:0;font-size:13px;">Select a preset or custom query on the left to see dynamic backend routing and live query execution results.</p>
          </div>
        </div>
      </div>
    </div>
  `;
}

function toggleLab16QueryInputs() {
  const type = document.getElementById('lab16-query-type').value;
  document.getElementById('lab16-input-point').style.display = type === 'point_lookup' ? 'block' : 'none';
  document.getElementById('lab16-input-filter').style.display = type === 'attribute_filter' ? 'block' : 'none';
  document.getElementById('lab16-input-graph').style.display = type === 'graph_traversal' ? 'block' : 'none';
}

function submitCustomLab16Query() {
  const type = document.getElementById('lab16-query-type').value;
  let params = {};
  if (type === 'point_lookup') {
    params.case_id = document.getElementById('lab16-case-id').value;
  } else if (type === 'attribute_filter') {
    params.risk_threshold = parseFloat(document.getElementById('lab16-risk-slider').value);
  } else if (type === 'graph_traversal') {
    params.suspect_id = document.getElementById('lab16-suspect-id').value;
    params.max_hops = parseInt(document.getElementById('lab16-max-hops').value, 10);
  }
  runLab16HybridQuery(type, params);
}

async function runLab16HybridQuery(type, params) {
  const resultBody = document.getElementById('lab16-result-body');
  const execTimeBadge = document.getElementById('lab16-exec-time');
  if (!resultBody) return;

  resultBody.innerHTML = '<div style="text-align:center;padding:40px;color:var(--text-muted);"><div class="spinner" style="margin:0 auto 12px;"></div>Routing query to backend engine...</div>';

  try {
    const payload = { query_type: type, ...params };
    const res = await fetch(`${API_BASE}/api/labs/lab16/query`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    renderLab16QueryResult(data);
  } catch (err) {
    resultBody.innerHTML = `<div class="badge" style="background:rgba(239,68,68,0.15);color:var(--red);padding:10px;width:100%;text-align:center;">Query failed: ${esc(err.message)}</div>`;
  }
}

function renderLab16QueryResult(data) {
  const resultBody = document.getElementById('lab16-result-body');
  const execTimeBadge = document.getElementById('lab16-exec-time');
  if (!resultBody) return;

  if (execTimeBadge) {
    execTimeBadge.textContent = `${data.execution_ms} ms`;
    execTimeBadge.style.display = 'inline-block';
  }

  const isMongo = data.routed_to.includes('MongoDB');
  const backendBadgeColor = isMongo ? 'var(--cyan)' : 'var(--purple)';
  const backendBg = isMongo ? 'rgba(6,182,212,0.15)' : 'rgba(139,92,246,0.15)';

  let resultsHtml = '';
  if (data.query_type === 'point_lookup') {
    const item = data.results[0];
    if (item) {
      resultsHtml = `
        <div style="background:var(--bg-input);border:1px solid var(--border-card);border-radius:var(--radius-sm);padding:14px;margin-bottom:12px;">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
            <span style="font-weight:700;color:var(--heading);font-size:14px;">${esc(item.case_id)} · ${esc(item.suspect_name || item.suspect_id)}</span>
            <span class="badge" style="background:${item.risk_score >= 0.8 ? 'rgba(239,68,68,0.2)' : 'rgba(16,185,129,0.2)'};color:${item.risk_score >= 0.8 ? 'var(--red)' : 'var(--green)'};">Risk: ${item.risk_score}</span>
          </div>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;font-size:12px;color:var(--text-muted);margin-bottom:8px;">
            <div><strong>Amount:</strong> ₹${item.amount.toLocaleString()} ${esc(item.currency || 'INR')}</div>
            <div><strong>Merchant:</strong> ${esc(item.merchant)}</div>
            <div><strong>Timestamp:</strong> ${esc(item.timestamp)}</div>
            <div><strong>Linked Accounts:</strong> ${item.linked_accounts ? item.linked_accounts.join(', ') : 'None'}</div>
          </div>
          <div style="display:flex;gap:4px;flex-wrap:wrap;">
            ${(item.tags || []).map(t => `<span style="font-size:10px;padding:2px 6px;border-radius:3px;background:var(--border-card);color:var(--text-dim);">${esc(t)}</span>`).join('')}
          </div>
        </div>
      `;
    } else {
      resultsHtml = '<div style="color:var(--text-muted);font-size:12px;">No document matched the provided case ID.</div>';
    }
  } else if (data.query_type === 'attribute_filter') {
    resultsHtml = `
      <div style="margin-bottom:8px;font-size:12px;color:var(--text-dim);">Matched <strong>${data.count}</strong> high-risk cases sorted by risk descending:</div>
      <div style="display:flex;flex-direction:column;gap:8px;max-height:220px;overflow-y:auto;margin-bottom:12px;">
        ${data.results.map(item => `
          <div style="background:var(--bg-input);border:1px solid var(--border-card);border-radius:var(--radius-sm);padding:10px;display:flex;justify-content:space-between;align-items:center;">
            <div>
              <div style="font-weight:700;color:var(--heading);font-size:12px;">${esc(item.case_id)}: ${esc(item.suspect_name || item.suspect_id)}</div>
              <div style="font-size:11px;color:var(--text-muted);">₹${item.amount.toLocaleString()} · ${esc(item.merchant)}</div>
            </div>
            <span class="badge" style="background:rgba(239,68,68,0.18);color:var(--red);font-weight:700;">Score ${item.risk_score}</span>
          </div>
        `).join('')}
      </div>
    `;
  } else if (data.query_type === 'graph_traversal') {
    resultsHtml = `
      <div style="margin-bottom:8px;font-size:12px;color:var(--text-dim);">Found <strong>${data.connected_suspect_count}</strong> connected suspects across degrees of device-sharing:</div>
      <div style="display:flex;flex-direction:column;gap:8px;max-height:240px;overflow-y:auto;margin-bottom:12px;">
        ${data.results.map(r => `
          <div style="background:var(--bg-input);border:1px solid var(--border-card);border-radius:var(--radius-sm);padding:10px;">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px;">
              <span style="font-weight:700;color:var(--heading);font-size:13px;">${esc(r.suspect_id)} (${esc(r.suspect_name)})</span>
              <span class="badge" style="background:rgba(139,92,246,0.2);color:var(--purple);font-size:11px;font-weight:700;">${r.hops} Hop${r.hops > 1 ? 's' : ''} Away</span>
            </div>
            <div style="font-size:11px;color:var(--cyan);font-family:var(--font-mono);margin-bottom:2px;">Path: ${esc(r.path)}</div>
            <div style="font-size:11px;color:var(--text-dim);">Shared Hardware/Token: ${r.shared_devices.map(d => `<span style="color:var(--orange);font-weight:600;">${esc(d)}</span>`).join(', ')}</div>
          </div>
        `).join('')}
      </div>
    `;
  }

  const html = `
    <!-- Routing Header -->
    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:14px;background:${backendBg};border:1px solid ${backendBadgeColor};border-radius:var(--radius-sm);padding:10px 14px;">
      <div>
        <div style="font-size:10px;text-transform:uppercase;color:${backendBadgeColor};font-weight:700;">Routed Target Database</div>
        <div style="font-size:15px;font-weight:800;color:var(--heading);">${esc(data.routed_to)}</div>
      </div>
      <span class="badge" style="background:${backendBadgeColor};color:#fff;font-weight:700;">${esc(data.route_category)}</span>
    </div>

    <!-- Query Syntax Block -->
    <div style="margin-bottom:14px;">
      <div style="font-size:11px;color:var(--text-dim);margin-bottom:4px;font-weight:700;">EXECUTED DATABASE OPERATION:</div>
      <pre style="background:var(--bg-card);border:1px solid var(--border-card);padding:10px;border-radius:var(--radius-sm);font-size:11px;color:var(--cyan);font-family:var(--font-mono);overflow-x:auto;margin:0;">${esc(data.query_syntax)}</pre>
    </div>

    <!-- Results List -->
    <div style="margin-bottom:14px;">
      <div style="font-size:11px;color:var(--text-dim);margin-bottom:4px;font-weight:700;">RETURNED RESULT SET:</div>
      ${resultsHtml}
    </div>

    <!-- Routing Justification -->
    <div style="background:rgba(16,185,129,0.08);border-left:3px solid var(--green);padding:10px 12px;border-radius:0 var(--radius-sm) var(--radius-sm) 0;margin-bottom:14px;">
      <div style="font-size:11px;font-weight:700;color:var(--green);margin-bottom:2px;">WHY THIS ENGINE?</div>
      <p style="font-size:12px;color:var(--text-muted);margin:0;line-height:1.5;">${esc(data.routing_justification)}</p>
    </div>

    <!-- Anti-Pattern Alert -->
    <div style="background:rgba(239,68,68,0.06);border:1px solid rgba(239,68,68,0.25);border-radius:var(--radius-sm);padding:10px 12px;">
      <div style="font-size:11px;font-weight:700;color:var(--red);margin-bottom:4px;">WHAT IF RUN IN OTHER DATABASES?</div>
      ${Object.entries(data.anti_pattern_critique || {}).map(([db, critique]) => `
        <div style="font-size:11px;margin-bottom:4px;line-height:1.4;">
          <strong style="color:var(--heading);text-transform:uppercase;">${esc(db)}:</strong> <span style="color:var(--text-muted);">${esc(critique)}</span>
        </div>
      `).join('')}
    </div>
  `;

  resultBody.innerHTML = html;
}

// ─── Sub-Tab 2: Schema Comparison ───
function buildLab16SchemasHtml(schemasData) {
  const dbs = schemasData.databases || {};
  return `
    <div style="margin-bottom:24px;">
      <div style="display:grid;grid-template-columns:repeat(auto-fit, minmax(320px, 1fr));gap:18px;margin-bottom:24px;">
        <!-- MongoDB Document Card -->
        <div class="section-panel" style="padding:18px;background:var(--bg-card);border:1px solid var(--border-card);border-radius:var(--radius-md);border-top:3px solid var(--cyan);">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
            <h3 style="font-size:16px;color:var(--cyan);margin:0;font-weight:800;">MongoDB</h3>
            <span class="badge" style="background:rgba(6,182,212,0.15);color:var(--cyan);font-size:10px;">Document Store</span>
          </div>
          <p style="font-size:12px;color:var(--text-muted);margin-bottom:10px;line-height:1.5;">${esc(dbs.mongodb?.strengths)}</p>
          
          <div style="font-size:11px;color:var(--text-dim);font-weight:700;margin-bottom:4px;">SCHEMA DEFINITION:</div>
          <pre style="background:var(--bg-input);padding:10px;border-radius:var(--radius-sm);font-size:10.5px;color:var(--heading);font-family:var(--font-mono);max-height:180px;overflow-y:auto;border:1px solid var(--border-card);margin-bottom:10px;">${esc(dbs.mongodb?.schema_code)}</pre>

          <div style="font-size:11px;color:var(--text-dim);font-weight:700;margin-bottom:4px;">REPRESENTATIVE QUERY:</div>
          <pre style="background:var(--bg-input);padding:8px;border-radius:var(--radius-sm);font-size:10.5px;color:var(--cyan);font-family:var(--font-mono);border:1px solid var(--border-card);margin-bottom:10px;">${esc(dbs.mongodb?.representative_query)}</pre>

          <div style="background:rgba(239,68,68,0.08);border-left:3px solid var(--red);padding:8px 10px;font-size:11px;color:var(--text-muted);">
            <strong style="color:var(--red);">Awkward Query:</strong> ${esc(dbs.mongodb?.awkward_query)}
          </div>
        </div>

        <!-- Cassandra Wide-Column Card -->
        <div class="section-panel" style="padding:18px;background:var(--bg-card);border:1px solid var(--border-card);border-radius:var(--radius-md);border-top:3px solid var(--orange);">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
            <h3 style="font-size:16px;color:var(--orange);margin:0;font-weight:800;">Apache Cassandra</h3>
            <span class="badge" style="background:rgba(249,115,22,0.15);color:var(--orange);font-size:10px;">Wide-Column</span>
          </div>
          <p style="font-size:12px;color:var(--text-muted);margin-bottom:10px;line-height:1.5;">${esc(dbs.cassandra?.strengths)}</p>
          
          <div style="font-size:11px;color:var(--text-dim);font-weight:700;margin-bottom:4px;">SCHEMA DEFINITION:</div>
          <pre style="background:var(--bg-input);padding:10px;border-radius:var(--radius-sm);font-size:10.5px;color:var(--heading);font-family:var(--font-mono);max-height:180px;overflow-y:auto;border:1px solid var(--border-card);margin-bottom:10px;">${esc(dbs.cassandra?.schema_code)}</pre>

          <div style="font-size:11px;color:var(--text-dim);font-weight:700;margin-bottom:4px;">REPRESENTATIVE QUERY:</div>
          <pre style="background:var(--bg-input);padding:8px;border-radius:var(--radius-sm);font-size:10.5px;color:var(--orange);font-family:var(--font-mono);border:1px solid var(--border-card);margin-bottom:10px;">${esc(dbs.cassandra?.representative_query)}</pre>

          <div style="background:rgba(239,68,68,0.08);border-left:3px solid var(--red);padding:8px 10px;font-size:11px;color:var(--text-muted);">
            <strong style="color:var(--red);">Awkward Query:</strong> ${esc(dbs.cassandra?.awkward_query)}
          </div>
        </div>

        <!-- Neo4j Graph Card -->
        <div class="section-panel" style="padding:18px;background:var(--bg-card);border:1px solid var(--border-card);border-radius:var(--radius-md);border-top:3px solid var(--purple);">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
            <h3 style="font-size:16px;color:var(--purple);margin:0;font-weight:800;">Neo4j</h3>
            <span class="badge" style="background:rgba(139,92,246,0.15);color:var(--purple);font-size:10px;">Property Graph</span>
          </div>
          <p style="font-size:12px;color:var(--text-muted);margin-bottom:10px;line-height:1.5;">${esc(dbs.neo4j?.strengths)}</p>
          
          <div style="font-size:11px;color:var(--text-dim);font-weight:700;margin-bottom:4px;">SCHEMA DEFINITION:</div>
          <pre style="background:var(--bg-input);padding:10px;border-radius:var(--radius-sm);font-size:10.5px;color:var(--heading);font-family:var(--font-mono);max-height:180px;overflow-y:auto;border:1px solid var(--border-card);margin-bottom:10px;">${esc(dbs.neo4j?.schema_code)}</pre>

          <div style="font-size:11px;color:var(--text-dim);font-weight:700;margin-bottom:4px;">REPRESENTATIVE QUERY:</div>
          <pre style="background:var(--bg-input);padding:8px;border-radius:var(--radius-sm);font-size:10.5px;color:var(--purple);font-family:var(--font-mono);border:1px solid var(--border-card);margin-bottom:10px;">${esc(dbs.neo4j?.representative_query)}</pre>

          <div style="background:rgba(239,68,68,0.08);border-left:3px solid var(--red);padding:8px 10px;font-size:11px;color:var(--text-muted);">
            <strong style="color:var(--red);">Awkward Query:</strong> ${esc(dbs.neo4j?.awkward_query)}
          </div>
        </div>
      </div>

      <!-- Comparative Architecture Table -->
      <div class="section-panel" style="padding:20px;background:var(--bg-card);border:1px solid var(--border-card);border-radius:var(--radius-md);">
        <h3 style="font-size:15px;color:var(--heading);margin-bottom:14px;font-weight:700;">Cross-Database Architectural Matrix</h3>
        <div style="overflow-x:auto;">
          <table style="width:100%;border-collapse:collapse;font-size:12px;">
            <thead>
              <tr style="border-bottom:2px solid var(--border-card);text-align:left;color:var(--text-dim);">
                <th style="padding:10px;width:22%;">Architectural Aspect</th>
                <th style="padding:10px;width:26%;color:var(--cyan);">MongoDB (Document)</th>
                <th style="padding:10px;width:26%;color:var(--orange);">Apache Cassandra (Column)</th>
                <th style="padding:10px;width:26%;color:var(--purple);">Neo4j (Property Graph)</th>
              </tr>
            </thead>
            <tbody>
              ${(schemasData.comparison_matrix || []).map(row => `
                <tr style="border-bottom:1px solid var(--border-card);">
                  <td style="padding:10px;font-weight:700;color:var(--heading);">${esc(row.criterion)}</td>
                  <td style="padding:10px;color:var(--text-muted);">${esc(row.mongodb)}</td>
                  <td style="padding:10px;color:var(--text-muted);">${esc(row.cassandra)}</td>
                  <td style="padding:10px;color:var(--text-muted);">${esc(row.neo4j)}</td>
                </tr>
              `).join('')}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  `;
}

// ─── Sub-Tab 3: Graph Topology Visualizer ───
function buildLab16TopologyHtml(topoData) {
  return `
    <div class="section-panel" style="padding:20px;background:var(--bg-card);border:1px solid var(--border-card);border-radius:var(--radius-md);margin-bottom:24px;">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px;flex-wrap:wrap;gap:12px;">
        <div>
          <h3 style="font-size:15px;color:var(--heading);margin:0 0 4px 0;display:flex;align-items:center;gap:8px;">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="color:var(--purple);"><circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><line x1="8.59" y1="13.51" x2="15.42" y2="17.49"/><line x1="15.41" y1="6.51" x2="8.59" y2="10.49"/></svg>
            Interactive Device-Sharing Suspect Graph
          </h3>
          <p style="font-size:12px;color:var(--text-muted);margin:0;">
            Visualizing the fraud ring network: suspects linked by common physical hardware tokens and mobile devices.
          </p>
        </div>
        <div style="display:flex;align-items:center;gap:12px;font-size:11px;">
          <span style="display:inline-flex;align-items:center;gap:4px;"><span style="width:10px;height:10px;border-radius:50%;background:#ef4444;display:inline-block;"></span> High Risk Suspect</span>
          <span style="display:inline-flex;align-items:center;gap:4px;"><span style="width:10px;height:10px;border-radius:50%;background:#f59e0b;display:inline-block;"></span> Medium Risk</span>
          <span style="display:inline-flex;align-items:center;gap:4px;"><span style="width:10px;height:10px;border-radius:50%;background:#10b981;display:inline-block;"></span> Low Risk</span>
          <span style="display:inline-flex;align-items:center;gap:4px;"><span style="width:10px;height:10px;border-radius:2px;background:#06b6d4;display:inline-block;"></span> Shared Device</span>
        </div>
      </div>

      <!-- SVG Graph Canvas -->
      <div id="lab16-topology-svg-container" style="width:100%;height:440px;background:var(--bg-input);border:1px solid var(--border-card);border-radius:var(--radius-sm);position:relative;overflow:hidden;">
        <svg id="lab16-topology-svg" width="100%" height="100%" style="display:block;"></svg>
      </div>

      <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-top:16px;">
        <div style="background:rgba(239,68,68,0.08);border:1px solid rgba(239,68,68,0.25);border-radius:var(--radius-sm);padding:14px;">
          <div style="font-size:12px;font-weight:700;color:var(--red);margin-bottom:6px;">SYNTHETIC FRAUD RING CLUSTER:</div>
          <div style="font-size:12px;color:var(--text-muted);line-height:1.5;">
            <strong>Arjun (U-101)</strong>, <strong>Sneha (U-102)</strong>, and <strong>Rahul (U-103)</strong> all log in from <code>DEV-500</code>. Rahul also shares burner hardware token <code>DEV-777</code> with <strong>Vikram (U-105)</strong>, bridging Arjun to Vikram in 3 hops!
          </div>
        </div>
        <div style="background:rgba(16,185,129,0.08);border:1px solid rgba(16,185,129,0.25);border-radius:var(--radius-sm);padding:14px;">
          <div style="font-size:12px;font-weight:700;color:var(--green);margin-bottom:6px;">DISJOINT CORPORATE CLUSTER:</div>
          <div style="font-size:12px;color:var(--text-muted);line-height:1.5;">
            <strong>Priya (U-104)</strong> and <strong>Ananya (U-106)</strong> share <code>DEV-999</code> with low risk scores (0.12 and 0.25) and zero graph connectivity to the Arjun-Rahul syndicate.
          </div>
        </div>
      </div>
    </div>
  `;
}

function renderTopologySvg(nodes, edges) {
  const svg = document.getElementById('lab16-topology-svg');
  if (!svg) return;

  const container = document.getElementById('lab16-topology-svg-container');
  const w = container ? container.clientWidth : 800;
  const h = 440;

  let svgHtml = '';

  // Render edges
  edges.forEach(e => {
    const fromNode = nodes.find(n => n.id === e.from);
    const toNode = nodes.find(n => n.id === e.to);
    if (!fromNode || !toNode) return;

    const x1 = (fromNode.x / 800) * w;
    const y1 = fromNode.y;
    const x2 = (toNode.x / 800) * w;
    const y2 = toNode.y;

    svgHtml += `
      <line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="rgba(255,255,255,0.2)" stroke-width="2" stroke-dasharray="4,4"/>
      <text x="${(x1 + x2) / 2}" y="${(y1 + y2) / 2 - 6}" fill="var(--text-dim)" font-size="9" text-anchor="middle" font-family="sans-serif">${esc(e.label)}</text>
    `;
  });

  // Render nodes
  nodes.forEach(n => {
    const cx = (n.x / 800) * w;
    const cy = n.y;
    const isDevice = n.type === 'device';

    if (isDevice) {
      svgHtml += `
        <rect x="${cx - 24}" y="${cy - 16}" width="48" height="32" rx="6" fill="${n.color}" fill-opacity="0.25" stroke="${n.color}" stroke-width="2"/>
        <text x="${cx}" y="${cy + 4}" fill="#ffffff" font-size="9" font-weight="bold" text-anchor="middle" font-family="monospace">${esc(n.id)}</text>
        <text x="${cx}" y="${cy + 28}" fill="var(--text-dim)" font-size="10" text-anchor="middle" font-family="sans-serif">${esc(n.name.split(' ')[0])}</text>
      `;
    } else {
      svgHtml += `
        <circle cx="${cx}" cy="${cy}" r="22" fill="${n.color}" fill-opacity="0.2" stroke="${n.color}" stroke-width="2.5"/>
        <text x="${cx}" y="${cy + 4}" fill="#ffffff" font-size="11" font-weight="bold" text-anchor="middle" font-family="monospace">${esc(n.id)}</text>
        <text x="${cx}" y="${cy + 34}" fill="var(--heading)" font-size="11" font-weight="600" text-anchor="middle" font-family="sans-serif">${esc(n.name)}</text>
        <text x="${cx}" y="${cy + 46}" fill="${n.color}" font-size="9.5" text-anchor="middle" font-family="sans-serif">${esc(n.badge)}</text>
      `;
    }
  });

  svg.innerHTML = svgHtml;
}

// ─── Sub-Tab 4: Decision Matrix & Benchmarks ───
function buildLab16BenchmarksHtml(benchData) {
  const benchmarks = benchData.benchmarks || [];
  return `
    <div class="section-panel" style="padding:20px;background:var(--bg-card);border:1px solid var(--border-card);border-radius:var(--radius-md);margin-bottom:24px;">
      <h3 style="font-size:15px;color:var(--heading);margin-bottom:14px;font-weight:700;">
        Polyglot Query Routing Decision Table & Algorithmic Complexity
      </h3>
      <p style="font-size:12px;color:var(--text-muted);margin-bottom:18px;line-height:1.6;">
        Empirical comparison across database families for the 4 core fraud detection query patterns, confirming why polyglot persistence outperforms single-database compromises.
      </p>

      <div style="overflow-x:auto;">
        <table style="width:100%;border-collapse:collapse;font-size:12px;">
          <thead>
            <tr style="border-bottom:2px solid var(--border-card);text-align:left;color:var(--text-dim);">
              <th style="padding:10px;width:26%;">Access Pattern</th>
              <th style="padding:10px;width:24%;color:var(--cyan);">MongoDB (Document)</th>
              <th style="padding:10px;width:24%;color:var(--orange);">Cassandra (Wide-Column)</th>
              <th style="padding:10px;width:26%;color:var(--purple);">Neo4j (Property Graph)</th>
            </tr>
          </thead>
          <tbody>
            ${benchmarks.map(b => `
              <tr style="border-bottom:1px solid var(--border-card);">
                <td style="padding:12px 10px;font-weight:700;color:var(--heading);">
                  ${esc(b.access_pattern)}
                </td>
                <td style="padding:10px;">
                  <div style="display:flex;align-items:center;gap:6px;margin-bottom:2px;">
                    <span style="font-weight:700;color:var(--cyan);font-family:var(--font-mono);">${b.mongodb.latency_ms} ms</span>
                    <span style="font-size:10px;color:var(--text-dim);">(${b.mongodb.complexity})</span>
                  </div>
                  <div style="font-size:11px;color:${b.mongodb.status === 'optimal' ? 'var(--green)' : (b.mongodb.status === 'supported' ? 'var(--cyan)' : 'var(--orange)')};">
                    ${esc(b.mongodb.verdict)}
                  </div>
                </td>
                <td style="padding:10px;">
                  <div style="display:flex;align-items:center;gap:6px;margin-bottom:2px;">
                    <span style="font-weight:700;color:var(--orange);font-family:var(--font-mono);">${b.cassandra.latency_ms} ms</span>
                    <span style="font-size:10px;color:var(--text-dim);">(${b.cassandra.complexity})</span>
                  </div>
                  <div style="font-size:11px;color:${b.cassandra.status === 'optimal' ? 'var(--green)' : 'var(--red)'};">
                    ${esc(b.cassandra.verdict)}
                  </div>
                </td>
                <td style="padding:10px;">
                  <div style="display:flex;align-items:center;gap:6px;margin-bottom:2px;">
                    <span style="font-weight:700;color:var(--purple);font-family:var(--font-mono);">${b.neo4j.latency_ms} ms</span>
                    <span style="font-size:10px;color:var(--text-dim);">(${b.neo4j.complexity})</span>
                  </div>
                  <div style="font-size:11px;color:${b.neo4j.status === 'optimal' ? 'var(--green)' : (b.neo4j.status === 'supported' ? 'var(--cyan)' : 'var(--orange)')};">
                    ${esc(b.neo4j.verdict)}
                  </div>
                </td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      </div>
    </div>
  `;
}

async function seedLab16Data() {
  try {
    const res = await fetch(`${API_BASE}/api/labs/lab16/seed`, { method: 'POST' });
    const data = await res.json();
    showToast(data.message || 'Lab 16 seeded successfully!');
    loadLab16();
  } catch (err) {
    showToast(`Seed failed: ${err.message}`);
  }
}
'''

if "// LAB 16: POLYGLOT DATA MODELING" not in code:
    code += "\n" + lab16_js

with open(app_js_path, "w", encoding="utf-8") as f:
    f.write(code)

print("Successfully patched app.js for Lab 16!")
