"""
Automated Test Runner for Lab 10
Executes Lab 10.1, Lab 10.2, and multi_document_transaction.
"""

import sys
import os
import time

# Ensure local imports work
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lab_01_bank_transfer import run_lab_10_1
from lab_02_inventory_reservation import run_lab_10_2
from config.connection import banner


def main():
    banner("Running All Lab 10 Verification Suites")
    start = time.perf_counter()

    print("\n[SUITE 1/2] Starting Lab 10.1: Bank Transfer Transactions...")
    run_lab_10_1()

    print("\n[SUITE 2/2] Starting Lab 10.2: Inventory Reservation & Deadlock Handling...")
    run_lab_10_2()

    total_time = time.perf_counter() - start
    banner(f"All Lab 10 Tasks Completed Successfully in {total_time:.2f}s")


if __name__ == "__main__":
    main()
