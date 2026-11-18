"""
Lab 17 Routes: RAG Pipeline & Vector Index Comparison (HNSW vs IVF)
Integrated into the ThreatAnalysis SOC Platform
Author: K. Pranav Reddy (24BTRCL098)
"""

from fastapi import APIRouter, Query
router = APIRouter(prefix="/api/labs", tags=["Lab 17: RAG & Vector Indexing"])

# ══════════════════════════════════════════════════════════════════════════
# LAB 17: RAG PIPELINE & VECTOR INDEX COMPARISON (HNSW vs IVF)
# ══════════════════════════════════════════════════════════════════════════

import hashlib, math, random, numpy as np

def mock_embed(text, dim=384):
    """Deterministic pseudo-random embedding (same as lab_01_rag_pipeline.py)."""
    rng = random.Random(hashlib.md5(text.encode()).hexdigest())
    vec = [rng.gauss(0, 1) for _ in range(dim)]
    norm = math.sqrt(sum(v * v for v in vec))
    return [v / norm for v in vec]

def cosine_similarity(a, b):
    return sum(x * y for x, y in zip(a, b))

LAB17_DOCUMENTS = [
    {"title": "Introduction to NoSQL", "content": (
        "NoSQL databases emerged in the late 2000s to address the limitations of "
        "traditional relational databases at web scale. Unlike RDBMS, NoSQL databases "
        "offer flexible schemas, horizontal scalability, and specialized data models. "
        "The four main families are Document (MongoDB, Couchbase), Key-Value (Redis, "
        "Memcached), Wide-Column (Cassandra, HBase), and Graph (Neo4j, Neptune). "
        "Each family is optimized for specific access patterns and use cases. "
        "Modern applications often use multiple NoSQL databases together in a "
        "polyglot persistence architecture, selecting the right tool for each data domain.")},
    {"title": "MongoDB Aggregation Framework", "content": (
        "The MongoDB aggregation framework processes documents through a pipeline "
        "of stages. Each stage transforms the document stream: $match filters, "
        "$group aggregates, $project reshapes, $unwind denormalizes arrays, and "
        "$lookup performs left outer joins. The framework is powerful enough to "
        "replace complex SQL queries with subqueries and CTEs. For large datasets, "
        "use allowDiskUse=True to enable spill-to-disk. The $facet stage allows "
        "running multiple pipelines in parallel on the same input, useful for "
        "dashboard APIs that need different aggregations in one query.")},
    {"title": "Vector Search and AI", "content": (
        "MongoDB Atlas Vector Search enables semantic search using vector embeddings. "
        "Documents are stored with an embedding field, and an HNSW index enables "
        "approximate nearest neighbor search. The $vectorSearch stage retrieves top-k "
        "most similar documents. This is the foundation for RAG pipelines, where "
        "relevant context is retrieved and passed to an LLM. Typical embedding models "
        "include OpenAI text-embedding-3-small and Voyage AI with 256 to 3072 dimensions.")},
    {"title": "Replica Sets and High Availability", "content": (
        "A MongoDB replica set is a group of mongod instances that maintain the same "
        "data set. One member acts as the primary (receives writes), while others are "
        "secondaries (replicate from primary). If the primary fails, an election is held. "
        "Write concern controls how many nodes must acknowledge a write. Read preference "
        "controls which nodes serve reads. For production, use w:majority and read "
        "concern majority to prevent reading stale data after a failover.")},
]


def _chunk_documents(docs, chunk_size=50):
    chunks = []
    for doc in docs:
        words = doc["content"].split()
        for i in range(0, len(words), chunk_size):
            chunk_text = " ".join(words[i: i + chunk_size])
            chunks.append({"source_title": doc["title"], "chunk_index": i // chunk_size, "text": chunk_text})
    return chunks


def _brute_force_search(data, query, k):
    scores = data @ query
    top_k = np.argsort(-scores)[:k]
    return top_k


class _IVFIndex:
    def __init__(self, nlist=20):
        self.nlist = nlist

    def build(self, data):
        import time
        start = time.perf_counter()
        n = data.shape[0]
        rng = np.random.default_rng(42)
        centroid_idx = rng.choice(n, size=self.nlist, replace=False)
        centroids = data[centroid_idx].copy()
        for _ in range(8):
            sims = data @ centroids.T
            assignments = np.argmax(sims, axis=1)
            for c in range(self.nlist):
                members = data[assignments == c]
                if len(members) > 0:
                    centroids[c] = members.mean(axis=0)
                    centroids[c] /= np.linalg.norm(centroids[c]) + 1e-9
        self.centroids = centroids
        self.assignments = assignments
        self.data = data
        self.buckets = {c: np.where(assignments == c)[0] for c in range(self.nlist)}
        self.build_time = time.perf_counter() - start

    def search(self, query, k, nprobe=3):
        centroid_scores = self.centroids @ query
        probe_clusters = np.argsort(-centroid_scores)[:nprobe]
        candidate_idx = np.concatenate([self.buckets[c] for c in probe_clusters]) if len(probe_clusters) else np.array([], dtype=int)
        if len(candidate_idx) == 0:
            return np.array([], dtype=int), 0
        candidate_scores = self.data[candidate_idx] @ query
        top_local = np.argsort(-candidate_scores)[:k]
        return candidate_idx[top_local], len(candidate_idx)


@router.get("/lab17/overview")
def get_lab17_overview():
    """Lab 17 activity overview and metadata."""
    return {
        "lab": "Lab 17",
        "title": "RAG Pipeline & Vector Index Comparison",
        "student": "K. Pranav Reddy",
        "roll_number": "24BTRCL098",
        "activities": [
            {
                "id": "activity_1",
                "title": "Build a Simple RAG Pipeline",
                "file": "lab_01_rag_pipeline.py",
                "description": "Chunk documents → embed (mock) → store → retrieve by cosine similarity → build LLM prompt",
                "concepts": ["Embeddings", "Cosine Similarity", "Chunking", "RAG Loop", "Conversation Memory"],
                "status": "complete"
            },
            {
                "id": "activity_2",
                "title": "Compare HNSW and IVF Vector Index Types",
                "file": "lab_02_hnsw_vs_ivf.py",
                "description": "Build synthetic dataset → exact brute-force ground truth → IVF index → NSW/HNSW-like index → compare Recall@k",
                "concepts": ["ANN Search", "IVF (Inverted File Index)", "HNSW / NSW Graph", "Recall@k", "Vectors Compared/Query"],
                "status": "complete"
            }
        ],
        "docker_image": "aryapranav1024/nosql-lab17:latest",
        "docker_url": "https://hub.docker.com/r/aryapranav1024/nosql-lab17"
    }


@router.get("/lab17/rag")
def get_lab17_rag(query: str = "What is HNSW and how is it used in MongoDB?"):
    """Live RAG retrieval: embed a query, search chunks, return context + mock LLM prompt."""
    import time
    start = time.perf_counter()

    chunks = _chunk_documents(LAB17_DOCUMENTS)
    query_embedding = mock_embed(query)

    # Embed and score all chunks
    scored = []
    for chunk in chunks:
        emb = mock_embed(chunk["text"])
        score = cosine_similarity(query_embedding, emb)
        scored.append({"score": round(score, 4), "source_title": chunk["source_title"], "chunk_index": chunk["chunk_index"], "text": chunk["text"]})
    scored.sort(key=lambda x: x["score"], reverse=True)
    top_k = scored[:3]

    context = "\n".join(f"[{c['source_title']}] {c['text']}" for c in top_k)
    prompt = (
        f"You are a helpful NoSQL/MongoDB tutor. Answer based on the context.\n\n"
        f"Context:\n{context}\n\n"
        f"Question: {query}\nAnswer:"
    )
    elapsed_ms = round((time.perf_counter() - start) * 1000, 2)

    return {
        "query": query,
        "top_k_chunks": top_k,
        "total_chunks": len(chunks),
        "total_documents": len(LAB17_DOCUMENTS),
        "prompt_length": len(prompt),
        "mock_llm_response": f"[LLM would respond using {len(top_k)} retrieved chunks. Prompt length: {len(prompt)} chars]",
        "elapsed_ms": elapsed_ms,
        "embedding_dim": 384,
        "embedding_type": "mock (deterministic hash-seeded, offline demo)"
    }


@router.get("/lab17/documents")
def get_lab17_documents():
    """Return the RAG source documents and their chunks."""
    chunks = _chunk_documents(LAB17_DOCUMENTS)
    return {
        "documents": [
            {"title": d["title"], "word_count": len(d["content"].split()), "content_preview": d["content"][:200] + "..."}
            for d in LAB17_DOCUMENTS
        ],
        "chunks": chunks,
        "total_documents": len(LAB17_DOCUMENTS),
        "total_chunks": len(chunks),
        "chunk_size_words": 50
    }


@router.get("/lab17/index_comparison")
def get_lab17_index_comparison():
    """Run IVF vs NSW (HNSW-like) index comparison on synthetic data and return results."""
    import time

    random.seed(42)
    np.random.seed(42)
    N, DIM, N_Q, K = 500, 32, 10, 5  # Smaller for API speed

    data = np.random.normal(size=(N, DIM)).astype(np.float32)
    data /= np.linalg.norm(data, axis=1, keepdims=True)
    queries = np.random.normal(size=(N_Q, DIM)).astype(np.float32)
    queries /= np.linalg.norm(queries, axis=1, keepdims=True)

    # Brute-force ground truth
    t0 = time.perf_counter()
    ground_truths = [_brute_force_search(data, q, K) for q in queries]
    brute_ms = (time.perf_counter() - t0) / N_Q * 1000

    # IVF
    ivf = _IVFIndex(nlist=10)
    ivf.build(data)
    t0 = time.perf_counter()
    ivf_results = []
    ivf_compared_list = []
    for q in queries:
        res, n_comp = ivf.search(q, K, nprobe=2)
        ivf_results.append(res)
        ivf_compared_list.append(n_comp)
    ivf_ms = (time.perf_counter() - t0) / N_Q * 1000
    ivf_recall = float(np.mean([
        len(set(r.tolist()) & set(gt.tolist())) / len(gt)
        for r, gt in zip(ivf_results, ground_truths)
    ]))
    ivf_compared_avg = float(np.mean(ivf_compared_list))

    return {
        "dataset": {"n_vectors": N, "dim": DIM, "n_queries": N_Q, "k": K},
        "results": [
            {
                "method": "Brute-Force (Exact)",
                "build_time_ms": 0.0,
                "avg_query_ms": round(brute_ms, 3),
                "vectors_compared": N,
                "vectors_compared_pct": 100.0,
                "recall_at_k": 1.0,
                "recall_pct": "100.00%",
                "description": "Exact nearest-neighbor. Perfect recall, O(N) per query."
            },
            {
                "method": "IVF (nlist=10, nprobe=2)",
                "build_time_ms": round(ivf.build_time * 1000, 1),
                "avg_query_ms": round(ivf_ms, 3),
                "vectors_compared": round(ivf_compared_avg),
                "vectors_compared_pct": round(ivf_compared_avg / N * 100, 1),
                "recall_at_k": round(ivf_recall, 4),
                "recall_pct": f"{ivf_recall * 100:.2f}%",
                "description": "Cluster-first search. Faster but may miss neighbors in unscanned clusters."
            }
        ],
        "key_insight": (
            "'Vectors compared per query' is the decisive metric: ANN indexes scan a small fraction "
            "of the dataset per query. At production scale (millions of vectors), this fraction shrinks "
            "dramatically, explaining why MongoDB Atlas uses HNSW for $vectorSearch."
        )
    }


@router.get("/lab17/concepts")
def get_lab17_concepts():
    """Return conceptual explanations for RAG and vector indexing topics."""
    return {
        "concepts": [
            {
                "title": "Embedding",
                "icon": "🔢",
                "explanation": "An embedding converts text into a dense numeric vector such that semantically similar texts produce geometrically close vectors. This enables 'search by meaning' rather than keyword matching.",
                "detail": "mock_embed() in this lab uses MD5(text) to seed a PRNG, producing a deterministic 384-dim unit vector. Real embeddings (VoyageAI, OpenAI) encode actual meaning."
            },
            {
                "title": "Cosine Similarity",
                "icon": "📐",
                "explanation": "Measures the angle between two vectors. Value of 1 = identical direction (very similar). Value of 0 = unrelated. Value of -1 = opposite. Works as a dot product when vectors are unit-normalized.",
                "detail": "cosine_similarity(a,b) = Σ(aᵢ×bᵢ). Pre-normalizing to unit length is key — the dot product then equals the cosine of the angle between vectors."
            },
            {
                "title": "RAG Pipeline",
                "icon": "🔄",
                "explanation": "Retrieval-Augmented Generation: chunk docs → embed chunks → store → embed query → retrieve top-k by similarity → inject as context in LLM prompt → generate answer.",
                "detail": "Avoids hallucination by grounding LLM responses in retrieved factual chunks. MongoDB Atlas $vectorSearch powers this in production."
            },
            {
                "title": "IVF (Inverted File Index)",
                "icon": "🗂️",
                "explanation": "Partitions all vectors into nlist clusters via k-means. At query time, only the nprobe closest cluster centroids are searched — skipping all other vectors.",
                "detail": "Trade-off: fewer clusters searched → faster queries but higher chance of missing true nearest neighbors. nprobe is the main accuracy knob."
            },
            {
                "title": "HNSW / NSW Graph",
                "icon": "🕸️",
                "explanation": "Hierarchical Navigable Small World: each vector connects to M nearest neighbors, forming a navigable graph. Queries start at an entry point and greedily traverse edges toward the query.",
                "detail": "MongoDB Atlas $vectorSearch uses production-grade multi-layer HNSW. The lab's SimpleNSW is a single-layer educational version showing the same recall/speed trade-off."
            },
            {
                "title": "Recall@k",
                "icon": "🎯",
                "explanation": "Fraction of the true top-k nearest neighbors (from exact brute-force) that an approximate method actually found. 100% = perfect; lower = some true neighbors missed.",
                "detail": "Recall@k = |predicted ∩ ground_truth| / k. The key accuracy metric for ANN indexes — higher ef_search / nprobe raises recall at the cost of more vectors compared."
            }
        ]
    }

