@echo off
REM Windows Batch Script to build, test, and push NoSQL Lab 18 Docker Image
REM Student: K. Pranav Reddy (24BTRCL098)
REM Docker Hub Image: aryapranav1024/nosql-lab18:latest

set USERNAME=aryapranav1024
set IMAGENAME=%USERNAME%/nosql-lab18:latest

echo ==============================================================================
echo  NoSQL Lab 18: Comparative Capstone Benchmark Docker Automation
echo  Image Target: %IMAGENAME%
echo ==============================================================================

echo.
echo [1/3] Building Docker image (%IMAGENAME%)...
wsl -d Ubuntu -u root -e docker build -t %IMAGENAME% "/mnt/c/Users/aryap/OneDrive/Desktop/NoSQL_Lab_18"
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Docker build failed!
    pause
    exit /b %ERRORLEVEL%
)
echo [OK] Docker image built successfully.

echo.
echo [2/3] Testing container execution (Automated Lab 18 Suite)...
wsl -d Ubuntu -u root -e docker run --rm %IMAGENAME% python3 run_all_labs.py
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Container test failed!
    pause
    exit /b %ERRORLEVEL%
)
echo [OK] Container verified: All lab activities passed!

echo.
echo ==============================================================================
echo  [3/3] Authenticating and Pushing to Docker Hub: %IMAGENAME%
echo ==============================================================================
wsl -d Ubuntu -u root -e docker login -u %USERNAME%
wsl -d Ubuntu -u root -e docker push %IMAGENAME%

if %ERRORLEVEL% EQU 0 (
    echo.
    echo [SUCCESS] Image is live on Docker Hub: https://hub.docker.com/r/%USERNAME%/nosql-lab18
) else (
    echo [WARNING] Docker push encountered an issue. Check network or credentials.
)
pause
