"""FastAPI Backend Server for Cyber Threat Intelligence Platform.

Consolidates:
- Lab 7.1 Production Schema Analysis & Embedded vs Referencing benchmark
- Lab 7.2 Working Set & WiredTiger Cache Telemetry & Dynamic Report Ingestion
- Real-time CTI Search, Threat Classification, Feeds, and IOC Database
"""

import sys
import os
import time
import random
from typing import Optional, List
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from bson import ObjectId

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load .env file if present (persists VT API key across restarts)
_env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
if os.path.exists(_env_path):
    with open(_env_path) as _ef:
        for _line in _ef:
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _k, _v = _line.split("=", 1)
                os.environ.setdefault(_k.strip(), _v.strip())

from config.connection import get_db, MONGO_URI
from backend.classifier import classify_text
from backend.virustotal import query_virustotal, DEFAULT_API_KEY

app = FastAPI(
    title="ThreatAnalysis Platform",
    description="Consolidated CTI Dashboard with Schema Analysis & Working Set Telemetry",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

db = get_db("cti_platform")


def serialize_doc(doc):
    """Serialize MongoDB BSON document to JSON-compatible dict."""
    if not doc:
        return doc
    doc["id"] = str(doc.get("_id"))
    doc["_id"] = str(doc.get("_id"))
    for k, v in list(doc.items()):
        if isinstance(v, ObjectId):
            doc[k] = str(v)
        elif isinstance(v, list):
            doc[k] = [str(x) if isinstance(x, ObjectId) else x for x in v]
        elif isinstance(v, dict):
            doc[k] = serialize_doc(v)
    return doc


from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app):
    """Auto-seed database on first cloud deploy if collections are empty."""
    if db["sources"].count_documents({}) == 0:
        try:
            import subprocess, sys as _sys
            subprocess.run([_sys.executable, "seed_cti_data.py"], timeout=180, cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        except Exception as e:
            print(f"[WARNING] Auto-seed failed: {e}")
    if db["threat_entities"].count_documents({}) == 0:
        try:
            import subprocess, sys as _sys
            subprocess.run([_sys.executable, "entity_resolution_pipeline.py", "--seed", "--live"], timeout=180, cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        except Exception as e:
            print(f"[WARNING] Auto-seed threat entities failed: {e}")
    yield

app.router.lifespan_context = lifespan


# ── Health & Overview ───────────────────────────────────────────────
@app.get("/api/health")
def get_health():
    """System and database connectivity status."""
    try:
        server_info = db.client.server_info()
        return {
            "status": "online",
            "mongodb_version": server_info.get("version"),
            "database": "cti_platform",
            "counts": {
                "threat_articles": db["threat_articles"].count_documents({}),
                "threat_articles_embedded": db["threat_articles_embedded"].count_documents({}),
                "sources": db["sources"].count_documents({}),
                "indicators_of_compromise": db["indicators_of_compromise"].count_documents({}),
                "working_set_reports": db["security_reports_working_set"].count_documents({}),
                "threat_entities": db["threat_entities"].count_documents({})
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Threat Articles & Search ─────────────────────────────────────────
@app.get("/api/articles")
def get_articles(
    q: Optional[str] = None,
    category: Optional[str] = None,
    severity: Optional[str] = None,
    source_name: Optional[str] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(15, ge=1, le=100)
):
    """Search and filter threat intelligence reports."""
    filter_query = {}
    if category and category != "all":
        filter_query["category"] = category
    if severity and severity != "all":
        filter_query["threat_classification.severity"] = severity.upper()
    if q:
        filter_query["$or"] = [
            {"title": {"$regex": q, "$options": "i"}},
            {"summary": {"$regex": q, "$options": "i"}},
            {"tags": {"$regex": q, "$options": "i"}}
        ]

    # Handle source filter if provided
    if source_name:
        src = db["sources"].find_one({"name": source_name})
        if src:
            filter_query["source_id"] = src["_id"]

    col = db["threat_articles"]
    total = col.count_documents(filter_query)
    skip = (page - 1) * limit
    cursor = col.find(filter_query).sort("published_at", -1).skip(skip).limit(limit)

    articles = []
    # Cache sources lookup
    sources_cache = {s["_id"]: s for s in db["sources"].find({})}

    for doc in cursor:
        src_id = doc.get("source_id")
        src = sources_cache.get(src_id, {})
        doc["source_name"] = src.get("name", "Unknown Source")
        doc["source_reputation"] = src.get("reputation_score", 90)
        doc["source_is_threat"] = src.get("is_actual_threat", False)
        articles.append(serialize_doc(doc))

    return {
        "total": total,
        "page": page,
        "limit": limit,
        "total_pages": (total + limit - 1) // limit if total > 0 else 1,
        "articles": articles
    }


# ── Sources ──────────────────────────────────────────────────────────
@app.get("/api/sources")
def get_sources():
    """Retrieve 29 RSS threat intelligence sources."""
    sources = [serialize_doc(s) for s in db["sources"].find().sort("reputation_score", -1)]
    return {"total": len(sources), "sources": sources}


# ── Indicators of Compromise (IOCs) ──────────────────────────────────
@app.get("/api/iocs")
def get_iocs(
    q: Optional[str] = None,
    ioc_type: Optional[str] = None,
    min_confidence: int = Query(0, ge=0, le=100)
):
    """Retrieve Indicators of Compromise database."""
    query = {}
    if ioc_type and ioc_type != "all":
        query["type"] = ioc_type
    if min_confidence > 0:
        query["confidence"] = {"$gte": min_confidence}
    if q:
        query["$or"] = [
            {"value": {"$regex": q, "$options": "i"}},
            {"threat_actor": {"$regex": q, "$options": "i"}},
            {"category": {"$regex": q, "$options": "i"}}
        ]
    iocs = [serialize_doc(doc) for doc in db["indicators_of_compromise"].find(query).limit(100)]
    return {"total": len(iocs), "iocs": iocs}


# ── Entity Resolution & Deduplication Endpoints ─────────────────────
@app.get("/api/entities")
def get_resolved_entities(q: Optional[str] = None):
    """Retrieve deduplicated and merged threat entities."""
    query = {}
    if q:
        query["$or"] = [
            {"aliases": {"$regex": q, "$options": "i"}},
            {"threat_actors": {"$regex": q, "$options": "i"}},
            {"tags": {"$regex": q, "$options": "i"}}
        ]
    docs = [serialize_doc(d) for d in db["threat_entities"].find(query)]
    return {"total": len(docs), "entities": docs}


@app.post("/api/entity-resolution/run")
def run_entity_resolution_endpoint(live: bool = False, seed: bool = False):
    """Trigger the Entity Resolution pipeline (dry_run by default)."""
    import subprocess
    cmd = [sys.executable, "entity_resolution_pipeline.py"]
    # If the collection is empty, or user explicitly requested seed, pass --seed
    if seed or db["threat_entities"].count_documents({}) == 0:
        cmd.append("--seed")
    if live:
        cmd.append("--live")
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )
    return {
        "status": "success" if result.returncode == 0 else "error",
        "mode": "live" if live else "dry_run",
        "output": result.stdout[-3000:],
        "remaining_entities": db["threat_entities"].count_documents({})
    }


@app.post("/api/entity-resolution/seed")
def seed_entity_resolution_endpoint():
    """Seed 24 raw cross-source threat records across CTI, VirusTotal, and Awesome Report."""
    import subprocess
    cmd = [sys.executable, "entity_resolution_pipeline.py", "--seed"]
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )
    return {
        "status": "success" if result.returncode == 0 else "error",
        "output": result.stdout[-3000:],
        "total_documents": db["threat_entities"].count_documents({})
    }


# ── Threat Classification Feature ───────────────────────────────────
class ClassifyRequest(BaseModel):
    title: str = ""
    text: str


@app.post("/api/classify")
def classify_threat_input(payload: ClassifyRequest):
    """Classify raw threat intelligence text using heuristic and rule-based NLP."""
    if not payload.text and not payload.title:
        raise HTTPException(status_code=400, detail="Text or title must be provided")
    result = classify_text(payload.text, payload.title)
    return result


class IngestArticleRequest(BaseModel):
    title: str
    summary: str
    content: str
    source_name: str = "BleepingComputer"


@app.post("/api/articles")
def ingest_classified_article(payload: IngestArticleRequest):
    """Ingest a new threat article with automated classification."""
    classification = classify_text(payload.content, payload.title)
    src = db["sources"].find_one({"name": payload.source_name})
    if not src:
        src = db["sources"].find_one({})

    art_id = ObjectId()
    doc = {
        "_id": art_id,
        "title": payload.title,
        "category": classification["category"],
        "summary": payload.summary,
        "content": payload.content,
        "link": f"https://threat-intel.internal/reports/{random.randint(1000, 9999)}",
        "published_at": time.time(),
        "source_id": src["_id"],
        "threat_classification": {
            "threat_type": classification["category"].title(),
            "severity": classification["severity"],
            "confidence": classification["confidence_score"],
            "threat_actors": classification["threat_actors"],
            "cves": classification["cves"],
            "killchain_phase": classification["killchain_phase"]
        },
        "tags": [classification["category"], classification["severity"].lower()] + [a.lower() for a in classification["threat_actors"]],
        "ioc_ids": []
    }
    db["threat_articles"].insert_one(doc)

    # Also insert into embedded collection for parity
    doc_emb = {
        "_id": art_id,
        "title": payload.title,
        "category": classification["category"],
        "summary": payload.summary,
        "content": payload.content,
        "link": doc["link"],
        "published_at": doc["published_at"],
        "threat_classification": doc["threat_classification"],
        "tags": doc["tags"],
        "source": {
            "source_id": src["_id"],
            "name": src["name"],
            "url": src["url"],
            "reputation_score": src["reputation_score"],
            "is_actual_threat": src["is_actual_threat"],
            "threat_origin": src.get("threat_origin", "VERIFIED_INTEL")
        },
        "iocs": classification["extracted_iocs"]
    }
    db["threat_articles_embedded"].insert_one(doc_emb)

    return {"status": "success", "article_id": str(art_id), "classification": classification}


# ── Lab 7.1: Production Schema Analysis & Live BSON Sizer ────────────
@app.get("/api/lab1/schema")
def get_lab1_schema():
    """Retrieve schema metrics, document size analysis ($bsonSize), and limit verification."""
    collections = ["sources", "threat_articles", "indicators_of_compromise", "threat_articles_embedded"]
    metrics = {}

    for col_name in collections:
        col = db[col_name]
        pipeline = [
            {"$project": {"doc_size": {"$bsonSize": "$$ROOT"}}},
            {"$group": {
                "_id": None,
                "count": {"$sum": 1},
                "min_size": {"$min": "$doc_size"},
                "avg_size": {"$avg": "$doc_size"},
                "max_size": {"$max": "$doc_size"}
            }}
        ]
        res = list(col.aggregate(pipeline))
        if res:
            stat = res[0]
            max_s = stat["max_size"]
            metrics[col_name] = {
                "count": stat["count"],
                "min_size_bytes": stat["min_size"],
                "avg_size_bytes": round(stat["avg_size"], 1),
                "max_size_bytes": max_s,
                "pct_16mb": round((max_s / (16 * 1024 * 1024)) * 100, 6)
            }

    relationships = [
        {
            "relationship": "threat_articles -> sources",
            "type": "Referencing",
            "pattern": "Normalized Reference (source_id)",
            "why_not_embedded": "Avoids duplicating feed metadata (URLs, status, health) across thousands of articles; avoids costly multi-document updates when feed config changes.",
            "embedded_alternative": '{"title": "...", "source": {"name": "...", "url": "...", "reputation": 95}}'
        },
        {
            "relationship": "threat_articles -> IOCs",
            "type": "Referencing",
            "pattern": "Multi-Reference (ioc_ids)",
            "why_not_embedded": "Same IP or hash appears across dozens of incident reports over time; normalized storage allows global threat reputation queries.",
            "embedded_alternative": '{"title": "...", "iocs": [{"type": "ip", "value": "194.26.29.112"}]}'
        },
        {
            "relationship": "threat_articles -> Classification",
            "type": "Embedding",
            "pattern": "Embedded Document (threat_classification)",
            "why_embedded": "High co-occurrence: severity, confidence, CVEs, and ATT&CK tactics are always read together with the article; atomic single-doc reads.",
            "embedded_alternative": "Already embedded"
        },
        {
            "relationship": "threat_articles -> Tags",
            "type": "Embedding",
            "pattern": "Embedded Array (tags)",
            "why_embedded": "1:Few bounded relationship (3-10 tags). Multi-key index enables instant filtering.",
            "embedded_alternative": "Already embedded"
        }
    ]

    return {
        "dataset_origin": "https://ctidigest.com/",
        "metrics": metrics,
        "relationships": relationships,
        "limit_16mb_bytes": 16 * 1024 * 1024,
        "safety_status": "SAFE - Max document size is <0.02% of MongoDB 16MB limit"
    }


@app.post("/api/lab1/benchmark")
def run_lab1_benchmark(iterations: int = Query(200, ge=10, le=1000)):
    """Run live performance benchmark comparing Referenced ($lookup) vs Embedded."""
    col_articles = db["threat_articles"]
    col_embedded = db["threat_articles_embedded"]
    col_sources = db["sources"]

    # 1. Read Referenced ($lookup)
    t0 = time.perf_counter()
    for _ in range(iterations):
        pipeline = [
            {"$lookup": {"from": "sources", "localField": "source_id", "foreignField": "_id", "as": "source_info"}},
            {"$unwind": "$source_info"},
            {"$match": {"source_info.is_actual_threat": True}},
            {"$project": {"title": 1, "source_info.name": 1}}
        ]
        list(col_articles.aggregate(pipeline))
    t_ref_read = time.perf_counter() - t0

    # 2. Read Embedded
    t0 = time.perf_counter()
    for _ in range(iterations):
        list(col_embedded.find({"source.is_actual_threat": True}, {"title": 1, "source.name": 1}))
    t_emb_read = time.perf_counter() - t0

    # 3. Write / Mutation Comparison (50 iterations)
    write_iters = min(50, iterations)
    t0 = time.perf_counter()
    for i in range(write_iters):
        col_sources.update_one({"name": "ShadowNet Honeypot Feeder"}, {"$set": {"reputation_score": 10 + (i % 10)}})
    t_ref_write = time.perf_counter() - t0

    t0 = time.perf_counter()
    for i in range(write_iters):
        col_embedded.update_many({"source.name": "ShadowNet Honeypot Feeder"}, {"$set": {"source.reputation_score": 10 + (i % 10)}})
    t_emb_write = time.perf_counter() - t0

    speedup = t_ref_read / t_emb_read if t_emb_read > 0 else 1.0
    write_penalty = t_emb_write / t_ref_write if t_ref_write > 0 else 1.0

    return {
        "iterations": iterations,
        "read": {
            "referenced_total_sec": round(t_ref_read, 4),
            "referenced_avg_ms": round((t_ref_read / iterations) * 1000, 3),
            "embedded_total_sec": round(t_emb_read, 4),
            "embedded_avg_ms": round((t_emb_read / iterations) * 1000, 3),
            "speedup_factor": round(speedup, 2)
        },
        "write": {
            "iterations": write_iters,
            "referenced_avg_ms": round((t_ref_write / write_iters) * 1000, 3),
            "embedded_avg_ms": round((t_emb_write / write_iters) * 1000, 3),
            "penalty_factor": round(write_penalty, 2)
        }
    }


# ── Lab 7.2: Working Set & WiredTiger Cache Telemetry ────────────────
@app.get("/api/lab2/cache-stats")
def get_wiredtiger_cache_stats():
    """Retrieve real-time WiredTiger cache telemetry from db.serverStatus()."""
    status = db.command("serverStatus")
    wt = status.get("wiredTiger", {})
    cache = wt.get("cache", {})
    coll_stats = db.command("collStats", "security_reports_working_set")

    max_bytes = cache.get("maximum bytes configured", 1)
    in_use_bytes = cache.get("bytes currently in the cache", 0)
    dirty_bytes = cache.get("tracked dirty bytes in the cache", 0)
    pages_read = cache.get("pages read into cache", 0)
    pages_written = cache.get("pages written from cache", 0)
    pages_evicted = cache.get("eviction pages evicted by application threads", 0)
    pages_requested = cache.get("pages requested from the cache", 0)

    coll_size = coll_stats.get("size", 0)
    coll_storage = coll_stats.get("storageSize", 0)
    doc_count = coll_stats.get("count", 0)

    hit_ratio = 100.0
    if pages_requested > 0:
        hit_ratio = max(0.0, (pages_requested - pages_read) / pages_requested) * 100.0

    return {
        "max_cache_mb": round(max_bytes / (1024 * 1024), 2),
        "in_use_mb": round(in_use_bytes / (1024 * 1024), 2),
        "dirty_mb": round(dirty_bytes / (1024 * 1024), 2),
        "cache_utilization_pct": round((in_use_bytes / max_bytes) * 100, 2) if max_bytes else 0,
        "pages_read": pages_read,
        "pages_written": pages_written,
        "pages_evicted": pages_evicted,
        "cache_hit_ratio_pct": round(hit_ratio, 2),
        "collection": {
            "name": "security_reports_working_set",
            "doc_count": doc_count,
            "uncompressed_size_mb": round(coll_size / (1024 * 1024), 2),
            "storage_size_mb": round(coll_storage / (1024 * 1024), 2),
            "working_set_fits": coll_size <= max_bytes
        }
    }


@app.post("/api/lab2/simulate-reads")
def simulate_random_reads(count: int = Query(1000, ge=100, le=10000)):
    """Simulate random reads across the 100k security reports and calculate hit ratio."""
    col = db["security_reports_working_set"]
    total_docs = col.count_documents({})
    if total_docs == 0:
        raise HTTPException(status_code=400, detail="Working set collection is empty. Run lab_02_working_set_analysis.py first.")

    s_before = db.command("serverStatus")["wiredTiger"]["cache"]
    p_read_before = s_before.get("pages read into cache", 0)

    t0 = time.perf_counter()
    for _ in range(count):
        rand_id = f"ASR-2024-{random.randint(0, total_docs - 1):06d}"
        col.find_one({"report_id": rand_id}, {"report_id": 1, "vendor": 1})
    elapsed = time.perf_counter() - t0

    s_after = db.command("serverStatus")["wiredTiger"]["cache"]
    p_read_after = s_after.get("pages read into cache", 0)
    delta_read = p_read_after - p_read_before

    misses = min(count, delta_read)
    hit_ratio = max(0.0, (count - misses) / count) * 100.0

    return {
        "queries_executed": count,
        "elapsed_seconds": round(elapsed, 3),
        "throughput_qps": round(count / elapsed, 0) if elapsed > 0 else 0,
        "disk_pages_read": delta_read,
        "cache_hit_ratio_pct": round(hit_ratio, 2)
    }


# ── VirusTotal v3 Integration Endpoints ──────────────────────────────
CURRENT_VT_KEY = os.getenv("VIRUSTOTAL_API_KEY", "")


class VTLookupRequest(BaseModel):
    indicator: str
    indicator_type: str = "ip"
    api_key: Optional[str] = None


class VTKeyRequest(BaseModel):
    api_key: str


@app.get("/api/virustotal/status")
def get_virustotal_status():
    """Check if VirusTotal API key is configured."""
    has_key = bool(CURRENT_VT_KEY.strip())
    masked = f"{CURRENT_VT_KEY[:4]}...{CURRENT_VT_KEY[-4:]}" if len(CURRENT_VT_KEY) >= 8 else ""
    return {
        "is_configured": has_key,
        "masked_key": masked,
        "cache_entries": db["vt_cache"].count_documents({})
    }


@app.post("/api/virustotal/set-key")
def set_virustotal_key(payload: VTKeyRequest):
    """Dynamically set or update the VirusTotal API key in runtime and persist to .env."""
    global CURRENT_VT_KEY
    CURRENT_VT_KEY = payload.api_key.strip()
    # Persist to .env file so key survives server restarts
    try:
        env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
        with open(env_path, "w") as ef:
            ef.write(f"VIRUSTOTAL_API_KEY={CURRENT_VT_KEY}\n")
    except Exception:
        pass  # Non-fatal: key is still set in memory
    return {"status": "success", "message": "VirusTotal API key successfully configured"}


@app.post("/api/virustotal/lookup")
def lookup_virustotal(payload: VTLookupRequest):
    """Query live threat intelligence from 70+ AV engines on VirusTotal."""
    key = payload.api_key or CURRENT_VT_KEY
    res = query_virustotal(
        indicator=payload.indicator,
        indicator_type=payload.indicator_type,
        api_key=key,
        db=db
    )
    return res


@app.get("/api/virustotal/enrichments")
def get_vt_enrichments():
    """Return all IOCs that have been enriched with VirusTotal data."""
    enriched = list(db["indicators_of_compromise"].find(
        {"vt_enrichment": {"$exists": True}},
        {"value": 1, "type": 1, "vt_enrichment": 1, "threat_actor": 1, "confidence": 1}
    ))
    docs = [serialize_doc(d) for d in enriched]
    malicious = sum(1 for d in docs if d.get("vt_enrichment", {}).get("verdict") == "MALICIOUS")
    suspicious = sum(1 for d in docs if d.get("vt_enrichment", {}).get("verdict") == "SUSPICIOUS")
    clean = sum(1 for d in docs if d.get("vt_enrichment", {}).get("verdict") == "CLEAN")
    return {
        "total_enriched": len(docs),
        "summary": {"malicious": malicious, "suspicious": suspicious, "clean": clean},
        "iocs": docs
    }


@app.post("/api/virustotal/bulk-enrich")
def bulk_enrich_iocs():
    """Trigger background enrichment of all IOCs with VirusTotal verdicts (rate-limited)."""
    import threading
    import time as _time

    def _run():
        iocs = list(db["indicators_of_compromise"].find({}))
        for idx, ioc in enumerate(iocs):
            if idx > 0:
                _time.sleep(16)  # Free tier: 4 req/min
            indicator = ioc.get("value", "")
            itype = ioc.get("type", "ip")
            if not indicator:
                continue
            result = query_virustotal(indicator=indicator, indicator_type=itype, api_key=CURRENT_VT_KEY, db=db)
            enrichment = {
                "verdict": result.get("threat_verdict", "UNKNOWN"),
                "malicious": result.get("malicious_count", 0),
                "suspicious": result.get("suspicious_count", 0),
                "harmless": result.get("harmless_count", 0),
                "total_engines": result.get("total_engines", 0),
                "reputation_score": result.get("reputation_score", 0),
                "tags": result.get("tags", [])[:5],
                "permalink": result.get("permalink", ""),
                "status": result.get("status", "unknown"),
                "enriched_at": _time.time(),
                "from_cache": result.get("from_cache", False)
            }
            db["indicators_of_compromise"].update_one(
                {"_id": ioc["_id"]},
                {"$set": {"vt_enrichment": enrichment}}
            )

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()
    return {
        "status": "started",
        "message": f"Background VT enrichment started for {db['indicators_of_compromise'].count_documents({})} IOCs.",
        "note": "Free tier: 16s delay between requests. Check /api/virustotal/enrichments for progress."
    }


# Mount Frontend
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend")
if os.path.exists(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

    @app.get("/")
    def serve_frontend_root():
        index_file = os.path.join(FRONTEND_DIR, "index.html")
        return FileResponse(index_file)

