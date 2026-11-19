# ==============================================================================
# Dockerfile: NoSQL Lab 17 - RAG Pipeline & Vector Indexing
# Course: NoSQL Database Engineering (Lab 17)
# Student: K. Pranav Reddy (24BTRCL098)
#
# Activities:
#   Activity 1 - Build a Simple RAG Pipeline (lab_01_rag_pipeline.py)
#   Activity 2 - Compare HNSW and IVF Vector Index Types (lab_02_hnsw_vs_ivf.py)
# ==============================================================================

FROM mongo:7.0

LABEL maintainer="K. Pranav Reddy <24btrcl098@university.edu>"
LABEL description="NoSQL Lab 17: RAG Pipeline and Vector Index Comparison (HNSW vs IVF)"
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
# - pymongo: MongoDB driver for lab_01 RAG pipeline
# - numpy:   Vector math for lab_02 HNSW vs IVF
# - rich:    Terminal table rendering used by both labs
RUN pip3 install --no-cache-dir \
    pymongo \
    "numpy>=1.24,<3" \
    rich

# Set working directory
WORKDIR /app

# Copy lab source files
COPY lab_01_rag_pipeline.py /app/lab_01_rag_pipeline.py
COPY lab_02_hnsw_vs_ivf.py  /app/lab_02_hnsw_vs_ivf.py
COPY run_all_labs.py         /app/run_all_labs.py
COPY entrypoint.sh           /app/entrypoint.sh
COPY config/                 /app/config/

# Fix line endings and permissions
RUN dos2unix /app/entrypoint.sh && \
    chmod +x /app/entrypoint.sh

# Expose MongoDB port
EXPOSE 27017

ENTRYPOINT ["/app/entrypoint.sh"]
