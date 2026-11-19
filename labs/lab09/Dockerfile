FROM aryapranav1024/mongodb-lab-10:latest

LABEL maintainer="aryapranav1024"
LABEL description="Unified NoSQL MongoDB Labs Suite - Labs 7, 8 & 9 (Schema, Replica Set, Write Concerns)"

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install rich and tabulate explicitly
RUN pip install --no-cache-dir rich tabulate

# Ensure required directories exist
RUN mkdir -p /data/db1 /data/db2 /data/db3 /var/log/mongodb \
             /app/lab9 /app/lab8 /app/lab7/config /app/lab7/data

# ── Lab 9 ──────────────────────────────────────────────────────────────────
COPY context/lab9/lab_01_write_concern_latency.py  /app/lab9/
COPY context/lab9/lab_01_latency_results.json      /app/lab9/
COPY context/lab9/lab_02_simulate_partition.py     /app/lab9/
COPY context/lab9/lab_02_simulate_partition.sh     /app/lab9/
COPY context/lab9/lab_02_partition_results.json    /app/lab9/

# ── Lab 8 ──────────────────────────────────────────────────────────────────
COPY context/lab8/activity_8_1_replica_set.py   /app/lab8/
COPY context/lab8/activity_8_2_failover.py      /app/lab8/
COPY context/lab8/lab_8_1_deploy_replicaset.py  /app/lab8/
COPY context/lab8/lab_8_2_failover_observer.py  /app/lab8/
COPY context/lab8/lab_02_failover_observer.py   /app/lab8/
COPY context/lab8/docker-compose.yml            /app/lab8/
COPY context/lab8/rs_init_basic.js              /app/lab8/

# ── Lab 7 ──────────────────────────────────────────────────────────────────
COPY context/lab7/lab_01_production_schema.py       /app/lab7/
COPY context/lab7/lab_02_working_set_analysis.py    /app/lab7/
COPY context/lab7/seed_cti_data.py                  /app/lab7/
COPY context/lab7/lab_01_try_yourself.py            /app/lab7/
COPY context/lab7/lab_02_try_yourself.py            /app/lab7/
COPY context/lab7/lab_01_production_schema.json     /app/lab7/
COPY context/lab7/lab_02_working_set_analysis.json  /app/lab7/
COPY context/lab7/lab_01_try_yourself.json          /app/lab7/
COPY context/lab7/lab_02_try_yourself.json          /app/lab7/
COPY context/lab7/config/connection.py              /app/lab7/config/
COPY context/lab7/config/__init__.py                /app/lab7/config/
COPY context/lab7/data/cti_platform_dump.json       /app/lab7/data/

# ── Master Demonstration & Root Files ──────────────────────────────────────
COPY context/root/run_all_labs.py                       /app/
COPY context/root/demo_menu.py                          /app/
COPY context/root/entrypoint.sh                         /app/
COPY context/root/K.PRANAV_REDDY_24BTRCL098_LAB_09.pdf  /app/

RUN chmod +x /app/entrypoint.sh /app/demo_menu.py /app/run_all_labs.py /app/lab9/lab_02_simulate_partition.sh

ENV MONGO_URI="mongodb://127.0.0.1:27017,127.0.0.1:27018,127.0.0.1:27019/?replicaSet=rs0&readPreference=primaryPreferred"
ENV REPLICA_SET_URI="mongodb://127.0.0.1:27017,127.0.0.1:27018,127.0.0.1:27019/?replicaSet=rs0"

ENTRYPOINT ["/app/entrypoint.sh"]
