FROM mongo:7.0

LABEL maintainer="K. Pranav Reddy <24btrcl098@university.edu>"
LABEL description="MongoDB Lab 15: Multi-Tenant SaaS Architecture & Tenant Migration"

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    dos2unix \
    procps \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install --no-cache-dir pymongo rich fastapi uvicorn

WORKDIR /app
COPY . /app

RUN dos2unix /app/entrypoint.sh && chmod +x /app/entrypoint.sh

EXPOSE 27017

ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["python3", "lab_01_multitenant_api.py"]
