"""Seed realistic Cyber Threat Intelligence dataset based on ctidigest.com and security reports.

Populates collections:
- `sources`: 29 threat intelligence RSS/API feeds with health, status, threat indicators
- `threat_articles`: Threat intelligence reports with referenced source_id, embedded classification, tags
- `indicators_of_compromise`: IOCs (IP, domain, URL, SHA256, MD5) with references
- `threat_articles_embedded`: Redesigned collection with embedded source threat classification for Activity 7.1
"""

import os
import sys
import json
from datetime import datetime, timedelta
import random
from bson import ObjectId

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config.connection import get_db, reset_collection, banner

# 29 Feed definitions directly from ctidigest.com
FEEDS_METADATA = [
    {"name": "BleepingComputer", "url": "https://www.bleepingcomputer.com/feed/", "category": "ransomware", "reputation": 96, "is_actual_threat": False, "threat_origin": "VERIFIED_INTEL"},
    {"name": "The Hacker News", "url": "https://feeds.feedburner.com/TheHackersNews", "category": "vulnerabilities", "reputation": 95, "is_actual_threat": False, "threat_origin": "VERIFIED_INTEL"},
    {"name": "Krebs on Security", "url": "https://krebsonsecurity.com/feed/", "category": "threat-actors", "reputation": 98, "is_actual_threat": False, "threat_origin": "VERIFIED_INTEL"},
    {"name": "Dark Reading", "url": "https://www.darkreading.com/rss.xml", "category": "threat-actors", "reputation": 92, "is_actual_threat": False, "threat_origin": "VERIFIED_INTEL"},
    {"name": "Infosecurity Magazine", "url": "https://www.infosecurity-magazine.com/rss/news/", "category": "compromised", "reputation": 90, "is_actual_threat": False, "threat_origin": "VERIFIED_INTEL"},
    {"name": "Security Week", "url": "https://www.securityweek.com/feed/", "category": "vulnerabilities", "reputation": 93, "is_actual_threat": False, "threat_origin": "VERIFIED_INTEL"},
    {"name": "Help Net Security", "url": "https://www.helpnetsecurity.com/feed/", "category": "patches", "reputation": 89, "is_actual_threat": False, "threat_origin": "VERIFIED_INTEL"},
    {"name": "CSO Online", "url": "https://www.csoonline.com/feed/?languages=en", "category": "government", "reputation": 91, "is_actual_threat": False, "threat_origin": "VERIFIED_INTEL"},
    {"name": "Computer Weekly Security", "url": "https://www.computerweekly.com/rss/IT-security.xml", "category": "cloud", "reputation": 88, "is_actual_threat": False, "threat_origin": "VERIFIED_INTEL"},
    {"name": "Schneier on Security", "url": "https://www.schneier.com/feed/atom/", "category": "cryptography", "reputation": 97, "is_actual_threat": False, "threat_origin": "VERIFIED_INTEL"},
    {"name": "Troy Hunt", "url": "https://www.troyhunt.com/rss/", "category": "compromised", "reputation": 96, "is_actual_threat": False, "threat_origin": "VERIFIED_INTEL"},
    {"name": "Graham Cluley", "url": "https://www.grahamcluley.com/feed/", "category": "malware", "reputation": 90, "is_actual_threat": False, "threat_origin": "VERIFIED_INTEL"},
    {"name": "Naked Security", "url": "https://news.sophos.com/en-us/category/threat-research/feed/", "category": "malware", "reputation": 91, "is_actual_threat": False, "threat_origin": "VERIFIED_INTEL"},
    {"name": "We Live Security", "url": "https://www.welivesecurity.com/feed/", "category": "threat-actors", "reputation": 93, "is_actual_threat": False, "threat_origin": "VERIFIED_INTEL"},
    {"name": "The Record", "url": "https://therecord.media/feed/", "category": "government", "reputation": 94, "is_actual_threat": False, "threat_origin": "VERIFIED_INTEL"},
    {"name": "Check Point Research", "url": "https://research.checkpoint.com/feed/", "category": "vulnerabilities", "reputation": 95, "is_actual_threat": False, "threat_origin": "VERIFIED_INTEL"},
    {"name": "Juniper Threat Research", "url": "https://blogs.juniper.net/threat-research/feed", "category": "iot", "reputation": 89, "is_actual_threat": False, "threat_origin": "VERIFIED_INTEL"},
    {"name": "SecPod Blog", "url": "https://www.secpod.com/blog/feed/", "category": "vulnerabilities", "reputation": 87, "is_actual_threat": False, "threat_origin": "VERIFIED_INTEL"},
    {"name": "Microsoft Security Blog", "url": "https://www.microsoft.com/en-us/security/blog/feed/", "category": "cloud", "reputation": 97, "is_actual_threat": False, "threat_origin": "VERIFIED_INTEL"},
    {"name": "Trellix Threat Research", "url": "https://www.trellix.com/feed/", "category": "malware", "reputation": 94, "is_actual_threat": False, "threat_origin": "VERIFIED_INTEL"},
    {"name": "SentinelOne Labs", "url": "https://www.sentinelone.com/labs/feed/", "category": "threat-actors", "reputation": 95, "is_actual_threat": False, "threat_origin": "VERIFIED_INTEL"},
    {"name": "SpecterOps", "url": "https://specterops.io/blog/feed/", "category": "threat-actors", "reputation": 92, "is_actual_threat": False, "threat_origin": "VERIFIED_INTEL"},
    {"name": "Trend Micro Security", "url": "https://feeds.trendmicro.com/TrendMicroSimplySecurity", "category": "ransomware", "reputation": 91, "is_actual_threat": False, "threat_origin": "VERIFIED_INTEL"},
    {"name": "Fortra Security Blog", "url": "https://www.fortra.com/blog/rss.xml", "category": "compromised", "reputation": 88, "is_actual_threat": False, "threat_origin": "VERIFIED_INTEL"},
    {"name": "UpGuard Blog", "url": "https://www.upguard.com/blog/rss.xml", "category": "compromised", "reputation": 87, "is_actual_threat": False, "threat_origin": "VERIFIED_INTEL"},
    {"name": "VirusTotal Blog", "url": "https://blog.virustotal.com/feeds/posts/default", "category": "malware", "reputation": 98, "is_actual_threat": False, "threat_origin": "VERIFIED_INTEL"},
    {"name": "Sophos Security Operations", "url": "https://news.sophos.com/en-us/category/security-operations/feed/", "category": "threat-actors", "reputation": 90, "is_actual_threat": False, "threat_origin": "VERIFIED_INTEL"},
    {"name": "Sophos AI Research", "url": "https://news.sophos.com/en-us/category/ai-research/feed/", "category": "malware", "reputation": 90, "is_actual_threat": False, "threat_origin": "VERIFIED_INTEL"},
    {"name": "ShadowNet Honeypot Feeder", "url": "http://185.220.101.5/darknet-feed.xml", "category": "threat-actors", "reputation": 14, "is_actual_threat": True, "threat_origin": "MALICIOUS_C2_FEED"}
]

SAMPLE_ARTICLES = [
    {
        "title": "LockBit 3.0 Ransomware Exploits ScreenConnect Vulnerabilities in Wild Campaigns",
        "category": "ransomware",
        "source_name": "BleepingComputer",
        "summary": "Affiliates associated with LockBit ransomware have weaponized ConnectWise ScreenConnect vulnerabilities (CVE-2024-1709) to gain initial access and deploy ransomware payloads within corporate networks.",
        "content": "Threat actors are deploying customized LockBit 3.0 (LockBit Black) payloads. The attackers bypass authentication using path traversal in the Setup Wizard. Once execution is gained, attackers disable antivirus solutions using custom PowerShell loaders, exfiltrate sensitive files using rclone, and encrypt virtualization hosts.",
        "threat_type": "Ransomware",
        "severity": "CRITICAL",
        "confidence": 98,
        "threat_actors": ["LockBit 3.0", "LockBit Supporter"],
        "cves": ["CVE-2024-1709", "CVE-2024-1708"],
        "killchain_phase": "Initial Access & Impact",
        "tags": ["ransomware", "connectwise", "screenconnect", "lockbit", "rce", "cve-2024-1709"],
        "iocs": [
            {"type": "ip", "value": "194.26.29.112", "confidence": 96, "category": "c2-server"},
            {"type": "sha256", "value": "5b4d7f763f03b29c9ef4c31e9a3b680c2fbf9ad2f8b50e386a34567210123456", "confidence": 99, "category": "ransomware-payload"},
            {"type": "domain", "value": "auth-screenconnect-update.net", "confidence": 94, "category": "phishing"}
        ]
    },
    {
        "title": "State-Sponsored Sandworm APT Deploys Kapeka Backdoor Targeting Critical Infrastructure",
        "category": "threat-actors",
        "source_name": "SentinelOne Labs",
        "summary": "Russian military intelligence (GRU) Sandworm group (Unit 74455) has been identified deploying a previously undocumented flexible backdoor dubbed Kapeka against Ukrainian and European entities.",
        "content": "Kapeka is a sophisticated Windows backdoor written in C++ that masquerades as a Microsoft Word add-in. The malware executes scheduled tasks, contacts dynamic C2 servers via HTTPS over non-standard ports, and drops modular second-stage plugins.",
        "threat_type": "Nation-State Espionage",
        "severity": "CRITICAL",
        "confidence": 95,
        "threat_actors": ["Sandworm", "APT44", "Unit 74455"],
        "cves": [],
        "killchain_phase": "Persistence & Command and Control",
        "tags": ["sandworm", "apt44", "kapeka", "russia", "gru", "backdoor", "scada"],
        "iocs": [
            {"type": "sha256", "value": "a1f59c8d23456789abcdef0123456789abcdef0123456789abcdef0123456789", "confidence": 97, "category": "backdoor-dll"},
            {"type": "ip", "value": "185.196.8.44", "confidence": 92, "category": "c2-node"}
        ]
    },
    {
        "title": "Critical RCE Vulnerability in Palo Alto PAN-OS GlobalProtect Under Active Attack (CVE-2024-3400)",
        "category": "vulnerabilities",
        "source_name": "The Hacker News",
        "summary": "Palo Alto Networks has released emergency hotfixes for an actively exploited maximum-severity zero-day command injection flaw in the GlobalProtect feature of PAN-OS software.",
        "content": "A command injection vulnerability in the GlobalProtect gateway feature of PAN-OS allows an unauthenticated remote attacker to execute arbitrary code with root privileges on the firewall. The threat actor, tracked as UTA0218, installed a custom Python backdoor dubbed UPSTREAM.",
        "threat_type": "Zero-Day Exploit",
        "severity": "CRITICAL",
        "confidence": 99,
        "threat_actors": ["UTA0218"],
        "cves": ["CVE-2024-3400"],
        "killchain_phase": "Exploitation",
        "tags": ["palo-alto", "pan-os", "cve-2024-3400", "zero-day", "rce", "firewall"],
        "iocs": [
            {"type": "ip", "value": "144.172.79.92", "confidence": 98, "category": "exploit-source"},
            {"type": "url", "value": "http://144.172.79.92/css/bootstrap.min.css", "confidence": 95, "category": "malicious-script"}
        ]
    },
    {
        "title": "CISA and NSA Release Joint Guidance on Securing Cloud-Hosted Active Directory Deployments",
        "category": "government",
        "source_name": "CSO Online",
        "summary": "Federal agencies outline best practices to mitigate identity compromise and golden SAML abuse across hybrid cloud Entra ID environments.",
        "content": "The advisory emphasizes hardening certificate services (AD CS), monitoring for DCSync anomalies, enforcing phishing-resistant FIDO2 MFA, and auditing federated trust relationships against token forgery attacks.",
        "threat_type": "Government Advisory",
        "severity": "MEDIUM",
        "confidence": 90,
        "threat_actors": ["APT29", "Midnight Blizzard"],
        "cves": [],
        "killchain_phase": "Credential Access & Defense Evasion",
        "tags": ["cisa", "nsa", "entra-id", "active-directory", "identity", "saml"],
        "iocs": []
    },
    {
        "title": "Qakbot Banking Trojan Resurges via Malicious PDF Phishing Campaigns",
        "category": "malware",
        "source_name": "Trellix Threat Research",
        "summary": "Despite international law enforcement takedowns, operators of Qakbot have resumed spam distributions utilizing weaponized PDF attachments containing embedded JavaScript loaders.",
        "content": "The attack begins with thread-hijacking phishing emails attaching password-protected PDF files. Upon user execution, the embedded JavaScript writes an obfuscated WSF file that contacts remote staging servers to pull the Qakbot DLL loader.",
        "threat_type": "Trojan / Loader",
        "severity": "HIGH",
        "confidence": 94,
        "threat_actors": ["Gold Lagoon", "Qakbot Operators"],
        "cves": [],
        "killchain_phase": "Delivery & Execution",
        "tags": ["qakbot", "phishing", "trojan", "malware", "botnet", "pdf"],
        "iocs": [
            {"type": "domain", "value": "cdn-cloud-storage-sync.com", "confidence": 91, "category": "staging-server"},
            {"type": "md5", "value": "8b1a9953c4611296a827abf8c47804d7", "confidence": 96, "category": "trojan-hash"}
        ]
    },
    {
        "title": "Midnight Blizzard Breaches Corporate Mailboxes via Password Spray Attack",
        "category": "compromised",
        "source_name": "Microsoft Security Blog",
        "summary": "Microsoft discloses state-sponsored actor Midnight Blizzard accessed senior executive emails utilizing password spraying on a legacy non-production tenant.",
        "content": "The actor utilized password spraying to compromise a legacy test tenant lacking MFA. They then created an OAuth application with full tenant permissions to read Exchange Online mailboxes.",
        "threat_type": "Nation-State Compromise",
        "severity": "HIGH",
        "confidence": 96,
        "threat_actors": ["Midnight Blizzard", "Nobelium", "APT29"],
        "cves": [],
        "killchain_phase": "Credential Access",
        "tags": ["microsoft", "midnight-blizzard", "apt29", "password-spray", "oauth", "email"],
        "iocs": [
            {"type": "ip", "value": "154.213.189.65", "confidence": 93, "category": "spray-source"}
        ]
    },
    {
        "title": "DarkSide Rebrand Clop Claims Multiple Zero-Day Injections in File Transfer Appliances",
        "category": "ransomware",
        "source_name": "Trend Micro Security",
        "summary": "Ransomware syndicates continue targeting edge managed file transfer (MFT) services to steal corporate data without deploying disk-encrypting payloads.",
        "content": "Extortionists exploit unauthenticated SQL injection endpoints in file transfer portals to extract relational databases, demanding ransoms under threat of public leak on dark web data portals.",
        "threat_type": "Data Extortion / Ransomware",
        "severity": "HIGH",
        "confidence": 93,
        "threat_actors": ["Clop", "FIN11", "TA505"],
        "cves": ["CVE-2023-34362", "CVE-2023-35036"],
        "killchain_phase": "Actions on Objectives",
        "tags": ["clop", "extortion", "mft", "sqli", "data-theft"],
        "iocs": [
            {"type": "domain", "value": "clop-leak-direct.onion", "confidence": 99, "category": "leak-portal"}
        ]
    },
    {
        "title": "Compromised Darknet Mirror Injecting Malicious C2 Payloads into Security Telemetry",
        "category": "threat-actors",
        "source_name": "ShadowNet Honeypot Feeder",
        "summary": "Telemetry feed broadcasting corrupted indicators and weaponized scripts designed to trigger blind RCE in downstream SIEM parsers.",
        "content": "This feed has been verified as an active malicious node broadcasting poisoned threat intelligence to exploit deserialization vulnerabilities in automated threat ingesters.",
        "threat_type": "Adversarial C2 Ingestion",
        "severity": "CRITICAL",
        "confidence": 99,
        "threat_actors": ["ShadowNet Syndicate"],
        "cves": ["CVE-2024-0012"],
        "killchain_phase": "Command and Control",
        "tags": ["malicious-source", "c2", "poisoning", "siem-exploit"],
        "iocs": [
            {"type": "ip", "value": "185.220.101.5", "confidence": 99, "category": "c2-poisoner"},
            {"type": "url", "value": "http://185.220.101.5/exploit.bin", "confidence": 98, "category": "weaponized-exploit"}
        ]
    }
]


def seed_database():
    """Populate CTI collections in MongoDB."""
    banner("Seeding CTI Database based on ctidigest.com")
    db = get_db("cti_platform")

    col_sources = reset_collection("cti_platform", "sources")
    col_articles = reset_collection("cti_platform", "threat_articles")
    col_iocs = reset_collection("cti_platform", "indicators_of_compromise")
    col_embedded = reset_collection("cti_platform", "threat_articles_embedded")

    # 1. Insert Sources
    print("1. Inserting 29 feed sources...")
    source_docs = []
    source_map = {}
    for feed in FEEDS_METADATA:
        src_id = ObjectId()
        doc = {
            "_id": src_id,
            "name": feed["name"],
            "url": feed["url"],
            "feed_status": "ok" if feed["reputation"] > 50 else "malicious_alert",
            "reputation_score": feed["reputation"],
            "is_actual_threat": feed["is_actual_threat"],
            "threat_origin": feed["threat_origin"],
            "category": feed["category"],
            "crawl_interval_minutes": 15,
            "last_polled": datetime.utcnow() - timedelta(minutes=random.randint(2, 60)),
            "health_metric": {
                "http_status": 200 if feed["reputation"] > 50 else 403,
                "latency_ms": random.randint(120, 850),
                "error_rate_pct": 0.0 if feed["reputation"] > 50 else 82.5
            }
        }
        source_docs.append(doc)
        source_map[feed["name"]] = doc

    col_sources.insert_many(source_docs)
    print(f"   [OK] Inserted {len(source_docs)} feed source profiles.")

    # 2. Insert IOCs and Articles
    print("2. Inserting Threat Articles and Indicators of Compromise (Referenced Architecture)...")
    articles_referenced = []
    articles_embedded = []
    ioc_docs = []

    now = datetime.utcnow()

    # Expand sample articles into 120 realistic threat intelligence records
    counter = 1
    for base in SAMPLE_ARTICLES:
        src_name = base["source_name"]
        src_doc = source_map.get(src_name, source_docs[0])
        src_id = src_doc["_id"]

        # Insert IOCs for this article
        article_id = ObjectId()
        article_ioc_ids = []

        for item in base["iocs"]:
            ioc_id = ObjectId()
            ioc_doc = {
                "_id": ioc_id,
                "type": item["type"],
                "value": item["value"],
                "confidence": item["confidence"],
                "category": item["category"],
                "threat_actor": base["threat_actors"][0] if base["threat_actors"] else "Unknown",
                "first_seen": now - timedelta(days=random.randint(1, 45)),
                "last_seen": now,
                "status": "active",
                "referenced_article_ids": [article_id]
            }
            ioc_docs.append(ioc_doc)
            article_ioc_ids.append(ioc_id)

        # Base referenced article
        art_ref = {
            "_id": article_id,
            "title": base["title"],
            "category": base["category"],
            "summary": base["summary"],
            "content": base["content"],
            "link": f"https://threat-intel.internal/reports/{counter:04d}",
            "published_at": now - timedelta(hours=random.randint(1, 168)),
            "source_id": src_id,  # REFERENCED RELATIONSHIP
            "threat_classification": {  # EMBEDDED RELATIONSHIP
                "threat_type": base["threat_type"],
                "severity": base["severity"],
                "confidence": base["confidence"],
                "threat_actors": base["threat_actors"],
                "cves": base["cves"],
                "killchain_phase": base["killchain_phase"]
            },
            "tags": base["tags"],  # EMBEDDED RELATIONSHIP
            "ioc_ids": article_ioc_ids  # REFERENCED RELATIONSHIP
        }
        articles_referenced.append(art_ref)

        # Embedded design (Activity 7.1 Try It Yourself)
        # Redesign: Embed the source threat classification directly in the article
        art_emb = {
            "_id": article_id,
            "title": base["title"],
            "category": base["category"],
            "summary": base["summary"],
            "content": base["content"],
            "link": art_ref["link"],
            "published_at": art_ref["published_at"],
            "threat_classification": art_ref["threat_classification"],
            "tags": art_ref["tags"],
            "source": {  # EMBEDDED SOURCE CLASSIFICATION
                "source_id": src_id,
                "name": src_doc["name"],
                "url": src_doc["url"],
                "reputation_score": src_doc["reputation_score"],
                "is_actual_threat": src_doc["is_actual_threat"],
                "threat_origin": src_doc["threat_origin"],
                "feed_status": src_doc["feed_status"]
            },
            "iocs": base["iocs"]  # EMBEDDED IOCs
        }
        articles_embedded.append(art_emb)
        counter += 1

    # Generate additional articles to reach 150 diverse reports across categories
    categories = ["threat-actors", "vulnerabilities", "ransomware", "patches", "malware", "government", "mobile", "cloud", "iot", "cryptography", "compromised"]
    severities = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
    threat_actors_pool = ["Lazarus Group", "Volt Typhoon", "LockBit 3.0", "BlackCat", "Midnight Blizzard", "Scattered Spider", "Sandworm", "APT41", "Play Ransomware", "Rhysida"]

    for i in range(len(articles_referenced), 150):
        src_doc = random.choice(source_docs)
        cat = random.choice(categories)
        sev = random.choice(severities)
        ta = random.sample(threat_actors_pool, k=random.randint(1, 2))
        cve = [f"CVE-2024-{random.randint(1000, 9999)}"] if cat in ["vulnerabilities", "ransomware", "patches"] else []
        art_id = ObjectId()
        
        art_ref = {
            "_id": art_id,
            "title": f"Threat Assessment #{i+1}: {cat.replace('-', ' ').title()} Intelligence Briefing",
            "category": cat,
            "summary": f"Automated analysis identifying indicators and attack vectors targeting enterprise infrastructure in {cat}.",
            "content": f"Detailed telemetry gathered across sensor honeytokens indicates elevated campaign traffic matching known signatures of {', '.join(ta)}. Exploit telemetry confirmed.",
            "link": f"https://threat-intel.internal/reports/{i+1:04d}",
            "published_at": now - timedelta(hours=random.randint(1, 500)),
            "source_id": src_doc["_id"],  # REFERENCED
            "threat_classification": {  # EMBEDDED
                "threat_type": cat.title(),
                "severity": sev,
                "confidence": random.randint(70, 99),
                "threat_actors": ta,
                "cves": cve,
                "killchain_phase": random.choice(["Initial Access", "Execution", "Persistence", "Privilege Escalation", "Exfiltration"])
            },
            "tags": [cat, sev.lower()] + [t.lower().replace(" ", "-") for t in ta],
            "ioc_ids": []
        }
        articles_referenced.append(art_ref)

        art_emb = {
            "_id": art_id,
            "title": art_ref["title"],
            "category": cat,
            "summary": art_ref["summary"],
            "content": art_ref["content"],
            "link": art_ref["link"],
            "published_at": art_ref["published_at"],
            "threat_classification": art_ref["threat_classification"],
            "tags": art_ref["tags"],
            "source": {  # EMBEDDED
                "source_id": src_doc["_id"],
                "name": src_doc["name"],
                "url": src_doc["url"],
                "reputation_score": src_doc["reputation_score"],
                "is_actual_threat": src_doc["is_actual_threat"],
                "threat_origin": src_doc["threat_origin"],
                "feed_status": src_doc["feed_status"]
            },
            "iocs": []
        }
        articles_embedded.append(art_emb)

    col_articles.insert_many(articles_referenced)
    col_embedded.insert_many(articles_embedded)
    if ioc_docs:
        col_iocs.insert_many(ioc_docs)

    print(f"   [OK] Inserted {len(articles_referenced)} threat articles (Referenced Architecture).")
    print(f"   [OK] Inserted {len(articles_embedded)} threat articles (Embedded Architecture).")
    print(f"   [OK] Inserted {len(ioc_docs)} indicators of compromise.")

    # Create indexes
    col_articles.create_index([("title", "text"), ("summary", "text")])
    col_articles.create_index("source_id")
    col_articles.create_index("category")
    col_articles.create_index("threat_classification.severity")
    col_embedded.create_index("source.is_actual_threat")
    col_embedded.create_index("threat_classification.severity")
    col_iocs.create_index("value")
    col_iocs.create_index("type")

    # Export dump to JSON in data/
    dump_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
    os.makedirs(dump_dir, exist_ok=True)
    dump_file = os.path.join(dump_dir, "cti_platform_dump.json")

    def json_serial(obj):
        if isinstance(obj, (datetime, ObjectId)):
            return str(obj)
        raise TypeError(f"Type {type(obj)} not serializable")

    dump_data = {
        "metadata": {
            "source_origin": "https://ctidigest.com/",
            "exported_at": str(now),
            "collection_counts": {
                "sources": len(source_docs),
                "threat_articles_referenced": len(articles_referenced),
                "threat_articles_embedded": len(articles_embedded),
                "indicators_of_compromise": len(ioc_docs)
            }
        },
        "sources": source_docs,
        "threat_articles": articles_referenced,
        "threat_articles_embedded": articles_embedded,
        "indicators_of_compromise": ioc_docs
    }

    with open(dump_file, "w", encoding="utf-8") as f:
        json.dump(dump_data, f, indent=2, default=json_serial)

    print(f"   [OK] Production schema dump exported to: {dump_file}")
    banner("Database Seeding Completed Successfully")


if __name__ == "__main__":
    seed_database()
