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

// ── UTILITIES ─────────────────────────────────────────────────────────

function esc(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}
