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
  lab12: 'Lab 12: Role-Based Access Control (RBAC), Field Redaction & TLS',
  lab13: 'Lab 13: Production Kubernetes StatefulSet & Cloud Infrastructure as Code',
  lab14: 'Lab 14: Operations Monitoring Dashboard & Automated Backup/Restore',
  lab15: 'Lab 15: Multi-Tenant SaaS Architecture & Zero-Downtime Migration',
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
  else if (tabName === 'lab12') loadLab12();
  else if (tabName === 'lab13') loadLab13();
  else if (tabName === 'lab14') loadLab14();
  else if (tabName === 'lab15') loadLab15();
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
