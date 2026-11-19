# ==============================================================================
# Dockerfile: NoSQL Lab 18 - Comparative Capstone Benchmark & Analysis
# Course: NoSQL Database Engineering (Lab 18 / Capstone)
# Student: K. Pranav Reddy (24BTRCL098)
#
# Activities:
#   Activity 1 - Comparative Capstone Benchmark (lab_01_comparative_capstone.py)
#   Activity 2 - Comparative Analysis Report (lab_02_comparative_report.py)
# ==============================================================================

FROM mongo:7.0

LABEL maintainer="K. Pranav Reddy <24btrcl098@university.edu>"
LABEL description="NoSQL Lab 18: Comparative Capstone Benchmark & Technical Report"
LABEL version="1.0"
LABEL course="NoSQL Database Engineering"
LABEL student="K. Pranav Reddy - 24BTRCL098"

# Install Python 3, pip, and required system tools
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        python3 \
        python3-pip \
        dos2unix \
        curl \
        procps && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
# - pymongo:   MongoDB official Python driver
# - rich:      Terminal table and formatting engine
# - reportlab: Publication-quality PDF generation engine
RUN pip3 install --no-cache-dir \
    pymongo \
    rich \
    reportlab

# Set working directory
WORKDIR /app

# Copy lab source files
COPY lab_01_comparative_capstone.py /app/lab_01_comparative_capstone.py
COPY lab_02_comparative_report.py   /app/lab_02_comparative_report.py
COPY generate_pdf_report.py         /app/generate_pdf_report.py
COPY run_all_labs.py                /app/run_all_labs.py
COPY entrypoint.sh                  /app/entrypoint.sh
COPY LAB_18_REPORT.md               /app/LAB_18_REPORT.md

# Ensure reports directory exists
RUN mkdir -p /app/reports

# Fix line endings and permissions
RUN dos2unix /app/entrypoint.sh && \
    chmod +x /app/entrypoint.sh

# Expose MongoDB port
EXPOSE 27017

ENTRYPOINT ["/app/entrypoint.sh"]
