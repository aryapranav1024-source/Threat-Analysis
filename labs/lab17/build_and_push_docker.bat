@echo off
REM ==============================================================================
REM Batch Script to build, test, and push NoSQL Lab 17 Docker Image
REM Student: K. Pranav Reddy (24BTRCL098)
REM ==============================================================================

set DEFAULT_USER=aryapranav1024
set /p DOCKER_USER="Enter your Docker Hub username [default: %DEFAULT_USER%]: "
if "%DOCKER_USER%"=="" set DOCKER_USER=%DEFAULT_USER%

set IMAGE_NAME=%DOCKER_USER%/nosql-lab17:latest

echo.
echo ==============================================================================
echo  NoSQL Lab 17: RAG Pipeline ^& Vector Indexing Docker Automation
echo  Building Image: %IMAGE_NAME%
echo ==============================================================================
wsl -d Ubuntu -u root -e docker build -t %IMAGE_NAME% "/mnt/c/Users/aryap/OneDrive/Desktop/NoSQL_Lab_17"

if errorlevel 1 (
    echo [ERROR] Docker build failed.
    pause
    exit /b 1
)

echo.
echo [OK] Docker build succeeded!
echo.
echo ==============================================================================
echo  Testing Container Execution (Automated Suite)...
echo ==============================================================================
wsl -d Ubuntu -u root -e docker run --rm %IMAGE_NAME% python3 run_all_labs.py

echo.
echo ==============================================================================
echo  Pushing image to Docker Hub: %IMAGE_NAME%
echo ==============================================================================
echo Logging into Docker Hub...
wsl -d Ubuntu -u root -e docker login -u %DOCKER_USER%

echo Pushing %IMAGE_NAME%...
wsl -d Ubuntu -u root -e docker push %IMAGE_NAME%

if errorlevel 1 (
    echo [ERROR] Docker push failed. Please verify your credentials or network.
    pause
    exit /b 1
)

echo.
echo [SUCCESS] Image is live on Docker Hub: https://hub.docker.com/r/%DOCKER_USER%/nosql-lab17
pause
