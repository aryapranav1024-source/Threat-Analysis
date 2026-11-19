// ============================================================
// Lab 8.1 Activity - MongoDB Shell Script (rs_init_arbiter.js)
// Initializes a 3-data-node + 1-arbiter replica set
//
// Run via:
//   docker exec mongo1 mongosh --port 27017 --file rs_init_arbiter.js
// ============================================================

print("=== Initiating replica set rs0 with Arbiter ===");

/*
  Replica set layout:
    _id 0  ->  127.0.0.1:27017  (data node, priority 2 - preferred primary)
    _id 1  ->  127.0.0.1:27018  (data node, priority 1)
    _id 2  ->  127.0.0.1:27019  (data node, priority 1)
    _id 3  ->  127.0.0.1:27020  (arbiter - votes but holds no data)

  WHY an arbiter?
  ---------------
  An arbiter participates in elections and provides an extra vote that
  ensures an odd number of voters (here: 4 nodes = 3 data + 1 arbiter).
  This guarantees a majority can always be formed even if one data node
  fails, without paying the storage and memory cost of a full data node.
  Arbiters do NOT replicate data, so they are lightweight.
*/

var cfg = {
  _id: "rs0",
  members: [
    { _id: 0, host: "127.0.0.1:27017", priority: 2 },
    { _id: 1, host: "127.0.0.1:27018", priority: 1 },
    { _id: 2, host: "127.0.0.1:27019", priority: 1 },
    { _id: 3, host: "127.0.0.1:27020", arbiterOnly: true }
  ]
};

var result = rs.initiate(cfg);
printjson(result);

print("\nWaiting 12 seconds for election...");
sleep(12000);

print("\n=== Replica Set Status ===");
var status = rs.status();
status.members.forEach(function(m) {
  var role = m.stateStr;
  if (m.arbiterOnly) role += " (ARBITER)";
  print("  Member:", m.name, "| Role:", role, "| Health:", m.health);
});

print("\n=== rs.conf() (configuration) ===");
var conf = rs.conf();
conf.members.forEach(function(m) {
  var arbTag = m.arbiterOnly ? " [ARBITER]" : "";
  print("  _id:", m._id, "| host:", m.host, "| priority:", m.priority, arbTag);
});

print("\n=== DONE - Replica set with Arbiter initialized ===");
