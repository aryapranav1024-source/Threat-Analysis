#!/bin/bash
set -e

echo "========================================================================"
echo "  MONGODB LAB 13: K8S STATEFULSET & PRODUCTION REPLICA SET IAC"
echo "  Student: K. Pranav Reddy | Roll No: 24BTRCL098"
echo "  Docker Image: aryapranav1024/nosql-lab13:latest"
echo "========================================================================"

echo "[1/2] Generating Kubernetes StatefulSet Manifests..."
python3 lab_02_k8s_statefulset.py || true

echo "[2/2] Displaying Generated Manifests & Architecture..."
ls -la k8s/

echo "========================================================================"
echo "  LAB 13 CONTAINER READY"
echo "========================================================================"
exec "$@"
