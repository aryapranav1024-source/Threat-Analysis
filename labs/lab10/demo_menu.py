#!/usr/bin/env python3
"""
Interactive Demonstration Suite: NoSQL MongoDB Lab 10
======================================================
Transactions, Atomicity, Durability & Deadlock Handling
Docker Repository: aryapranav1024/mongodb-lab-10:latest
Student: K. Pranav Reddy (24BTRCL098)
"""

import os
import sys
import subprocess
import time


def clear():
    os.system("clear" if os.name == "posix" else "cls")


def banner():
    print("=" * 78)
    print("    NoSQL MongoDB Lab 10: Multi-Document Transactions & Concurrency")
    print("    Docker Image: aryapranav1024/mongodb-lab-10:latest")
    print("    Student: K. Pranav Reddy | Roll No: 24BTRCL098")
    print("=" * 78)


def menu():
    while True:
        clear()
        banner()
        print("\n  Select a Demonstration Task:\n")
        print("  [1] Lab 10.1: Bank Transfer Transaction (ACID, Rollback & Exponential Backoff)")
        print("  [2] Lab 10.2: Inventory Reservation (Contention, Optimistic Locking & Retries)")
        print("  [3] Lab 10.2: Run Concurrency Throughput Benchmark (1, 4, 8, 16 Threads)")
        print("  [4] Run Sample Multi-Document Transaction Script")
        print("  [5] Run ALL Verification Suites Sequentially")
        print("  [6] Open MongoDB Interactive Shell (mongosh)")
        print("  [7] Open Bash Shell in Container")
        print("  [0] Exit Demonstration")
        print("\n" + "-" * 78)

        choice = input("  Enter option [0-7]: ").strip()

        if choice == "1":
            clear()
            print("Running Lab 10.1: Bank Transfer Transaction...")
            subprocess.run([sys.executable, "lab_01_bank_transfer.py"])
            input("\nPress Enter to return to menu...")
        elif choice == "2":
            clear()
            print("Running Lab 10.2: Inventory Reservation...")
            subprocess.run([sys.executable, "lab_02_inventory_reservation.py"])
            input("\nPress Enter to return to menu...")
        elif choice == "3":
            clear()
            print("Running Concurrency Benchmark...")
            from lab_02_inventory_reservation import benchmark_concurrency_throughput
            from pymongo import MongoClient
            client = MongoClient(os.getenv("MONGO_URI", "mongodb://localhost:27017/?replicaSet=rs0&directConnection=true"))
            benchmark_concurrency_throughput(client)
            client.close()
            input("\nPress Enter to return to menu...")
        elif choice == "4":
            clear()
            print("Running multi_document_transaction.py...")
            subprocess.run([sys.executable, "multi_document_transaction.py"])
            input("\nPress Enter to return to menu...")
        elif choice == "5":
            clear()
            print("Running all verification suites...")
            subprocess.run([sys.executable, "run_all.py"])
            input("\nPress Enter to return to menu...")
        elif choice == "6":
            print("\nLaunching mongosh connected to replica set rs0...")
            subprocess.run(["mongosh", os.getenv("MONGO_URI", "mongodb://localhost:27017/?replicaSet=rs0&directConnection=true")])
            input("\nPress Enter to return to menu...")
        elif choice == "7":
            shell = "/bin/bash" if os.path.exists("/bin/bash") else "powershell"
            print(f"\nEntering {shell}. Type 'exit' to return to menu.\n")
            subprocess.run([shell])
        elif choice == "0":
            print("\nExiting demonstration suite. Thank you!")
            break
        else:
            print("\nInvalid choice. Please select from the menu.")
            time.sleep(1)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        if "10.1" in arg or "bank" in arg:
            subprocess.run([sys.executable, "lab_01_bank_transfer.py"])
        elif "10.2" in arg or "inventory" in arg:
            subprocess.run([sys.executable, "lab_02_inventory_reservation.py"])
        elif "all" in arg:
            subprocess.run([sys.executable, "run_all.py"])
        else:
            subprocess.run(sys.argv[1:])
    else:
        menu()
