"""VirusTotal v3 API Integration Module for CTI Platform.

Supports:
- IP Address lookups (/api/v3/ip_addresses/{ip})
- File Hash lookups (SHA256, MD5, SHA1) (/api/v3/files/{hash})
- Domain lookups (/api/v3/domains/{domain})
- URL scanning & analysis (/api/v3/urls/{id})
- MongoDB 24-hour caching layer to respect free API rate limits (4 req/min)
"""

import os
import time
import base64
import requests
from typing import Dict, Any, Optional

VT_API_BASE = "https://www.virustotal.com/api/v3"
DEFAULT_API_KEY = os.getenv("VIRUSTOTAL_API_KEY", "")


def get_vt_headers(api_key: Optional[str] = None) -> Dict[str, str]:
    key = api_key or os.getenv("VIRUSTOTAL_API_KEY", DEFAULT_API_KEY)
    return {
        "x-apikey": key.strip(),
        "Accept": "application/json"
    }


def query_virustotal(indicator: str, indicator_type: str, api_key: Optional[str] = None, db=None) -> Dict[str, Any]:
    """Query VirusTotal v3 API with 24-hour MongoDB caching."""
    indicator = indicator.strip()
    key = api_key or os.getenv("VIRUSTOTAL_API_KEY", DEFAULT_API_KEY)

    # 1. Check MongoDB cache first if db is provided
    if db is not None:
        try:
            cached = db["vt_cache"].find_one({"indicator": indicator})
            if cached and (time.time() - cached.get("cached_at", 0)) < 86400:  # 24h TTL
                res = cached["result"]
                res["from_cache"] = True
                return res
        except Exception:
            pass

    # 2. If no API key provided, return structured prompt with heuristic baseline
    if not key:
        return {
            "status": "key_required",
            "indicator": indicator,
            "type": indicator_type,
            "message": "VirusTotal API key is not configured. Provide your API key to fetch live threat intelligence from 70+ antivirus engines.",
            "has_key": False
        }

    # 3. Determine endpoint
    headers = get_vt_headers(key)
    try:
        if indicator_type in ["sha256", "md5", "sha1", "hash"]:
            url = f"{VT_API_BASE}/files/{indicator}"
        elif indicator_type in ["ip", "ipv4"]:
            url = f"{VT_API_BASE}/ip_addresses/{indicator}"
        elif indicator_type in ["domain", "hostname"]:
            url = f"{VT_API_BASE}/domains/{indicator}"
        elif indicator_type in ["url"]:
            url_id = base64.urlsafe_b64encode(indicator.encode()).decode().strip("=")
            url = f"{VT_API_BASE}/urls/{url_id}"
        else:
            url = f"{VT_API_BASE}/search?query={indicator}"

        resp = requests.get(url, headers=headers, timeout=12)

        if resp.status_code == 200:
            data = resp.json().get("data", {})
            attrs = data.get("attributes", {})
            stats = attrs.get("last_analysis_stats", {})
            malicious = stats.get("malicious", 0)
            suspicious = stats.get("suspicious", 0)
            harmless = stats.get("harmless", 0)
            undetected = stats.get("undetected", 0)
            total = malicious + suspicious + harmless + undetected

            rep = attrs.get("reputation", 0)
            tags = attrs.get("tags", [])
            categories = attrs.get("categories", {})

            result = {
                "status": "success",
                "indicator": indicator,
                "type": indicator_type,
                "has_key": True,
                "malicious_count": malicious,
                "suspicious_count": suspicious,
                "harmless_count": harmless,
                "undetected_count": undetected,
                "total_engines": total,
                "reputation_score": rep,
                "tags": tags[:8],
                "threat_verdict": "MALICIOUS" if malicious > 5 else ("SUSPICIOUS" if (malicious > 0 or suspicious > 0) else "CLEAN"),
                "last_analysis_date": attrs.get("last_analysis_date", int(time.time())),
                "permalink": f"https://www.virustotal.com/gui/{'file' if indicator_type == 'hash' else indicator_type}/{indicator}",
                "from_cache": False
            }

            # Cache to MongoDB
            if db is not None:
                try:
                    db["vt_cache"].update_one(
                        {"indicator": indicator},
                        {"$set": {"indicator": indicator, "cached_at": time.time(), "result": result}},
                        upsert=True
                    )
                except Exception:
                    pass

            return result

        elif resp.status_code in (404, 400):
            return {
                "status": "not_found",
                "indicator": indicator,
                "type": indicator_type,
                "has_key": True,
                "message": "Indicator not found in VirusTotal database (not yet seen or classified).",
                "malicious_count": 0,
                "total_engines": 0,
                "threat_verdict": "UNKNOWN",
                "from_cache": False
            }
        elif resp.status_code in (401, 403):
            return {
                "status": "auth_error",
                "has_key": False,
                "message": "Invalid or expired VirusTotal API key. Please check your key credentials."
            }
        elif resp.status_code == 429:
            return {
                "status": "rate_limited",
                "has_key": True,
                "message": "VirusTotal API rate limit exceeded (Free tier: 4 requests/min). Retry in 60s."
            }
        else:
            return {
                "status": "error",
                "http_status": resp.status_code,
                "indicator": indicator,
                "message": resp.text[:200]
            }

    except Exception as e:
        return {
            "status": "error",
            "message": f"Connection error querying VirusTotal: {str(e)}"
        }
