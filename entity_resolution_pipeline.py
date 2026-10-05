"""Entity Resolution & Deduplication Pipeline for ThreatAnalysis Platform.

Performs cross-source matching and merging of duplicate threat records ingested
from three disparate intelligence feeds:
    1. CTI Digest Threats      (prefix: CTI_, threat_)
    2. VirusTotal Telemetry    (suffix: _vt, _vt_scan)
    3. Awesome Annual Report   (prefix: ASR_, k., suffix: _roll_no_)

Execution modes:
    python entity_resolution_pipeline.py              # Dry run (default)
    python entity_resolution_pipeline.py --live        # Live database mutation
    python entity_resolution_pipeline.py --seed        # Seed test duplicates first
    python entity_resolution_pipeline.py --seed --live # Seed + merge in one pass

Author: K. Pranav Reddy (24BTRCL098)
Project: ThreatAnalysis Platform -- NoSQL Lab 7
"""

import os
import sys
import re
import logging
import argparse
from datetime import datetime, timedelta, timezone
from collections import defaultdict
from typing import Optional

from bson import ObjectId

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config.connection import get_db, banner

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

console = Console()

# -- Logging Configuration ------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("EntityResolver")

# -- Constants ------------------------------------------------------
COLLECTION_NAME = "threat_entities"

SOURCE_PRIORITY = {
    "virustotal":           1,    # Highest priority (multi-engine verified)
    "cti_digest":           2,    # Curated editorial threat intelligence
    "github_awesome_report": 3,   # Community-sourced annual security reports
}

SEVERITY_RANK = {
    "CRITICAL": 4,
    "HIGH":     3,
    "MEDIUM":   2,
    "LOW":      1,
    "UNKNOWN":  0,
}


# ===================================================================
# STEP 1: NORMALIZATION & ENTITY RESOLUTION LOGIC
# ===================================================================

def normalize_entity_identifier(raw_id: str) -> str:
    """Process raw threat names/IDs into a canonical normalized key.

    Normalization pipeline:
        1. Lowercase + strip whitespace
        2. Remove domain-specific prefix/suffix noise
        3. Normalize separators (-, ., space) -> underscore
        4. Collapse multi-underscores and strip edges
        5. Return the canonical key for grouping

    Args:
        raw_id: Raw identifier string from any of the 3 ingestion sources.

    Returns:
        Normalized canonical string key for entity grouping.

    Examples:
        >>> normalize_entity_identifier("CTI_LockBit3_Ransomware")
        'lockbit3_ransomware'
        >>> normalize_entity_identifier("lockbit3-ransomware-vt-telemetry")
        'lockbit3_ransomware'
        >>> normalize_entity_identifier("ASR_LockBit3_Ransomware_report")
        'lockbit3_ransomware'
        >>> normalize_entity_identifier("CTI_Lazarus_Group_DPRK_alert")
        'lazarus_group_dprk'
        >>> normalize_entity_identifier("lazarus-group-dprk-vt-scan")
        'lazarus_group_dprk'
        >>> normalize_entity_identifier("ASR_Sandworm_APT44")
        'sandworm_apt44'
    """
    if not raw_id:
        return ""

    # Stage 1: Lowercase and strip
    text = raw_id.lower().strip()

    # Stage 2: Remove domain-specific prefixes
    # Order matters: more specific patterns before generic ones
    prefix_patterns = [
        r'^cti[_\-]?',           # CTI Digest prefix:     CTI_, CTI-, CTI
        r'^threat[_\-]?',        # Generic threat prefix:  threat_, threat-
        r'^asr[_\-]?',           # Awesome Report prefix:  ASR_, ASR-
        r'^report[_\-]?',        # Report prefix:          report_
        r'^k\.',                 # Honorific prefix:       k.
    ]
    for pattern in prefix_patterns:
        text = re.sub(pattern, '', text, count=1)

    # Stage 2b: Remove domain-specific suffixes
    suffix_patterns = [
        r'[_\-]?vt[_\-]?(scan|telemetry|lookup)?$',  # VirusTotal suffixes
        r'[_\-]?(scan|feed|alert|entry|report)$',      # Generic trailing tokens
    ]
    for pattern in suffix_patterns:
        text = re.sub(pattern, '', text, count=1)

    # Stage 2c: Remove inline noise tokens
    inline_patterns = [
        r'[_\-]?roll[_\-]?no[_\-]?',   # Academic noise: roll_no_, roll-no-
    ]
    for pattern in inline_patterns:
        text = re.sub(pattern, '_', text)

    # Stage 3: Normalize separators -> underscore
    text = re.sub(r'[-.\s]+', '_', text)

    # Stage 4: Collapse consecutive underscores, strip edges
    text = re.sub(r'_+', '_', text)
    text = text.strip('_')

    return text


# ===================================================================
# STEP 2: SOURCE-AWARE MERGING STRATEGY
# ===================================================================

def _get_source_priority(doc: dict) -> int:
    """Return numeric priority for a document's data source (lower = higher priority)."""
    source = doc.get("data_source", "unknown").lower().strip()
    return SOURCE_PRIORITY.get(source, 99)


def _get_severity_rank(sev: str) -> int:
    """Convert severity string to numeric rank for comparison."""
    return SEVERITY_RANK.get(str(sev).upper(), 0)


def _field_completeness_score(doc: dict) -> int:
    """Score a document by how many meaningful fields are populated."""
    score = 0
    for key in ["title", "summary", "content", "threat_actors", "cves",
                 "iocs", "tags", "severity", "confidence"]:
        val = doc.get(key)
        if val:
            if isinstance(val, (list, dict)):
                score += len(val)
            else:
                score += 1
    return score


def select_canonical_record(group: list[dict]) -> tuple[dict, list[dict]]:
    """Select the canonical (primary) record from a group of matched duplicates.

    Selection criteria:
        1. Highest source priority (VirusTotal > CTI Digest > Awesome Report)
        2. Tie-breaker: Most populated fields (schema completeness)

    Returns:
        Tuple of (canonical_doc, list_of_secondary_docs)
    """
    sorted_group = sorted(
        group,
        key=lambda d: (_get_source_priority(d), -_field_completeness_score(d))
    )
    return sorted_group[0], sorted_group[1:]


def merge_entity_fields(canonical: dict, secondaries: list[dict]) -> dict:
    """Build merged field payload from canonical + secondary duplicate records.

    Field Union Rules:
        - aliases:       Set union of all raw identifiers
        - sources:       Deduplicated source labels
        - iocs:          Set union by (type, value) tuple
        - threat_actors: Set union
        - cves:          Set union
        - tags:          Set union
        - first_seen:    min() across all timestamps
        - last_seen:     max() across all timestamps
        - confidence:    max() of confidence scores
        - severity:      Highest ranked severity
        - content/title: From canonical record (already selected)
    """
    all_docs = [canonical] + secondaries

    # -- Aliases: preserve all original identifiers --
    aliases = set()
    for doc in all_docs:
        raw = doc.get("raw_identifier", doc.get("entity_id", ""))
        if raw:
            aliases.add(raw)
        # Also collect any pre-existing aliases
        for alias in doc.get("aliases", []):
            aliases.add(alias)

    # -- Sources: deduplicated origin labels --
    sources = list(set(
        doc.get("data_source", "unknown") for doc in all_docs
    ))

    # -- IOCs: set union by (type, value) --
    seen_iocs = set()
    merged_iocs = []
    for doc in all_docs:
        for ioc in doc.get("iocs", []):
            key = (ioc.get("type", ""), ioc.get("value", ""))
            if key not in seen_iocs and key[1]:
                seen_iocs.add(key)
                merged_iocs.append(ioc)

    # -- Threat Actors: set union --
    threat_actors = list(set(
        actor
        for doc in all_docs
        for actor in doc.get("threat_actors", [])
    ))

    # -- CVEs: set union --
    cves = list(set(
        cve
        for doc in all_docs
        for cve in doc.get("cves", [])
    ))

    # -- Tags: set union --
    tags = list(set(
        tag
        for doc in all_docs
        for tag in doc.get("tags", [])
    ))

    # -- Timestamps: min(first_seen), max(last_seen) --
    fallback_ts = datetime.now(timezone.utc)
    all_first = [doc.get("first_seen", fallback_ts) for doc in all_docs if doc.get("first_seen")]
    all_last = [doc.get("last_seen", fallback_ts) for doc in all_docs if doc.get("last_seen")]
    first_seen = min(all_first) if all_first else fallback_ts
    last_seen = max(all_last) if all_last else fallback_ts

    # -- Confidence: maximum across group --
    confidence = max(
        (doc.get("confidence", 0) for doc in all_docs),
        default=0
    )

    # -- Severity: highest ranked --
    severity = max(
        (doc.get("severity", "UNKNOWN") for doc in all_docs),
        key=_get_severity_rank,
        default="UNKNOWN"
    )

    # -- Build the merged $set payload --
    merged = {
        "aliases":        sorted(list(aliases)),
        "sources":        sorted(sources),
        "iocs":           merged_iocs,
        "threat_actors":  sorted(threat_actors),
        "cves":           sorted(cves),
        "tags":           sorted(tags),
        "first_seen":     first_seen,
        "last_seen":      last_seen,
        "confidence":     confidence,
        "severity":       severity,
        "merged_count":   len(all_docs),
        "merge_strategy": "source_priority_union",
        "updated_at":     datetime.now(timezone.utc),
    }

    return merged


# ===================================================================
# STEP 3: MONGODB EXECUTION & SAFETY RULES
# ===================================================================

def execute_entity_resolution(dry_run: bool = True):
    """Run the full entity resolution pipeline against MongoDB.

    Args:
        dry_run: If True (default), only print proposed merges.
                 If False, atomically update canonical docs and delete duplicates.
    """
    banner("Entity Resolution & Deduplication Pipeline")
    mode_label = "[DRY RUN]" if dry_run else "[LIVE EXECUTION]"
    console.print(f"\n  Mode: [bold {'cyan' if dry_run else 'red'}]{mode_label}[/bold {'cyan' if dry_run else 'red'}]\n")

    db = get_db("cti_platform")
    col = db[COLLECTION_NAME]

    total_docs = col.count_documents({})
    if total_docs == 0:
        console.print("[yellow]  No documents found in '{COLLECTION_NAME}'. Run with --seed to populate test data.[/yellow]")
        return

    logger.info(f"Loaded {total_docs} documents from '{COLLECTION_NAME}'")

    # -- Phase 1: Group documents by normalized key --
    all_docs = list(col.find({}))
    groups = defaultdict(list)

    for doc in all_docs:
        raw_id = doc.get("entity_id", doc.get("raw_identifier", doc.get("title", "")))
        normalized = normalize_entity_identifier(raw_id)
        if normalized:
            groups[normalized].append(doc)
        else:
            logger.warning(f"Empty normalized key for doc _id={doc['_id']}, raw='{raw_id}'")

    # Separate into merge groups and unique entities
    merge_groups = {k: v for k, v in groups.items() if len(v) > 1}
    unique_entities = {k: v[0] for k, v in groups.items() if len(v) == 1}

    # -- Phase 2: Display merge plan --
    console.print(Panel(
        f"[bold]Total Documents:[/bold] {total_docs}\n"
        f"[bold]Normalized Entity Keys:[/bold] {len(groups)}\n"
        f"[bold]Merge Groups (duplicates):[/bold] [yellow]{len(merge_groups)}[/yellow]\n"
        f"[bold]Unique Entities (no dupes):[/bold] [green]{len(unique_entities)}[/green]\n"
        f"[bold]Documents to Delete:[/bold] [red]{sum(len(v) - 1 for v in merge_groups.values())}[/red]",
        title="Entity Resolution Summary",
        border_style="cyan"
    ))

    if not merge_groups:
        console.print("\n  [green]No duplicate entities detected. Dataset is clean.[/green]")
        return

    # Build detailed merge plan table
    plan_table = Table(
        title="Proposed Entity Merge Plan",
        box=box.ROUNDED,
        show_lines=True,
        header_style="bold cyan"
    )
    plan_table.add_column("#", style="dim", width=4)
    plan_table.add_column("Normalized Key", style="bold white", width=22)
    plan_table.add_column("Matched Raw Identifiers", width=42)
    plan_table.add_column("Sources", width=20)
    plan_table.add_column("Canonical", style="green", width=18)
    plan_table.add_column("Action", width=14)

    merge_operations = []  # Store operations for live execution

    for idx, (norm_key, group_docs) in enumerate(merge_groups.items(), 1):
        canonical, secondaries = select_canonical_record(group_docs)
        merged_fields = merge_entity_fields(canonical, secondaries)

        raw_ids = [d.get("entity_id", d.get("raw_identifier", "?")) for d in group_docs]
        src_labels = merged_fields["sources"]
        canonical_id = canonical.get("entity_id", canonical.get("raw_identifier", "?"))
        secondary_ids = [d["_id"] for d in secondaries]

        plan_table.add_row(
            str(idx),
            norm_key,
            "\n".join(f"* {r}" for r in raw_ids),
            "\n".join(src_labels),
            canonical_id,
            f"Merge {len(group_docs)}->1"
        )

        merge_operations.append({
            "canonical_doc": canonical,
            "secondaries": secondaries,
            "secondary_ids": secondary_ids,
            "merged_fields": merged_fields,
            "norm_key": norm_key,
        })

    console.print(plan_table)

    # -- Phase 3: Field union detail for each merge --
    detail_table = Table(
        title="Field Union Statistics per Merge Group",
        box=box.SIMPLE_HEAVY,
        header_style="bold blue"
    )
    detail_table.add_column("Normalized Key", style="white", width=22)
    detail_table.add_column("Aliases", justify="center", width=8)
    detail_table.add_column("IOCs", justify="center", width=8)
    detail_table.add_column("Actors", justify="center", width=8)
    detail_table.add_column("CVEs", justify="center", width=8)
    detail_table.add_column("Tags", justify="center", width=8)
    detail_table.add_column("Severity", width=10)
    detail_table.add_column("Confidence", justify="center", width=10)

    for op in merge_operations:
        mf = op["merged_fields"]
        detail_table.add_row(
            op["norm_key"],
            str(len(mf["aliases"])),
            str(len(mf["iocs"])),
            str(len(mf["threat_actors"])),
            str(len(mf["cves"])),
            str(len(mf["tags"])),
            mf["severity"],
            str(mf["confidence"]),
        )

    console.print(detail_table)

    # -- Phase 4: Execute or stop --
    if dry_run:
        console.print(f"\n  [bold cyan][DRY RUN COMPLETE][/bold cyan] No database changes were made.")
        console.print(f"  To execute live merges, run:  [bold]python entity_resolution_pipeline.py --live[/bold]\n")
        return

    # LIVE EXECUTION
    console.print(f"\n  [bold red]Executing {len(merge_operations)} merge operations on MongoDB...[/bold red]\n")

    merged_count = 0
    deleted_count = 0

    for op in merge_operations:
        canonical = op["canonical_doc"]
        secondary_ids = op["secondary_ids"]
        merged_fields = op["merged_fields"]

        try:
            # Atomic $set on canonical document
            result_update = col.update_one(
                {"_id": canonical["_id"]},
                {"$set": merged_fields}
            )

            if result_update.modified_count == 1:
                logger.info(
                    f"  [MERGED] {op['norm_key']} -> canonical _id={canonical['_id']} "
                    f"(set {len(merged_fields)} fields)"
                )
                merged_count += 1
            else:
                logger.warning(
                    f"  [WARN] Update matched but did not modify canonical _id={canonical['_id']}"
                )

            # Delete secondary duplicates
            if secondary_ids:
                result_delete = col.delete_many({"_id": {"$in": secondary_ids}})
                deleted_count += result_delete.deleted_count
                logger.info(
                    f"  [DELETED] {result_delete.deleted_count} duplicate(s) for '{op['norm_key']}'"
                )

        except Exception as e:
            logger.error(f"  [ERROR] Failed to merge '{op['norm_key']}': {e}")

    # -- Phase 5: Verification --
    remaining = col.count_documents({})
    console.print(Panel(
        f"[bold green]Merge Operations Completed[/bold green]\n\n"
        f"  Canonical docs updated:   {merged_count}\n"
        f"  Duplicate docs deleted:   {deleted_count}\n"
        f"  Documents remaining:      {remaining}\n"
        f"  Original document count:  {total_docs}",
        title="Post-Merge Verification",
        border_style="green"
    ))

    # Verify no duplicate normalized keys remain
    remaining_docs = list(col.find({}))
    post_groups = defaultdict(list)
    for doc in remaining_docs:
        raw_id = doc.get("entity_id", doc.get("raw_identifier", doc.get("title", "")))
        normalized = normalize_entity_identifier(raw_id)
        post_groups[normalized].append(doc)

    remaining_dupes = {k: v for k, v in post_groups.items() if len(v) > 1}
    if remaining_dupes:
        console.print(f"  [yellow][!] {len(remaining_dupes)} groups still contain duplicates (may need manual review).[/yellow]")
    else:
        console.print(f"  [green][OK] Zero duplicate normalized keys remain. Dataset is fully deduplicated.[/green]")

    banner("Entity Resolution Pipeline Completed")


# ===================================================================
# SEED: CREATE REALISTIC CROSS-SOURCE DUPLICATE TEST DATA
# ===================================================================

def seed_duplicate_test_data():
    """Insert realistic cross-source duplicate threat records into MongoDB.

    Creates 24 documents representing 8 unique entities, each appearing
    across 3 different sources with different naming conventions.
    """
    banner("Seeding Cross-Source Duplicate Test Data")

    db = get_db("cti_platform")
    col = db[COLLECTION_NAME]
    col.drop()
    logger.info(f"Dropped and recreating '{COLLECTION_NAME}' collection")

    now = datetime.now(timezone.utc)

    # 8 unique entities x 3 sources = 24 documents with realistic naming variance
    test_entities = [
        {
            "core_name": "lazarus_group_dprk",
            "variants": [
                {"entity_id": "CTI_Lazarus_Group_DPRK_alert",  "data_source": "cti_digest"},
                {"entity_id": "lazarus-group-dprk-vt-scan",    "data_source": "virustotal"},
                {"entity_id": "ASR_Lazarus_Group_DPRK_entry",  "data_source": "github_awesome_report"},
            ],
            "threat_actors": ["Lazarus Group", "APT38", "Hidden Cobra"],
            "severity": "CRITICAL",
            "confidence": 98,
            "tags": ["dprk", "cryptocurrency", "byovd", "bank-heist", "nation-state"],
            "cves": ["CVE-2024-21338"],
            "iocs": [
                {"type": "ip", "value": "175.45.176.1", "confidence": 95},
                {"type": "sha256", "value": "7c4a8d09ca3762af61e59520943dc26494f8941b523a4982a7a57a92cfb371b2", "confidence": 99},
            ],
        },
        {
            "core_name": "lockbit3_ransomware",
            "variants": [
                {"entity_id": "CTI_LockBit3_Ransomware",       "data_source": "cti_digest"},
                {"entity_id": "lockbit3-ransomware-vt-telemetry", "data_source": "virustotal"},
                {"entity_id": "ASR_LockBit3_Ransomware_report", "data_source": "github_awesome_report"},
            ],
            "threat_actors": ["LockBit 3.0", "LockBit Supporter"],
            "severity": "CRITICAL",
            "confidence": 99,
            "tags": ["ransomware", "lockbit", "cve-2024-1709", "screenconnect"],
            "cves": ["CVE-2024-1709", "CVE-2024-1708"],
            "iocs": [
                {"type": "ip", "value": "194.26.29.112", "confidence": 96},
                {"type": "sha256", "value": "5b4d7f763f03b29c9ef4c31e9a3b680c2fbf9ad2f8b50e386a34567210123456", "confidence": 99},
            ],
        },
        {
            "core_name": "sandworm_apt44",
            "variants": [
                {"entity_id": "threat_sandworm_apt44_feed",  "data_source": "cti_digest"},
                {"entity_id": "sandworm-apt44-vt-telemetry", "data_source": "virustotal"},
                {"entity_id": "ASR_Sandworm_APT44",          "data_source": "github_awesome_report"},
            ],
            "threat_actors": ["Sandworm", "APT44", "Unit 74455"],
            "severity": "CRITICAL",
            "confidence": 95,
            "tags": ["apt", "russia", "gru", "kapeka", "scada"],
            "iocs": [
                {"type": "ip", "value": "185.196.8.44", "confidence": 92},
                {"type": "sha256", "value": "a1f59c8d23456789abcdef0123456789abcdef0123456789abcdef0123456789", "confidence": 97},
            ],
        },
        {
            "core_name": "midnight_blizzard",
            "variants": [
                {"entity_id": "CTI_Midnight_Blizzard_alert", "data_source": "cti_digest"},
                {"entity_id": "midnight-blizzard-vt",         "data_source": "virustotal"},
                {"entity_id": "k.midnight_blizzard",          "data_source": "github_awesome_report"},
            ],
            "threat_actors": ["Midnight Blizzard", "APT29", "Nobelium"],
            "severity": "HIGH",
            "confidence": 96,
            "tags": ["password-spray", "oauth", "microsoft", "email"],
            "iocs": [
                {"type": "ip", "value": "154.213.189.65", "confidence": 93},
            ],
        },
        {
            "core_name": "qakbot_loader",
            "variants": [
                {"entity_id": "threat_Qakbot_Loader",         "data_source": "cti_digest"},
                {"entity_id": "qakbot-loader-vt-scan",         "data_source": "virustotal"},
                {"entity_id": "ASR_Qakbot_Loader_entry",       "data_source": "github_awesome_report"},
            ],
            "threat_actors": ["Gold Lagoon", "Qakbot Operators"],
            "severity": "HIGH",
            "confidence": 94,
            "tags": ["trojan", "phishing", "botnet", "pdf"],
            "iocs": [
                {"type": "domain", "value": "cdn-cloud-storage-sync.com", "confidence": 91},
                {"type": "md5", "value": "8b1a9953c4611296a827abf8c47804d7", "confidence": 96},
            ],
        },
        {
            "core_name": "volt_typhoon",
            "variants": [
                {"entity_id": "CTI_Volt_Typhoon_scan",   "data_source": "cti_digest"},
                {"entity_id": "volt_typhoon_vt",          "data_source": "virustotal"},
                {"entity_id": "ASR_Volt_Typhoon",         "data_source": "github_awesome_report"},
            ],
            "threat_actors": ["Volt Typhoon"],
            "severity": "CRITICAL",
            "confidence": 92,
            "tags": ["china", "critical-infrastructure", "living-off-land"],
        },
        {
            "core_name": "scattered_spider",
            "variants": [
                {"entity_id": "threat_scattered_spider_alert", "data_source": "cti_digest"},
                {"entity_id": "scattered-spider-vt",            "data_source": "virustotal"},
                {"entity_id": "k.scattered_spider_report",      "data_source": "github_awesome_report"},
            ],
            "threat_actors": ["Scattered Spider", "UNC3944"],
            "severity": "HIGH",
            "confidence": 91,
            "tags": ["social-engineering", "sim-swap", "okta"],
        },
        {
            "core_name": "clop_extortion",
            "variants": [
                {"entity_id": "CTI_Clop_Extortion",        "data_source": "cti_digest"},
                {"entity_id": "clop-extortion-vt-telemetry","data_source": "virustotal"},
                {"entity_id": "ASR_Clop_Extortion_report",  "data_source": "github_awesome_report"},
            ],
            "threat_actors": ["Clop", "FIN11", "TA505"],
            "severity": "HIGH",
            "confidence": 93,
            "tags": ["extortion", "mft", "sqli", "data-theft"],
            "cves": ["CVE-2023-34362", "CVE-2023-35036"],
            "iocs": [
                {"type": "domain", "value": "clop-leak-direct.onion", "confidence": 99},
            ],
        },
    ]

    docs_to_insert = []

    for entity in test_entities:
        base_first_seen = now - timedelta(days=random.randint(30, 180))

        for variant in entity["variants"]:
            # Each source variant has slightly different field completeness
            source = variant["data_source"]

            # Introduce realistic variation: VT has more IOCs, CTI has more context, ASR is leaner
            doc_iocs = entity.get("iocs", []).copy()
            doc_cves = entity.get("cves", []).copy()
            doc_actors = entity.get("threat_actors", []).copy()
            doc_tags = entity.get("tags", []).copy()

            # VT source gets extra IOC telemetry
            if source == "virustotal" and doc_iocs:
                doc_iocs.append({
                    "type": "ip",
                    "value": f"10.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}",
                    "confidence": 60
                })
                doc_tags.append("vt-enriched")

            # CTI source gets an extra CVE sometimes
            if source == "cti_digest" and doc_cves:
                doc_cves.append(f"CVE-2024-{random.randint(1000, 9999)}")

            # ASR source is usually leaner
            if source == "github_awesome_report":
                doc_iocs = doc_iocs[:1]  # Only first IOC
                doc_tags = doc_tags[:3]  # Fewer tags

            # Source-specific timestamp jitter
            jitter_days = random.randint(0, 14)
            first_seen = base_first_seen + timedelta(days=jitter_days)
            last_seen = now - timedelta(hours=random.randint(1, 48))

            doc = {
                "_id":             ObjectId(),
                "entity_id":       variant["entity_id"],
                "raw_identifier":  variant["entity_id"],
                "data_source":     source,
                "title":           f"Threat Entity: {variant['entity_id']}",
                "summary":         f"Cross-source threat record from {source} for entity '{entity['core_name']}'.",
                "content":         f"Detailed telemetry ingested from {source} pipeline. "
                                   f"Core entity corresponds to threat group/family '{entity['core_name']}'.",
                "threat_actors":   doc_actors,
                "severity":        entity["severity"],
                "confidence":      entity["confidence"] + random.randint(-5, 5),
                "cves":            doc_cves,
                "tags":            doc_tags,
                "iocs":            doc_iocs,
                "first_seen":      first_seen,
                "last_seen":       last_seen,
                "aliases":         [variant["entity_id"]],
                "sources":         [source],
            }
            docs_to_insert.append(doc)

    col.insert_many(docs_to_insert)

    # Create indexes
    col.create_index("entity_id")
    col.create_index("data_source")
    col.create_index("severity")

    console.print(f"\n  [green][OK] Inserted {len(docs_to_insert)} documents ({len(test_entities)} unique entities x 3 sources)[/green]")
    console.print(f"  [dim]  Collection: {COLLECTION_NAME}[/dim]\n")

    # Show what was seeded
    seed_table = Table(title="Seeded Cross-Source Duplicate Records", box=box.ROUNDED)
    seed_table.add_column("Core Entity", style="bold cyan")
    seed_table.add_column("CTI Digest ID", style="yellow")
    seed_table.add_column("VirusTotal ID", style="green")
    seed_table.add_column("Awesome Report ID", style="blue")

    for entity in test_entities:
        ids = {v["data_source"]: v["entity_id"] for v in entity["variants"]}
        seed_table.add_row(
            entity["core_name"],
            ids.get("cti_digest", "--"),
            ids.get("virustotal", "--"),
            ids.get("github_awesome_report", "--"),
        )

    console.print(seed_table)
    banner("Test Data Seeding Complete")


# ===================================================================
# SELF-VERIFICATION: EDGE CASE UNIT TESTS
# ===================================================================

def run_self_verification():
    """Verify normalize_entity_identifier handles all edge cases correctly."""
    banner("Self-Verification: Edge Case Tests")

    test_cases = [
        # (input, expected_output, description)
        ("CTI_LockBit3_Ransomware",       "lockbit3_ransomware", "CTI Digest prefix removal"),
        ("lockbit3-ransomware-vt-telemetry", "lockbit3_ransomware", "VT telemetry suffix + hyphens"),
        ("ASR_LockBit3_Ransomware_report","lockbit3_ransomware", "Awesome Report prefix & report suffix"),
        ("CTI_Lazarus_Group_DPRK_alert",  "lazarus_group_dprk",  "CTI prefix + alert suffix"),
        ("lazarus-group-dprk-vt-scan",    "lazarus_group_dprk",  "VT scan suffix with hyphenated APT"),
        ("ASR_Lazarus_Group_DPRK_entry",  "lazarus_group_dprk",  "ASR prefix + entry suffix"),
        ("threat_sandworm_apt44_feed",    "sandworm_apt44",      "Threat prefix + feed suffix"),
        ("sandworm-apt44-vt-telemetry",   "sandworm_apt44",      "VT telemetry suffix + hyphens"),
        ("ASR_Sandworm_APT44",            "sandworm_apt44",      "ASR prefix standard"),
        ("  CTI_Volt_Typhoon_scan  ",     "volt_typhoon",        "Whitespace stripping + CTI scan"),
        ("",                              "",                    "Empty string safety"),
        ("UNIQUE_MALWARE_ZERO_DAY",       "unique_malware_zero_day", "No prefix/suffix match -> passthrough"),
        ("threat_scattered_spider_report","scattered_spider",    "Threat prefix + report suffix"),
        ("CTI_Midnight_Blizzard_alert",  "midnight_blizzard",   "CTI prefix + alert suffix"),
        ("midnight-blizzard-vt",         "midnight_blizzard",   "Hyphen + VT suffix"),
    ]

    results_table = Table(title="Normalization Edge Case Verification", box=box.ROUNDED, show_lines=True)
    results_table.add_column("Input", style="white", width=36)
    results_table.add_column("Expected", style="cyan", width=22)
    results_table.add_column("Actual", width=22)
    results_table.add_column("Status", width=8)
    results_table.add_column("Description", style="dim", width=36)

    passed = 0
    failed = 0

    for raw_input, expected, desc in test_cases:
        actual = normalize_entity_identifier(raw_input)
        ok = actual == expected
        if ok:
            passed += 1
        else:
            failed += 1

        results_table.add_row(
            f"`{raw_input}`",
            expected or "(empty)",
            actual or "(empty)",
            "[green]PASS[/green]" if ok else f"[red]FAIL[/red]",
            desc,
        )

    console.print(results_table)
    console.print(f"\n  Results: [green]{passed} passed[/green], [red]{failed} failed[/red] out of {len(test_cases)} tests.\n")

    if failed > 0:
        logger.error(f"{failed} normalization tests failed -- review regex patterns before running pipeline.")
    else:
        logger.info("All normalization edge cases passed successfully.")

    banner("Self-Verification Complete")
    return failed == 0


# ===================================================================
# CLI ENTRYPOINT
# ===================================================================

import random  # needed by seed function

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="ThreatAnalysis Entity Resolution & Deduplication Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python entity_resolution_pipeline.py                # Dry run (default)
  python entity_resolution_pipeline.py --live          # Execute live merges
  python entity_resolution_pipeline.py --seed          # Seed test data + dry run
  python entity_resolution_pipeline.py --seed --live   # Seed + live merge
  python entity_resolution_pipeline.py --verify        # Run edge case tests only
        """
    )
    parser.add_argument("--live",   action="store_true", help="Execute live database mutations (default: dry_run=True)")
    parser.add_argument("--seed",   action="store_true", help="Seed test duplicate data before running pipeline")
    parser.add_argument("--verify", action="store_true", help="Run self-verification edge case tests and exit")

    args = parser.parse_args()

    if args.verify:
        run_self_verification()
        sys.exit(0)

    if args.seed:
        seed_duplicate_test_data()

    # Always run verification first
    if not run_self_verification():
        console.print("[red]Aborting: normalization tests failed.[/red]")
        sys.exit(1)

    execute_entity_resolution(dry_run=not args.live)
