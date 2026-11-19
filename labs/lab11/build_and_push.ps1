# build_and_push.ps1
# Builds Docker image for Lab 11 and pushes to Docker Hub.
# Run from: c:\Users\aryap\OneDrive\Desktop\lab 11\

$ErrorActionPreference = "Stop"
$base = "c:\Users\aryap\OneDrive\Desktop\lab 11"

Write-Host "`n========================================================" -ForegroundColor Cyan
Write-Host "  BUILDING & PUSHING MONGODB LAB 11 DOCKER IMAGE" -ForegroundColor Cyan
Write-Host "  Repository: aryapranav1024/mongodb-lab-11:latest" -ForegroundColor Cyan
Write-Host "========================================================`n" -ForegroundColor Cyan

# 1. Regenerate benchmarks and PDF report first
Write-Host "[1/3] Generating benchmark telemetry and PDF report..." -ForegroundColor Yellow
python "$base\lab_01_shard_key_eval.py"
python "$base\lab_02_shard_key_hotspot.py"
python "$base\generate_pdf_report.py"

# 2. Build Docker Image
Write-Host "`n[2/3] Building Docker image..." -ForegroundColor Yellow
docker build `
  -t aryapranav1024/mongodb-lab-11:latest `
  -t aryapranav1024/nosql-mongodb-labs:lab11 `
  "$base"

# 3. Push to Docker Hub
Write-Host "`n[3/3] Pushing to Docker Hub..." -ForegroundColor Yellow
docker push aryapranav1024/mongodb-lab-11:latest
docker push aryapranav1024/nosql-mongodb-labs:lab11

Write-Host "`n========================================================" -ForegroundColor Green
Write-Host "  SUCCESS! Image pushed to Docker Hub." -ForegroundColor Green
Write-Host "  Pull URL: docker pull aryapranav1024/mongodb-lab-11:latest" -ForegroundColor Green
Write-Host "  Hub URL : https://hub.docker.com/r/aryapranav1024/mongodb-lab-11" -ForegroundColor Green
Write-Host "========================================================`n" -ForegroundColor Green
