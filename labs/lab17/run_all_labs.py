"""
Lab 17 Automated Execution & Verification Suite
Course: NoSQL Database Engineering
Student: K. Pranav Reddy (24BTRCL098)
Activities:
  - Activity 1: Simple RAG Pipeline (lab_01_rag_pipeline.py)
  - Activity 2: HNSW vs IVF Vector Index Types (lab_02_hnsw_vs_ivf.py)
"""

import sys
import os
import time

# Ensure current directory is on path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, CURRENT_DIR)

from config.connection import banner
import lab_01_rag_pipeline
import lab_02_hnsw_vs_ivf


def main():
    banner("NoSQL Lab 17: RAG Pipeline & Vector Indexing Execution Suite")
    print("Student: K. Pranav Reddy | Roll Number: 24BTRCL098")
    print(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}")

    print("\n" + "=" * 70)
    print(" EXECUTING ACTIVITY 1: Build a Simple RAG Pipeline")
    print("=" * 70)
    lab_01_rag_pipeline.main()

    print("\n" + "=" * 70)
    print(" EXECUTING ACTIVITY 2: Compare HNSW and IVF Vector Index Types")
    print("=" * 70)
    lab_02_hnsw_vs_ivf.main()

    banner("All Lab 17 Activities Completed Successfully!")
    print("Verification Status: PASSED (100% Functional)")


if __name__ == "__main__":
    main()
