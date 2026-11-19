
# build_and_push.ps1
# Stages lab files (removing spaces from paths), builds Docker image, and pushes to Docker Hub.
# Run from: c:\Users\aryap\OneDrive\Desktop\lab 9\

$ErrorActionPreference = "Stop"
$base   = "c:\Users\aryap\OneDrive\Desktop\lab 9"
$ctx    = "$base\context"

Write-Host "`n[1/4] Preparing build context (staging files)..." -ForegroundColor Cyan

# Clean and recreate staging dirs
Remove-Item "$ctx" -Recurse -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force "$ctx\lab9"                | Out-Null
New-Item -ItemType Directory -Force "$ctx\lab8"                | Out-Null
New-Item -ItemType Directory -Force "$ctx\lab7\config"         | Out-Null
New-Item -ItemType Directory -Force "$ctx\lab7\data"           | Out-Null
New-Item -ItemType Directory -Force "$ctx\root"                | Out-Null

# ── Lab 9 ──────────────────────────────────────────────────────────────
$lab9src = "$base"
Copy-Item "$lab9src\lab_01_write_concern_latency.py" "$ctx\lab9\"
Copy-Item "$lab9src\lab_01_latency_results.json"     "$ctx\lab9\"
Copy-Item "$lab9src\lab_02_simulate_partition.py"    "$ctx\lab9\"
Copy-Item "$lab9src\lab_02_simulate_partition.sh"    "$ctx\lab9\"
Copy-Item "$lab9src\lab_02_partition_results.json"   "$ctx\lab9\"

# ── Lab 8 ──────────────────────────────────────────────────────────────
$lab8src = "$base\lab 8"
Copy-Item "$lab8src\activity_8_1_replica_set.py"  "$ctx\lab8\"
Copy-Item "$lab8src\activity_8_2_failover.py"     "$ctx\lab8\"
Copy-Item "$lab8src\lab_8_1_deploy_replicaset.py" "$ctx\lab8\"
Copy-Item "$lab8src\lab_8_2_failover_observer.py" "$ctx\lab8\"
Copy-Item "$lab8src\lab_02_failover_observer.py"  "$ctx\lab8\"
Copy-Item "$lab8src\docker-compose.yml"           "$ctx\lab8\"
Copy-Item "$lab8src\rs_init_basic.js"             "$ctx\lab8\"

# ── Lab 7 ──────────────────────────────────────────────────────────────
$lab7src = "$base\lab 7"
Copy-Item "$lab7src\lab_01_production_schema.py"      "$ctx\lab7\"
Copy-Item "$lab7src\lab_02_working_set_analysis.py"   "$ctx\lab7\"
Copy-Item "$lab7src\lab_01_try_yourself.py"           "$ctx\lab7\"
Copy-Item "$lab7src\lab_02_try_yourself.py"           "$ctx\lab7\"
Copy-Item "$lab7src\lab_01_production_schema.json"    "$ctx\lab7\"
Copy-Item "$lab7src\lab_02_working_set_analysis.json" "$ctx\lab7\"
Copy-Item "$lab7src\lab_01_try_yourself.json"         "$ctx\lab7\"
Copy-Item "$lab7src\lab_02_try_yourself.json"         "$ctx\lab7\"
Copy-Item "$lab7src\config\connection.py"             "$ctx\lab7\config\"
Copy-Item "$lab7src\config\__init__.py"               "$ctx\lab7\config\"
Copy-Item "$lab7src\data\cti_platform_dump.json"      "$ctx\lab7\data\"

# ── Root files ─────────────────────────────────────────────────────────
Copy-Item "$base\demo_menu.py"                          "$ctx\root\"
Copy-Item "$base\entrypoint.sh"                         "$ctx\root\"
Copy-Item "$base\K.PRANAV_REDDY_24BTRCL098_LAB_09.pdf" "$ctx\root\"

Write-Host "    Staging complete." -ForegroundColor Green

# ── Build ──────────────────────────────────────────────────────────────
Write-Host "`n[2/4] Building Docker image (this takes ~15-20 min for first build)..." -ForegroundColor Cyan
docker build `
  -t aryapranav1024/nosql-mongodb-labs:latest `
  -t aryapranav1024/mongodb-lab-09:latest `
  "$base"

Write-Host "`n[3/4] Pushing to Docker Hub..." -ForegroundColor Cyan
docker push aryapranav1024/nosql-mongodb-labs:latest
docker push aryapranav1024/mongodb-lab-09:latest

Write-Host "`n[4/4] Cleaning staging directory..." -ForegroundColor Cyan
Remove-Item "$ctx" -Recurse -Force -ErrorAction SilentlyContinue

Write-Host "`n============================================" -ForegroundColor Green
Write-Host "  SUCCESS! Image pushed to Docker Hub." -ForegroundColor Green
Write-Host "  Pull URL: docker pull aryapranav1024/nosql-mongodb-labs:latest" -ForegroundColor Green
Write-Host "  Hub URL : https://hub.docker.com/r/aryapranav1024/nosql-mongodb-labs" -ForegroundColor Green
Write-Host "============================================`n" -ForegroundColor Green
