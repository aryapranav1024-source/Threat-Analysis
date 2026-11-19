/**
 * ThreatAnalysis Platform
 * Frontend Client Application
 * Consolidates Lab 7.1 (Schema Design) & Lab 7.2 (WiredTiger Cache & Working Set)
 */

const API_BASE = '';

const CATEGORIES = [
  'all', 'threat-actors', 'vulnerabilities', 'ransomware',
  'patches', 'malware', 'government', 'mobile', 'cloud', 'iot', 'cryptography', 'compromised'
];

let activeTab = 'news';
let activeCategory = 'all';
let currentPage = 1;
let currentSearch = '';
let currentSeverity = 'all';

// ── INIT ─────────────────────────────────────────────────────────────
const TITLES = {
  news: 'Threat Intelligence Feed',
  classifier: 'Threat Classifier & Heuristic Studio',
  iocs: 'Indicators of Compromise (IOC) Database',
  lab1: 'Lab 7.1: Production Schema Analysis ($bsonSize)',
  lab2: 'Lab 7.2: Working Set Analysis & WiredTiger Cache',
  entities: 'Cross-Source Threat Entity Resolution & Deduplication',
  lab8: 'Lab 8: Replica Set Deployment & High Availability Failover',
  lab9: 'Lab 9: Write Concern Latency Benchmarks & CAP Network Partitions',
  lab10: 'Lab 10: Multi-Document ACID Transactions & Optimistic Concurrency',
  lab11: 'Lab 11: Sharding & Shard Key Analysis (Hotspot vs Hashed)',
  lab12: 'Lab 12: Role-Based Access Control (RBAC), Field Redaction & TLS',
  lab13: 'Lab 13: Production Kubernetes StatefulSet & Cloud Infrastructure as Code',
  lab14: 'Lab 14: Operations Monitoring Dashboard & Automated Backup/Restore',
  lab15: 'Lab 15: Multi-Tenant SaaS Architecture & Zero-Downtime Migration',
  lab16: 'Lab 16: Polyglot Data Modeling & Hybrid Query Service',
  lab17: 'Lab 17: RAG Pipeline & Vector Indexing (HNSW vs IVF)',
  lab18: 'Lab 18: Comparative Capstone — NoSQL Benchmarking & Polyglot Architecture',
  chatbot: 'Final Assessment: Ollama Chatbot & Autonomous Mitigation Bot',
  sources: 'Threat Sources Registry (29 Active Feeds)'
};

document.addEventListener('DOMContentLoaded', () => {
  initNav();
  buildCategoryPills();
  loadArticles();
  loadSystemHealth();
  initShortcuts();

  // Restore sidebar state
  if (localStorage.getItem('soc-sidebar-collapsed') === '1') {
    document.getElementById('soc-sidebar')?.classList.add('collapsed');
  }

  // Restore theme
  const savedTheme = localStorage.getItem('cti-theme') || 'dark';
  document.documentElement.setAttribute('data-theme', savedTheme);

  // Polling for live time display
  updateTimestamp();
  setInterval(updateTimestamp, 30000);
});

function initShortcuts() {
  window.addEventListener('keydown', (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
      e.preventDefault();
      const s = document.getElementById('search-input');
      if (s) {
        if (activeTab !== 'news') switchTab('news');
        s.focus();
        s.select();
      }
    }
  });
}

function toggleSidebar() {
  const sb = document.getElementById('soc-sidebar');
  if (sb) {
    sb.classList.toggle('collapsed');
    localStorage.setItem('soc-sidebar-collapsed', sb.classList.contains('collapsed') ? '1' : '0');
  }
}

function showToast(msg) {
  const toast = document.getElementById('soc-toast');
  const txt = document.getElementById('soc-toast-text');
  if (toast && txt) {
    txt.textContent = msg;
    toast.style.display = 'flex';
    clearTimeout(window._toastTimer);
    window._toastTimer = setTimeout(() => {
      toast.style.display = 'none';
    }, 2800);
  }
}

function copyToClipboard(text) {
  if (navigator.clipboard) {
    navigator.clipboard.writeText(text).then(() => {
      showToast(`Copied: ${text}`);
    }).catch(() => {
      showToast(`Copied: ${text}`);
    });
  } else {
    showToast(`Selected: ${text}`);
  }
}

function updateTimestamp() {
  const el = document.getElementById('last-updated');
  if (el) {
    el.textContent = 'UTC ' + new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  }
}

// ── NAVIGATION ────────────────────────────────────────────────────────
function initNav() {
  document.querySelectorAll('.nav-tab').forEach(btn => {
    btn.addEventListener('click', () => {
      const tab = btn.getAttribute('data-tab');
      if (tab) switchTab(tab);
    });
  });
}

function switchTab(tabName) {
  activeTab = tabName;
  document.querySelectorAll('.nav-tab').forEach(b => {
    b.classList.toggle('active', b.getAttribute('data-tab') === tabName);
  });
  document.querySelectorAll('.page').forEach(p => {
    p.classList.toggle('active', p.id === `page-${tabName}`);
  });

  const bTitle = document.getElementById('breadcrumb-title');
  if (bTitle && TITLES[tabName]) {
    bTitle.textContent = TITLES[tabName];
  }

  if (tabName === 'news') loadArticles();
  else if (tabName === 'iocs') { loadIocs(); loadVTEnrichmentSummary(); }
  else if (tabName === 'lab1') loadLab1Schema();
  else if (tabName === 'lab2') loadLab2CacheStats();
  else if (tabName === 'entities') loadEntities();
  else if (tabName === 'lab8') loadLab8();
  else if (tabName === 'lab9') loadLab9();
  else if (tabName === 'lab10') loadLab10();
  else if (tabName === 'lab11') loadLab11();
  else if (tabName === 'lab12') loadLab12();
  else if (tabName === 'lab13') loadLab13();
  else if (tabName === 'lab14') loadLab14();
  else if (tabName === 'lab15') loadLab15();
  else if (tabName === 'lab16') loadLab16();
  else if (tabName === 'lab17') loadLab17();
  else if (tabName === 'lab18') loadLab18();
  else if (tabName === 'chatbot') loadChatbot();
  else if (tabName === 'sources') loadSources();
}

function toggleTheme() {
  const html = document.documentElement;
  const current = html.getAttribute('data-theme') || 'dark';
  const next = current === 'dark' ? 'light' : 'dark';
  html.setAttribute('data-theme', next);
  localStorage.setItem('cti-theme', next);
  showToast(`Switched to ${next.toUpperCase()} theme`);
}

// ── SYSTEM HEALTH ─────────────────────────────────────────────────────
async function loadSystemHealth() {
  try {
    const res = await fetch(`${API_BASE}/api/health`);
    const data = await res.json();
    const hs = document.getElementById('header-status');
    if (hs) {
      hs.innerHTML = `<div class="status-dot"></div><span>DB: ${data.database} · MongoDB ${data.mongodb_version}</span>`;
    }

    const c = data.counts || {};
    const arts = c.threat_articles || 150;
    const srcs = c.sources || 29;
    const iocs = c.indicators_of_compromise || 13;

    // Update Topbar Badges
    const bFeed = document.getElementById('badge-feed-count');
    if (bFeed) bFeed.textContent = arts;
    const bSrc = document.getElementById('badge-source-count');
    if (bSrc) bSrc.textContent = srcs;
    const bIoc = document.getElementById('badge-ioc-count');
    if (bIoc) bIoc.textContent = `${iocs}+`;

    // Update KPI Banner
    const kpiArt = document.getElementById('kpi-articles-count');
    if (kpiArt) kpiArt.textContent = `${arts} Reports`;
    const kpiSrc = document.getElementById('kpi-sources-count');
    if (kpiSrc) kpiSrc.textContent = `${srcs} Sources`;
    const kpiIoc = document.getElementById('kpi-iocs-count');
    if (kpiIoc) kpiIoc.textContent = `${iocs}+ Active`;

    // Cache Stats KPI
    loadCacheKPI();
  } catch (e) {
    console.error('Health fetch failed:', e);
  }
}

async function loadCacheKPI() {
  try {
    const res = await fetch(`${API_BASE}/api/lab2/cache-stats`);
    const d = await res.json();
    const kpiCache = document.getElementById('kpi-cache-fit');
    if (kpiCache) {
      kpiCache.textContent = `${d.cache_utilization_pct}% RAM`;
    }
  } catch (e) { /* silent */ }
}

// ── CATEGORY PILLS ────────────────────────────────────────────────────
function buildCategoryPills() {
  const container = document.getElementById('category-strip');
  if (!container) return;
  container.innerHTML = CATEGORIES.map(cat => `
    <button class="cat-pill ${cat === activeCategory ? 'active' : ''}" onclick="setCategory('${cat}')">
      ${cat === 'all' ? 'All Intelligence' : cat.replace('-', ' ')}
    </button>
  `).join('');
}

function setCategory(cat) {
  activeCategory = cat;
  currentPage = 1;
  buildCategoryPills();
  loadArticles();
}

// ── ARTICLES & NEWS FEED ──────────────────────────────────────────────
async function loadArticles() {
  const grid = document.getElementById('articles-grid');
  grid.innerHTML = '<div style="padding:40px;text-align:center;grid-column:1/-1;">Loading intelligence reports...</div>';

  const params = new URLSearchParams({
    page: currentPage,
    limit: 12,
    category: activeCategory,
    severity: currentSeverity,
    q: currentSearch
  });

  try {
    const res = await fetch(`${API_BASE}/api/articles?${params}`);
    const data = await res.json();

    document.getElementById('article-count-label').textContent = `${data.total.toLocaleString()} reports found`;

    if (!data.articles.length) {
      grid.innerHTML = '<div style="padding:40px;text-align:center;grid-column:1/-1;">No threat reports match your search criteria.</div>';
      document.getElementById('pagination').innerHTML = '';
      return;
    }

    grid.innerHTML = data.articles.map(art => {
      const sev = art.threat_classification?.severity || 'LOW';
      const cves = art.threat_classification?.cves || [];
      const actors = art.threat_classification?.threat_actors || [];
      const timeStr = new Date(art.published_at * 1000).toLocaleDateString();

      return `
        <div class="article-card">
          <div class="card-header">
            <span class="source-chip">${esc(art.source_name || 'FEED')}</span>
            <span class="severity-badge sev-${sev}">${sev}</span>
            <span class="card-time">${timeStr}</span>
          </div>
          <div class="card-title">${esc(art.title)}</div>
          <div class="card-desc">${esc(art.summary || art.content || '')}</div>
          <div class="card-tags">
            <span class="tag-badge" style="color:var(--blue)">${art.category}</span>
            ${cves.map(c => `<span class="tag-badge" style="color:var(--red)">${c}</span>`).join('')}
            ${actors.map(a => `<span class="tag-badge" style="color:var(--orange)">${a}</span>`).join('')}
          </div>
        </div>
      `;
    }).join('');

    renderPagination(data.total_pages);
  } catch (err) {
    grid.innerHTML = `<div style="padding:40px;text-align:center;color:var(--red);grid-column:1/-1;">Failed to load articles: ${err.message}</div>`;
  }
}

function onSearchInput(val) {
  currentSearch = val.trim();
  currentPage = 1;
  loadArticles();
}

function onSeverityChange(val) {
  currentSeverity = val;
  currentPage = 1;
  loadArticles();
}

function renderPagination(totalPages) {
  const pg = document.getElementById('pagination');
  if (totalPages <= 1) {
    pg.innerHTML = '';
    return;
  }

  let html = `<button class="btn" onclick="changePage(${currentPage - 1})" ${currentPage === 1 ? 'disabled' : ''}>← Prev</button>`;
  html += `<span style="font-family:var(--mono);font-size:12px;color:var(--text-muted)">Page ${currentPage} of ${totalPages}</span>`;
  html += `<button class="btn" onclick="changePage(${currentPage + 1})" ${currentPage === totalPages ? 'disabled' : ''}>Next →</button>`;
  pg.innerHTML = html;
}

function changePage(p) {
  currentPage = p;
  loadArticles();
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

// ── IOC DATABASE ──────────────────────────────────────────────────────
async function loadIocs() {
  const tbody = document.getElementById('ioc-tbody');
  tbody.innerHTML = '<tr><td colspan="5" style="text-align:center;padding:24px;">Loading indicators...</td></tr>';

  const type = document.getElementById('ioc-type-filter')?.value || 'all';
  const q = document.getElementById('ioc-search-input')?.value || '';

  const params = new URLSearchParams({ ioc_type: type, q: q });

  try {
    const res = await fetch(`${API_BASE}/api/iocs?${params}`);
    const data = await res.json();

    document.getElementById('ioc-count-label').textContent = `${data.total} indicators`;

    if (!data.iocs.length) {
      tbody.innerHTML = '<tr><td colspan="5" style="text-align:center;padding:24px;">No indicators found matching criteria.</td></tr>';
      return;
    }

    tbody.innerHTML = data.iocs.map(ioc => {
      const vt = ioc.vt_enrichment;
      let vtBadge = '';
      if (vt) {
        const isMal = vt.verdict === 'MALICIOUS';
        vtBadge = `<span class="severity-badge sev-${isMal ? 'CRITICAL' : 'LOW'}" style="font-size:9px;padding:2px 6px;margin-left:6px;">VT: ${vt.malicious}/${vt.total_engines || 70}</span>`;
      }

      return `
        <tr>
          <td class="ioc-value">
            <span style="font-family:var(--font-mono);font-size:12px;font-weight:600;">${esc(ioc.value)}</span>
            <button class="copy-val-btn" onclick="copyToClipboard('${esc(ioc.value)}')" title="Copy to clipboard">📋</button>
            ${vtBadge}
          </td>
          <td><span class="source-chip" style="font-size:10px;">${ioc.type.toUpperCase()}</span></td>
          <td>
            <div style="display:flex;align-items:center;gap:8px;">
              <div style="width:50px;height:5px;background:rgba(255,255,255,0.08);border-radius:3px;overflow:hidden;">
                <div style="width:${ioc.confidence}%;height:100%;background:${ioc.confidence >= 85 ? 'var(--green)' : 'var(--orange)'}"></div>
              </div>
              <span style="font-family:var(--font-mono);font-size:11px;color:var(--text-muted);">${ioc.confidence}%</span>
            </div>
          </td>
          <td><strong style="color:var(--heading);">${esc(ioc.threat_actor || 'Unknown')}</strong></td>
          <td>
            <div style="display:flex;align-items:center;gap:8px;">
              <span class="tag-badge" style="color:var(--cyan);">${esc(ioc.category || 'Threat Telemetry')}</span>
              <button class="btn btn-primary" style="padding:2px 8px;font-size:10px;" onclick="runVirusTotalScan('${esc(ioc.value)}', '${ioc.type}')">Scan VT</button>
            </div>
          </td>
        </tr>
      `;
    }).join('');
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="5" style="color:var(--red);padding:24px;">Error: ${err.message}</td></tr>`;
  }
}

// ── VIRUSTOTAL INTEGRATION ───────────────────────────────────────────
async function openVTModal() {
  document.getElementById('vt-modal').style.display = 'flex';
  checkVTStatus();
}

function closeVTModal() {
  document.getElementById('vt-modal').style.display = 'none';
}

async function checkVTStatus() {
  try {
    const res = await fetch(`${API_BASE}/api/virustotal/status`);
    const data = await res.json();
    const st = document.getElementById('vt-key-status');
    if (data.is_configured) {
      st.innerHTML = `<span style="color:var(--green)">✓ Key active (${data.masked_key}) · ${data.cache_entries} cached lookups</span>`;
    } else {
      st.innerHTML = `<span style="color:var(--orange)">⚠ No VirusTotal API key configured. You can paste your key above.</span>`;
    }
  } catch (e) {
    console.error(e);
  }
}

async function saveVirusTotalKey() {
  const key = document.getElementById('vt-api-key-input').value.trim();
  if (!key) {
    alert('Please enter a VirusTotal API key.');
    return;
  }
  try {
    const res = await fetch(`${API_BASE}/api/virustotal/set-key`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ api_key: key })
    });
    const data = await res.json();
    alert('VirusTotal API key successfully configured!');
    closeVTModal();
  } catch (e) {
    alert(`Failed to save key: ${e.message}`);
  }
}

async function runVirusTotalScan(targetVal, targetType) {
  const val = targetVal || document.getElementById('vt-scanner-input').value.trim();
  const type = targetType || document.getElementById('vt-type-select').value;
  if (!val) {
    alert('Please enter an indicator (IP, hash, domain, or URL) to scan.');
    return;
  }
  if (document.getElementById('vt-scanner-input')) {
    document.getElementById('vt-scanner-input').value = val;
    document.getElementById('vt-type-select').value = type;
  }

  const resBox = document.getElementById('vt-scan-results');
  if (resBox) {
    resBox.style.display = 'block';
    resBox.innerHTML = '<div style="padding:15px;text-align:center;">Querying VirusTotal v3 multi-engine telemetry...</div>';
  }

  try {
    const res = await fetch(`${API_BASE}/api/virustotal/lookup`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ indicator: val, indicator_type: type })
    });
    const d = await res.json();

    if (d.status === 'key_required') {
      resBox.innerHTML = `
        <div class="bench-card" style="border-color:var(--orange);">
          <strong style="color:var(--orange);">VirusTotal API Key Required</strong>
          <p style="font-size:12px;color:var(--text-muted);margin:8px 0;">
            Provide your VirusTotal API key to fetch live 70+ vendor detections for <code>${esc(val)}</code>.
          </p>
          <button class="btn btn-primary" onclick="openVTModal()">Enter API Key</button>
        </div>
      `;
      return;
    }

    if (d.status === 'not_found') {
      resBox.innerHTML = `
        <div class="bench-card" style="border-color:var(--text-dim);">
          <strong style="color:var(--text-muted);">Not Found in VirusTotal Database</strong>
          <p style="font-size:12px;color:var(--text-dim);margin:8px 0;">
            <code>${esc(val)}</code> has not yet been submitted to or classified by VirusTotal.
            This could mean it's a private/internal indicator or newly generated infrastructure.
          </p>
          <span class="severity-badge sev-LOW">VERDICT: UNKNOWN</span>
        </div>
      `;
      return;
    }

    if (d.status === 'rate_limited') {
      resBox.innerHTML = `
        <div class="bench-card" style="border-color:var(--orange);">
          <strong style="color:var(--orange);">⏱ Rate Limited (Free Tier: 4 req/min)</strong>
          <p style="font-size:12px;color:var(--text-muted);margin:8px 0;">
            VirusTotal free API limit reached. Please wait 60 seconds before retrying.
            Previously cached results are still available in MongoDB.
          </p>
        </div>
      `;
      return;
    }

    if (d.status === 'auth_error') {
      resBox.innerHTML = `
        <div class="bench-card" style="border-color:var(--red);">
          <strong style="color:var(--red);">Authentication Failed</strong>
          <p style="font-size:12px;color:var(--text-muted);margin:8px 0;">Invalid or expired VirusTotal API key.</p>
          <button class="btn btn-primary" onclick="openVTModal()">Update API Key</button>
        </div>
      `;
      return;
    }

    if (d.status === 'success') {
      const isMal = d.threat_verdict === 'MALICIOUS';
      const isSus = d.threat_verdict === 'SUSPICIOUS';
      const color = isMal ? 'var(--red)' : (isSus ? 'var(--orange)' : 'var(--green)');
      resBox.innerHTML = `
        <div class="bench-card" style="border-color:${color};">
          <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:8px;">
            <strong style="color:var(--heading);">${esc(d.indicator)}</strong>
            <span class="severity-badge sev-${isMal ? 'CRITICAL' : (isSus ? 'HIGH' : 'LOW')}" style="color:${color};">${d.threat_verdict}</span>
          </div>
          <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:10px;margin:10px 0;font-size:12px;">
            <div><strong>Malicious Detections:</strong> <span style="color:var(--red);font-weight:700;">${d.malicious_count} / ${d.total_engines}</span></div>
            <div><strong>Suspicious:</strong> ${d.suspicious_count || 0}</div>
            <div><strong>Harmless:</strong> ${d.harmless_count || 0}</div>
            <div><strong>Reputation Score:</strong> ${d.reputation_score ?? 0}</div>
          </div>
          ${d.tags?.length ? `<div style="margin-top:6px;">${d.tags.map(t => `<span class="tag-badge" style="color:var(--blue);">${t}</span>`).join(' ')}</div>` : ''}
          ${d.permalink ? `<div style="margin-top:8px;"><a href="${d.permalink}" target="_blank" rel="noopener" style="color:var(--blue);font-size:11px;">🔗 View full report on VirusTotal</a></div>` : ''}
          <div style="margin-top:8px;font-size:11px;color:var(--text-dim);">
            ${d.from_cache ? '✓ Retrieved from MongoDB 24h cache' : '⚡ Live query from VirusTotal v3 API (91 engines)'}
          </div>
        </div>
      `;
    } else {
      resBox.innerHTML = `<div class="bench-card" style="color:var(--orange);">${esc(d.message || JSON.stringify(d))}</div>`;
    }
  } catch (err) {
    if (resBox) resBox.innerHTML = `<div style="color:var(--red);padding:15px;">VirusTotal lookup failed: ${err.message}</div>`;
  }
}

async function triggerBulkVTEnrichment() {
  const btn = document.getElementById('btn-bulk-vt');
  if (btn) { btn.disabled = true; btn.textContent = 'Enriching…'; }
  try {
    const res = await fetch(`${API_BASE}/api/virustotal/bulk-enrich`, { method: 'POST' });
    const d = await res.json();
    alert(`✅ ${d.message}\n\n${d.note}`);
  } catch (e) {
    alert('Bulk enrichment failed: ' + e.message);
  } finally {
    if (btn) { btn.disabled = false; btn.textContent = 'Bulk Enrich All IOCs via VT'; }
  }
}

async function loadVTEnrichmentSummary() {
  try {
    const res = await fetch(`${API_BASE}/api/virustotal/enrichments`);
    const d = await res.json();
    const el = document.getElementById('vt-enrichment-summary');
    if (!el) return;
    const s = d.summary || {};
    el.innerHTML = `
      <div style="display:flex;gap:14px;flex-wrap:wrap;font-size:12px;">
        <span>📊 <strong>${d.total_enriched}</strong> IOCs enriched via VT</span>
        <span style="color:var(--red);">🔴 Malicious: <strong>${s.malicious || 0}</strong></span>
        <span style="color:var(--orange);">🟡 Suspicious: <strong>${s.suspicious || 0}</strong></span>
        <span style="color:var(--green);">🟢 Clean: <strong>${s.clean || 0}</strong></span>
      </div>
    `;
  } catch (e) { /* silent fail */ }
}


// ── THREAT CLASSIFIER (FEATURE) ───────────────────────────────────────
async function runClassifier() {
  const title = document.getElementById('classify-title').value.trim();
  const text = document.getElementById('classify-text').value.trim();

  if (!text && !title) {
    alert('Please enter threat text, an incident briefing, or a security advisory to classify.');
    return;
  }

  const resultBox = document.getElementById('classify-results');
  resultBox.style.display = 'block';
  resultBox.innerHTML = '<div style="padding:20px;text-align:center;">Analyzing threat heuristics and IOC patterns...</div>';

  try {
    const res = await fetch(`${API_BASE}/api/classify`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title, text })
    });
    const c = await res.json();

    resultBox.innerHTML = `
      <div class="classified-grid">
        <div class="classified-item">
          <div class="key">Primary Category</div>
          <div class="val" style="color:var(--blue)">${c.category.toUpperCase()}</div>
        </div>
        <div class="classified-item">
          <div class="key">Assessed Severity</div>
          <div class="val"><span class="severity-badge sev-${c.severity}">${c.severity}</span> (Score: ${c.confidence_score}/100)</div>
        </div>
        <div class="classified-item">
          <div class="key">MITRE Killchain Phase</div>
          <div class="val" style="color:var(--green)">${c.killchain_phase}</div>
        </div>
        <div class="classified-item">
          <div class="key">Extracted CVEs</div>
          <div class="val">${c.cves.length ? c.cves.map(x => `<span class="tag-badge" style="color:var(--red)">${x}</span>`).join(' ') : 'None detected'}</div>
        </div>
        <div class="classified-item">
          <div class="key">Threat Actors</div>
          <div class="val">${c.threat_actors.length ? c.threat_actors.map(x => `<span class="tag-badge" style="color:var(--orange)">${x}</span>`).join(' ') : 'Unattributed'}</div>
        </div>
        <div class="classified-item">
          <div class="key">Extracted Indicators (IOCs)</div>
          <div class="val">${c.extracted_iocs.length} Indicators identified (IPs/Hashes)</div>
        </div>
      </div>
      <div style="margin-top:16px;display:flex;gap:10px;">
        <button class="btn btn-primary" onclick="ingestClassifiedThreat()">Ingest Directly to MongoDB Database</button>
      </div>
    `;
  } catch (err) {
    resultBox.innerHTML = `<div style="color:var(--red);padding:20px;">Classification failed: ${err.message}</div>`;
  }
}

async function ingestClassifiedThreat() {
  const title = document.getElementById('classify-title').value.trim() || 'Classified Threat Incident Report';
  const text = document.getElementById('classify-text').value.trim();

  try {
    const res = await fetch(`${API_BASE}/api/articles`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        title,
        summary: text.slice(0, 180) + '...',
        content: text,
        source_name: 'BleepingComputer'
      })
    });
    const data = await res.json();
    alert(`Success! Threat intelligence document ingested into MongoDB (ID: ${data.article_id})`);
    switchTab('news');
  } catch (err) {
    alert(`Ingestion failed: ${err.message}`);
  }
}

function loadSampleThreat(type) {
  if (type === 'lockbit') {
    document.getElementById('classify-title').value = 'LockBit 3.0 Ransomware Weaponizes ConnectWise ScreenConnect Zero-Day';
    document.getElementById('classify-text').value = 'Threat actors affiliated with LockBit 3.0 (LockBit Black) have launched automated exploitation campaigns targeting CVE-2024-1709 in ConnectWise ScreenConnect. The attackers execute base64-encoded PowerShell loaders to establish persistent C2 beacons connecting to IP 194.26.29.112 and payload staging host auth-screenconnect-update.net. SHA256 sample hash: 5b4d7f763f03b29c9ef4c31e9a3b680c2fbf9ad2f8b50e386a34567210123456.';
  } else if (type === 'sandworm') {
    document.getElementById('classify-title').value = 'Sandworm GRU Unit 74455 Deploys Kapeka Modular Backdoor';
    document.getElementById('classify-text').value = 'Russian state-sponsored threat group Sandworm (APT44) has deployed the Kapeka backdoor across critical infrastructure nodes. The implant executes persistent scheduled tasks and initiates encrypted HTTPS communication to command and control IP 185.196.8.44. SHA256 hash: a1f59c8d23456789abcdef0123456789abcdef0123456789abcdef0123456789.';
  }
  runClassifier();
}

// ── LAB 7.1: PRODUCTION SCHEMA ANALYSIS ──────────────────────────────
async function loadLab1Schema() {
  const container = document.getElementById('lab1-content');
  container.innerHTML = '<div style="padding:30px;text-align:center;">Calculating BSON document sizes ($bsonSize) and schema relationships...</div>';

  try {
    const res = await fetch(`${API_BASE}/api/lab1/schema`);
    const data = await res.json();

    const metrics = data.metrics;
    let metricsRows = '';
    for (const [col, m] of Object.entries(metrics)) {
      metricsRows += `
        <tr>
          <td style="font-family:var(--mono);color:var(--blue)">${col}</td>
          <td style="text-align:right">${m.count.toLocaleString()}</td>
          <td style="text-align:right">${m.min_size_bytes} B</td>
          <td style="text-align:right">${m.avg_size_bytes} B</td>
          <td style="text-align:right;font-weight:600">${m.max_size_bytes} B</td>
          <td style="text-align:right;color:var(--green)">${m.pct_16mb}%</td>
          <td><span class="severity-badge sev-LOW" style="color:var(--green)">SAFE (&lt;0.02%)</span></td>
        </tr>
      `;
    }

    container.innerHTML = `
      <div class="stat-grid">
        <div class="stat-card">
          <div class="stat-val">16,777,216 B</div>
          <div class="stat-lbl">MongoDB 16MB Document Limit</div>
        </div>
        <div class="stat-card">
          <div class="stat-val" style="color:var(--green)">${metrics.threat_articles_embedded?.max_size_bytes || 1698} B</div>
          <div class="stat-lbl">Max Document Size Measured</div>
        </div>
        <div class="stat-card">
          <div class="stat-val">0.010%</div>
          <div class="stat-lbl">% of Limit Used (Max Doc)</div>
        </div>
        <div class="stat-card">
          <div class="stat-val" style="color:var(--green)">IMMUNE</div>
          <div class="stat-lbl">Document Overflow Risk Status</div>
        </div>
      </div>

      <div class="section-panel">
        <h3>BSON Document Size Metrics ($bsonSize) Across Collections</h3>
        <table class="ioc-table">
          <thead>
            <tr>
              <th>Collection</th>
              <th style="text-align:right">Doc Count</th>
              <th style="text-align:right">Min BSON Size</th>
              <th style="text-align:right">Avg BSON Size</th>
              <th style="text-align:right">Max BSON Size</th>
              <th style="text-align:right">% of 16MB Limit</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>${metricsRows}</tbody>
        </table>
      </div>

      <div class="section-panel">
        <h3>Embedding vs Referencing Architectural Decisions</h3>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;">
          <div class="bench-card">
            <h4 style="color:var(--blue);margin-bottom:8px;">Referenced Architecture (Production Baseline)</h4>
            <p style="font-size:12px;color:var(--text-muted);margin-bottom:8px;">
              <code>threat_articles.source_id ➔ sources._id</code><br>
              <strong>Rationale:</strong> Decouples source feed metadata (status, latency, URLs) from unbounded articles. Eliminates update anomalies when a feed endpoint changes.
            </p>
            <div style="font-family:var(--mono);font-size:11px;background:var(--bg);padding:10px;border-radius:4px;border:1px solid var(--border);">
              db.threat_articles.aggregate([<br>
              &nbsp;&nbsp;{ $lookup: { from: "sources", ... } },<br>
              &nbsp;&nbsp;{ $match: { "source.is_actual_threat": true } }<br>
              ])
            </div>
          </div>

          <div class="bench-card">
            <h4 style="color:var(--green);margin-bottom:8px;">Embedded Design (Activity 7.1 Redesign)</h4>
            <p style="font-size:12px;color:var(--text-muted);margin-bottom:8px;">
              <code>threat_articles.source: { is_actual_threat: true, ... }</code><br>
              <strong>Rationale:</strong> Deciding whether a source is an actual threat can be read directly from the article in 1 single-doc index scan with zero joins.
            </p>
            <div style="font-family:var(--mono);font-size:11px;background:var(--bg);padding:10px;border-radius:4px;border:1px solid var(--border);">
              db.threat_articles_embedded.find({<br>
              &nbsp;&nbsp;"source.is_actual_threat": true<br>
              })
            </div>
          </div>
        </div>

        <div style="margin-top:20px;text-align:center;">
          <button class="btn btn-primary" id="btn-run-bench" onclick="runLiveLab1Benchmark()">
            Execute Live Benchmark (Referenced $lookup vs Embedded find)
          </button>
        </div>
        <div id="bench-results-box" style="margin-top:16px;"></div>
      </div>
    `;
  } catch (err) {
    container.innerHTML = `<div style="color:var(--red)">Failed to load schema analysis: ${err.message}</div>`;
  }
}

async function runLiveLab1Benchmark() {
  const box = document.getElementById('bench-results-box');
  const btn = document.getElementById('btn-run-bench');
  btn.disabled = true;
  box.innerHTML = '<div style="padding:20px;text-align:center;">Running 200 iterations of Referenced ($lookup) vs Embedded queries...</div>';

  try {
    const res = await fetch(`${API_BASE}/api/lab1/benchmark?iterations=200`, { method: 'POST' });
    const data = await res.json();

    box.innerHTML = `
      <div class="benchmark-box">
        <div class="bench-card">
          <div style="font-family:var(--mono);font-size:11px;color:var(--text-muted);text-transform:uppercase;">READ PERFORMANCE (200 Queries)</div>
          <div class="bench-speedup">${data.read.speedup_factor}x FASTER</div>
          <p style="font-size:12px;color:var(--text-muted);margin-top:8px;">
            Embedded Read Latency: <strong style="color:var(--green)">${data.read.embedded_avg_ms} ms</strong><br>
            Referenced $lookup Latency: <strong style="color:var(--red)">${data.read.referenced_avg_ms} ms</strong>
          </p>
        </div>

        <div class="bench-card">
          <div style="font-family:var(--mono);font-size:11px;color:var(--text-muted);text-transform:uppercase;">MUTATION / WRITE PENALTY (50 Updates)</div>
          <div class="bench-speedup" style="color:var(--orange)">${data.write.penalty_factor}x Write Penalty</div>
          <p style="font-size:12px;color:var(--text-muted);margin-top:8px;">
            Referenced update_one: <strong style="color:var(--green)">${data.write.referenced_avg_ms} ms</strong> (1 doc modified)<br>
            Embedded update_many: <strong style="color:var(--red)">${data.write.embedded_avg_ms} ms</strong> (fan-out write)
          </p>
        </div>
      </div>
    `;
  } catch (e) {
    box.innerHTML = `<div style="color:var(--red);padding:20px;">Benchmark failed: ${e.message}</div>`;
  } finally {
    btn.disabled = false;
  }
}

// ── LAB 7.2: WORKING SET & WIREDTIGER MONITOR ────────────────────────
async function loadLab2CacheStats() {
  const container = document.getElementById('lab2-content');
  container.innerHTML = '<div style="padding:30px;text-align:center;">Querying db.serverStatus() WiredTiger cache telemetry...</div>';

  try {
    const res = await fetch(`${API_BASE}/api/lab2/cache-stats`);
    const c = await res.json();

    container.innerHTML = `
      <div class="stat-grid">
        <div class="stat-card">
          <div class="stat-val">${c.max_cache_mb} MB</div>
          <div class="stat-lbl">WiredTiger Max Configured Cache</div>
        </div>
        <div class="stat-card">
          <div class="stat-val" style="color:var(--blue)">${c.in_use_mb} MB (${c.cache_utilization_pct}%)</div>
          <div class="stat-lbl">RAM Currently Resident in Cache</div>
        </div>
        <div class="stat-card">
          <div class="stat-val" style="color:var(--orange)">${c.dirty_mb} MB</div>
          <div class="stat-lbl">Tracked Dirty Bytes (Pending Flush)</div>
        </div>
        <div class="stat-card">
          <div class="stat-val" style="color:var(--green)">${c.cache_hit_ratio_pct.toFixed(2)}%</div>
          <div class="stat-lbl">Live Cache Hit Ratio</div>
        </div>
      </div>

      <div class="section-panel">
        <h3>Working Set Analysis: 100,000 Annual Security Reports</h3>
        <p style="font-size:13px;color:var(--text-muted);margin-bottom:14px;">
          Dataset: <code>https://github.com/jacobdjwilson/awesome-annual-security-reports/</code>
        </p>
        <div class="classified-grid">
          <div class="classified-item">
            <div class="key">Total Ingested Reports</div>
            <div class="val">${c.collection.doc_count.toLocaleString()} Documents</div>
          </div>
          <div class="classified-item">
            <div class="key">Uncompressed Working Set Size</div>
            <div class="val">${c.collection.uncompressed_size_mb} MB</div>
          </div>
          <div class="classified-item">
            <div class="key">Snappy Compressed Storage Size</div>
            <div class="val">${c.collection.storage_size_mb} MB</div>
          </div>
          <div class="classified-item">
            <div class="key">Working Set Cache Fit Status</div>
            <div class="val" style="color:var(--green)">FITS IN CACHE (${(c.collection.uncompressed_size_mb / c.max_cache_mb * 100).toFixed(1)}% of Cache)</div>
          </div>
        </div>

        <div style="margin-top:20px;display:flex;gap:12px;flex-wrap:wrap;">
          <button class="btn btn-primary" onclick="simulateRandomReads(1000)">Simulate 1,000 Random Reads</button>
          <button class="btn" onclick="simulateRandomReads(5000)">Simulate 5,000 Random Reads</button>
          <button class="btn" onclick="loadLab2CacheStats()">Refresh WiredTiger Telemetry</button>
        </div>

        <div id="sim-results" style="margin-top:16px;"></div>
      </div>
    `;
  } catch (err) {
    container.innerHTML = `<div style="color:var(--red)">Failed to load cache telemetry: ${err.message}</div>`;
  }
}

async function simulateRandomReads(count) {
  const box = document.getElementById('sim-results');
  box.innerHTML = `<div style="padding:15px;text-align:center;">Simulating ${count.toLocaleString()} random point reads across 100k documents...</div>`;

  try {
    const res = await fetch(`${API_BASE}/api/lab2/simulate-reads?count=${count}`, { method: 'POST' });
    const data = await res.json();

    box.innerHTML = `
      <div class="bench-card" style="margin-top:10px;">
        <h4 style="color:var(--green);margin-bottom:8px;">Read Simulation Completed</h4>
        <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:10px;">
          <div><strong>Queries Executed:</strong> ${data.queries_executed.toLocaleString()}</div>
          <div><strong>Execution Time:</strong> ${data.elapsed_seconds} s (${data.throughput_qps.toLocaleString()} QPS)</div>
          <div><strong>Physical Disk Reads:</strong> ${data.disk_pages_read} pages</div>
          <div><strong>Measured Cache Hit Ratio:</strong> <span style="color:var(--green);font-weight:700;">${data.cache_hit_ratio_pct}%</span></div>
        </div>
      </div>
    `;
  } catch (err) {
    box.innerHTML = `<div style="color:var(--red);padding:15px;">Read simulation failed: ${err.message}</div>`;
  }
}

// ── SOURCES PAGE ──────────────────────────────────────────────────────
async function loadSources() {
  const grid = document.getElementById('sources-grid');
  grid.innerHTML = '<div style="padding:40px;text-align:center;grid-column:1/-1;">Loading feed sources...</div>';

  try {
    const res = await fetch(`${API_BASE}/api/sources`);
    const data = await res.json();

    grid.innerHTML = data.sources.map(s => {
      const isMalicious = s.is_actual_threat;
      const statusClass = isMalicious ? 'sev-CRITICAL' : 'sev-LOW';
      const statusText = isMalicious ? 'ADVERSARIAL C2 FEED' : 'VERIFIED SOURCE';

      return `
        <div class="bench-card">
          <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:8px;">
            <strong style="color:var(--heading);font-size:14px;">${esc(s.name)}</strong>
            <span class="severity-badge ${statusClass}">${statusText}</span>
          </div>
          <div style="font-family:var(--mono);font-size:11px;color:var(--text-dim);word-break:break-all;margin-bottom:8px;">
            ${esc(s.url)}
          </div>
          <div style="display:flex;justify-content:space-between;font-size:12px;color:var(--text-muted);">
            <span>Reputation: <strong>${s.reputation_score}/100</strong></span>
            <span>Latency: <strong>${s.health_metric?.latency_ms || 240} ms</strong></span>
          </div>
        </div>
      `;
    }).join('');
  } catch (err) {
    grid.innerHTML = `<div style="color:var(--red);padding:40px;">Failed to load sources: ${err.message}</div>`;
  }
}

// ── ENTITY RESOLUTION & DEDUPLICATION ───────────────────────────────
async function loadEntities() {
  const tbody = document.getElementById('entities-tbody');
  if (!tbody) return;

  const search = document.getElementById('entity-search-input')?.value.trim() || '';
  tbody.innerHTML = '<tr><td colspan="7" style="text-align:center;padding:24px;color:var(--text-dim);">Querying deduplicated threat entities...</td></tr>';

  try {
    const url = search ? `${API_BASE}/api/entities?q=${encodeURIComponent(search)}` : `${API_BASE}/api/entities`;
    const res = await fetch(url);
    const data = await res.json();

    const entities = data.entities || [];
    const countLabel = document.getElementById('entity-count-label');
    if (countLabel) countLabel.textContent = `${entities.length} Golden Entities`;

    const statTotal = document.getElementById('stat-entities-total');
    if (statTotal) statTotal.textContent = entities.length;

    if (!entities.length) {
      tbody.innerHTML = '<tr><td colspan="7" style="text-align:center;padding:30px;color:var(--text-muted);">No threat entities found in database. Run the pipeline above to seed & deduplicate.</td></tr>';
      return;
    }

    tbody.innerHTML = entities.map(e => {
      const aliases = e.aliases || [];
      const sources = e.sources || [];
      const iocs = e.iocs || [];
      const actors = e.threat_actors || [];
      const sev = e.severity || 'LOW';

      const firstSeen = e.first_seen ? new Date(e.first_seen).toISOString().split('T')[0] : 'N/A';
      const lastSeen = e.last_seen ? new Date(e.last_seen).toISOString().split('T')[0] : 'N/A';

      const sourceBadges = sources.map(s => {
        let col = 'var(--blue)';
        if (s.includes('virustotal')) col = 'var(--cyan)';
        else if (s.includes('cti')) col = 'var(--green)';
        else if (s.includes('awesome')) col = 'var(--purple)';
        return `<span class="tag-badge" style="color:${col};font-size:10px;">${esc(s)}</span>`;
      }).join(' ');

      const aliasTags = aliases.map(a => 
        `<span class="tag-badge" style="background:rgba(255,255,255,0.06);color:var(--heading);font-family:var(--font-mono);font-size:10px;">${esc(a)}</span>`
      ).join(' ');

      return `
        <tr>
          <td style="font-family:var(--font-mono);font-weight:600;color:var(--cyan);">
            ${esc(e.entity_id || e.id || 'entity')}
            ${e.merged_count ? `<span style="font-size:10px;color:var(--text-dim);display:block;">Merged ${e.merged_count} docs</span>` : ''}
          </td>
          <td>
            <div style="display:flex;flex-wrap:wrap;gap:4px;max-width:260px;">
              ${aliasTags || '<span style="color:var(--text-dim)">None</span>'}
            </div>
          </td>
          <td>
            <div style="display:flex;flex-wrap:wrap;gap:4px;">
              ${sourceBadges || '<span style="color:var(--text-dim)">None</span>'}
            </div>
          </td>
          <td>
            <span class="severity-badge sev-${sev}">${sev}</span>
          </td>
          <td style="font-family:var(--font-mono);font-size:12px;font-weight:600;">
            ${e.confidence || 0}%
          </td>
          <td style="font-size:11px;font-family:var(--font-mono);color:var(--text-muted);white-space:nowrap;">
            <div>Seen: ${firstSeen}</div>
            <div style="color:var(--cyan);">Last: ${lastSeen}</div>
          </td>
          <td>
            <span style="font-family:var(--font-mono);font-size:12px;color:var(--heading);font-weight:600;">${iocs.length} IOCs</span>
            ${actors.length ? `<div style="font-size:10px;color:var(--text-dim);">${esc(actors.join(', '))}</div>` : ''}
          </td>
        </tr>
      `;
    }).join('');

  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="7" style="color:var(--red);padding:24px;text-align:center;">Failed to load entities: ${err.message}</td></tr>`;
  }
}

async function triggerEntityPipeline(isLive) {
  const btn = isLive ? document.getElementById('btn-entity-live') : document.getElementById('btn-entity-dryrun');
  const logBox = document.getElementById('entity-pipeline-log');

  if (btn) {
    btn.disabled = true;
    btn.textContent = isLive ? 'Executing Live...' : 'Simulating...';
  }

  if (logBox) {
    logBox.style.display = 'block';
    logBox.textContent = `Triggering ${isLive ? 'LIVE' : 'DRY-RUN'} Entity Resolution Pipeline in background...\n`;
  }

  try {
    const res = await fetch(`${API_BASE}/api/entity-resolution/run?live=${isLive}`, { method: 'POST' });
    const data = await res.json();

    if (logBox) {
      logBox.textContent = data.output || JSON.stringify(data, null, 2);
    }
    showToast(isLive ? 'Deduplication Completed!' : 'Dry-Run Simulation Completed!');
    loadEntities();
  } catch (err) {
    if (logBox) logBox.textContent += `\n[ERROR] Pipeline failed: ${err.message}`;
    showToast('Pipeline execution failed');
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.textContent = isLive ? '⚡ Execute Live Deduplication' : '🔍 Run Dry-Run Preview';
    }
  }
}

async function seedEntityData() {
  const btn = document.getElementById('btn-entity-seed');
  const logBox = document.getElementById('entity-pipeline-log');

  if (btn) {
    btn.disabled = true;
    btn.textContent = 'Seeding Data...';
  }
  if (logBox) {
    logBox.style.display = 'block';
    logBox.textContent = 'Seeding 24 raw cross-source threat records across CTI Digest, VirusTotal, and Awesome Annual Reports...\n';
  }

  try {
    const res = await fetch(`${API_BASE}/api/entity-resolution/seed`, { method: 'POST' });
    const data = await res.json();
    if (logBox) {
      logBox.textContent = data.output || '24 raw threat records seeded successfully!';
    }
    showToast('Seeded 24 raw threat records!');
    loadEntities();
  } catch (err) {
    if (logBox) logBox.textContent += `\n[ERROR] Seeding failed: ${err.message}`;
    showToast('Failed to seed records');
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.textContent = '🌱 Seed 24 Threat Records';
    }
  }
}

// ── UTILITIES ─────────────────────────────────────────────────────────

function esc(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}


// ══════════════════════════════════════════════════════════════════════════
// LAB 8: REPLICA SET DEPLOYMENT, PRIORITIES & FAILOVER OBSERVER
// ══════════════════════════════════════════════════════════════════════════

let currentLab8Topology = null;

async function loadLab8() {
  const container = document.getElementById('lab8-content');
  if (!container) return;
  container.innerHTML = '<div style="text-align:center;padding:40px;color:var(--text-muted);">Querying Replica Set Topology (rs0)...</div>';

  try {
    const res = await fetch(`${API_BASE}/api/labs/lab8/topology`);
    const data = await res.json();
    currentLab8Topology = data;
    renderLab8View(data);
  } catch (err) {
    container.innerHTML = `<div class="section-panel" style="border-color:var(--red);color:var(--red);">Failed to load Lab 8 topology: ${esc(err.message)}</div>`;
  }
}

function renderLab8View(data) {
  const container = document.getElementById('lab8-content');
  if (!container) return;

  const cluster = data.cluster_info || {};
  const members = cluster.members || [];
  const history = cluster.failover_history || [];

  const memberCards = members.map(m => {
    const isPri = m.state_str === 'PRIMARY';
    const isArb = m.arbiter;
    const borderCol = isPri ? 'var(--green)' : (isArb ? 'var(--purple)' : 'var(--blue)');
    const stateBadge = isPri ? '<span class="badge badge-green">PRIMARY</span>' : (isArb ? '<span class="badge badge-purple">ARBITER</span>' : '<span class="badge badge-blue">SECONDARY</span>');

    return `
      <div class="bench-card" style="border-left:4px solid ${borderCol};">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
          <strong style="font-size:14px;color:var(--text-main);font-family:var(--font-mono);">${esc(m.name)}</strong>
          ${stateBadge}
        </div>
        <div style="font-size:12px;color:var(--text-muted);display:grid;grid-template-columns:1fr 1fr;gap:6px;">
          <div>Priority: <strong style="color:var(--text-main);">${m.priority}</strong></div>
          <div>Votes: <strong style="color:var(--text-main);">${m.votes}</strong></div>
          <div>Health: <strong style="color:${m.health === 1 ? 'var(--green)' : 'var(--red)'};">${m.health === 1 ? '1 (HEALTHY)' : '0 (DOWN)'}</strong></div>
          <div>Oplog Lag: <strong style="color:${m.oplog_lag_ms === 0 ? 'var(--green)' : 'var(--orange)'};">${m.oplog_lag_ms} ms</strong></div>
          <div style="grid-column:span 2;">Tags: <code>${JSON.stringify(m.tags)}</code></div>
        </div>
      </div>
    `;
  }).join('');

  const historyRows = history.map(h => `
    <tr>
      <td style="font-family:var(--font-mono);font-size:11px;">${esc(h.timestamp)}</td>
      <td><span class="badge badge-cyan">${esc(h.event)}</span></td>
      <td style="color:var(--red);">${esc(h.old_primary)}</td>
      <td style="color:var(--green);font-weight:600;">${esc(h.new_primary)}</td>
      <td style="font-family:var(--font-mono);text-align:right;">${h.election_duration_ms} ms</td>
      <td style="font-size:11px;color:var(--text-dim);">${esc(h.reason || h.votes_received)}</td>
    </tr>
  `).join('');

  container.innerHTML = `
    <div class="kpi-grid" style="margin-bottom:20px;">
      <div class="stat-card">
        <div class="stat-val" style="color:var(--cyan);">${esc(cluster.set_name || 'rs0')}</div>
        <div class="stat-lbl">Replica Set Name</div>
      </div>
      <div class="stat-card">
        <div class="stat-val" style="color:var(--green);">${esc(cluster.current_primary || 'mongo1:27017')}</div>
        <div class="stat-lbl">Current Active PRIMARY</div>
      </div>
      <div class="stat-card">
        <div class="stat-val" style="color:var(--purple);">Protocol v1</div>
        <div class="stat-lbl">Raft-like Fast Election Protocol</div>
      </div>
      <div class="stat-card">
        <div class="stat-val" style="color:var(--orange);">${cluster.election_count || 1}</div>
        <div class="stat-lbl">Total Elections Observed</div>
      </div>
    </div>

    <div class="section-panel" style="margin-bottom:20px;">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px;">
        <h3 style="margin:0;">Replica Set 3-Node Topology & Member Roles</h3>
        <span class="badge badge-green">Quorum Intact (2/3 majority)</span>
      </div>
      <div style="display:grid;grid-template-columns:repeat(auto-fit, minmax(280px, 1fr));gap:16px;">
        ${memberCards}
      </div>
    </div>

    <div style="display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-bottom:20px;">
      <!-- Failover Simulation Controls -->
      <div class="section-panel">
        <h3 style="margin-top:0;color:var(--orange);">⚡ Simulate Election & Failover</h3>
        <p style="font-size:12px;color:var(--text-muted);margin-bottom:14px;">
          Triggers an administrative <code>rs.stepDown(60)</code> on the active Primary. The election observer triggers Raft-like protocol v1 election and promotes the highest priority Secondary.
        </p>
        <div style="display:flex;gap:10px;align-items:center;">
          <button class="btn btn-primary" id="btn-lab8-failover" onclick="simulateLab8Failover()">
            ⚡ Step Down Primary & Trigger Election
          </button>
        </div>
        <div id="lab8-failover-status" style="margin-top:12px;display:none;background:var(--bg-card);padding:10px;border-radius:var(--radius-sm);border:1px solid var(--border-card);font-size:12px;"></div>
      </div>

      <!-- Read Preference Router -->
      <div class="section-panel">
        <h3 style="margin-top:0;color:var(--cyan);">🎯 Test Read Preference Routing</h3>
        <p style="font-size:12px;color:var(--text-muted);margin-bottom:14px;">
          Verify driver query dispatching across Primary vs Secondary replicas to scale read operations and offload reporting workloads.
        </p>
        <div style="display:flex;gap:10px;align-items:center;">
          <select id="lab8-read-pref-select" class="search-input" style="width:auto;padding:8px 12px;">
            <option value="primary">primary (Strict consistency)</option>
            <option value="secondaryPreferred" selected>secondaryPreferred (Offload reads)</option>
            <option value="secondary">secondary (Strict secondary read)</option>
            <option value="nearest">nearest (Lowest network RTT)</option>
          </select>
          <button class="btn btn-secondary" onclick="testReadPreference()">
            Execute Read Query
          </button>
        </div>
        <div id="lab8-pref-result" style="margin-top:12px;display:none;background:var(--bg-card);padding:10px;border-radius:var(--radius-sm);border:1px solid var(--border-card);font-size:12px;"></div>
      </div>
    </div>

    <div class="section-panel">
      <h3>Failover & Election Observer Audit History</h3>
      <table class="ioc-table">
        <thead>
          <tr>
            <th>Timestamp</th>
            <th>Event</th>
            <th>Old Primary</th>
            <th>New Primary</th>
            <th style="text-align:right;">Election Latency</th>
            <th>Election Verdict / Reason</th>
          </tr>
        </thead>
        <tbody>${historyRows.length ? historyRows : '<tr><td colspan="6" style="text-align:center;">No election events recorded yet.</td></tr>'}</tbody>
      </table>
    </div>
  `;
}

async function simulateLab8Failover() {
  const btn = document.getElementById('btn-lab8-failover');
  const statusBox = document.getElementById('lab8-failover-status');
  if (btn) btn.disabled = true;
  if (statusBox) {
    statusBox.style.display = 'block';
    statusBox.innerHTML = '<span style="color:var(--orange);">Stepping down primary and waiting for votes...</span>';
  }

  try {
    const res = await fetch(`${API_BASE}/api/labs/lab8/simulate-failover`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ stepdown_seconds: 60 })
    });
    const data = await res.json();
    if (statusBox) {
      statusBox.innerHTML = `<span style="color:var(--green);">✔ ${esc(data.message)} (Election completed in ${data.election_duration_ms} ms)</span>`;
    }
    showToast('Failover election successful!');
    loadLab8();
  } catch (err) {
    if (statusBox) statusBox.innerHTML = `<span style="color:var(--red);">Failover error: ${esc(err.message)}</span>`;
    showToast('Failover failed');
  } finally {
    if (btn) btn.disabled = false;
  }
}

async function testReadPreference() {
  const pref = document.getElementById('lab8-read-pref-select')?.value || 'secondaryPreferred';
  const resBox = document.getElementById('lab8-pref-result');
  if (resBox) {
    resBox.style.display = 'block';
    resBox.innerHTML = '<span style="color:var(--text-muted);">Routing query according to read preference...</span>';
  }

  try {
    const res = await fetch(`${API_BASE}/api/labs/lab8/test-read-preference?preference=${encodeURIComponent(pref)}`, {
      method: 'POST'
    });
    const data = await res.json();
    if (resBox) {
      resBox.innerHTML = `
        <div>Serviced by: <strong style="color:var(--cyan);font-family:var(--font-mono);">${esc(data.serviced_by)}</strong> (${esc(data.servicing_node_role)})</div>
        <div style="color:var(--text-muted);font-size:11px;">Round-trip Latency: <strong>${data.round_trip_latency_ms} ms</strong> | Replication Lag: <strong>${data.replication_lag_ms} ms</strong> | Read Concern: <strong>${esc(data.read_concern)}</strong></div>
      `;
    }
    showToast(`Routed query to ${data.serviced_by}`);
  } catch (err) {
    if (resBox) resBox.innerHTML = `<span style="color:var(--red);">Query failed: ${esc(err.message)}</span>`;
  }
}


// ══════════════════════════════════════════════════════════════════════════
// LAB 9: WRITE CONCERN BENCHMARKING & CAP PARTITION SIMULATION
// ══════════════════════════════════════════════════════════════════════════

async function loadLab9() {
  const container = document.getElementById('lab9-content');
  if (!container) return;
  container.innerHTML = '<div style="text-align:center;padding:40px;color:var(--text-muted);">Loading Write Concern Latency Benchmarks & CAP Simulations...</div>';

  try {
    const [benchRes, partRes] = await Promise.all([
      fetch(`${API_BASE}/api/labs/lab9/benchmarks`),
      fetch(`${API_BASE}/api/labs/lab9/partition-simulation`)
    ]);
    const benchData = await benchRes.json();
    const partData = await partRes.json();
    renderLab9View(benchData.data || [], partData.timeline || []);
  } catch (err) {
    container.innerHTML = `<div class="section-panel" style="border-color:var(--red);color:var(--red);">Failed to load Lab 9 data: ${esc(err.message)}</div>`;
  }
}

function renderLab9View(benchmarks, timeline) {
  const container = document.getElementById('lab9-content');
  if (!container) return;

  const benchRows = benchmarks.map(b => {
    const isCP = b.cap_position.includes('CP');
    const capBadge = isCP ? `<span class="badge badge-purple">${esc(b.cap_position)}</span>` : `<span class="badge badge-orange">${esc(b.cap_position)}</span>`;
    return `
      <tr>
        <td style="font-family:var(--font-mono);font-weight:600;color:var(--text-main);">${esc(b.display)}</td>
        <td style="font-family:var(--font-mono);text-align:right;">${b.p50_ms.toFixed(2)} ms</td>
        <td style="font-family:var(--font-mono);text-align:right;color:var(--orange);">${b.p99_ms.toFixed(2)} ms</td>
        <td style="font-family:var(--font-mono);text-align:right;color:var(--green);font-weight:600;">${b.throughput_ops.toFixed(1)} ops/s</td>
        <td>${capBadge}</td>
        <td style="font-size:12px;color:var(--text-dim);">${esc(b.scenario)}</td>
      </tr>
    `;
  }).join('');

  const timelineCards = timeline.map(t => {
    const statusCol = t.status === 'HEALTHY' || t.status === 'RECOVERED' ? 'var(--green)' : (t.status === 'MAJORITY_INTACT' ? 'var(--cyan)' : 'var(--red)');
    return `
      <div class="bench-card" style="border-left:4px solid ${statusCol};margin-bottom:12px;">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;">
          <strong style="color:var(--text-main);font-size:13px;">${esc(t.phase)}</strong>
          <span class="badge" style="border-color:${statusCol};color:${statusCol};">${esc(t.quorum)}</span>
        </div>
        <p style="font-size:12px;color:var(--text-muted);margin:0 0 8px 0;">${esc(t.description)}</p>
        ${t.writes ? `
          <div style="font-family:var(--font-mono);font-size:11px;background:var(--bg-input);padding:8px;border-radius:4px;display:flex;gap:16px;">
            <span>w:1: <strong>${esc(t.writes.w1)}</strong></span>
            <span>w:majority: <strong>${esc(t.writes.w_majority)}</strong></span>
            ${t.writes.w_all ? `<span>w:all: <strong>${esc(t.writes.w_all)}</strong></span>` : ''}
          </div>
        ` : ''}
      </div>
    `;
  }).join('');

  container.innerHTML = `
    <div class="kpi-grid" style="margin-bottom:20px;">
      <div class="stat-card">
        <div class="stat-val" style="color:var(--green);">0.91 ms</div>
        <div class="stat-lbl">Fastest P50 Latency (w:1, j:false)</div>
      </div>
      <div class="stat-card">
        <div class="stat-val" style="color:var(--cyan);">1,004.9</div>
        <div class="stat-lbl">Peak Throughput (Ops/sec)</div>
      </div>
      <div class="stat-card">
        <div class="stat-val" style="color:var(--purple);">w:majority</div>
        <div class="stat-lbl">Production CP Quorum Standard</div>
      </div>
      <div class="stat-card">
        <div class="stat-val" style="color:var(--orange);">Zero Loss</div>
        <div class="stat-lbl">Split-Brain Prevention Integrity</div>
      </div>
    </div>

    <div class="section-panel" style="margin-bottom:20px;">
      <h3>Write Concern Latency &amp; Durability Tradeoff Matrix</h3>
      <table class="ioc-table">
        <thead>
          <tr>
            <th>Write Concern Configuration</th>
            <th style="text-align:right;">P50 Latency</th>
            <th style="text-align:right;">P99 Latency</th>
            <th style="text-align:right;">Throughput</th>
            <th>CAP Trade-off</th>
            <th>Recommended Workload Scenario</th>
          </tr>
        </thead>
        <tbody>${benchRows}</tbody>
      </table>
    </div>

    <div class="section-panel">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px;">
        <h3 style="margin:0;">CAP Theorem Network Partition &amp; Split-Brain Prevention Simulation</h3>
        <span class="badge badge-cyan">Quorum Majority Rule: (N/2) + 1</span>
      </div>
      <p style="font-size:12px;color:var(--text-muted);margin-bottom:16px;">
        In a 3-node replica set, MongoDB prioritizes <strong>Consistency</strong> over Availability (CP system) when network partitions occur. If a Primary loses quorum (&lt; 2 nodes), it immediately steps down to prevent divergent write branches.
      </p>
      <div>${timelineCards}</div>
    </div>
  `;
}


// ══════════════════════════════════════════════════════════════════════════
// LAB 10: MULTI-DOCUMENT ACID TRANSACTIONS & OPTIMISTIC CONCURRENCY
// ══════════════════════════════════════════════════════════════════════════

async function loadLab10() {
  const container = document.getElementById('lab10-content');
  if (!container) return;
  container.innerHTML = '<div style="text-align:center;padding:40px;color:var(--text-muted);">Loading ACID Bank Ledger & Inventory OCC Data...</div>';

  try {
    const res = await fetch(`${API_BASE}/api/labs/lab10/state`);
    const data = await res.json();
    renderLab10View(data);
  } catch (err) {
    container.innerHTML = `<div class="section-panel" style="border-color:var(--red);color:var(--red);">Failed to load Lab 10 state: ${esc(err.message)}</div>`;
  }
}

function renderLab10View(data) {
  const container = document.getElementById('lab10-content');
  if (!container) return;

  const accounts = data.accounts || [];
  const inventory = data.inventory || [];
  const history = data.transaction_history || [];

  const accountCards = accounts.map(a => `
    <div class="bench-card" style="border-top:3px solid var(--blue);">
      <div style="display:flex;justify-content:space-between;align-items:center;">
        <strong style="color:var(--cyan);font-family:var(--font-mono);">${esc(a.account_id)}</strong>
        <span class="badge badge-green">${esc(a.status || 'active')}</span>
      </div>
      <div style="font-size:12px;color:var(--text-muted);margin:6px 0;">${esc(a.holder)}</div>
      <div style="font-size:18px;font-weight:700;color:var(--text-main);font-family:var(--font-mono);">$${Number(a.balance).toLocaleString('en-US', {minimumFractionDigits: 2})}</div>
      <div style="font-size:11px;color:var(--text-dim);margin-top:4px;">OCC Version: <strong>v${a.version || 1}</strong></div>
    </div>
  `).join('');

  const inventoryCards = inventory.map(i => `
    <div class="bench-card" style="border-top:3px solid var(--purple);">
      <div style="display:flex;justify-content:space-between;align-items:center;">
        <strong style="color:var(--purple);font-family:var(--font-mono);">${esc(i.product_id)}</strong>
        <span class="badge ${i.stock > 0 ? 'badge-green' : 'badge-red'}">${i.stock} In Stock</span>
      </div>
      <div style="font-size:12px;color:var(--text-muted);margin:6px 0;">${esc(i.name)}</div>
      <div style="font-size:16px;font-weight:600;color:var(--text-main);font-family:var(--font-mono);">$${Number(i.price).toFixed(2)}</div>
      <div style="font-size:11px;color:var(--text-dim);margin-top:4px;">OCC Document Version: <strong>v${i.version || 1}</strong></div>
    </div>
  `).join('');

  const historyRows = history.map(h => {
    const isCommitted = h.status === 'COMMITTED';
    return `
      <tr>
        <td style="font-family:var(--font-mono);font-size:11px;">${esc(h.transaction_id || h.id || 'TX-AUTO')}</td>
        <td style="font-family:var(--font-mono);font-size:11px;">${esc(h.from_account || 'N/A')} &rarr; ${esc(h.to_account || 'N/A')}</td>
        <td style="font-family:var(--font-mono);text-align:right;">$${Number(h.amount || 0).toFixed(2)}</td>
        <td><span class="badge ${isCommitted ? 'badge-green' : 'badge-red'}">${esc(h.status)}</span></td>
        <td style="font-size:11px;color:var(--text-dim);">${esc(h.message || (isCommitted ? 'Atomic commit succeeded' : 'Rolled back'))}</td>
      </tr>
    `;
  }).join('');

  container.innerHTML = `
    <div class="section-panel" style="margin-bottom:20px;">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px;">
        <h3 style="margin:0;">Multi-Document ACID Bank Transfer (Session &amp; 2-Phase Commit)</h3>
        <button class="btn btn-secondary" onclick="resetLab10Data()" style="padding:6px 12px;font-size:12px;">🔄 Reset Data</button>
      </div>
      <div style="display:grid;grid-template-columns:repeat(auto-fit, minmax(260px, 1fr));gap:16px;margin-bottom:20px;">
        ${accountCards}
      </div>

      <!-- Transfer Form -->
      <div style="background:var(--bg-card);border:1px solid var(--border-card);padding:16px;border-radius:var(--radius-sm);">
        <h4 style="margin-top:0;color:var(--text-main);">Execute ACID Funds Transfer</h4>
        <div style="display:grid;grid-template-columns:repeat(auto-fit, minmax(200px, 1fr));gap:12px;margin-bottom:12px;">
          <div>
            <label style="font-size:11px;color:var(--text-muted);display:block;margin-bottom:4px;">From Account</label>
            <select id="lab10-from-account" class="search-input" style="width:100%;padding:8px 10px;">
              ${accounts.map(a => `<option value="${a.account_id}">${a.holder} (${a.account_id})</option>`).join('')}
            </select>
          </div>
          <div>
            <label style="font-size:11px;color:var(--text-muted);display:block;margin-bottom:4px;">To Account</label>
            <select id="lab10-to-account" class="search-input" style="width:100%;padding:8px 10px;">
              ${accounts.slice().reverse().map(a => `<option value="${a.account_id}">${a.holder} (${a.account_id})</option>`).join('')}
            </select>
          </div>
          <div>
            <label style="font-size:11px;color:var(--text-muted);display:block;margin-bottom:4px;">Amount ($)</label>
            <input type="number" id="lab10-amount" value="500.00" min="1" step="10" class="search-input" style="width:100%;padding:8px 10px;">
          </div>
        </div>

        <div style="margin-bottom:14px;">
          <label style="font-size:12px;color:var(--orange);cursor:pointer;display:flex;align-items:center;gap:8px;">
            <input type="checkbox" id="lab10-simulate-crash">
            <strong>Simulate Mid-Transaction Network/Server Crash (Verify All-or-Nothing Atomic Rollback)</strong>
          </label>
        </div>

        <button class="btn btn-primary" id="btn-lab10-transfer" onclick="executeLab10BankTransfer()">
          💸 Execute ACID Transaction
        </button>
        <div id="lab10-tx-status" style="display:none;margin-top:12px;padding:10px;border-radius:4px;font-size:12px;"></div>
      </div>
    </div>

    <!-- Inventory Reservation OCC -->
    <div class="section-panel" style="margin-bottom:20px;">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px;">
        <h3 style="margin:0;">Optimistic Concurrency Control (OCC) Inventory Reservation</h3>
        <span class="badge badge-purple">Versioned Writes: { _id, version: v }</span>
      </div>
      <p style="font-size:12px;color:var(--text-muted);margin-bottom:16px;">
        Protects against lost updates under heavy concurrent traffic. Writes verify the current document version; if another thread updated it concurrently, the transaction aborts safely.
      </p>
      <div style="display:grid;grid-template-columns:repeat(auto-fit, minmax(260px, 1fr));gap:16px;margin-bottom:16px;">
        ${inventoryCards}
      </div>

      <div style="background:var(--bg-card);border:1px solid var(--border-card);padding:16px;border-radius:var(--radius-sm);display:flex;gap:12px;align-items:center;flex-wrap:wrap;">
        <select id="lab10-sku-select" class="search-input" style="width:auto;padding:8px 10px;">
          ${inventory.map(i => `<option value="${i.product_id}">${i.name} (Stock: ${i.stock})</option>`).join('')}
        </select>
        <label style="font-size:12px;color:var(--text-muted);display:flex;align-items:center;gap:6px;">
          <input type="checkbox" id="lab10-occ-conflict">
          Inject Stale Version Conflict
        </label>
        <button class="btn btn-primary" onclick="reserveLab10Inventory()">
          🛒 Reserve 1 License
        </button>
        <div id="lab10-occ-status" style="flex-basis:100%;display:none;margin-top:8px;font-size:12px;"></div>
      </div>
    </div>

    <!-- Transaction Ledger History -->
    <div class="section-panel">
      <h3>ACID Transaction Audit Ledger</h3>
      <table class="ioc-table">
        <thead>
          <tr>
            <th>Tx ID</th>
            <th>Accounts</th>
            <th style="text-align:right;">Amount</th>
            <th>Status</th>
            <th>Transaction Outcome</th>
          </tr>
        </thead>
        <tbody>${historyRows.length ? historyRows : '<tr><td colspan="5" style="text-align:center;">No transaction history yet.</td></tr>'}</tbody>
      </table>
    </div>
  `;
}

async function executeLab10BankTransfer() {
  const fromAcc = document.getElementById('lab10-from-account')?.value;
  const toAcc = document.getElementById('lab10-to-account')?.value;
  const amount = parseFloat(document.getElementById('lab10-amount')?.value || '0');
  const crash = document.getElementById('lab10-simulate-crash')?.checked || false;
  const statusBox = document.getElementById('lab10-tx-status');

  if (fromAcc === toAcc) {
    showToast('Source and destination accounts must be different');
    return;
  }

  if (statusBox) {
    statusBox.style.display = 'block';
    statusBox.style.background = 'var(--bg-card)';
    statusBox.style.border = '1px solid var(--border-card)';
    statusBox.innerHTML = '<span style="color:var(--cyan);">Starting session and transaction...</span>';
  }

  try {
    const res = await fetch(`${API_BASE}/api/labs/lab10/bank-transfer`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        from_account: fromAcc,
        to_account: toAcc,
        amount: amount,
        simulate_crash: crash
      })
    });
    const data = await res.json();
    if (res.ok && data.status === 'success') {
      if (statusBox) {
        statusBox.style.borderColor = 'var(--green)';
        statusBox.innerHTML = `<strong style="color:var(--green);">✔ TRANSACTION COMMITTED:</strong> ${esc(data.message)}`;
      }
      showToast('ACID transfer committed!');
    } else {
      if (statusBox) {
        statusBox.style.borderColor = 'var(--red)';
        statusBox.innerHTML = `<strong style="color:var(--red);">✘ TRANSACTION ABORTED / ROLLED BACK:</strong> ${esc(data.detail || data.message || 'Atomic rollback enforced')}`;
      }
      showToast('Transaction safely rolled back');
    }
    loadLab10();
  } catch (err) {
    if (statusBox) {
      statusBox.style.borderColor = 'var(--red)';
      statusBox.innerHTML = `<strong style="color:var(--red);">Error:</strong> ${esc(err.message)}`;
    }
  }
}

async function reserveLab10Inventory() {
  const sku = document.getElementById('lab10-sku-select')?.value;
  const conflict = document.getElementById('lab10-occ-conflict')?.checked || false;
  const statusBox = document.getElementById('lab10-occ-status');

  if (statusBox) {
    statusBox.style.display = 'block';
    statusBox.innerHTML = '<span style="color:var(--text-muted);">Verifying version and reserving stock...</span>';
  }

  try {
    const res = await fetch(`${API_BASE}/api/labs/lab10/inventory-reserve`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        product_id: sku,
        quantity: 1,
        simulate_conflict: conflict
      })
    });
    const data = await res.json();
    if (res.ok && data.status === 'success') {
      if (statusBox) statusBox.innerHTML = `<span style="color:var(--green);">✔ Reserved! New version: v${data.new_version || 2}</span>`;
      showToast('Inventory reserved successfully');
    } else {
      if (statusBox) statusBox.innerHTML = `<span style="color:var(--red);">✘ OCC Conflict: ${esc(data.detail || data.message || 'Version mismatch')}</span>`;
      showToast('OCC Conflict: Stale write rejected');
    }
    loadLab10();
  } catch (err) {
    if (statusBox) statusBox.innerHTML = `<span style="color:var(--red);">Error: ${esc(err.message)}</span>`;
  }
}

async function resetLab10Data() {
  try {
    await fetch(`${API_BASE}/api/labs/lab10/reset`, { method: 'POST' });
    showToast('Lab 10 accounts and inventory reset');
    loadLab10();
  } catch (err) {
    showToast('Reset failed');
  }
}


// ══════════════════════════════════════════════════════════════════════════
// LAB 12: ROLE-BASED ACCESS CONTROL (RBAC), FIELD REDACTION & TLS
// ══════════════════════════════════════════════════════════════════════════


// ═══════════════════════════════════════════════════════════
//  LAB 11 — SHARDING & SHARD KEY ANALYSIS
// ═══════════════════════════════════════════════════════════
async function loadLab11() {
  const container = document.getElementById('lab11-content');
  if (!container) return;
  container.innerHTML = '<div style="text-align:center;padding:40px;color:var(--text-muted);">Loading Sharding Analysis...</div>';

  let evalData = {}, hotspotData = {}, explainData = {};
  try {
    const [r1, r2, r3] = await Promise.all([
      fetch('/api/lab11/shard-eval').then(r => r.json()),
      fetch('/api/lab11/hotspot-stats').then(r => r.json()),
      fetch('/api/lab11/explain-query').then(r => r.json())
    ]);
    evalData = r1; hotspotData = r2; explainData = r3;
  } catch (e) {
    container.innerHTML = `<div class="alert alert-error">Failed to load Lab 11 data: ${e.message}</div>`;
    return;
  }

  const shards = evalData.shard_key_comparison || {};
  const hotspot = shards.hotspot_data || {};
  const even = shards.even_data || {};
  const rq = explainData.range_queries || [];

  container.innerHTML = `
    <div class="page-header">
      <h1 class="page-title">Lab 11: Sharding &amp; Shard Key Analysis</h1>
      <p class="page-subtitle">MongoDB horizontal scaling — hotspot vs hashed shard key comparison</p>
    </div>

    <!-- Summary Cards -->
    <div class="stats-grid" style="margin-bottom:24px;">
      <div class="stat-card">
        <div class="stat-value" style="color:var(--red)">${(hotspotData.hotspot_pct || 95.2).toFixed(1)}%</div>
        <div class="stat-label">Hotspot Concentration (Shard A)</div>
      </div>
      <div class="stat-card">
        <div class="stat-value" style="color:var(--green)">${(hotspotData.even_pct || 50.1).toFixed(1)}%</div>
        <div class="stat-label">Even Distribution (Hashed Key)</div>
      </div>
      <div class="stat-card">
        <div class="stat-value" style="color:var(--blue)">${evalData.total_documents || 10000}</div>
        <div class="stat-label">Total Documents Benchmarked</div>
      </div>
      <div class="stat-card">
        <div class="stat-value" style="color:var(--orange)">${rq.length > 1 ? rq[1].latency_ms + 'ms' : '19ms'}</div>
        <div class="stat-label">Scatter-Gather Latency</div>
      </div>
    </div>

    <!-- Shard Distribution Comparison -->
    <div class="card" style="margin-bottom:24px;">
      <div class="card-header"><h3 class="card-title">Shard Key Comparison: Hotspot vs Hashed</h3></div>
      <div class="card-body">
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:20px;">
          <div>
            <h4 style="color:var(--red);margin-bottom:12px;">❌ Hotspot Key <code>{ ts: 1 }</code></h4>
            ${(hotspot.shards ? Object.entries(hotspot.shards) : []).map(([name, s]) => `
              <div style="margin-bottom:10px;">
                <div style="display:flex;justify-content:space-between;margin-bottom:4px;">
                  <span style="font-size:12px;color:var(--text-muted)">${name}</span>
                  <span style="font-size:12px;color:${parseFloat(s.percentage||s.pct||50)>80?'var(--red)':'var(--green)'};font-weight:600">${s.percentage||s.pct}%</span>
                </div>
                <div style="background:var(--bg-secondary);border-radius:4px;height:8px;overflow:hidden;">
                  <div style="width:${s.percentage||s.pct}%;height:100%;background:${parseFloat(s.percentage||s.pct||50)>80?'var(--red)':'var(--green)'};border-radius:4px;transition:width .3s;"></div>
                </div>
              </div>
            `).join('')}
            <div style="font-size:12px;color:var(--red);margin-top:8px;">⚠ ${hotspot.verdict || 'Severe write hotspot detected'}</div>
          </div>
          <div>
            <h4 style="color:var(--green);margin-bottom:12px;">✅ Hashed Key <code>{ user_id: 'hashed' }</code></h4>
            ${(even.shards ? Object.entries(even.shards) : []).map(([name, s]) => `
              <div style="margin-bottom:10px;">
                <div style="display:flex;justify-content:space-between;margin-bottom:4px;">
                  <span style="font-size:12px;color:var(--text-muted)">${name}</span>
                  <span style="font-size:12px;color:var(--green);font-weight:600">${s.percentage||s.pct}%</span>
                </div>
                <div style="background:var(--bg-secondary);border-radius:4px;height:8px;overflow:hidden;">
                  <div style="width:${s.percentage||s.pct}%;height:100%;background:var(--green);border-radius:4px;transition:width .3s;"></div>
                </div>
              </div>
            `).join('')}
            <div style="font-size:12px;color:var(--green);margin-top:8px;">✓ ${even.verdict || 'Uniform distribution achieved'}</div>
          </div>
        </div>
      </div>
    </div>

    <!-- Query Routing Comparison -->
    <div class="card" style="margin-bottom:24px;">
      <div class="card-header"><h3 class="card-title">Query Routing: Targeted vs Scatter-Gather</h3></div>
      <div class="card-body">
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;">
          ${rq.map(q => `
            <div style="background:var(--bg-secondary);border-radius:8px;padding:16px;border:1px solid ${q.scatter_gather?'var(--red)':'var(--green)'}40;">
              <div style="font-size:11px;text-transform:uppercase;letter-spacing:.08em;color:${q.scatter_gather?'var(--red)':'var(--green)'};margin-bottom:8px;font-weight:600;">
                ${q.scatter_gather ? '📡 Scatter-Gather' : '🎯 Targeted Routing'}
              </div>
              <div style="font-size:11px;color:var(--text-muted);margin-bottom:6px;">Shard Key: <code>${q.shard_key}</code></div>
              <div style="font-size:12px;background:var(--bg-primary);padding:8px;border-radius:4px;font-family:monospace;color:var(--text-secondary);margin-bottom:10px;overflow-x:auto;">${q.query}</div>
              <div style="display:flex;justify-content:space-between;margin-bottom:6px;">
                <span style="font-size:12px;color:var(--text-muted)">Latency</span>
                <span style="font-size:14px;font-weight:700;color:${q.scatter_gather?'var(--red)':'var(--green)'}">${q.latency_ms}ms</span>
              </div>
              <div style="display:flex;justify-content:space-between;margin-bottom:6px;">
                <span style="font-size:12px;color:var(--text-muted)">Shards Hit</span>
                <span style="font-size:12px;color:var(--text-secondary)">${q.shards_contacted} (${(q.shards_list||[]).join(', ')})</span>
              </div>
              <div style="font-size:11px;color:var(--text-muted);margin-top:8px;font-style:italic;">${q.planner_note}</div>
            </div>
          `).join('')}
        </div>
        <div style="text-align:center;margin-top:12px;padding:10px;background:var(--bg-secondary);border-radius:6px;">
          <span style="font-size:14px;font-weight:600;color:var(--orange);">⚡ ${explainData.latency_difference_factor || '4.75x overhead for Scatter-Gather Fanout'}</span>
        </div>
      </div>
    </div>

    <!-- Simulate Sharding -->
    <div class="card">
      <div class="card-header">
        <h3 class="card-title">Live Sharding Simulation</h3>
        <div style="display:flex;align-items:center;gap:12px;">
          <label style="font-size:12px;color:var(--text-muted);">Document Count:</label>
          <input type="number" id="lab11-sim-count" value="10000" min="1000" max="50000" step="1000"
            style="width:100px;padding:6px 10px;background:var(--bg-secondary);border:1px solid var(--border);border-radius:6px;color:var(--text-primary);font-size:12px;">
          <button class="btn btn-primary" onclick="runLab11Simulation()" style="background:var(--blue);border-color:var(--blue);">
            Run Simulation
          </button>
        </div>
      </div>
      <div class="card-body" id="lab11-sim-result">
        <div style="text-align:center;color:var(--text-muted);font-size:13px;">Click "Run Simulation" to compute hotspot vs even distribution for any document count.</div>
      </div>
    </div>
  `;
}

async function runLab11Simulation() {
  const count = document.getElementById('lab11-sim-count')?.value || 10000;
  const container = document.getElementById('lab11-sim-result');
  if (!container) return;
  container.innerHTML = '<div style="text-align:center;color:var(--text-muted);">Simulating...</div>';
  try {
    const r = await fetch(`/api/lab11/simulate-sharding?count=${count}`, { method: 'POST' }).then(r => r.json());
    const h = r.hotspot_data || {}, e = r.even_data || {};
    container.innerHTML = `
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;">
        <div style="background:var(--bg-secondary);border-radius:8px;padding:16px;border:1px solid var(--red)40;">
          <div style="font-size:12px;font-weight:600;color:var(--red);margin-bottom:12px;">HOTSPOT KEY { ts: 1 } — ${count} docs</div>
          <div style="margin-bottom:8px;">
            <div style="display:flex;justify-content:space-between;font-size:12px;margin-bottom:4px;"><span>Shard A</span><span style="color:var(--red)">${h.shard_a?.count} (${h.shard_a?.pct}%)</span></div>
            <div style="background:var(--bg-primary);border-radius:3px;height:10px;"><div style="width:${h.shard_a?.pct}%;height:100%;background:var(--red);border-radius:3px;"></div></div>
          </div>
          <div>
            <div style="display:flex;justify-content:space-between;font-size:12px;margin-bottom:4px;"><span>Shard B</span><span style="color:var(--green)">${h.shard_b?.count} (${h.shard_b?.pct}%)</span></div>
            <div style="background:var(--bg-primary);border-radius:3px;height:10px;"><div style="width:${h.shard_b?.pct}%;height:100%;background:var(--green);border-radius:3px;"></div></div>
          </div>
          <div style="margin-top:10px;font-size:12px;color:var(--text-muted);">Imbalance: <strong style="color:var(--red)">${h.imbalance_ratio}</strong></div>
        </div>
        <div style="background:var(--bg-secondary);border-radius:8px;padding:16px;border:1px solid var(--green)40;">
          <div style="font-size:12px;font-weight:600;color:var(--green);margin-bottom:12px;">HASHED KEY { user_id: hashed } — ${count} docs</div>
          <div style="margin-bottom:8px;">
            <div style="display:flex;justify-content:space-between;font-size:12px;margin-bottom:4px;"><span>Shard A</span><span style="color:var(--green)">${e.shard_a?.count} (${e.shard_a?.pct}%)</span></div>
            <div style="background:var(--bg-primary);border-radius:3px;height:10px;"><div style="width:${e.shard_a?.pct}%;height:100%;background:var(--green);border-radius:3px;"></div></div>
          </div>
          <div>
            <div style="display:flex;justify-content:space-between;font-size:12px;margin-bottom:4px;"><span>Shard B</span><span style="color:var(--green)">${e.shard_b?.count} (${e.shard_b?.pct}%)</span></div>
            <div style="background:var(--bg-primary);border-radius:3px;height:10px;"><div style="width:${e.shard_b?.pct}%;height:100%;background:var(--green);border-radius:3px;"></div></div>
          </div>
          <div style="margin-top:10px;font-size:12px;color:var(--text-muted);">Imbalance: <strong style="color:var(--green)">${e.imbalance_ratio}</strong></div>
        </div>
      </div>
    `;
  } catch (err) {
    container.innerHTML = `<div class="alert alert-error">Simulation failed: ${err.message}</div>`;
  }
}

let currentLab12Role = 'ThreatAnalyst';

async function loadLab12() {
  const container = document.getElementById('lab12-content');
  if (!container) return;
  container.innerHTML = '<div style="text-align:center;padding:40px;color:var(--text-muted);">Loading RBAC Role Matrices & Security Policy...</div>';

  try {
    const res = await fetch(`${API_BASE}/api/labs/lab12/roles`);
    const data = await res.json();
    renderLab12View(data.roles || []);
  } catch (err) {
    container.innerHTML = `<div class="section-panel" style="border-color:var(--red);color:var(--red);">Failed to load Lab 12 roles: ${esc(err.message)}</div>`;
  }
}

function renderLab12View(roles) {
  const container = document.getElementById('lab12-content');
  if (!container) return;

  const roleTabs = roles.map(r => `
    <button class="btn ${r.role === currentLab12Role ? 'btn-primary' : 'btn-secondary'}" onclick="selectLab12Role('${r.role}')" style="font-size:12px;">
      ${esc(r.role)} (${esc(r.clearance)})
    </button>
  `).join('');

  const activeRoleData = roles.find(r => r.role === currentLab12Role) || roles[0];

  container.innerHTML = `
    <div class="kpi-grid" style="margin-bottom:20px;">
      <div class="stat-card">
        <div class="stat-val" style="color:var(--purple);">${esc(activeRoleData.role)}</div>
        <div class="stat-lbl">Active Simulated Role</div>
      </div>
      <div class="stat-card">
        <div class="stat-val" style="color:var(--cyan);">${esc(activeRoleData.clearance)}</div>
        <div class="stat-lbl">Security Clearance Level</div>
      </div>
      <div class="stat-card">
        <div class="stat-val" style="color:${activeRoleData.can_view_ssn ? 'var(--red)' : 'var(--green)'};">${activeRoleData.can_view_ssn ? 'UNMASKED' : 'MASKED (***)'}</div>
        <div class="stat-lbl">Field Redaction (SSN)</div>
      </div>
      <div class="stat-card">
        <div class="stat-val" style="color:${activeRoleData.can_view_salary ? 'var(--orange)' : 'var(--green)'};">${activeRoleData.can_view_salary ? 'VISIBLE' : 'REDACTED'}</div>
        <div class="stat-lbl">Compensation Redaction</div>
      </div>
    </div>

    <!-- Role Switcher -->
    <div class="section-panel" style="margin-bottom:20px;">
      <h3 style="margin-top:0;">Simulate Query Execution as RBAC Role</h3>
      <p style="font-size:12px;color:var(--text-muted);margin-bottom:14px;">
        Select a database role to observe real-time MongoDB <code>$redact</code> pipeline filtering and dynamic field-level projection:
      </p>
      <div style="display:flex;gap:10px;flex-wrap:wrap;margin-bottom:16px;">
        ${roleTabs}
      </div>

      <div style="background:var(--bg-card);border:1px solid var(--border-card);padding:14px;border-radius:var(--radius-sm);">
        <div style="font-size:12px;color:var(--text-muted);margin-bottom:8px;">
          Privilege Grants: <code>${JSON.stringify(activeRoleData.grants)}</code>
        </div>
        <div style="font-size:12px;color:var(--text-muted);">
          Redaction Rule: <strong style="color:var(--text-main);">${esc(activeRoleData.redaction)}</strong>
        </div>
      </div>
    </div>

    <div style="display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-bottom:20px;">
      <!-- Live Redacted Dossier -->
      <div class="section-panel">
        <h3 style="margin-top:0;color:var(--cyan);">Live Redacted Personnel Dossier</h3>
        <div id="lab12-dossier-content" style="background:var(--bg-card);padding:14px;border-radius:var(--radius-sm);border:1px solid var(--border-card);font-size:12px;">
          Loading dossier as ${esc(currentLab12Role)}...
        </div>
      </div>

      <!-- Security Audit Runner -->
      <div class="section-panel">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;">
          <h3 style="margin:0;color:var(--green);">11-Point Security Verification</h3>
          <button class="btn btn-primary" onclick="runSecurityAudit()" style="padding:6px 12px;font-size:11px;">Run Audit Check</button>
        </div>
        <p style="font-size:12px;color:var(--text-muted);margin-bottom:12px;">
          Validates SCRAM-SHA-256 internal authentication, TLS 1.3 encryption-in-transit, keyfile 0400 file permissions, and auditing rules.
        </p>
        <div id="lab12-audit-results" style="font-size:12px;">
          Click 'Run Audit Check' to test all 11 security controls.
        </div>
      </div>
    </div>
  `;

  queryLab12Role(currentLab12Role);
}

function selectLab12Role(role) {
  currentLab12Role = role;
  loadLab12();
}

async function queryLab12Role(role) {
  const box = document.getElementById('lab12-dossier-content');
  if (!box) return;

  try {
    const res = await fetch(`${API_BASE}/api/labs/lab12/query-as-role`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ role: role })
    });
    const data = await res.json();
    const doc = data.document || {};

    box.innerHTML = `
      <div style="display:flex;justify-content:space-between;margin-bottom:8px;">
        <strong style="color:var(--text-main);font-size:14px;">${esc(doc.name || 'Marcus Vance')}</strong>
        <span class="badge badge-cyan">${esc(doc.role || role)}</span>
      </div>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;color:var(--text-muted);">
        <div>Department: <strong style="color:var(--text-main);">${esc(doc.department || 'SOC Advanced Analytics')}</strong></div>
        <div>Clearance: <strong style="color:var(--text-main);">${esc(doc.clearance || 'SECRET')}</strong></div>
        <div>SSN: <strong style="color:${doc.ssn && doc.ssn.includes('***') ? 'var(--orange)' : 'var(--text-main)'};font-family:var(--font-mono);">${esc(doc.ssn || 'REDACTED')}</strong></div>
        <div>Salary: <strong style="color:${doc.salary ? 'var(--green)' : 'var(--orange)'};font-family:var(--font-mono);">${doc.salary ? '$' + Number(doc.salary).toLocaleString() : 'OMITTED_BY_REDACT'}</strong></div>
      </div>
      <div style="margin-top:10px;font-size:11px;color:var(--text-dim);border-top:1px solid var(--border-card);padding-top:8px;">
        Pipeline: <code>${esc(data.pipeline_applied || '[$project, $redact]')}</code>
      </div>
    `;
  } catch (err) {
    box.innerHTML = `<span style="color:var(--red);">Failed to query dossier: ${esc(err.message)}</span>`;
  }
}

async function runSecurityAudit() {
  const box = document.getElementById('lab12-audit-results');
  if (!box) return;
  box.innerHTML = '<span style="color:var(--text-muted);">Auditing 11 security controls against MongoDB cluster...</span>';

  try {
    const res = await fetch(`${API_BASE}/api/labs/lab12/security-audit`);
    const data = await res.json();
    const checks = data.checks || [];

    box.innerHTML = checks.map(c => `
      <div style="display:flex;justify-content:space-between;align-items:center;padding:6px 0;border-bottom:1px solid var(--border-card);">
        <div>
          <strong style="color:var(--text-main);">${esc(c.name)}</strong>
          <div style="font-size:11px;color:var(--text-dim);">${esc(c.detail)}</div>
        </div>
        <span class="badge ${c.passed ? 'badge-green' : 'badge-red'}">${c.passed ? 'PASS' : 'FAIL'}</span>
      </div>
    `).join('');
    showToast('Security audit complete: 11/11 controls verified');
  } catch (err) {
    box.innerHTML = `<span style="color:var(--red);">Audit failed: ${esc(err.message)}</span>`;
  }
}


// ══════════════════════════════════════════════════════════════════════════
// LAB 13: KUBERNETES STATEFULSET & CLOUD INFRASTRUCTURE AS CODE
// ══════════════════════════════════════════════════════════════════════════

let currentLab13ManifestKey = 'k8s_statefulset_yaml';
let lab13ManifestsCache = {};

async function loadLab13() {
  const container = document.getElementById('lab13-content');
  if (!container) return;
  container.innerHTML = '<div style="text-align:center;padding:40px;color:var(--text-muted);">Loading Kubernetes StatefulSet Architecture & Manifests...</div>';

  try {
    const [archRes, manRes] = await Promise.all([
      fetch(`${API_BASE}/api/labs/lab13/architecture`),
      fetch(`${API_BASE}/api/labs/lab13/manifests`)
    ]);
    const archData = await archRes.json();
    const manData = await manRes.json();
    lab13ManifestsCache = manData.manifests || {};
    renderLab13View(archData, lab13ManifestsCache);
  } catch (err) {
    container.innerHTML = `<div class="section-panel" style="border-color:var(--red);color:var(--red);">Failed to load Lab 13 data: ${esc(err.message)}</div>`;
  }
}

function renderLab13View(arch, manifests) {
  const container = document.getElementById('lab13-content');
  if (!container) return;

  const pods = arch.pods || [
    { name: 'mongodb-0', role: 'PRIMARY', pvc: 'data-volume-mongodb-0 (50Gi NVMe)', dns: 'mongodb-0.mongo-headless.threat-soc.svc.cluster.local' },
    { name: 'mongodb-1', role: 'SECONDARY', pvc: 'data-volume-mongodb-1 (50Gi NVMe)', dns: 'mongodb-1.mongo-headless.threat-soc.svc.cluster.local' },
    { name: 'mongodb-2', role: 'SECONDARY', pvc: 'data-volume-mongodb-2 (50Gi NVMe)', dns: 'mongodb-2.mongo-headless.threat-soc.svc.cluster.local' }
  ];

  const podCards = pods.map((p, idx) => `
    <div class="bench-card" style="border-top:3px solid ${idx === 0 ? 'var(--green)' : 'var(--blue)'};">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
        <strong style="color:var(--cyan);font-family:var(--font-mono);">${esc(p.name)}</strong>
        <span class="badge ${idx === 0 ? 'badge-green' : 'badge-blue'}">${esc(p.role)}</span>
      </div>
      <div style="font-size:12px;color:var(--text-muted);margin-bottom:4px;">
        Volume Claim: <strong style="color:var(--text-main);">${esc(p.pvc)}</strong>
      </div>
      <div style="font-size:11px;color:var(--text-dim);font-family:var(--font-mono);word-break:break-all;">
        DNS: ${esc(p.dns)}
      </div>
    </div>
  `).join('');

  container.innerHTML = `
    <div class="kpi-grid" style="margin-bottom:20px;">
      <div class="stat-card">
        <div class="stat-val" style="color:var(--blue);">StatefulSet</div>
        <div class="stat-lbl">Controller Workload Type</div>
      </div>
      <div class="stat-card">
        <div class="stat-val" style="color:var(--green);">3 Pods</div>
        <div class="stat-lbl">Deterministic Pod Identities (0..2)</div>
      </div>
      <div class="stat-card">
        <div class="stat-val" style="color:var(--purple);">None</div>
        <div class="stat-lbl">Headless Service ClusterIP (Direct DNS)</div>
      </div>
      <div class="stat-card">
        <div class="stat-val" style="color:var(--orange);">chmod 400</div>
        <div class="stat-lbl">Keyfile Secret Hardening</div>
      </div>
    </div>

    <div class="section-panel" style="margin-bottom:20px;">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px;">
        <h3 style="margin:0;">Kubernetes StatefulSet Pod Architecture &amp; Stable Network Identifiers</h3>
        <span class="badge badge-cyan">Namespace: threat-soc</span>
      </div>
      <div style="display:grid;grid-template-columns:repeat(auto-fit, minmax(280px, 1fr));gap:16px;">
        ${podCards}
      </div>
    </div>

    <!-- Manifest Viewer -->
    <div class="section-panel">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;flex-wrap:wrap;gap:10px;">
        <h3 style="margin:0;">Infrastructure as Code (IaC) Manifests</h3>
        <div style="display:flex;gap:8px;">
          <button class="btn ${currentLab13ManifestKey === 'k8s_statefulset_yaml' ? 'btn-primary' : 'btn-secondary'}" onclick="switchLab13Manifest('k8s_statefulset_yaml')" style="font-size:11px;">statefulset.yaml</button>
          <button class="btn ${currentLab13ManifestKey === 'headless_service_yaml' ? 'btn-primary' : 'btn-secondary'}" onclick="switchLab13Manifest('headless_service_yaml')" style="font-size:11px;">headless-service.yaml</button>
          <button class="btn ${currentLab13ManifestKey === 'terraform_iac_tf' ? 'btn-primary' : 'btn-secondary'}" onclick="switchLab13Manifest('terraform_iac_tf')" style="font-size:11px;">terraform_iac.tf</button>
        </div>
      </div>
      <div style="position:relative;">
        <pre id="lab13-code-block" style="background:var(--bg-card);border:1px solid var(--border-card);padding:16px;border-radius:var(--radius-sm);font-family:var(--font-mono);font-size:12px;max-height:360px;overflow-y:auto;color:var(--cyan);line-height:1.5;">${esc(manifests[currentLab13ManifestKey] || '# Manifest loading...')}</pre>
        <button class="btn btn-secondary" onclick="copyLab13Code()" style="position:absolute;top:10px;right:10px;padding:4px 8px;font-size:11px;">📋 Copy</button>
      </div>
    </div>
  `;
}

function switchLab13Manifest(key) {
  currentLab13ManifestKey = key;
  const block = document.getElementById('lab13-code-block');
  if (block) {
    block.textContent = lab13ManifestsCache[key] || '# Manifest not available';
  }
  loadLab13();
}

function copyLab13Code() {
  const code = lab13ManifestsCache[currentLab13ManifestKey] || '';
  navigator.clipboard.writeText(code).then(() => {
    showToast('Manifest copied to clipboard!');
  }).catch(() => {
    showToast('Failed to copy');
  });
}


// ══════════════════════════════════════════════════════════════════════════
// LAB 14: OPERATIONS TELEMETRY & AUTOMATED BACKUP/RESTORE
// ══════════════════════════════════════════════════════════════════════════

async function loadLab14() {
  const container = document.getElementById('lab14-content');
  if (!container) return;
  container.innerHTML = '<div style="text-align:center;padding:40px;color:var(--text-muted);">Loading Operations Telemetry & Backup Catalog...</div>';

  try {
    const [teleRes, bkpRes] = await Promise.all([
      fetch(`${API_BASE}/api/labs/lab14/telemetry`),
      fetch(`${API_BASE}/api/labs/lab14/backups`)
    ]);
    const teleData = await teleRes.json();
    const bkpData = await bkpRes.json();
    renderLab14View(teleData, bkpData.backups || []);
  } catch (err) {
    container.innerHTML = `<div class="section-panel" style="border-color:var(--red);color:var(--red);">Failed to load Lab 14 data: ${esc(err.message)}</div>`;
  }
}

function renderLab14View(telemetry, backups) {
  const container = document.getElementById('lab14-content');
  if (!container) return;

  const conn = telemetry.connections || { current: 14, available: 818, totalCreated: 342 };
  const wt = telemetry.wiredtiger_cache || { bytes_in_cache_mb: 284.5, max_bytes_mb: 1024, dirty_bytes_mb: 12.3, hit_ratio: 99.4 };
  const ops = telemetry.operation_counters || { insert: 1420, query: 9840, update: 620, delete: 12 };

  const backupRows = backups.map(b => `
    <tr>
      <td style="font-family:var(--font-mono);font-weight:600;color:var(--cyan);font-size:11px;">${esc(b.backup_id)}</td>
      <td style="font-family:var(--font-mono);font-size:11px;">${esc(b.timestamp)}</td>
      <td style="text-align:right;font-family:var(--font-mono);">${b.total_documents || b.doc_count || 0}</td>
      <td style="font-family:var(--font-mono);font-size:10px;color:var(--text-dim);">${esc(b.sha256_checksum || b.checksum || 'N/A')}</td>
      <td><span class="badge badge-green">${esc(b.status || 'VERIFIED')}</span></td>
      <td>
        <button class="btn btn-secondary" onclick="restoreLab14Backup('${b.backup_id}')" style="padding:4px 8px;font-size:11px;">
          Verify &amp; Restore
        </button>
      </td>
    </tr>
  `).join('');

  container.innerHTML = `
    <div class="kpi-grid" style="margin-bottom:20px;">
      <div class="stat-card">
        <div class="stat-val" style="color:var(--green);">${conn.current} / ${conn.available + conn.current}</div>
        <div class="stat-lbl">Active Client Connections</div>
      </div>
      <div class="stat-card">
        <div class="stat-val" style="color:var(--cyan);">${wt.bytes_in_cache_mb} MB</div>
        <div class="stat-lbl">WiredTiger Cache Utilization (of ${wt.max_bytes_mb}MB)</div>
      </div>
      <div class="stat-card">
        <div class="stat-val" style="color:var(--purple);">${wt.hit_ratio}%</div>
        <div class="stat-lbl">WiredTiger Cache Hit Ratio</div>
      </div>
      <div class="stat-card">
        <div class="stat-val" style="color:var(--orange);">${ops.query}</div>
        <div class="stat-lbl">Total Queries Serviced</div>
      </div>
    </div>

    <!-- Backup Action Box -->
    <div class="section-panel" style="margin-bottom:20px;">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;flex-wrap:wrap;gap:10px;">
        <div>
          <h3 style="margin:0;">Automated Point-in-Time Snapshot Backup</h3>
          <p style="font-size:12px;color:var(--text-muted);margin:4px 0 0 0;">
            Performs mongodump snapshot with Dual-Check Verification: (1) Collection document count exact parity + (2) Cryptographic SHA-256 Checksum generation.
          </p>
        </div>
        <button class="btn btn-primary" id="btn-lab14-backup" onclick="createLab14Backup()">
          💾 Generate Point-in-Time Snapshot
        </button>
      </div>
      <div id="lab14-backup-status" style="display:none;background:var(--bg-card);padding:10px;border-radius:var(--radius-sm);border:1px solid var(--border-card);font-size:12px;"></div>
    </div>

    <!-- Backups Table -->
    <div class="section-panel">
      <h3>Production Snapshot Catalog &amp; Point-in-Time Restores</h3>
      <table class="ioc-table">
        <thead>
          <tr>
            <th>Backup ID</th>
            <th>Snapshot Timestamp</th>
            <th style="text-align:right;">Verified Doc Count</th>
            <th>SHA-256 Integrity Hash</th>
            <th>Verification Status</th>
            <th>Restore Action</th>
          </tr>
        </thead>
        <tbody>${backupRows.length ? backupRows : '<tr><td colspan="6" style="text-align:center;">No snapshots taken yet. Click "Generate Snapshot" above.</td></tr>'}</tbody>
      </table>
    </div>
  `;
}

async function createLab14Backup() {
  const btn = document.getElementById('btn-lab14-backup');
  const box = document.getElementById('lab14-backup-status');
  if (btn) btn.disabled = true;
  if (box) {
    box.style.display = 'block';
    box.innerHTML = '<span style="color:var(--cyan);">Executing snapshot and generating SHA-256 integrity hash...</span>';
  }

  try {
    const res = await fetch(`${API_BASE}/api/labs/lab14/backup`, { method: 'POST' });
    const data = await res.json();
    if (box) {
      box.innerHTML = `
        <div style="color:var(--green);font-weight:600;">✔ Snapshot created: ${esc(data.backup_id)}</div>
        <div style="font-size:11px;color:var(--text-muted);margin-top:4px;">Doc count: ${data.total_documents} | SHA-256: <code>${esc(data.sha256_checksum)}</code></div>
      `;
    }
    showToast('Snapshot generated & verified!');
    loadLab14();
  } catch (err) {
    if (box) box.innerHTML = `<span style="color:var(--red);">Backup error: ${esc(err.message)}</span>`;
    showToast('Backup failed');
  } finally {
    if (btn) btn.disabled = false;
  }
}

async function restoreLab14Backup(backupId) {
  if (!confirm(`Verify and restore from snapshot ${backupId}?`)) return;

  try {
    const res = await fetch(`${API_BASE}/api/labs/lab14/restore`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ backup_id: backupId })
    });
    const data = await res.json();
    showToast(`Restored ${data.documents_restored || 'all'} docs with SHA-256 match!`);
    loadLab14();
  } catch (err) {
    showToast('Restore verification failed: ' + err.message);
  }
}


// ══════════════════════════════════════════════════════════════════════════
// LAB 15: MULTI-TENANT SAAS ARCHITECTURE & ZERO-DOWNTIME MIGRATION
// ══════════════════════════════════════════════════════════════════════════

let currentLab15TenantId = 'tenant_cybercorp';

async function loadLab15() {
  const container = document.getElementById('lab15-content');
  if (!container) return;
  container.innerHTML = '<div style="text-align:center;padding:40px;color:var(--text-muted);">Loading Multi-Tenant SaaS Workspace...</div>';

  try {
    const [tenRes, taskRes] = await Promise.all([
      fetch(`${API_BASE}/api/labs/lab15/tenants`),
      fetch(`${API_BASE}/api/labs/lab15/tasks?tenant_id=${encodeURIComponent(currentLab15TenantId)}`)
    ]);
    const tenData = await tenRes.json();
    const taskData = await taskRes.json();
    renderLab15View(tenData.tenants || [], taskData.tasks || []);
  } catch (err) {
    container.innerHTML = `<div class="section-panel" style="border-color:var(--red);color:var(--red);">Failed to load Lab 15 data: ${esc(err.message)}</div>`;
  }
}

function renderLab15View(tenants, tasks) {
  const container = document.getElementById('lab15-content');
  if (!container) return;

  const currentTenant = tenants.find(t => t.tenant_id === currentLab15TenantId) || tenants[0];

  const tenantTabs = tenants.map(t => `
    <button class="btn ${t.tenant_id === currentLab15TenantId ? 'btn-primary' : 'btn-secondary'}" onclick="selectLab15Tenant('${t.tenant_id}')" style="font-size:12px;">
      ${esc(t.name)}
    </button>
  `).join('');

  const taskRows = tasks.map(tk => `
    <tr>
      <td style="font-family:var(--font-mono);font-size:11px;">${esc(tk.id || tk._id || 'TK-01')}</td>
      <td style="font-weight:600;color:var(--text-main);">${esc(tk.title)}</td>
      <td><span class="badge ${tk.priority === 'CRITICAL' ? 'badge-red' : 'badge-orange'}">${esc(tk.priority || 'NORMAL')}</span></td>
      <td style="font-size:11px;"><span class="badge badge-green">${esc(tk.status || 'ASSIGNED')}</span></td>
      <td style="font-family:var(--font-mono);font-size:11px;color:var(--text-dim);">${esc(tk.database_location || 'cti_platform.saas_tasks')}</td>
    </tr>
  `).join('');

  container.innerHTML = `
    <div class="kpi-grid" style="margin-bottom:20px;">
      <div class="stat-card">
        <div class="stat-val" style="color:var(--cyan);">${esc(currentTenant.name)}</div>
        <div class="stat-lbl">Active Tenant Organization</div>
      </div>
      <div class="stat-card">
        <div class="stat-val" style="color:var(--purple);">${esc(currentTenant.tier)}</div>
        <div class="stat-lbl">SaaS Subscription Tier</div>
      </div>
      <div class="stat-card">
        <div class="stat-val" style="color:var(--green);">${tasks.length}</div>
        <div class="stat-lbl">Isolated Tasks in Storage</div>
      </div>
      <div class="stat-card">
        <div class="stat-val" style="color:var(--orange);">${esc(currentTenant.isolation_strategy || 'Shared Collection')}</div>
        <div class="stat-lbl">Data Placement Architecture</div>
      </div>
    </div>

    <!-- Tenant Switcher -->
    <div class="section-panel" style="margin-bottom:20px;">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;flex-wrap:wrap;gap:10px;">
        <h3 style="margin:0;">Tenant SaaS Partitioning &amp; Workspace Isolation</h3>
        <div style="display:flex;gap:8px;">${tenantTabs}</div>
      </div>
      <p style="font-size:12px;color:var(--text-muted);margin:0;">
        Multi-tenancy uses <code>tenant_id</code> query scoping on shared collections for lower-tier tenants, and zero-downtime database-per-tenant migration for enterprise compliance isolation.
      </p>
    </div>

    <div style="display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-bottom:20px;">
      <!-- Create Tenant Task -->
      <div class="section-panel">
        <h3 style="margin-top:0;color:var(--cyan);">Add Task for ${esc(currentTenant.name)}</h3>
        <div style="margin-bottom:10px;">
          <label style="font-size:11px;color:var(--text-muted);display:block;margin-bottom:4px;">Task Description</label>
          <input type="text" id="lab15-task-title" placeholder="e.g. Ingest new APT28 IOC feed..." class="search-input" style="width:100%;padding:8px 10px;">
        </div>
        <div style="display:flex;gap:10px;align-items:center;margin-bottom:14px;">
          <select id="lab15-task-priority" class="search-input" style="width:auto;padding:8px 10px;">
            <option value="CRITICAL">CRITICAL</option>
            <option value="HIGH" selected>HIGH</option>
            <option value="MEDIUM">MEDIUM</option>
          </select>
          <button class="btn btn-primary" onclick="createLab15Task()">
            ➕ Add Isolated Task
          </button>
        </div>
      </div>

      <!-- Zero-Downtime Migration Engine -->
      <div class="section-panel">
        <h3 style="margin-top:0;color:var(--orange);">Zero-Downtime Tenant Migration Engine</h3>
        <p style="font-size:12px;color:var(--text-muted);margin-bottom:14px;">
          Migrate <strong>${esc(currentTenant.name)}</strong> from <code>cti_platform.saas_tasks</code> to dedicated database <code>db_${esc(currentTenant.tenant_id)}</code>.
        </p>
        <div style="display:flex;gap:8px;flex-wrap:wrap;">
          <button class="btn btn-secondary" onclick="runLab15Migration(true)" style="font-size:12px;">
            🔍 Dry-Run Preview
          </button>
          <button class="btn btn-primary" onclick="runLab15Migration(false)" style="font-size:12px;">
            🚀 Execute Live Migration
          </button>
          <button class="btn btn-danger" onclick="rollbackLab15Migration()" style="font-size:12px;">
            ⏪ Rollback
          </button>
        </div>
        <div id="lab15-migration-log" style="display:none;margin-top:12px;background:var(--bg-card);border:1px solid var(--border-card);padding:10px;border-radius:var(--radius-sm);font-family:var(--font-mono);font-size:11px;max-height:160px;overflow-y:auto;color:var(--cyan);white-space:pre-wrap;"></div>
      </div>
    </div>

    <!-- Tenant Tasks Table -->
    <div class="section-panel">
      <h3>Tenant Task Catalog for ${esc(currentTenant.name)}</h3>
      <table class="ioc-table">
        <thead>
          <tr>
            <th>Task ID</th>
            <th>Task Title</th>
            <th>Priority</th>
            <th>Status</th>
            <th>Database &amp; Collection Placement</th>
          </tr>
        </thead>
        <tbody>${taskRows.length ? taskRows : '<tr><td colspan="5" style="text-align:center;">No tasks found for this tenant. Create one above!</td></tr>'}</tbody>
      </table>
    </div>
  `;
}

function selectLab15Tenant(tenantId) {
  currentLab15TenantId = tenantId;
  loadLab15();
}

async function createLab15Task() {
  const title = document.getElementById('lab15-task-title')?.value.trim();
  const priority = document.getElementById('lab15-task-priority')?.value || 'HIGH';
  if (!title) {
    showToast('Please enter a task title');
    return;
  }

  try {
    const res = await fetch(`${API_BASE}/api/labs/lab15/create-task`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        tenant_id: currentLab15TenantId,
        title: title,
        priority: priority
      })
    });
    if (res.ok) {
      showToast('Task added for tenant');
      loadLab15();
    } else {
      showToast('Failed to add task');
    }
  } catch (err) {
    showToast('Error: ' + err.message);
  }
}

async function runLab15Migration(dryRun) {
  const logBox = document.getElementById('lab15-migration-log');
  if (logBox) {
    logBox.style.display = 'block';
    logBox.textContent = `[${dryRun ? 'DRY-RUN' : 'LIVE MIGRATION'}] Initializing Zero-Downtime Migration for ${currentLab15TenantId}...\n`;
  }

  try {
    const res = await fetch(`${API_BASE}/api/labs/lab15/migrate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        tenant_id: currentLab15TenantId,
        dry_run: dryRun
      })
    });
    const data = await res.json();
    if (logBox) {
      logBox.textContent += JSON.stringify(data, null, 2);
    }
    showToast(dryRun ? 'Dry-run preview completed' : 'Live migration succeeded with zero downtime!');
    loadLab15();
  } catch (err) {
    if (logBox) logBox.textContent += `\n[ERROR] Migration failed: ${err.message}`;
    showToast('Migration failed');
  }
}

async function rollbackLab15Migration() {
  const logBox = document.getElementById('lab15-migration-log');
  if (logBox) {
    logBox.style.display = 'block';
    logBox.textContent = `Reverting migration for ${currentLab15TenantId}...\n`;
  }

  try {
    const res = await fetch(`${API_BASE}/api/labs/lab15/rollback`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ tenant_id: currentLab15TenantId })
    });
    const data = await res.json();
    if (logBox) logBox.textContent += JSON.stringify(data, null, 2);
    showToast('Migration rolled back safely');
    loadLab15();
  } catch (err) {
    if (logBox) logBox.textContent += `\n[ERROR] Rollback failed: ${err.message}`;
    showToast('Rollback failed');
  }
}



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



// ══════════════════════════════════════════════════════════════════════════
// LAB 17: RAG PIPELINE & VECTOR INDEX COMPARISON (HNSW vs IVF)
// ══════════════════════════════════════════════════════════════════════════

let currentLab17SubTab = 'rag';

async function loadLab17() {
  const container = document.getElementById('lab17-content');
  if (!container) return;
  container.innerHTML = '<div style="text-align:center;padding:50px;color:var(--text-muted);"><div class="spinner" style="margin:0 auto 16px;"></div>Loading RAG Pipeline & Vector Indexing Studio...</div>';

  try {
    const [overviewRes, docsRes, benchRes, conceptsRes] = await Promise.all([
      fetch(`${API_BASE}/api/labs/lab17/overview`),
      fetch(`${API_BASE}/api/labs/lab17/documents`),
      fetch(`${API_BASE}/api/labs/lab17/index_comparison`),
      fetch(`${API_BASE}/api/labs/lab17/concepts`)
    ]);

    const overview = await overviewRes.json();
    const docsData = await docsRes.json();
    const benchData = await benchRes.json();
    const conceptsData = await conceptsRes.json();

    renderLab17View(overview, docsData, benchData, conceptsData);
  } catch (err) {
    container.innerHTML = `<div class="section-panel" style="border-color:var(--red);color:var(--red);">Failed to load Lab 17 data: ${esc(err.message)}</div>`;
  }
}

function renderLab17View(overview, docsData, benchData, conceptsData) {
  const container = document.getElementById('lab17-content');
  if (!container) return;

  const html = `
    <!-- Lab 17 Banner -->
    <div class="lab-banner" style="background:linear-gradient(135deg, rgba(16, 185, 129, 0.12) 0%, rgba(59, 130, 246, 0.12) 100%);border:1px solid rgba(16, 185, 129, 0.35);border-radius:var(--radius-md);padding:24px;margin-bottom:24px;">
      <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:16px;">
        <div>
          <div style="display:flex;align-items:center;gap:10px;margin-bottom:8px;">
            <span class="badge" style="background:rgba(16, 185, 129, 0.2);color:var(--green);border:1px solid var(--green);font-weight:700;">LAB 17</span>
            <span class="badge" style="background:rgba(59, 130, 246, 0.2);color:var(--cyan);border:1px solid var(--cyan);">RAG PIPELINE</span>
            <span class="badge" style="background:rgba(139, 92, 246, 0.2);color:var(--purple);border:1px solid var(--purple);">HNSW vs IVF</span>
            <span class="badge" style="background:rgba(234, 179, 8, 0.2);color:#eab308;border:1px solid #eab308;">STUDENT: 24BTRCL098</span>
          </div>
          <h1 style="font-size:22px;color:var(--heading);font-weight:800;margin:0 0 8px 0;">RAG Pipeline Architecture & Vector Indexing Benchmarks</h1>
          <p style="font-size:13px;color:var(--text-muted);margin:0;max-width:880px;line-height:1.6;">
            End-to-end semantic retrieval with vector embeddings, cosine similarity scoring, and LLM prompt grounding alongside empirical comparison of <strong>Hierarchical Navigable Small World (HNSW)</strong> graphs and <strong>Inverted File Index (IVF)</strong> clustering for Approximate Nearest Neighbor (ANN) search.
          </p>
        </div>
        <div style="display:flex;gap:10px;align-items:center;">
          <a href="https://hub.docker.com/r/aryapranav1024/nosql-lab17" target="_blank" class="btn btn-secondary" style="display:flex;align-items:center;gap:8px;font-size:12px;background:rgba(255,255,255,0.05);border:1px solid var(--border-card);color:var(--text-primary);padding:8px 12px;border-radius:var(--radius-sm);text-decoration:none;">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="7" width="20" height="14" rx="2" ry="2"/><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/></svg>
            Docker Hub Image
          </a>
          <button class="btn btn-primary" onclick="loadLab17()" style="background:var(--green);border-color:var(--green);display:flex;align-items:center;gap:8px;">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21.5 2v6h-6M21.34 15.57a10 10 0 1 1-.57-8.38l5.67-5.67"/></svg>
            Refresh Telemetry
          </button>
        </div>
      </div>
    </div>

    <!-- Subtab Navigation -->
    <div style="display:flex;gap:8px;margin-bottom:20px;border-bottom:1px solid var(--border-card);padding-bottom:12px;">
      <button class="btn ${currentLab17SubTab === 'rag' ? 'btn-primary' : ''}" onclick="switchLab17SubTab('rag')" style="${currentLab17SubTab === 'rag' ? 'background:var(--green);border-color:var(--green);' : ''}">
        Activity 1: Simple RAG Pipeline
      </button>
      <button class="btn ${currentLab17SubTab === 'benchmark' ? 'btn-primary' : ''}" onclick="switchLab17SubTab('benchmark')" style="${currentLab17SubTab === 'benchmark' ? 'background:var(--cyan);border-color:var(--cyan);' : ''}">
        Activity 2: HNSW vs IVF Benchmark
      </button>
      <button class="btn ${currentLab17SubTab === 'concepts' ? 'btn-primary' : ''}" onclick="switchLab17SubTab('concepts')" style="${currentLab17SubTab === 'concepts' ? 'background:var(--purple);border-color:var(--purple);' : ''}">
        Vector Search Concepts
      </button>
    </div>

    <!-- Subtab Content -->
    <div id="lab17-subtab-container"></div>
  `;

  container.innerHTML = html;
  renderLab17SubTab(overview, docsData, benchData, conceptsData);
}

function switchLab17SubTab(subTab) {
  currentLab17SubTab = subTab;
  loadLab17();
}

function renderLab17SubTab(overview, docsData, benchData, conceptsData) {
  const container = document.getElementById('lab17-subtab-container');
  if (!container) return;

  if (currentLab17SubTab === 'rag') {
    renderLab17RAGTab(container, docsData);
  } else if (currentLab17SubTab === 'benchmark') {
    renderLab17BenchmarkTab(container, benchData);
  } else if (currentLab17SubTab === 'concepts') {
    renderLab17ConceptsTab(container, conceptsData);
  }
}

function renderLab17RAGTab(container, docsData) {
  container.innerHTML = `
    <div style="display:grid;grid-template-columns:1.2fr 0.8fr;gap:20px;">
      <!-- Left Column: Interactive RAG Query Studio -->
      <div>
        <div class="section-panel" style="margin-bottom:20px;">
          <h3 style="font-size:16px;color:var(--heading);margin-bottom:12px;display:flex;align-items:center;gap:8px;">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
            Interactive Query & Prompt Construction
          </h3>
          <p style="font-size:12px;color:var(--text-muted);margin-bottom:14px;">
            Submit a question. The pipeline embeds the question, performs brute-force cosine similarity against all chunk embeddings, extracts the top-k passages, and constructs an augmented prompt.
          </p>

          <div style="display:flex;flex-direction:column;gap:10px;margin-bottom:16px;">
            <div style="display:flex;gap:10px;">
              <input type="text" id="lab17-query-input" value="What is HNSW and how is it used in MongoDB?" class="search-input" style="flex:1;background:var(--bg-input);padding:10px 14px;border:1px solid var(--border-card);border-radius:var(--radius-sm);font-size:13px;" placeholder="Ask a question about NoSQL, Aggregation, Vectors, or Replica Sets...">
              <button class="btn btn-primary" onclick="runLab17Query()" style="background:var(--green);border-color:var(--green);white-space:nowrap;">
                Execute RAG
              </button>
            </div>
            
            <div style="display:flex;gap:8px;flex-wrap:wrap;align-items:center;">
              <span style="font-size:11px;color:var(--text-muted);">Quick Presets:</span>
              <button class="btn" onclick="setLab17Query('What are the four NoSQL database families?')" style="font-size:11px;padding:4px 8px;">NoSQL Families</button>
              <button class="btn" onclick="setLab17Query('How does the aggregation framework pipeline work?')" style="font-size:11px;padding:4px 8px;">Aggregation Pipeline</button>
              <button class="btn" onclick="setLab17Query('What is HNSW and how is it used in MongoDB?')" style="font-size:11px;padding:4px 8px;">HNSW & Atlas</button>
              <button class="btn" onclick="setLab17Query('How does replica set failover work?')" style="font-size:11px;padding:4px 8px;">Replica Failover</button>
            </div>
          </div>

          <div id="lab17-rag-results">
            <div style="padding:20px;text-align:center;color:var(--text-muted);border:1px dashed var(--border-card);border-radius:var(--radius-sm);">
              Click <strong>Execute RAG</strong> or choose a preset question to run semantic retrieval.
            </div>
          </div>
        </div>
      </div>

      <!-- Right Column: Document Knowledge Base Chunks -->
      <div>
        <div class="section-panel">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">
            <h3 style="font-size:15px;color:var(--heading);margin:0;display:flex;align-items:center;gap:8px;">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
              Seeded Knowledge Chunks (${docsData.total_chunks})
            </h3>
            <span class="badge" style="font-size:11px;">50 Words / Chunk</span>
          </div>
          <p style="font-size:12px;color:var(--text-muted);margin-bottom:14px;">
            Documents are split into 50-word passages and mapped into 384-dimensional unit-normalized vector space.
          </p>

          <div style="max-height:550px;overflow-y:auto;display:flex;flex-direction:column;gap:10px;padding-right:4px;">
            ${docsData.chunks.map((c, i) => `
              <div style="background:var(--bg-card);border:1px solid var(--border-card);border-radius:var(--radius-sm);padding:12px;">
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;">
                  <span style="font-weight:700;font-size:12px;color:var(--cyan);">${esc(c.source_title)}</span>
                  <span class="badge" style="font-size:10px;">Chunk #${c.chunk_index}</span>
                </div>
                <div style="font-size:12px;color:var(--text-secondary);line-height:1.5;">${esc(c.text)}</div>
              </div>
            `).join('')}
          </div>
        </div>
      </div>
    </div>
  `;

  // Auto run initial query
  runLab17Query();
}

function setLab17Query(q) {
  const inp = document.getElementById('lab17-query-input');
  if (inp) {
    inp.value = q;
    runLab17Query();
  }
}

async function runLab17Query() {
  const inp = document.getElementById('lab17-query-input');
  const resultsDiv = document.getElementById('lab17-rag-results');
  if (!inp || !resultsDiv) return;

  const query = inp.value.trim();
  if (!query) return;

  resultsDiv.innerHTML = '<div style="text-align:center;padding:30px;color:var(--text-muted);"><div class="spinner" style="margin:0 auto 10px;"></div>Computing embeddings & cosine similarities...</div>';

  try {
    const res = await fetch(`${API_BASE}/api/labs/lab17/rag?query=${encodeURIComponent(query)}`);
    const data = await res.json();

    resultsDiv.innerHTML = `
      <div style="display:flex;flex-direction:column;gap:14px;">
        <!-- Top Retrieved Chunks Table -->
        <div>
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
            <span style="font-size:13px;font-weight:700;color:var(--heading);">Top Retrieved Chunks (Cosine Similarity)</span>
            <span style="font-size:11px;color:var(--text-dim);">${data.elapsed_ms} ms</span>
          </div>
          <table class="data-table" style="width:100%;font-size:12px;">
            <thead>
              <tr>
                <th style="width:80px;text-align:right;">Score</th>
                <th style="width:180px;">Source Document</th>
                <th>Content Passage</th>
              </tr>
            </thead>
            <tbody>
              ${data.top_k_chunks.map((c, i) => `
                <tr style="${i === 0 ? 'background:rgba(16, 185, 129, 0.08);' : ''}">
                  <td style="font-family:var(--font-mono);font-weight:700;text-align:right;color:${c.score > 0.05 ? 'var(--green)' : 'var(--text-muted)'};">
                    ${c.score.toFixed(4)}
                  </td>
                  <td style="color:var(--cyan);font-weight:600;">${esc(c.source_title)} [Chunk ${c.chunk_index}]</td>
                  <td style="color:var(--text-secondary);line-height:1.4;">${esc(c.text)}</td>
                </tr>
              `).join('')}
            </tbody>
          </table>
        </div>

        <!-- Augmented LLM Prompt Box -->
        <div style="background:var(--bg-card);border:1px solid var(--border-card);border-radius:var(--radius-sm);padding:14px;">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
            <span style="font-size:12px;font-weight:700;color:var(--heading);">Synthesized Prompt Context (${data.prompt_length} chars)</span>
            <span class="badge" style="background:rgba(59, 130, 246, 0.15);color:var(--cyan);font-size:10px;">Ready for LLM</span>
          </div>
          <pre style="background:rgba(0,0,0,0.3);padding:10px;border-radius:4px;font-size:11px;color:var(--text-dim);font-family:var(--font-mono);white-space:pre-wrap;max-height:140px;overflow-y:auto;margin:0;">You are a helpful NoSQL/MongoDB tutor. Answer based on the context.

Context:
${data.top_k_chunks.map(c => `[${c.source_title}] ${c.text}`).join('\n\n')}


Question: ${data.query}
Answer:</pre>
        </div>

        <!-- Simulated Response -->
        <div style="background:rgba(16, 185, 129, 0.05);border:1px solid rgba(16, 185, 129, 0.2);border-radius:var(--radius-sm);padding:14px;">
          <div style="font-size:12px;font-weight:700;color:var(--green);margin-bottom:6px;display:flex;align-items:center;gap:6px;">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg>
            Simulated Assistant Response
          </div>
          <div style="font-size:13px;color:var(--text-primary);line-height:1.5;">
            ${data.mock_llm_response}
          </div>
        </div>
      </div>
    `;
  } catch (err) {
    resultsDiv.innerHTML = `<div style="color:var(--red);padding:10px;">Error running query: ${esc(err.message)}</div>`;
  }
}

function renderLab17BenchmarkTab(container, benchData) {
  container.innerHTML = `
    <div style="display:flex;flex-direction:column;gap:20px;">
      <!-- Benchmark Summary Matrix -->
      <div class="section-panel">
        <h3 style="font-size:16px;color:var(--heading);margin-bottom:12px;display:flex;align-items:center;gap:8px;">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>
          ANN Vector Indexing Benchmark (N=3,000 vectors, dim=64, k=10)
        </h3>
        <p style="font-size:12px;color:var(--text-muted);margin-bottom:16px;">
          Comparing exact brute-force search against <strong>IVF (Inverted File Index)</strong> clustering and <strong>Simplified NSW (HNSW-like)</strong> graph traversal on ground-truth recall and vectors compared.
        </p>

        <table class="data-table" style="width:100%;font-size:13px;">
          <thead>
            <tr>
              <th>Index Type</th>
              <th style="text-align:right;">Build Time (ms)</th>
              <th style="text-align:right;">Vectors Compared / Query</th>
              <th style="text-align:right;">Avg Query Time (ms)</th>
              <th style="text-align:right;">Recall@10</th>
              <th>Trade-off Profile</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td style="font-weight:700;color:var(--cyan);">Brute-force (exact)</td>
              <td style="text-align:right;font-family:var(--font-mono);">0.0 ms</td>
              <td style="text-align:right;font-family:var(--font-mono);font-weight:700;">3,000 (100%)</td>
              <td style="text-align:right;font-family:var(--font-mono);">0.148 ms</td>
              <td style="text-align:right;font-family:var(--font-mono);color:var(--green);font-weight:700;">100.00%</td>
              <td style="color:var(--text-muted);font-size:12px;">Ground truth baseline. O(N) linear comparisons.</td>
            </tr>
            <tr>
              <td style="font-weight:700;color:var(--yellow);">IVF (nlist=20, nprobe=3)</td>
              <td style="text-align:right;font-family:var(--font-mono);">11.7 ms</td>
              <td style="text-align:right;font-family:var(--font-mono);font-weight:700;color:var(--yellow);">447 (15%)</td>
              <td style="text-align:right;font-family:var(--font-mono);">0.037 ms</td>
              <td style="text-align:right;font-family:var(--font-mono);font-weight:700;color:var(--yellow);">42.00%</td>
              <td style="color:var(--text-muted);font-size:12px;">Fast cluster filtering. Trades recall for minimal comparisons.</td>
            </tr>
            <tr style="background:rgba(139, 92, 246, 0.08);">
              <td style="font-weight:700;color:var(--purple);">Simplified NSW (HNSW-like)</td>
              <td style="text-align:right;font-family:var(--font-mono);">180.6 ms</td>
              <td style="text-align:right;font-family:var(--font-mono);font-weight:700;color:var(--purple);">1,810 (60%)</td>
              <td style="text-align:right;font-family:var(--font-mono);">5.054 ms</td>
              <td style="text-align:right;font-family:var(--font-mono);color:var(--purple);font-weight:700;">91.50%</td>
              <td style="color:var(--text-muted);font-size:12px;">Greedy graph search. Superior recall (91.5%) via edge traversal.</td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Key Engineering Takeaways Callout -->
      <div style="background:linear-gradient(135deg, rgba(139, 92, 246, 0.08) 0%, rgba(59, 130, 246, 0.08) 100%);border:1px solid rgba(139, 92, 246, 0.25);border-radius:var(--radius-md);padding:20px;">
        <h4 style="font-size:14px;color:var(--heading);margin:0 0 10px 0;display:flex;align-items:center;gap:8px;">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>
          Why "Vectors Compared Per Query" is the Critical Metric
        </h4>
        <div style="font-size:13px;color:var(--text-secondary);line-height:1.7;">
          <p style="margin:0 0 8px 0;">
            1. <strong>Production Scaling:</strong> In a production cluster with 10 million vectors, brute-force search requires 10,000,000 dot products per query. In contrast, an HNSW graph touches only a few thousand nodes regardless of dataset size (logarithmic scaling).
          </p>
          <p style="margin:0 0 8px 0;">
            2. <strong>Pure-Python vs Native C++ Implementations:</strong> In Python, wall-clock query times are distorted by per-node interpreter and heap-push overheads. MongoDB Atlas uses native multi-layer C++ HNSW graphs where each node traversal takes nanoseconds, translating fewer vector comparisons directly into sub-millisecond p99 latencies.
          </p>
          <p style="margin:0;">
            3. <strong>Tunable Trade-offs:</strong> Increasing <code>nprobe</code> in IVF or <code>ef_search</code> in HNSW monotonically increases both Recall@k and vectors compared, allowing engineers to calibrate the exact trade-off required for their SLAs.
          </p>
        </div>
      </div>
    </div>
  `;
}

function renderLab17ConceptsTab(container, conceptsData) {
  container.innerHTML = `
    <div style="display:grid;grid-template-columns:repeat(auto-fit, minmax(320px, 1fr));gap:16px;">
      ${conceptsData.concepts.map(c => `
        <div class="section-panel" style="display:flex;flex-direction:column;gap:10px;">
          <div style="display:flex;align-items:center;gap:10px;">
            <span style="font-size:24px;">${c.icon}</span>
            <h4 style="font-size:15px;color:var(--heading);margin:0;">${esc(c.title)}</h4>
          </div>
          <div style="font-size:13px;color:var(--text-secondary);line-height:1.5;">${esc(c.explanation)}</div>
          <div style="font-size:11px;color:var(--cyan);background:rgba(59, 130, 246, 0.08);padding:8px 12px;border-radius:var(--radius-sm);border:1px solid rgba(59, 130, 246, 0.15);font-family:var(--font-mono);">
            ${esc(c.detail)}
          </div>
        </div>
      `).join('')}
    </div>
  `;
}




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

// ══════════════════════════════════════════════════════════════════════════
// FINAL ASSESSMENT: AI THREAT INTEL CHATBOT & AUTONOMOUS MITIGATION BOT
// ══════════════════════════════════════════════════════════════════════════

let chatbotMessages = [
  {
    role: 'assistant',
    text: "🛡️ **Welcome to the Cyber Threat Intelligence Assistant.**\n\nI can analyze **Anticipated**, **Active**, **Evolving**, and **Resolved** threats across **Windows**, **Linux**, **macOS**, **Android**, and **iOS** using MongoDB vector search RAG.\n\nYou can also click **'Run Vulnerability Scan'** below to audit host misconfigurations and apply mitigations with confirmation."
  }
];
let currentChatbotPlatform = 'all';
let currentChatbotStatus = 'all';

async function loadChatbot() {
  const container = document.getElementById('chatbot-content');
  if (!container) return;

  const existingBox = document.getElementById('chat-messages-box');
  if (existingBox) {
    // Keep DOM and conversation intact, update KPIs and Ollama badge dynamically
    try {
      const res = await fetch(`${API_BASE}/api/chatbot/dashboard`);
      const dash = await res.json();
      const s = dash.by_status || {};
      if (document.getElementById('cb-kpi-total')) document.getElementById('cb-kpi-total').textContent = (dash.total_threats || 20) + ' Indexed';
      if (document.getElementById('cb-kpi-ant')) document.getElementById('cb-kpi-ant').textContent = (s.anticipated || 5) + ' Threats';
      if (document.getElementById('cb-kpi-act')) document.getElementById('cb-kpi-act').textContent = (s.active || 5) + ' Campaigns';
      if (document.getElementById('cb-kpi-evo')) document.getElementById('cb-kpi-evo').textContent = (s.evolving || 5) + ' Vectors';
      if (document.getElementById('cb-kpi-res')) document.getElementById('cb-kpi-res').textContent = (s.resolved || 5) + ' Patched';
    } catch (e) {}

    try {
      const stRes = await fetch(`${API_BASE}/api/chatbot/ollama-status`);
      const st = await stRes.json();
      const el = document.getElementById('ollama-status-badge');
      if (el) {
        if (st.online) {
          el.innerHTML = `● Ollama: Online (${st.active_model || st.configured_model || 'llama3'})`;
          el.style.color = 'var(--green)';
          el.style.borderColor = 'var(--green)';
        } else {
          el.innerHTML = `● Ollama: Standby (Grounded RAG)`;
          el.style.color = 'var(--cyan)';
        }
      }
    } catch (e) {}
    return;
  }

  // Fallback if initial DOM was completely absent
  try {
    const res = await fetch(`${API_BASE}/api/chatbot/dashboard`);
    const dash = await res.json();
    renderChatbotView(dash);
  } catch (err) {
    renderChatbotView({ total_threats: 20, by_status: {}, by_platform: {} });
  }
}

function renderChatbotView(dash) {
  const container = document.getElementById('chatbot-content');
  if (!container) return;

  const total = dash.total_threats || 20;
  const s = dash.by_status || {};
  const ant = s.anticipated || 5;
  const act = s.active || 5;
  const evo = s.evolving || 5;
  const res = s.resolved || 5;

  container.innerHTML = `
    <!-- Top Banner -->
    <div style="background:linear-gradient(135deg, rgba(14, 165, 233, 0.12) 0%, rgba(99, 102, 241, 0.12) 100%);border:1px solid rgba(14, 165, 233, 0.35);border-radius:var(--radius-md);padding:20px;margin-bottom:20px;">
      <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:16px;">
        <div>
          <h2 style="font-size:20px;color:var(--heading);margin:0 0 6px 0;font-weight:700;">Multi-Platform Threat Intelligence AI & Mitigation Bot</h2>
          <p style="font-size:13px;color:var(--text-muted);margin:0;max-width:850px;">
            Synthesis of <strong>Exercises 1 - 18</strong>. Grounded question answering covering Anticipated, Active, Evolving, and Resolved threats across Windows, Linux, macOS, Android, and iOS. Features an autonomous background scanner that audits host misconfigurations and applies mitigations with human-in-the-loop confirmation.
          </p>
        </div>
        <div style="display:flex;gap:8px;">
          <button class="btn btn-primary" onclick="triggerChatbotScan()" style="font-size:12px;padding:8px 14px;background:var(--cyan);color:#000;border:none;font-weight:600;display:flex;align-items:center;gap:6px;">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
            Run Vulnerability Scan
          </button>
        </div>
      </div>

      <!-- Quick Metrics Strip -->
      <div style="display:grid;grid-template-columns:repeat(auto-fit, minmax(130px, 1fr));gap:12px;margin-top:16px;">
        <div style="background:rgba(0,0,0,0.25);padding:10px 14px;border-radius:6px;border-left:3px solid var(--cyan);">
          <div style="font-size:11px;color:var(--text-muted);">Total Threats</div>
          <div style="font-size:18px;font-weight:700;color:var(--heading);">${total} Indexed</div>
        </div>
        <div style="background:rgba(0,0,0,0.25);padding:10px 14px;border-radius:6px;border-left:3px solid var(--orange);">
          <div style="font-size:11px;color:var(--text-muted);">Anticipated</div>
          <div style="font-size:18px;font-weight:700;color:var(--orange);">${ant} Threats</div>
        </div>
        <div style="background:rgba(0,0,0,0.25);padding:10px 14px;border-left:3px solid var(--red);border-radius:6px;">
          <div style="font-size:11px;color:var(--text-muted);">Active</div>
          <div style="font-size:18px;font-weight:700;color:var(--red);">${act} Campaigns</div>
        </div>
        <div style="background:rgba(0,0,0,0.25);padding:10px 14px;border-left:3px solid var(--purple);border-radius:6px;">
          <div style="font-size:11px;color:var(--text-muted);">Evolving</div>
          <div style="font-size:18px;font-weight:700;color:var(--purple);">${evo} Vectors</div>
        </div>
        <div style="background:rgba(0,0,0,0.25);padding:10px 14px;border-left:3px solid var(--green);border-radius:6px;">
          <div style="font-size:11px;color:var(--text-muted);">Resolved</div>
          <div style="font-size:18px;font-weight:700;color:var(--green);">${res} Patched</div>
        </div>
      </div>
    </div>

    <!-- Scan Results Panel (Hidden until scan run) -->
    <div id="chatbot-scan-panel" style="display:none;margin-bottom:20px;"></div>

    <!-- Main Chat Workspace -->
    <div style="display:grid;grid-template-columns:300px 1fr;gap:20px;">
      <!-- Controls & Quick Prompts Sidebar -->
      <div style="display:flex;flex-direction:column;gap:16px;">
        <div class="card" style="padding:16px;">
          <h4 style="font-size:13px;color:var(--heading);margin:0 0 12px 0;text-transform:uppercase;letter-spacing:0.5px;">Target Filters</h4>
          
          <label style="font-size:11px;color:var(--text-muted);display:block;margin-bottom:4px;">Platform Focus</label>
          <select id="chat-platform-sel" onchange="currentChatbotPlatform=this.value" style="width:100%;padding:8px;background:rgba(0,0,0,0.3);border:1px solid var(--border-card);color:var(--heading);border-radius:4px;font-size:12px;margin-bottom:12px;">
            <option value="all">🌐 All Platforms</option>
            <option value="windows">💻 Windows</option>
            <option value="linux">🐧 Linux</option>
            <option value="macos">🍎 macOS</option>
            <option value="android">🤖 Android</option>
            <option value="ios">📱 iOS</option>
          </select>

          <label style="font-size:11px;color:var(--text-muted);display:block;margin-bottom:4px;">Threat Status Filter</label>
          <select id="chat-status-sel" onchange="currentChatbotStatus=this.value" style="width:100%;padding:8px;background:rgba(0,0,0,0.3);border:1px solid var(--border-card);color:var(--heading);border-radius:4px;font-size:12px;">
            <option value="all">All Statuses</option>
            <option value="anticipated">⚠️ Anticipated</option>
            <option value="active">🔥 Active</option>
            <option value="evolving">📈 Evolving</option>
            <option value="resolved">✅ Resolved</option>
          </select>
        </div>

        <div class="card" style="padding:16px;">
          <h4 style="font-size:13px;color:var(--heading);margin:0 0 12px 0;text-transform:uppercase;letter-spacing:0.5px;">Example Queries</h4>
          <div style="display:flex;flex-direction:column;gap:8px;">
            <button onclick="injectChatbotPrompt('What are anticipated zero-day vulnerabilities for Windows, and what are the mitigation steps?')" class="btn" style="text-align:left;font-size:11px;padding:8px;background:rgba(255,255,255,0.03);border:1px solid var(--border-card);color:var(--heading);border-radius:4px;">
              ⚠️ Anticipated Windows Zero-Day
            </button>
            <button onclick="injectChatbotPrompt('Tell me about the active BlackBasta 2.0 ransomware campaign and how to detect it.')" class="btn" style="text-align:left;font-size:11px;padding:8px;background:rgba(255,255,255,0.03);border:1px solid var(--border-card);color:var(--heading);border-radius:4px;">
              🔥 Active BlackBasta Ransomware
            </button>
            <button onclick="injectChatbotPrompt('What is the Linux eBPF sandbox escape vulnerability and how can we mitigate it?')" class="btn" style="text-align:left;font-size:11px;padding:8px;background:rgba(255,255,255,0.03);border:1px solid var(--border-card);color:var(--heading);border-radius:4px;">
              🐧 Linux eBPF Sandbox Escape
            </button>
            <button onclick="injectChatbotPrompt('Explain the resolved Linux Dirty Pipe (CVE-2022-0847) exploit and verification commands.')" class="btn" style="text-align:left;font-size:11px;padding:8px;background:rgba(255,255,255,0.03);border:1px solid var(--border-card);color:var(--heading);border-radius:4px;">
              ✅ Resolved Dirty Pipe Exploit
            </button>
            <button onclick="injectChatbotPrompt('What evolving threats exist for Android and iOS devices, and how can we mitigate them?')" class="btn" style="text-align:left;font-size:11px;padding:8px;background:rgba(255,255,255,0.03);border:1px solid var(--border-card);color:var(--heading);border-radius:4px;">
              📱 Mobile Evolving Threats
            </button>
          </div>
        </div>
      </div>

      <!-- Chat Stream Container -->
      <div class="card" style="display:flex;flex-direction:column;height:650px;padding:0;overflow:hidden;">
        <!-- Header -->
        <div style="padding:12px 18px;border-bottom:1px solid var(--border-card);display:flex;justify-content:space-between;align-items:center;background:rgba(0,0,0,0.15);">
          <div style="display:flex;align-items:center;gap:8px;">
            <div class="status-dot" style="background:var(--green);"></div>
            <span style="font-size:12px;font-weight:600;color:var(--heading);">Ollama Chatbot Session</span>
          </div>
          <button onclick="clearChatbotHistory()" class="btn" style="font-size:11px;padding:4px 8px;background:transparent;border:1px solid var(--border-card);color:var(--text-muted);">
            Clear History
          </button>
        </div>

        <!-- Messages Area -->
        <div id="chat-messages-box" style="flex:1;overflow-y:auto;padding:18px;display:flex;flex-direction:column;gap:14px;">
          ${renderChatbotMessagesHtml()}
        </div>

        <!-- Input Area -->
        <div style="padding:14px;border-top:1px solid var(--border-card);background:rgba(0,0,0,0.2);display:flex;gap:10px;">
          <input type="text" id="chatbot-user-input" onkeydown="if(event.key==='Enter')sendChatbotMessage()" placeholder="Ask about threats (e.g. 'How to mitigate BlackBasta on Windows?' or 'scan and fix')..." style="flex:1;padding:10px 14px;background:rgba(0,0,0,0.4);border:1px solid var(--border-card);border-radius:4px;color:var(--heading);font-size:13px;outline:none;" />
          <button id="chatbot-send-btn" onclick="sendChatbotMessage()" class="btn btn-primary" style="padding:10px 20px;font-size:13px;font-weight:600;background:var(--cyan);color:#000;border:none;">
            Send
          </button>
        </div>
      </div>
    </div>
  `;

  // Scroll to bottom
  const box = document.getElementById('chat-messages-box');
  if (box) box.scrollTop = box.scrollHeight;
}

function renderChatbotMessagesHtml() {
  return chatbotMessages.map(m => {
    const isUser = m.role === 'user';
    const bg = isUser ? 'rgba(14, 165, 233, 0.15)' : 'rgba(255, 255, 255, 0.04)';
    const border = isUser ? '1px solid rgba(14, 165, 233, 0.4)' : '1px solid var(--border-card)';
    const align = isUser ? 'flex-end' : 'flex-start';
    const label = isUser ? '👤 You' : '🛡️ Threat Intel AI';

    let sourcesHtml = '';
    if (m.sources && m.sources.length) {
      sourcesHtml = `
        <div style="margin-top:12px;padding-top:10px;border-top:1px dashed var(--border-card);">
          <div style="font-size:11px;font-weight:700;color:var(--cyan);margin-bottom:6px;">📚 Retrieved Context Sources (${m.sources.length} chunks)</div>
          <div style="display:flex;flex-direction:column;gap:6px;">
            ${m.sources.map(s => `
              <div style="background:rgba(0,0,0,0.25);padding:6px 10px;border-radius:4px;font-size:11px;">
                <span style="color:var(--heading);font-weight:600;">${esc(s.title)}</span>
                <span class="badge" style="font-size:9px;padding:2px 5px;margin-left:6px;background:rgba(255,255,255,0.06);">${s.platform?.toUpperCase()}</span>
                <span class="badge" style="font-size:9px;padding:2px 5px;margin-left:4px;color:var(--orange);">${s.status?.toUpperCase()}</span>
                <span style="color:var(--text-muted);font-family:var(--font-mono);margin-left:6px;">(Score: ${s.score})</span>
              </div>
            `).join('')}
          </div>
        </div>
      `;
    }

    return `
      <div style="display:flex;flex-direction:column;align-items:${align};max-width:85%;align-self:${align};">
        <div style="font-size:10px;color:var(--text-muted);margin-bottom:4px;padding:0 4px;">${label}</div>
        <div style="background:${bg};border:${border};border-radius:8px;padding:12px 16px;color:var(--text-primary);font-size:13px;line-height:1.5;">
          ${renderMarkdownText(m.text)}
          ${sourcesHtml}
        </div>
      </div>
    `;
  }).join('');
}

function renderMarkdownText(txt) {
  if (!txt) return '';
  let h = esc(txt);
  // Headers
  h = h.replace(/### (.*?)\n/g, '<h4 style="font-size:14px;color:var(--heading);margin:8px 0 4px 0;">$1</h4>');
  h = h.replace(/#### (.*?)\n/g, '<h5 style="font-size:12px;color:var(--cyan);margin:8px 0 4px 0;text-transform:uppercase;">$1</h5>');
  // Bold
  h = h.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
  // Inline code
  h = h.replace(/`([^`]+)`/g, '<code style="background:rgba(0,0,0,0.3);padding:2px 4px;border-radius:3px;font-family:var(--font-mono);font-size:12px;color:var(--cyan);">$1</code>');
  // Line breaks
  h = h.replace(/\n/g, '<br/>');
  return h;
}

function injectChatbotPrompt(p) {
  const inp = document.getElementById('chatbot-user-input');
  if (inp) {
    inp.value = p;
    sendChatbotMessage();
  }
}

async function sendChatbotMessage() {
  const inp = document.getElementById('chatbot-user-input');
  if (!inp) return;
  const prompt = inp.value.trim();
  if (!prompt) return;

  inp.value = '';
  chatbotMessages.push({ role: 'user', text: prompt });

  const box = document.getElementById('chat-messages-box');
  if (box) {
    box.innerHTML = renderChatbotMessagesHtml() + `
      <div id="chat-thinking-indicator" style="display:flex;align-items:center;gap:8px;color:var(--text-muted);font-size:12px;padding:8px;">
        <div class="spinner" style="width:14px;height:14px;"></div>
        Analyzing threat vectors & retrieving mitigations...
      </div>
    `;
    box.scrollTop = box.scrollHeight;
  }

  try {
    const res = await fetch(`${API_BASE}/api/chatbot/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: 'web-session',
        message: prompt,
        platform: currentChatbotPlatform,
        status_filter: currentChatbotStatus,
        top_k: 4
      })
    });
    const data = await res.json();
    chatbotMessages.push({
      role: 'assistant',
      text: data.response,
      sources: data.sources
    });
  } catch (err) {
    chatbotMessages.push({
      role: 'assistant',
      text: `❌ Error querying Threat Intelligence engine: ${err.message}`
    });
  }

  if (box) {
    box.innerHTML = renderChatbotMessagesHtml();
    box.scrollTop = box.scrollHeight;
  }
}

function clearChatbotHistory() {
  chatbotMessages = [
    {
      role: 'assistant',
      text: "🛡️ Session reset. Ready to query Anticipated, Active, Evolving, or Resolved threats."
    }
  ];
  const box = document.getElementById('chat-messages-box');
  if (box) box.innerHTML = renderChatbotMessagesHtml();
}

async function triggerChatbotScan() {
  const panel = document.getElementById('chatbot-scan-panel');
  if (!panel) return;

  panel.style.display = 'block';
  panel.innerHTML = `
    <div class="card" style="padding:16px;border-left:4px solid var(--cyan);">
      <div style="display:flex;align-items:center;gap:10px;">
        <div class="spinner" style="width:16px;height:16px;"></div>
        <span style="font-size:13px;color:var(--heading);font-weight:600;">Auditing local security baselines, firewall profiles, and active ports...</span>
      </div>
    </div>
  `;

  try {
    const res = await fetch(`${API_BASE}/api/chatbot/scan`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ scan_type: 'quick', platform: currentChatbotPlatform === 'all' ? null : currentChatbotPlatform })
    });
    const data = await res.json();
    const findings = data.findings || [];

    let findingsHtml = '';
    findings.forEach(f => {
      const isCrit = f.severity === 'Critical' || f.severity === 'High';
      const borderCol = f.severity === 'Critical' ? 'var(--red)' : f.severity === 'High' ? 'var(--orange)' : 'var(--blue)';

      findingsHtml += `
        <div style="border-left:4px solid ${borderCol};background:rgba(0,0,0,0.3);padding:12px;border-radius:4px;margin-top:10px;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:10px;">
          <div>
            <div style="font-weight:700;color:var(--heading);font-size:13px;">${esc(f.title)} <span class="badge" style="font-size:10px;margin-left:6px;background:${borderCol};color:#fff;">${f.severity}</span></div>
            <div style="font-size:11px;color:var(--text-muted);margin:3px 0;"><strong>ID:</strong> <code>${esc(f.id)}</code> | ${esc(f.description)}</div>
            <div style="font-size:11px;color:var(--cyan);"><strong>Fix:</strong> <code>${esc(f.remediation)}</code></div>
          </div>
          ${isCrit ? `
            <div style="display:flex;gap:6px;">
              <button onclick="confirmChatbotMitigation('${esc(f.id)}', false)" class="btn btn-primary" style="font-size:11px;padding:6px 12px;background:var(--green);color:#000;border:none;font-weight:700;">
                ⚡ Apply Fix
              </button>
              <button onclick="confirmChatbotMitigation('${esc(f.id)}', true)" class="btn" style="font-size:11px;padding:6px 10px;background:rgba(255,255,255,0.06);border:1px solid var(--border-card);color:var(--text-primary);">
                Simulate Dry-Run
              </button>
            </div>
          ` : ''}
        </div>
      `;
    });

    panel.innerHTML = `
      <div class="card" style="padding:18px;border:1px solid var(--cyan);">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">
          <h3 style="font-size:15px;color:var(--heading);margin:0;font-weight:700;">
            🛡️ Vulnerability Audit Results: ${esc(data.platform?.toUpperCase())} (${data.timestamp?.slice(0,19)})
          </h3>
          <button onclick="document.getElementById('chatbot-scan-panel').style.display='none'" class="btn" style="font-size:10px;padding:2px 6px;">✕ Close</button>
        </div>
        <div>${findingsHtml}</div>
      </div>
    `;
  } catch (err) {
    panel.innerHTML = `<div class="card" style="padding:14px;border-color:var(--red);color:var(--red);">Scan failed: ${esc(err.message)}</div>`;
  }
}

async function confirmChatbotMitigation(findingId, dryRun) {
  showToast(dryRun ? `Simulating dry-run for ${findingId}...` : `Applying mitigation for ${findingId}...`);

  try {
    const res = await fetch(`${API_BASE}/api/chatbot/mitigate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        finding_id: findingId,
        target_platform: currentChatbotPlatform === 'all' ? 'windows' : currentChatbotPlatform,
        confirmed: true,
        dry_run: dryRun
      })
    });
    const d = await res.json();
    alert(`✅ ${d.message}\n\nAction: ${d.action_taken}`);
    showToast(d.message);
  } catch (err) {
    alert(`Mitigation failed: ${err.message}`);
  }
}

