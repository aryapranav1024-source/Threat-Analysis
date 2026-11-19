// ============================================================
// Lab 8.1 - MongoDB Shell Script (rs_init_basic.js)
// Initializes the 3-node replica set rs0
// Run via: docker exec mongo1 mongosh --port 27017 --file rs_init_basic.js
// ============================================================

// Step 1: Initiate the replica set
print("=== Initiating replica set rs0 ===");
var result = rs.initiate({
  _id: "rs0",
  members: [
    { _id: 0, host: "127.0.0.1:27017" },
    { _id: 1, host: "127.0.0.1:27018" },
    { _id: 2, host: "127.0.0.1:27019" }
  ]
});
printjson(result);

// Step 2: Wait for election
print("Waiting 10 seconds for election...");
sleep(10000);

// Step 3: Show replica set status
print("\n=== Replica Set Status ===");
var status = rs.status();
status.members.forEach(function(m) {
  print("  Member:", m.name, "| State:", m.stateStr, "| Health:", m.health);
});

// Step 4: Insert a document on the primary
print("\n=== Inserting document into PRIMARY ===");
use("testdb");
var insertResult = db.testcollection.insertOne({
  message: "Hello from replica set!",
  lab: "8.1",
  timestamp: new Date()
});
print("  Inserted _id:", insertResult.insertedId);

print("\n=== DONE - rs0 initialized and data inserted ===");
