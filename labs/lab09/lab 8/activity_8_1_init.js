// ============================================================
// Activity 8.1: Respective MongoDB File
// activity_8_1_init.js
// Objective: Initialize 3-node replica set rs0 and verify replication
// ============================================================

print("=================================================");
print("  MongoDB Shell: Initialize Replica Set rs0");
print("=================================================");

// 1. Initialize replica set with 3 data-bearing nodes
try {
  var initRes = rs.initiate({
    _id: "rs0",
    members: [
      { _id: 0, host: "mongo1:27017" },
      { _id: 1, host: "mongo2:27018" },
      { _id: 2, host: "mongo3:27019" }
    ]
  });
  printjson(initRes);
} catch (e) {
  print("Replica set already initialized or notice: " + e.message);
}

print("\nWaiting 10 seconds for election to complete...");
sleep(10000);

// 2. Identify Primary, Secondaries, and Health States
print("\n--- Current Replica Set Status (rs.status()) ---");
var status = rs.status();
status.members.forEach(function(m) {
  print("  Node: " + m.name + " | State: " + m.stateStr + " | Health: " + m.health);
});

// 3. Insert document into Primary
print("\n--- Inserting Document into Primary ---");
use("testdb");
var ins = db.records.insertOne({
  lab: "8.1",
  event: "Replication Verification Test",
  timestamp: new Date()
});
print("Inserted document _id: " + ins.insertedId);

print("\n=================================================");
print("  Initialization and verification complete.");
print("=================================================");
