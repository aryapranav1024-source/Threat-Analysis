"""Lab 3.1 - Design an Embedded Document Schema
Course enrollment with embedded students, schedule, and JSON Schema validation.
"""

import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.connection import get_db, banner, print_json
from bson import json_util


COURSES = [
    {
        "title": "Introduction to Machine Learning",
        "code": "AIML101",
        "instructor": "Dr. Priya Sharma",
        "credits": 4,
        "schedule": {
            "days": ["Monday", "Wednesday"],
            "time": "10:00-11:30",
            "room": "LH-201"
        },
        "enrolled_students": [
            {"student_id": "STU1001", "name": "Arjun Mehta", "grade": "A"},
            {"student_id": "STU1002", "name": "Sneha Reddy", "grade": "B+"},
            {"student_id": "STU1003", "name": "Rahul Kumar", "grade": "A-"},
            {"student_id": "STU1004", "name": "Divya Patel", "grade": "B"}
        ]
    },
    {
        "title": "Deep Learning with PyTorch",
        "code": "AIML301",
        "instructor": "Dr. Anil Gupta",
        "credits": 3,
        "schedule": {
            "days": ["Tuesday", "Thursday"],
            "time": "14:00-15:30",
            "room": "LH-305"
        },
        "enrolled_students": [
            {"student_id": "STU1001", "name": "Arjun Mehta", "grade": None},
            {"student_id": "STU1005", "name": "Kavya Nair", "grade": "A"},
            {"student_id": "STU1006", "name": "Vikram Singh", "grade": "A+"}
        ]
    },
    {
        "title": "Natural Language Processing",
        "code": "AIML201",
        "instructor": "Dr. Priya Sharma",
        "credits": 3,
        "schedule": {
            "days": ["Monday", "Wednesday", "Friday"],
            "time": "09:00-10:00",
            "room": "LH-102"
        },
        "enrolled_students": [
            {"student_id": "STU1002", "name": "Sneha Reddy", "grade": "B+"},
            {"student_id": "STU1003", "name": "Rahul Kumar", "grade": None},
            {"student_id": "STU1007", "name": "Priya Das", "grade": "A-"},
            {"student_id": "STU1001", "name": "Arjun Mehta", "grade": None},
            {"student_id": "STU1008", "name": "Neha Gupta", "grade": "B"}
        ]
    }
]

# JSON Schema for validation
COURSE_VALIDATOR = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": ["title", "code", "instructor", "schedule", "enrolled_students"],
        "properties": {
            "title": {
                "bsonType": "string",
                "description": "Course title is required and must be a string"
            },
            "code": {
                "bsonType": "string",
                "pattern": r"^[A-Z]{2,4}\d{3}$",
                "description": "Course code format: e.g. CS401 or AIML101"
            },
            "instructor": {
                "bsonType": "string",
                "description": "Instructor name is required and must be a string"
            },
            "credits": {
                "bsonType": "int",
                "minimum": 1,
                "maximum": 6,
                "description": "Credits must be an integer between 1 and 6"
            },
            "schedule": {
                "bsonType": "object",
                "required": ["days", "time", "room"],
                "properties": {
                    "days": {
                        "bsonType": "array",
                        "items": {"bsonType": "string"}
                    },
                    "time": {"bsonType": "string"},
                    "room": {"bsonType": "string"}
                }
            },
            "enrolled_students": {
                "bsonType": "array",
                "items": {
                    "bsonType": "object",
                    "required": ["student_id", "name"],
                    "properties": {
                        "student_id": {"bsonType": "string"},
                        "name": {"bsonType": "string"},
                        "grade": {"bsonType": ["string", "null"]}
                    }
                }
            }
        }
    }
}


def main():
    banner("Lab 3.1: Embedded Document Schema Design")
    db = get_db("nosql_labs")

    # Drop and recreate collection with schema validation
    if "courses" in db.list_collection_names():
        db.drop_collection("courses")
    db.create_collection("courses", validator=COURSE_VALIDATOR)
    col = db["courses"]
    print("[OK] Created 'courses' collection with JSON Schema validation.\n")

    # Step 1: Insert 3 course documents
    col.insert_many(COURSES)
    print(f"[OK] Successfully inserted {len(COURSES)} course documents.\n")

    # Step 2: Query for all courses that meet on Monday
    print("=== Step 1 Query: Courses that meet on Monday ===")
    monday_courses = col.find(
        {"schedule.days": "Monday"},
        {"title": 1, "code": 1, "schedule.days": 1, "schedule.time": 1, "schedule.room": 1, "_id": 0}
    )
    for c in monday_courses:
        print(f"  [{c['code']}] {c['title']} | Days: {', '.join(c['schedule']['days'])} | Time: {c['schedule']['time']} | Room: {c['schedule']['room']}")

    # Step 3: Query for all students enrolled in courses taught by a specific instructor
    target_instructor = "Dr. Priya Sharma"
    print(f"\n=== Step 3 Query: Students in courses taught by '{target_instructor}' ===")
    instructor_courses = col.find(
        {"instructor": target_instructor},
        {"title": 1, "code": 1, "enrolled_students": 1, "_id": 0}
    )
    for course in instructor_courses:
        print(f"\n  Course: {course['title']} ({course['code']})")
        print(f"  Total Enrolled: {len(course['enrolled_students'])}")
        for stu in course["enrolled_students"]:
            grade_str = stu['grade'] if stu['grade'] is not None else 'In Progress'
            print(f"    - ID: {stu['student_id']:<8} | Name: {stu['name']:<15} | Grade: {grade_str}")

    # Step 4: Test Schema Validation enforcement
    print("\n=== Testing Schema Validation Enforcement ===")
    invalid_doc = {
        "title": "Invalid Course Without Required Fields",
        "credits": 3
    }
    try:
        col.insert_one(invalid_doc)
        print("  [FAIL] Document without required fields was inserted unexpectedly.")
    except Exception as e:
        print("  [SUCCESS] Schema validation rejected invalid document as expected.")
        if hasattr(e, "details") and e.details and "errmsg" in e.details:
            print(f"  Validation Message: {e.details['errmsg']}")
        else:
            print(f"  Validation Error: {str(e)[:100]}")

    # Export documents to JSON
    json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "lab_01_embedded_schema.json")
    all_docs = list(col.find())
    with open(json_path, "w", encoding="utf-8") as f:
        f.write(json_util.dumps(all_docs, indent=2))
    print(f"\n[OK] Exported {len(all_docs)} documents to '{os.path.basename(json_path)}'")

    banner("Lab 3.1 Complete")


if __name__ == "__main__":
    main()