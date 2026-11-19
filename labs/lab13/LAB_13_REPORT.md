# Lab 13: Production Replica Set & Kubernetes StatefulSet for MongoDB

## Executive Summary
This lab covers two production-grade deployment paradigms for MongoDB Replica Sets:
1. **Docker Compose with Internal keyFile Authentication & RBAC**: Moving from the development replica set in Chapter 8 to an authenticated production topology.
2. **Kubernetes StatefulSet Architecture**: Deploying a self-healing, multi-node MongoDB replica set using Headless Services, stable network identifiers, and dynamic per-pod PersistentVolumeClaims (`volumeClaimTemplates`).

---

## Activity 1: Deploy a Production Replica Set with Docker Compose

### 1. Architectural Topics & Order of Operations
- **`keyFile` Authentication (Internal Peer Trust)**:
  `keyFile` authentication governs internal cluster communication between `mongod` instances. Every member shares the exact same secret key (chmod 400, 6 to 1024 bytes). This prevents unauthorized or rogue mongod nodes from joining the cluster and tampering with replication. It operates at the cluster communication layer, completely distinct from RBAC user credentials used by client applications.
- **The Localhost Exception & Order of Operations**:
  When `--auth` and `--keyFile` are enabled, MongoDB permits an administrative user to be created on `localhost` **only before** any users exist and before the replica set is clustered/enforced. Once the replica set is initiated, inter-member traffic immediately requires keyFile authentication, and client operations require RBAC credentials. Creating the admin user first guarantees that administrative access is preserved.

### 2. Side-by-Side Comparison: Chapter 8 vs. Chapter 13

| Aspect | Chapter 8 (`lab_01_deploy_replicaset.sh`) | Chapter 13 (`lab_01_deploy_prod.sh`) |
| :--- | :--- | :--- |
| **Keyfile Secret** | None. Nodes connect openly without mutual cluster verification. | **Step 1**: Generates 756-byte random secret (`openssl rand -base64 756 > keyfile`) and restricts permissions (`chmod 400 keyfile`). |
| **Docker Compose File** | `docker-compose-replicaset.yml` | `docker-compose-production.yml` |
| **Container Flags** | `command: ["--replSet", "rs0", "--bind_ip_all", "--port", "..."]` | Adds `--auth` and `--keyFile /etc/mongodb/keyfile` to all nodes. |
| **Volume Mounts** | Container data volume only (`rs0_data1:/data/db`). | Mounts data volume (`prod_data1:/data/db`) **plus** `./keyfile:/etc/mongodb/keyfile:ro`. |
| **Healthchecks** | Unauthenticated: `db.runCommand({ping:1})`. | Authenticated: `mongosh -u admin -p AdminPass123! --authenticationDatabase admin`. |
| **Initial Admin Setup** | Skipped completely. No database users created. | **Step 3**: Connects to unclustered node on `27017` via localhost exception and provisions `admin` user with `userAdminAnyDatabase`, `clusterAdmin`, and `readWriteAnyDatabase`. |
| **Replica Set Initiation** | Unauthenticated `rs.initiate({...})`. | Authenticated: `mongosh -u admin -p AdminPass123! --authenticationDatabase admin` calls `rs.initiate({...})`. |
| **Verification & Status** | Checks unauthenticated `rs.status()` and performs unauthenticated writes to `testdb`. | Authenticated `rs.status()` verifying each member's state string (`PRIMARY`, `SECONDARY`, `ARBITER`). |
| **Connection String** | `mongodb://host.docker.internal:27017,host.docker.internal:27018,host.docker.internal:27019/?replicaSet=rs0` | `mongodb://admin:AdminPass123!@host.docker.internal:27017,host.docker.internal:27018,host.docker.internal:27019/admin?replicaSet=rs0&authSource=admin` |

---

## Activity 2: Kubernetes StatefulSet for MongoDB

### 1. Pre-Manifest Analysis & Prediction

#### Question
> Predict what `serviceName` field the StatefulSet needs to reference for stable pod-naming to work, and what would break if it referenced the wrong Service (or none at all).

#### Prediction & Technical Breakdown
- **Target `serviceName`**:
  The StatefulSet spec requires:
  ```yaml
  spec:
    serviceName: mongo
  ```
  This must match the `metadata.name` of the headless Service (`01-headless-service.yaml`).
- **What Breaks if Wrong or Missing**:
  1. **DNS A/SRV Record Generation Fails**: Kubernetes CoreDNS uses `serviceName` to construct predictable, pod-specific FQDNs:
     `<pod-name>.<service-name>.<namespace>.svc.cluster.local` (e.g., `mongo-0.mongo.nosql-labs.svc.cluster.local`).
  2. **Inter-Node Reachability Fails**: Without the headless service link, pods only receive ephemeral pod IP addresses.
  3. **Cluster Initiation Failure**: The replica set initialization job (`03-replicaset-init-job.yaml`) initiates `rs0` pointing to `mongo-0.mongo.nosql-labs.svc.cluster.local`, `mongo-1...`, and `mongo-2...`. If `serviceName` is invalid, DNS resolution fails (`getaddrinfo ENOTFOUND`), the replica set never forms, and no Primary is elected.

### 2. Manifest Execution & Generated Artifacts
Running `lab_02_k8s_statefulset.py` automatically generated four Kubernetes manifests under `k8s/`:

```mermaid
flowchart TD
    NS["00-namespace.yaml<br/>(nosql-labs)"] --> SVC["01-headless-service.yaml<br/>(clusterIP: None)"]
    SVC --> STS["02-statefulset.yaml<br/>(mongo-0, mongo-1, mongo-2)"]
    STS --> PVC["volumeClaimTemplates<br/>(mongo-data-mongo-X 5Gi)"]
    STS --> JOB["03-replicaset-init-job.yaml<br/>(rs.initiate via FQDN)"]
```

#### Manifest Breakdown
1. **`00-namespace.yaml`**: Isolates the lab resources inside the `nosql-labs` namespace.
2. **`01-headless-service.yaml`**:
   - `clusterIP: None`: Disables round-robin virtual IP load balancing.
   - Creates direct DNS mappings for each pod selector `app: mongo`.
3. **`02-statefulset.yaml`**:
   - `serviceName: mongo`: Associates the StatefulSet with the headless service.
   - `replicas: 3`: Provisions pods in sequential order (`mongo-0`, `mongo-1`, `mongo-2`).
   - `readinessProbe` & `livenessProbe`: Evaluates `db.runCommand({ping:1})` using `mongosh`.
   - `volumeClaimTemplates`: Creates independent PersistentVolumeClaims (`ReadWriteOnce`, 5Gi) per pod so that pod restarts or rescheduling to other Kubernetes worker nodes preserve the exact data directory for that specific replica set member.
4. **`03-replicaset-init-job.yaml`**:
   - Runs a one-shot container executing `rs.initiate()` with the 3 stable FQDN endpoints once all StatefulSet pods are ready.

---

## Deployment & Verification Commands

### Manual Execution against a Kubernetes Cluster
```bash
# 1. Apply namespace and headless service
kubectl apply -f k8s/00-namespace.yaml
kubectl apply -f k8s/01-headless-service.yaml

# 2. Deploy the StatefulSet and wait for pods
kubectl apply -f k8s/02-statefulset.yaml
kubectl rollout status statefulset/mongo -n nosql-labs --timeout=180s

# 3. Initialize the replica set
kubectl apply -f k8s/03-replicaset-init-job.yaml

# 4. Verify Replica Set topology
kubectl exec -n nosql-labs -it mongo-0 -- mongosh --eval "rs.status().members.forEach(m => print(m.name, m.stateStr))"
```
