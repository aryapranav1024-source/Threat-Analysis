"""Activity 3.1 (Try It Yourself) - Course Prerequisite Tracking
Design decision: Referenced vs Embedded Prerequisites in MongoDB.
Demonstrates prerequisite graph traversal ($graphLookup) and eligibility checks.
"""

import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.connection import get_db, banner, print_json
from bson import json_util


COURSES_WITH_PREREQUISITES = [
    {
        "code": "CS101",
        "title": "Introduction to Programming",
        "instructor": "Dr. Sarah Jenkins",
        "credits": 4,
        "prerequisites": [],  # Fundamental course, no prerequisites
        "schedule": {"days": ["Monday", "Wednesday"], "time": "09:00-10:30", "room": "LH-101"},
        "enrolled_students": [
            {"student_id": "STU1001", "name": "Arjun Mehta", "grade": "A"}
        ]
    },
    {
        "code": "MATH201",
        "title": "Linear Algebra & Calculus",
        "instructor": "Dr. Ramanujan Iyer",
        "credits": 4,
        "prerequisites": [],
        "schedule": {"days": ["Tuesday", "Thursday"], "time": "10:00-11:30", "room": "LH-105"},
        "enrolled_students": [
            {"student_id": "STU1001", "name": "Arjun Mehta", "grade": "A-"},
            {"student_id": "STU1002", "name": "Sneha Reddy", "grade": "B+"}
        ]
    },
    {
        "code": "CS201",
        "title": "Data Structures & Algorithms",
        "instructor": "Dr. Sarah Jenkins",
        "credits": 4,
        "prerequisites": ["CS101"],  # Referenced prerequisite
        "schedule": {"days": ["Monday", "Wednesday"], "time": "11:00-12:30", "room": "LH-102"},
        "enrolled_students": [
            {"student_id": "STU1001", "name": "Arjun Mehta", "grade": "A"},
            {"student_id": "STU1003", "name": "Rahul Kumar", "grade": "B"}
        ]
    },
    {
        "code": "AIML101",
        "title": "Introduction to Machine Learning",
        "instructor": "Dr. Priya Sharma",
        "credits": 4,
        "prerequisites": ["CS201", "MATH201"],  # Multiple prerequisites
        "schedule": {"days": ["Monday", "Wednesday"], "time": "14:00-15:30", "room": "LH-201"},
        "enrolled_students": [
            {"student_id": "STU1001", "name": "Arjun Mehta", "grade": "A"},
            {"student_id": "STU1002", "name": "Sneha Reddy", "grade": "B+"}
        ]
    },
    {
        "code": "AIML301",
        "title": "Deep Learning with PyTorch",
        "instructor": "Dr. Anil Gupta",
        "credits": 3,
        "prerequisites": ["AIML101"],  # Multi-level transitive prerequisite
        "schedule": {"days": ["Tuesday", "Thursday"], "time": "14:00-15:30", "room": "LH-305"},
        "enrolled_students": [
            {"student_id": "STU1001", "name": "Arjun Mehta", "grade": None}
        ]
    }
]


def print_architectural_justification():
    print("=" * 80)
    print("ARCHITECTURAL JUSTIFICATION: EMBEDDING VS REFERENCING PREREQUISITES")
    print("=" * 80)
    justification = """
1. Decision: REFERENCING (Array of Course Codes/IDs) is the optimal design choice.
2. Why Full Embedding is Problematic for Prerequisites:
   - Duplication & Stale Data: A foundational course like CS101 serves as a prerequisite
     for 20+ courses. Embedding the full course document inside each downstream course
     would duplicate instructors, credits, and syllabus across dozens of records. Any update
     to CS101 would require updating every dependent course document.
   - Circular/Recursive Dependency: Advanced courses have multi-tier prerequisite trees
     (AIML301 -> AIML101 -> CS201 -> CS101). Embedding deep hierarchies leads to unbounded
     document nesting and circular reference risks.
3. Why Referencing Works Best:
   - Direct Lookup: Simple arrays of course codes (e.g. ['CS201', 'MATH201']) keep parent
     documents compact and lightning fast.
   - Graph Traversal ($graphLookup): MongoDB natively supports recursive tree exploration
     across referenced keys in a single aggregation pipeline.
   - Single Source of Truth: Each course definition exists once and is referenced everywhere.
"""
    print(justification)
    print("=" * 80 + "\n")


def main():
    banner("Activity 3.1: Prerequisite Tracking (Try It Yourself)")
    print_architectural_justification()

    db = get_db("nosql_labs")
    col = db["courses_prerequisites"]
    col.drop()

    # Insert courses with prerequisite references
    col.insert_many(COURSES_WITH_PREREQUISITES)
    print(f"[OK] Inserted {len(COURSES_WITH_PREREQUISITES)} courses with prerequisite relationships.\n")

    # Query 1: Direct Prerequisites
    target_code = "AIML101"
    print(f"=== Query 1: Direct Prerequisites for '{target_code}' ===")
    course = col.find_one({"code": target_code}, {"title": 1, "code": 1, "prerequisites": 1, "_id": 0})
    print(f"  Course: {course['title']} ({course['code']})")
    print(f"  Direct Prerequisite Codes: {course['prerequisites']}")
    if course['prerequisites']:
        prereq_details = list(col.find({"code": {"$in": course['prerequisites']}}, {"title": 1, "code": 1, "_id": 0}))
        for p in prereq_details:
            print(f"    -> [{p['code']}] {p['title']}")

    # Query 2: Full Prerequisite Tree using $graphLookup (Transitive Closure)
    advanced_code = "AIML301"
    print(f"\n=== Query 2: Complete Recursive Prerequisite Tree for '{advanced_code}' ($graphLookup) ===")
    pipeline = [
        {"$match": {"code": advanced_code}},
        {
            "$graphLookup": {
                "from": "courses_prerequisites",
                "startWith": "$prerequisites",
                "connectFromField": "prerequisites",
                "connectToField": "code",
                "as": "all_prerequisites_tree",
                "depthField": "level"
            }
        },
        {
            "$project": {
                "code": 1,
                "title": 1,
                "direct_prereqs": "$prerequisites",
                "all_prerequisites_tree.code": 1,
                "all_prerequisites_tree.title": 1,
                "all_prerequisites_tree.level": 1,
                "_id": 0
            }
        }
    ]
    result = list(col.aggregate(pipeline))
    if result:
        res = result[0]
        print(f"  Target Course: {res['title']} ({res['code']})")
        print(f"  Direct Prerequisites: {res['direct_prereqs']}")
        print("  All Required Prerequisite Courses (Traversed recursively):")
        sorted_tree = sorted(res["all_prerequisites_tree"], key=lambda x: x["level"])
        for item in sorted_tree:
            print(f"    [Tier {item['level'] + 1}] {item['code']}: {item['title']}")

    # Query 3: Student Eligibility Verification Check
    print("\n=== Query 3: Student Enrollment Eligibility Check ===")
    student_record = {
        "student_id": "STU1002",
        "name": "Sneha Reddy",
        "completed_courses": ["MATH201"]  # Has only MATH201, missing CS201 & CS101
    }
    course_to_enroll = "AIML101"
    req_course = col.find_one({"code": course_to_enroll})
    required_prereqs = set(req_course["prerequisites"])
    completed = set(student_record["completed_courses"])
    missing_prereqs = required_prereqs - completed

    print(f"  Student: {student_record['name']} (Completed: {student_record['completed_courses']})")
    print(f"  Applying for: {req_course['title']} ({course_to_enroll})")
    print(f"  Required Prerequisites: {list(required_prereqs)}")
    if not missing_prereqs:
        print("  Status: [APPROVED] Student meets all prerequisites.")
    else:
        print(f"  Status: [REJECTED] Missing required prerequisite(s): {list(missing_prereqs)}")

    # Export collection to JSON
    json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "lab_01_try_yourself.json")
    all_docs = list(col.find())
    with open(json_path, "w", encoding="utf-8") as f:
        f.write(json_util.dumps(all_docs, indent=2))
    print(f"\n[OK] Exported {len(all_docs)} documents to '{os.path.basename(json_path)}'")

    banner("Activity 3.1 Complete")


if __name__ == "__main__":
    main()
