// ============================================================
// Lab 8.2 - MongoDB Shell Script (rs_failover.js)
// Performs rs.stepDown() and shows election result
//
// Run this WHILE lab_8_2_failover_observer.py is running in another terminal.
// Command: docker exec <primary_container> mongosh --port <port> --file rs_failover.js
//
// For priority-based election (Activity), see rs_priority.js
// ============================================================

print("=== Lab 8.2: Force Failover via rs.stepDown() ===");

// Show current primary before stepDown
print("\n--- Replica Set Status BEFORE stepDown ---");
var s = rs.status();
var currentPrimary = null;
s.members.forEach(function(m) {
  print("  " + m.name + " | " + m.stateStr + " | health:" + m.health);
  if (m.stateStr === "PRIMARY") currentPrimary = m.name;
});
print("Current PRIMARY:", currentPrimary);

// Force stepDown (30s stepdown period, 10s freeze on this node)
print("\n--- Calling rs.stepDown() ---");
try {
  var result = rs.stepDown(30, 10);
  printjson(result);
} catch(e) {
  // stepDown throws a connection error as the node steps down - this is expected
  print("Connection closed after stepDown (expected). Error:", e.message || e);
}

print("\n=== Failover triggered. Run rs.status() from another node to see new PRIMARY ===");
