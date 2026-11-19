// ============================================================
// Activity 8.2: Respective MongoDB File
// activity_8_2_stepdown.js
// Objective: Stepdown Primary and Observe Election
// ============================================================

print("=================================================");
print("  MongoDB Shell: Stepdown Primary and Observe rs.status");
print("=================================================");

// 1. Identify current primary before stepdown
var initialStatus = rs.status();
var primaryNode = null;
initialStatus.members.forEach(function(m) {
  if (m.stateStr === "PRIMARY") {
    primaryNode = m.name;
  }
});

print("Current Active PRIMARY: " + primaryNode);

// 2. Execute stepdown
print("\nExecuting rs.stepDown(30)... (Primary will relinquish leadership)");
try {
  var res = rs.stepDown(30);
  printjson(res);
} catch (e) {
  print("Stepdown initiated successfully (expected disconnect: " + e.message + ")");
}

print("\nWaiting 8 seconds for election and consensus...");
sleep(8000);

// 3. Inspect status on the new primary
print("\n--- Post-Failover Replica Set Status (rs.status()) ---");
var newStatus = rs.status();
var newPrimary = null;
newStatus.members.forEach(function(m) {
  print("  Node: " + m.name + " | State: " + m.stateStr + " | Health: " + m.health);
  if (m.stateStr === "PRIMARY") {
    newPrimary = m.name;
  }
});

print("\nResult: Election complete!");
print("  Old Primary: " + primaryNode);
print("  New Primary: " + newPrimary);
print("=================================================");
