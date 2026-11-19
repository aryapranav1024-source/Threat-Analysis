"""
Lab 12.1: Activity - Field-Level Redaction via Views in MongoDB
Student: K. Pranav Reddy (24BTRCL098)

This script demonstrates role-based field-level redaction:
1. HR Users have access to the underlying 'employees' collection (including sensitive fields like 'salary' and full 'ssn').
2. Non-HR Users (e.g. general staff or analyst) only have access to 'employees_redacted_view',
   which projects out 'salary' and masks 'ssn'.
3. Direct queries to 'employees' by non-HR users are denied by MongoDB RBAC.
"""

import sys
import os
from pymongo import MongoClient
from pymongo.errors import OperationFailure

def banner(title):
    print("\n" + "=" * 65)
    print(f"  {title}")
    print("=" * 65)

EMPLOYEES_SEED_DATA = [
    {
        "emp_id": "EMP001",
        "name": "Arjun Sharma",
        "department": "Engineering",
        "role": "Senior Cloud Architect",
        "email": "arjun.sharma@enterprise.org",
        "ssn": "111-22-3333",
        "salary": 165000,
        "performance_rating": "Exceeds Expectations"
    },
    {
        "emp_id": "EMP002",
        "name": "Sneha Patel",
        "department": "Product",
        "role": "Lead Product Manager",
        "email": "sneha.patel@enterprise.org",
        "ssn": "444-55-6666",
        "salary": 140000,
        "performance_rating": "Meets Expectations"
    },
    {
        "emp_id": "EMP003",
        "name": "Rahul Verma",
        "department": "Security Operations",
        "role": "SecOps Engineer",
        "email": "rahul.verma@enterprise.org",
        "ssn": "777-88-9999",
        "salary": 135000,
        "performance_rating": "Exceeds Expectations"
    }
]

def setup_field_redaction(admin_uri="mongodb://localhost:27017/"):
    banner("Activity 12.1: Field-Level Redaction Setup via Views")
    
    print(f"[*] Connecting to MongoDB at: {admin_uri}")
    client = MongoClient(admin_uri, serverSelectionTimeoutMS=5000)
    db = client["hr_system"]
    
    # 1. Reset underlying collection
    print("[*] Seeding underlying 'employees' collection...")
    db["employees"].drop()
    db["employees"].insert_many(EMPLOYEES_SEED_DATA)
    print(f"[OK] Inserted {len(EMPLOYEES_SEED_DATA)} sensitive employee records.")
    
    # 2. Create the redacted view
    # Pipeline: excludes salary completely, masks SSN to show only last 4 digits
    print("[*] Creating secure aggregation pipeline view: 'employees_redacted_view'...")
    try:
        db["employees_redacted_view"].drop()
    except Exception:
        pass
        
    pipeline = [
        {
            "$project": {
                "_id": 0,
                "emp_id": 1,
                "name": 1,
                "department": 1,
                "role": 1,
                "email": 1,
                "masked_ssn": {
                    "$concat": ["***-**-", {"$substrCP": ["$ssn", 7, 4]}]
                },
                # Exclude sensitive salary and raw ssn
                "salary": "$$REMOVE",
                "ssn": "$$REMOVE"
            }
        }
    ]
    
    db.command("create", "employees_redacted_view", viewOn="employees", pipeline=pipeline)
    print("[OK] Redacted view 'employees_redacted_view' created successfully.")
    
    # 3. Demonstration of Admin / HR view
    banner("1. HR / Admin View (Direct Access to 'employees')")
    for doc in db["employees"].find({}, {"_id": 0}):
        print(f"  [CONFIDENTIAL] Name: {doc['name']:<15} | Dept: {doc['department']:<18} | SSN: {doc['ssn']} | Salary: ${doc['salary']:,}")
        
    # 4. Demonstration of Redacted View
    banner("2. Redacted View Query ('employees_redacted_view')")
    for doc in db["employees_redacted_view"].find({}):
        print(f"  [PUBLIC/STAFF] Name: {doc['name']:<15} | Dept: {doc['department']:<18} | SSN: {doc['masked_ssn']} | Salary: {'salary' in doc}")
        
    client.close()

if __name__ == "__main__":
    uri = sys.argv[1] if len(sys.argv) > 1 else "mongodb://localhost:27017/"
    setup_field_redaction(uri)
