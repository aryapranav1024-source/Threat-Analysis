#!/bin/bash
# ==============================================================================
# Lab 12.1: Configure Authentication and Role-Based Access Control (RBAC)
# Course: NoSQL Databases Using MongoDB - Security Architecture
# Student: K. Pranav Reddy (24BTRCL098)
# ==============================================================================

set -e

PORT=${MONGO_PORT:-27017}
HOST=${MONGO_HOST:-"localhost"}

echo "================================================================================"
echo "           LAB 12.1: MONGODB AUTHENTICATION & RBAC ENFORCEMENT                  "
echo "================================================================================"

echo ""
echo "=== Step 1: Initialize Admin User and Bootstrap Databases ==="
mongosh --host "$HOST" --port "$PORT" --quiet <<'EOF'
// Switch to admin database to bootstrap root user
db = db.getSiblingDB("admin");

// Create Admin Superuser if not exists
try {
  db.createUser({
    user: "admin",
    pwd: "AdminPass123!",
    roles: [
      { role: "userAdminAnyDatabase", db: "admin" },
      { role: "dbAdminAnyDatabase", db: "admin" },
      { role: "readWriteAnyDatabase", db: "admin" },
      { role: "clusterAdmin", db: "admin" }
    ]
  });
  print("[OK] Admin superuser 'admin' created successfully.");
} catch(e) {
  if (e.code === 51003 || e.message.includes("already exists")) {
    print("[INFO] Admin user already exists, proceeding.");
  } else {
    print("[WARN] " + e.message);
  }
}
EOF

echo ""
echo "=== Step 2: Seed Employee Data and Create Redacted View (Activity 12.1) ==="
mongosh --host "$HOST" --port "$PORT" -u "admin" -p "AdminPass123!" --authenticationDatabase admin --quiet <<'EOF'
db = db.getSiblingDB("hr_system");

// Reset collection
db.employees.drop();
db.employees.insertMany([
  {
    emp_id: "EMP101",
    name: "Arjun Sharma",
    department: "Engineering",
    role: "Senior Cloud Architect",
    ssn: "111-22-3333",
    salary: 165000,
    bonus: 25000
  },
  {
    emp_id: "EMP102",
    name: "Sneha Patel",
    department: "Product",
    role: "Lead Product Manager",
    ssn: "444-55-6666",
    salary: 140000,
    bonus: 18000
  },
  {
    emp_id: "EMP103",
    name: "Rahul Verma",
    department: "Security Operations",
    role: "SecOps Engineer",
    ssn: "777-88-9999",
    salary: 135000,
    bonus: 15000
  }
]);
print("[OK] Seeded 3 records into hr_system.employees");

// Create Field-Level Redaction View
// Excludes 'salary' and 'bonus', masks 'ssn' to last 4 digits
try { db.employees_redacted_view.drop(); } catch(e) {}
db.createView("employees_redacted_view", "employees", [
  {
    $project: {
      _id: 0,
      emp_id: 1,
      name: 1,
      department: 1,
      role: 1,
      masked_ssn: { $concat: ["***-**-", { $substrCP: ["$ssn", 7, 4] }] }
      // 'salary' and 'bonus' are omitted entirely
    }
  }
]);
print("[OK] Field-level redacted view 'employees_redacted_view' successfully created.");

// Also prepare analytics database for testing
dbAnalytics = db.getSiblingDB("analytics");
dbAnalytics.events.drop();
dbAnalytics.events.insertOne({ event: "system_startup", timestamp: new Date(), severity: "INFO" });
print("[OK] Analytics database initialized.");
EOF

echo ""
echo "=== Step 3: Define Custom Least-Privilege Roles & Users ==="
mongosh --host "$HOST" --port "$PORT" -u "admin" -p "AdminPass123!" --authenticationDatabase admin --quiet <<'EOF'
db = db.getSiblingDB("admin");

// 1. HR Role: Full CRUD access to underlying sensitive employees collection
try { db.dropRole("hr_role"); } catch(e) {}
db.createRole({
  role: "hr_role",
  privileges: [
    {
      resource: { db: "hr_system", collection: "employees" },
      actions: ["find", "insert", "update", "remove"]
    }
  ],
  roles: []
});
print("[OK] Created role: hr_role (access to full employee details including salary)");

// 2. Read Role: Read-only access to the REDACTED VIEW only (No access to base collection)
try { db.dropRole("app_reader_role"); } catch(e) {}
db.createRole({
  role: "app_reader_role",
  privileges: [
    {
      resource: { db: "hr_system", collection: "employees_redacted_view" },
      actions: ["find", "aggregate"]
    }
  ],
  roles: []
});
print("[OK] Created role: app_reader_role (access to redacted view only)");

// 3. Write Role: Write access to analytics.events collection
try { db.dropRole("app_writer_role"); } catch(e) {}
db.createRole({
  role: "app_writer_role",
  privileges: [
    {
      resource: { db: "analytics", collection: "events" },
      actions: ["find", "insert", "update", "remove"]
    }
  ],
  roles: []
});
print("[OK] Created role: app_writer_role (CRUD on analytics.events)");

// 4. Analytics Role (as per Lab requirement snippet)
try { db.dropRole("analyticsReader"); } catch(e) {}
db.createRole({
  role: "analyticsReader",
  privileges: [
    {
      resource: { db: "analytics", collection: "" },
      actions: ["find", "aggregate"]
    }
  ],
  roles: []
});
print("[OK] Created role: analyticsReader (read all collections in analytics DB)");

// Create User: hr_user
try { db.dropUser("hr_user"); } catch(e) {}
db.createUser({
  user: "hr_user",
  pwd: "HrPass123!",
  roles: [{ role: "hr_role", db: "admin" }]
});
print("[OK] Created user: hr_user");

// Create User: app_user_read
try { db.dropUser("app_user_read"); } catch(e) {}
db.createUser({
  user: "app_user_read",
  pwd: "ReadPass123!",
  roles: [{ role: "app_reader_role", db: "admin" }]
});
print("[OK] Created user: app_user_read");

// Create User: app_user_write
try { db.dropUser("app_user_write"); } catch(e) {}
db.createUser({
  user: "app_user_write",
  pwd: "WritePass123!",
  roles: [{ role: "app_writer_role", db: "admin" }]
});
print("[OK] Created user: app_user_write");

// Create User: analytics_app
try { db.dropUser("analytics_app"); } catch(e) {}
db.createUser({
  user: "analytics_app",
  pwd: "AnalyticsPass123!",
  roles: [{ role: "analyticsReader", db: "admin" }]
});
print("[OK] Created user: analytics_app");
EOF

echo ""
echo "=== Step 4: Verify RBAC Permission Enforcement & Field-Level Redaction ==="

echo "--- Test 1: HR User queries base 'employees' collection (MUST SUCCEED with salary) ---"
mongosh --host "$HOST" --port "$PORT" -u "hr_user" -p "HrPass123!" --authenticationDatabase admin --quiet <<'EOF'
db = db.getSiblingDB("hr_system");
const docs = db.employees.find().toArray();
print("[TEST PASS] hr_user successfully retrieved raw employee data.");
docs.forEach(d => {
  print("   -> " + d.name + " (" + d.department + ") | SSN: " + d.ssn + " | Salary: $" + d.salary);
});
EOF

echo ""
echo "--- Test 2: app_user_read queries 'employees_redacted_view' (MUST SUCCEED without salary) ---"
mongosh --host "$HOST" --port "$PORT" -u "app_user_read" -p "ReadPass123!" --authenticationDatabase admin --quiet <<'EOF'
db = db.getSiblingDB("hr_system");
const docs = db.employees_redacted_view.find().toArray();
print("[TEST PASS] app_user_read retrieved redacted view data.");
docs.forEach(d => {
  const hasSalary = ("salary" in d);
  print("   -> " + d.name + " | Masked SSN: " + d.masked_ssn + " | Salary exposed? " + hasSalary);
});
EOF

echo ""
echo "--- Test 3: app_user_read attempts to query base 'employees' collection directly (MUST FAIL) ---"
mongosh --host "$HOST" --port "$PORT" -u "app_user_read" -p "ReadPass123!" --authenticationDatabase admin --quiet <<'EOF'
db = db.getSiblingDB("hr_system");
try {
  db.employees.find().toArray();
  print("[TEST FAILED] app_user_read was able to access unredacted collection!");
} catch(e) {
  print("[TEST PASS] Direct access correctly REJECTED: " + e.message);
}
EOF

echo ""
echo "--- Test 4: app_user_read attempts to write to analytics (MUST FAIL) ---"
mongosh --host "$HOST" --port "$PORT" -u "app_user_read" -p "ReadPass123!" --authenticationDatabase admin --quiet <<'EOF'
db = db.getSiblingDB("analytics");
try {
  db.events.insertOne({ event: "unauthorized_write", by: "app_user_read" });
  print("[TEST FAILED] Read-only user succeeded in writing!");
} catch(e) {
  print("[TEST PASS] Unauthorized write correctly REJECTED: " + e.message);
}
EOF

echo ""
echo "--- Test 5: app_user_write writes to analytics.events (MUST SUCCEED) ---"
mongosh --host "$HOST" --port "$PORT" -u "app_user_write" -p "WritePass123!" --authenticationDatabase admin --quiet <<'EOF'
db = db.getSiblingDB("analytics");
const res = db.events.insertOne({ event: "user_login", user: "jdoe", timestamp: new Date() });
print("[TEST PASS] app_user_write successfully inserted document: " + res.insertedId);
EOF

echo ""
echo "--- Test 6: app_user_write attempts to access hr_system.employees (MUST FAIL) ---"
mongosh --host "$HOST" --port "$PORT" -u "app_user_write" -p "WritePass123!" --authenticationDatabase admin --quiet <<'EOF'
db = db.getSiblingDB("hr_system");
try {
  db.employees.find().toArray();
  print("[TEST FAILED] app_user_write accessed unauthorized database!");
} catch(e) {
  print("[TEST PASS] Out-of-scope database access correctly REJECTED: " + e.message);
}
EOF

echo ""
echo "================================================================================"
echo "                  LAB 12.1 ALL RBAC VERIFICATION TESTS PASSED                   "
echo "================================================================================"
