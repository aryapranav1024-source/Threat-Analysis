@echo off
REM ==============================================================================
REM Script to build, test, and push the MongoDB Security Lab 12 Docker image
REM Student: K. Pranav Reddy (24BTRCL098)
REM ==============================================================================

set DEFAULT_USER=pranav24btrcl098
set /p DOCKER_USER="Enter your Docker Hub username [default: %DEFAULT_USER%]: "
if "%DOCKER_USER%"=="" set DOCKER_USER=%DEFAULT_USER%

set IMAGE_NAME=%DOCKER_USER%/mongodb-security-lab12:latest

echo.
echo ==============================================================================
echo Building Docker image: %IMAGE_NAME%
echo ==============================================================================
docker build -t %IMAGE_NAME% .

if errorlevel 1 (
    echo [ERROR] Docker build failed. Ensure Docker Desktop is running!
    pause
    exit /b 1
)

echo.
echo [OK] Docker build succeeded!
echo.
echo ==============================================================================
echo Testing Docker container locally (Automated Security Suite)...
echo ==============================================================================
docker run --rm %IMAGE_NAME% /lab12/run_all_labs.sh

echo.
echo ==============================================================================
echo Pushing image to Docker Hub: %IMAGE_NAME%
echo ==============================================================================
echo Logging in to Docker Hub (if not already logged in)...
docker login

echo Pushing %IMAGE_NAME%...
docker push %IMAGE_NAME%

if errorlevel 1 (
    echo [ERROR] Docker push failed. Please check your credentials or network.
    pause
    exit /b 1
)

echo.
echo ==============================================================================
echo SUCCESS! Docker image is live on Docker Hub:
echo https://hub.docker.com/r/%DOCKER_USER%/mongodb-security-lab12
echo ==============================================================================
pause
