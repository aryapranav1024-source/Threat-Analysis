# rs.initiate()
rs.conf = {
    _id: "rs0",
    members: [
        {_id: 0, host: "localhost:27017", priority: 2},
        {_id: 1, host: "localhost:27018", priority: 1},
        {_id: 2, host: "localhost:27019", priority: 1, arbiterOnly: false}
    ]
}
rs.initiate(rs.conf)

# Check replica set status
rs.status()

# View current configuration
rs.conf()
