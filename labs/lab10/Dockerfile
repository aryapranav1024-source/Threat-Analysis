FROM mongo:7.0

# Install Python 3, pip, and compilation tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    python3-dev \
    gcc \
    dos2unix \
    && rm -rf /var/lib/apt/lists/*

# Install required python packages (pip 22.0 on Ubuntu 22.04)
RUN pip3 install --no-cache-dir \
    pymongo \
    matplotlib \
    reportlab \
    python-dotenv

WORKDIR /app

# Copy application files
COPY . /app

# Ensure LF line endings and executable flags for shell scripts
RUN dos2unix /app/entrypoint.sh /app/demo_menu.py && \
    chmod +x /app/entrypoint.sh /app/demo_menu.py

EXPOSE 27017

ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["python3", "/app/demo_menu.py"]
