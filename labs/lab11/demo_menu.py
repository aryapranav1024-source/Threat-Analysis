"""
Interactive Demonstration Menu for Lab 11: MongoDB Sharding & Shard Key Optimization
Author: K. Pranav Reddy (24BTRCL098)
Course: NoSQL Databases Using MongoDB
Docker Hub: aryapranav1024/mongodb-lab-11:latest
"""

import os
import sys
import subprocess

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def clear():
    os.system("cls" if os.name == "nt" else "clear")


def print_header():
    print("=" * 76)
    print("  NOSQL DATABASES (MONGODB) - LAB 11 DEMONSTRATION SUITE")
    print("  Student: K. Pranav Reddy  |  Roll: 24BTRCL098")
    print("  Topic  : Shard Key Selection, Hotspot Detection & Resharding")
    print("  Docker : aryapranav1024/mongodb-lab-11:latest")
    print("=" * 76)


def run_script(script_name):
    script_path = os.path.join(SCRIPT_DIR, script_name)
    print(f"\n>>> Executing {script_name}...\n")
    try:
        subprocess.run([sys.executable, script_path], check=True)
    except Exception as e:
        print(f"\n[Error executing {script_name}]: {e}")
    input("\nPress Enter to return to main menu...")


def display_topology():
    print("\n" + "=" * 76)
    print("  MONGODB SHARDED CLUSTER ARCHITECTURE")
    print("=" * 76)
    print("""
                   +----------------------------------+
                   |   Client Application / Driver    |
                   +-----------------+----------------+
                                     |
                                     v
                   +----------------------------------+
                   |    mongos Query Router (:27017)   |
                   +--------+----------------+--------+
                            |                |
             +--------------+                +---------------+
             |                                               |
             v                                               v
    +------------------+                            +------------------+
    | Shard A (:27018) |                            | Shard B (:27020) |
    | ReplSet: shard1  |                            | ReplSet: shard2  |
    +--------+---------+                            +--------+---------+
             |                                               |
             | [hotspot_data: 95.2% docs]                    | [hotspot_data: 4.8% docs]
             | [even_data:    50.1% docs]                    | [even_data:    49.9% docs]
             +-----------------------+-----------------------+
                                     |
                                     v
                   +----------------------------------+
                   | Config Server ReplSet (:27019)   |
                   | Cluster Metadata & Chunk Ranges  |
                   +----------------------------------+
    """)
    input("\nPress Enter to return to main menu...")


def main():
    while True:
        clear()
        print_header()
        print("\nAvailable Demonstrations:")
        print("  [1] Run Lab 11.1: Shard Key Evaluation & Decision Matrix")
        print("  [2] Run Lab 11.2: Shard Key Hotspot Detection & explain() Analysis")
        print("  [3] Run Complete Lab 11 End-to-End Suite")
        print("  [4] Generate Official PDF Submission Report")
        print("  [5] View Sharded Cluster Architecture Diagram")
        print("  [0] Exit")
        print("-" * 76)

        choice = input("Select an option (0-5): ").strip()
        if choice == "1":
            run_script("lab_01_shard_key_eval.py")
        elif choice == "2":
            run_script("lab_02_shard_key_hotspot.py")
        elif choice == "3":
            print("\n>>> Running Complete Lab 11 Suite...\n")
            subprocess.run([sys.executable, os.path.join(SCRIPT_DIR, "lab_01_shard_key_eval.py")])
            subprocess.run([sys.executable, os.path.join(SCRIPT_DIR, "lab_02_shard_key_hotspot.py")])
            input("\nBoth labs completed. Press Enter to return to menu...")
        elif choice == "4":
            run_script("generate_pdf_report.py")
        elif choice == "5":
            display_topology()
        elif choice == "0":
            print("\nExiting Lab 11 Demonstration Suite. Goodbye!\n")
            break
        else:
            input("\nInvalid option. Press Enter to try again...")


if __name__ == "__main__":
    main()
