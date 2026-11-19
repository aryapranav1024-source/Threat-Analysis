"""
NoSQL Capstone Lab 18 - Complete Test Runner
File: run_all_labs.py
Author: K. Pranav Reddy (24BTRCL098)
Docker Hub: aryapranav1024/nosql-lab18:latest

Executes both activities in sequence:
- Activity 1: Comparative Capstone Lab (lab_01_comparative_capstone.py)
- Activity 2: Comparative Analysis Report Generator (lab_02_comparative_report.py)
"""

import sys
import os
import subprocess

def run_script(script_name: str, desc: str) -> bool:
    print("\n" + "=" * 80)
    print(f"  RUNNING: {desc} ({script_name})")
    print("=" * 80)
    
    script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), script_name)
    res = subprocess.run([sys.executable, script_path], check=False)
    if res.returncode == 0:
        print(f"[OK] {script_name} completed successfully.")
        return True
    else:
        print(f"[FAILED] {script_name} exited with return code {res.returncode}")
        return False

def main():
    print("*" * 80)
    print("  NoSQL Lab 18: Comparative Capstone & Technical Analysis Report")
    print("  Student: K. Pranav Reddy (24BTRCL098)")
    print("  Docker Hub: https://hub.docker.com/r/aryapranav1024/nosql-lab18")
    print("*" * 80)

    success_1 = run_script("lab_01_comparative_capstone.py", "Activity 1 - Comparative Benchmark")
    success_2 = run_script("lab_02_comparative_report.py", "Activity 2 - Comparative Report Generator")

    print("\n" + "=" * 80)
    print("  LAB 18 AUTOMATED SUITE SUMMARY")
    print("=" * 80)
    print(f"  Activity 1 (lab_01_comparative_capstone.py) : {'[PASSED]' if success_1 else '[FAILED]'}")
    print(f"  Activity 2 (lab_02_comparative_report.py)    : {'[PASSED]' if success_2 else '[FAILED]'}")

    if success_1 and success_2:
        print("\n[ALL TESTS PASSED] Ready for Docker deployment and submission.")
        sys.exit(0)
    else:
        print("\n[TESTS FAILED] One or more lab activities encountered an error.")
        sys.exit(1)

if __name__ == "__main__":
    main()
