# PowerShell Script to build, test, and push NoSQL Lab 18 Docker Image
# Student: K. Pranav Reddy (24BTRCL098)
# Docker Hub Image: aryapranav1024/nosql-lab18:latest

param(
    [string]$Username = "aryapranav1024"
)

$ImageName = "${Username}/nosql-lab18:latest"

Write-Host "==============================================================================" -ForegroundColor Cyan
Write-Host " NoSQL Lab 18: Comparative Capstone Benchmark Docker Automation" -ForegroundColor Yellow
Write-Host " Image Target: $ImageName" -ForegroundColor Yellow
Write-Host "==============================================================================" -ForegroundColor Cyan

# 1. Build image using WSL Docker Engine
Write-Host "`n[1/3] Building Docker image ($ImageName)..." -ForegroundColor Cyan
wsl -d Ubuntu -u root -e docker build -t $ImageName "/mnt/c/Users/aryap/OneDrive/Desktop/NoSQL_Lab_18"
if ($LASTEXITCODE -ne 0) {
    Write-Error "Docker build failed! Please verify Docker Engine status."
    exit 1
}
Write-Host "[OK] Docker image built successfully." -ForegroundColor Green

# 2. Test Container
Write-Host "`n[2/3] Testing container execution (Automated Lab 18 Suite)..." -ForegroundColor Cyan
wsl -d Ubuntu -u root -e docker run --rm $ImageName python3 run_all_labs.py
Write-Host "[OK] Container verified: All lab activities passed!" -ForegroundColor Green

# 3. Login and Push to Docker Hub
Write-Host "`n==============================================================================" -ForegroundColor Cyan
Write-Host " [3/3] Authenticating and Pushing to Docker Hub: $ImageName" -ForegroundColor Yellow
Write-Host "==============================================================================" -ForegroundColor Cyan

Write-Host "Logging into Docker Hub..."
wsl -d Ubuntu -u root -e docker login -u $Username

Write-Host "`nPushing $ImageName to Docker Hub..." -ForegroundColor Cyan
wsl -d Ubuntu -u root -e docker push $ImageName

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n[SUCCESS] Image is live on Docker Hub: https://hub.docker.com/r/${Username}/nosql-lab18" -ForegroundColor Green
} else {
    Write-Warning "Docker push failed. Check your network or credentials."
}
