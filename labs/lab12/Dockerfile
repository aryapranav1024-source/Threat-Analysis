# ==============================================================================
# Dockerfile: MongoDB Security Lab 12 (Authentication, RBAC, TLS Encryption)
# Course: NoSQL Databases Using MongoDB
# Student: K. Pranav Reddy (24BTRCL098)
# ==============================================================================

FROM mongo:7.0

LABEL maintainer="K. Pranav Reddy <24btrcl098@university.edu>"
LABEL description="MongoDB Security Lab 12: Authentication, RBAC, Field Redaction, and TLS Encryption in Transit"
LABEL version="1.0"

# Install Python3, pip, OpenSSL, and utilities
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        python3 \
        python3-pip \
        openssl \
        procps \
        curl \
        nano && \
    rm -rf /var/lib/apt/lists/*

# Install PyMongo and Cryptography for TLS & security verification
RUN pip3 install --no-cache-dir pymongo cryptography

# Set working directory
WORKDIR /lab12

# Copy lab source files and scripts
COPY lab_01_rbac_setup.sh /lab12/lab_01_rbac_setup.sh
COPY rbac_field_redaction.py /lab12/rbac_field_redaction.py
COPY generate_certs.sh /lab12/generate_certs.sh
COPY generate_certs.py /lab12/generate_certs.py
COPY lab_02_tls_setup.sh /lab12/lab_02_tls_setup.sh
COPY lab_02_tls_pymongo.py /lab12/lab_02_tls_pymongo.py
COPY test_security_suite.py /lab12/test_security_suite.py
COPY run_all_labs.sh /lab12/run_all_labs.sh
COPY entrypoint.sh /lab12/entrypoint.sh
COPY ["Threat Modelling.jpg", "/lab12/threat_modelling.jpg"]
COPY README.md /lab12/README.md

# Make scripts executable
RUN chmod +x /lab12/*.sh

# Pre-generate PKI certificates during image build
RUN mkdir -p /lab12/tls && bash /lab12/generate_certs.sh /lab12/tls

# Expose ports:
# 27017: MongoDB Auth / RBAC Instance
# 27100: MongoDB TLS-Enforced Instance
EXPOSE 27017 27100

# Set Entrypoint
ENTRYPOINT ["/bin/bash", "/lab12/entrypoint.sh"]
