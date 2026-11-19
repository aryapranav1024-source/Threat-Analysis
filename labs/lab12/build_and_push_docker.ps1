# PowerShell Script to build, test, and push MongoDB Security Lab 12 Docker Image
# Student: K. Pranav Reddy (24BTRCL098)

param(
    [string]$Username = "pranav24btrcl098"
)

$ImageName = "${Username}/mongodb-security-lab12:latest"

Write-Host "==============================================================================" -ForegroundColor Cyan
Write-Host " Building Docker image: $ImageName" -ForegroundColor Yellow
Write-Host "==============================================================================" -ForegroundColor Cyan

docker build -t $ImageName .
if ($LASTEXITCODE -ne 0) {
    Write-Error "Docker build failed! Please check if Docker Desktop is running."
    exit 1
}

Write-Host "`n[OK] Docker build succeeded! Testing container with automated test suite..." -ForegroundColor Green
docker run --rm $ImageName /lab12/run_all_labs.sh

Write-Host "`n==============================================================================" -ForegroundColor Cyan
Write-Host " Pushing Docker image to Docker Hub: $ImageName" -ForegroundColor Yellow
Write-Host "==============================================================================" -ForegroundColor Cyan

docker login
docker push $ImageName

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n[SUCCESS] Image is live on Docker Hub: https://hub.docker.com/r/${Username}/mongodb-security-lab12" -ForegroundColor Green
} else {
    Write-Warning "Docker push failed. Check your network or credentials."
}
