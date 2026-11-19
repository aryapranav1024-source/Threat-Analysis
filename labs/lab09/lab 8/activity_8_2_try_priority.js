// ============================================================
// Activity 8.2 Try It Yourself: Respective MongoDB File
// activity_8_2_try_priority.js
// Configures member priorities and triggers failover election
// ============================================================

print("=== Configuring Replica Set Member Priorities ===");

var cfg = rs.conf();

// Ensure 3 data members have distinct priorities:
// mongo1:27017 -> Priority 1
// mongo2:27018 -> Priority 10  (HIGHEST - Target Candidate)
// mongo3:27019 -> Priority 2
cfg.members.forEach(function(m) {
  if (m.host.indexOf("27017") !== -1) {
    m.priority = 1;
  } else if (m.host.indexOf("27018") !== -1) {
    m.priority = 10;
  } else if (m.host.indexOf("27019") !== -1) {
    m.priority = 2;
  }
});

print("Applying new configuration (rs.reconfig)...");
var reconfigResult = rs.reconfig(cfg);
printjson(reconfigResult);

print("\n--- Updated Priorities from rs.conf() ---");
rs.conf().members.forEach(function(m) {
  print("  Member:", m.host, "| Priority:", m.priority);
});

print("\nPREDICTION:");
print("  Secondary mongo2:27018 has the highest priority (10).");
print("  When current primary steps down, mongo2:27018 will be elected new PRIMARY.");

print("\n--- Triggering rs.stepDown(30) on Current Primary ---");
try {
  rs.stepDown(30);
} catch (e) {
  print("Stepdown executed (connection reset expected): " + e.message);
}

print("\nWaiting 10 seconds for election to complete...");
sleep(10000);

print("\n--- Post-Election Replica Set Status ---");
var status = rs.status();
status.members.forEach(function(m) {
  print("  Member:", m.name, "| State:", m.stateStr, "| Health:", m.health);
});
