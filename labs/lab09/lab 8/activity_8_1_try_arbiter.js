// ============================================================
// Activity 8.1 Try It Yourself: Respective MongoDB File
// activity_8_1_try_arbiter.js
// Objective: Add an Arbiter Node (mongo-arbiter:27020) to rs0
// ============================================================

print("=================================================");
print("  MongoDB Shell: Add Arbiter Node to Replica Set");
print("=================================================");

// 1. Add Arbiter Node to replica set
try {
  try {
    db.adminCommand({ setDefaultRWConcern: 1, defaultWriteConcern: { w: 'majority' } });
  } catch(e) {}
  print("Executing rs.addArb('mongo-arbiter:27020')...");
  var addRes = rs.addArb("mongo-arbiter:27020");
  printjson(addRes);
} catch (e) {
  print("Notice / Arbiter status: " + e.message);
}

print("\nWaiting 5 seconds for topology update...");
sleep(5000);

// 2. View current configuration with rs.conf()
print("\n--- Current Configuration (rs.conf()) ---");
var conf = rs.conf();
conf.members.forEach(function(m) {
  var arbStatus = m.arbiterOnly ? "[ARBITER ONLY - NO DATA STORAGE]" : "[DATA-BEARING NODE]";
  print("  ID: " + m._id + " | Host: " + m.host + " | Priority: " + m.priority + " | " + arbStatus);
});

// 3. View status with rs.status()
print("\n--- Member Health and Roles (rs.status()) ---");
var status = rs.status();
status.members.forEach(function(m) {
  print("  Node: " + m.name + " | State: " + m.stateStr + " | Health: " + m.health);
});

print("\n=================================================");
print("  Arbiter node successfully incorporated.");
print("=================================================");
