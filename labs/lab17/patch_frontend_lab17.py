import os

app_js_path = r"c:\Users\aryap\OneDrive\Desktop\lab 7\frontend\js\app.js"

with open(app_js_path, "r", encoding="utf-8") as f:
    code = f.read()

lab17_js = '''

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
'''

if "// LAB 17: RAG PIPELINE" not in code:
    with open(app_js_path, "a", encoding="utf-8") as f:
        f.write("\n" + lab17_js + "\n")
    print("Lab 17 JavaScript appended successfully.")
else:
    print("Lab 17 JavaScript already present.")
