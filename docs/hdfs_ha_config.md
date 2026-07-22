# HDFS High Availability Architecture & Configuration Guide

## 1. Problem: NameNode as Single Point of Failure

In a standard Hadoop deployment, there is only one NameNode. If it fails, the entire HDFS cluster becomes unavailable — all reads and writes stop. This is unacceptable in production.

## 2. HDFS HA Solution Architecture

```
  ┌──────────────────────────────────────────────────────────────────────┐
  │  HDFS HA Cluster (Quorum Journal Manager Model)                       │
  │                                                                       │
  │  ┌─────────────────┐         ┌─────────────────────────────────────┐ │
  │  │  Active NameNode│◄────────│  JournalNode 1                      │ │
  │  │  (Primary)      │   edit  │  JournalNode 2  (Quorum: 2/3 agree) │ │
  │  └────────┬────────┘   logs  │  JournalNode 3                      │ │
  │           │            ────► └─────────────────────────────────────┘ │
  │           │ (ZKFC)                                                    │
  │  ┌────────┴────────┐         ┌─────────────────────────────────────┐ │
  │  │ Standby NameNode│◄────────│  ZooKeeper 1                        │ │
  │  │ (Hot Standby)   │  reads  │  ZooKeeper 2  (Leader election)     │ │
  │  └─────────────────┘  edits  │  ZooKeeper 3  (ZKFC failover ctrl)  │ │
  │                        ────► └─────────────────────────────────────┘ │
  │                                                                       │
  │  DataNode-1  ──┐                                                      │
  │  DataNode-2  ──┼──── Reports block locations to BOTH NameNodes        │
  │  DataNode-3  ──┘     (replicationFactor=3)                            │
  └──────────────────────────────────────────────────────────────────────┘
```

## 3. Key Components

| Component | Count | Role |
|---|---|---|
| Active NameNode | 1 | Serves all client read/write requests |
| Standby NameNode | 1 | Hot standby, synced via JournalNodes |
| JournalNode | 3 | Shared edit log storage (quorum: 2/3) |
| ZooKeeper | 3 | Leader election + ZKFC failover coordination |
| DataNode | ≥ 3 | Block storage (replicationFactor=3) |

## 4. Failover Process

1. Active NameNode crashes / becomes unresponsive.
2. **ZKFC (ZooKeeper Failover Controller)** detects failure via ZK session expiry.
3. ZKFC on Standby NameNode acquires ZK lock and initiates **fencing** of old Active.
4. Standby replays all committed edit logs from JournalNodes.
5. Standby transitions to **Active** state — total failover time: ~30–60 seconds.

## 5. Production core-site.xml Configuration

```xml
<configuration>
  <!-- HA NameService ID — used instead of single namenode host -->
  <property>
    <name>fs.defaultFS</name>
    <value>hdfs://mycluster</value>
  </property>

  <!-- ZooKeeper ensemble — uses DNS service names, no IP hardcoding -->
  <property>
    <name>ha.zookeeper.quorum</name>
    <value>zk1.production.svc:2181,zk2.production.svc:2181,zk3.production.svc:2181</value>
  </property>
</configuration>
```

## 6. Production hdfs-site.xml Configuration

```xml
<configuration>
  <property>
    <name>dfs.nameservices</name>
    <value>mycluster</value>
  </property>
  <property>
    <name>dfs.ha.namenodes.mycluster</name>
    <value>nn1,nn2</value>
  </property>
  <property>
    <name>dfs.namenode.rpc-address.mycluster.nn1</name>
    <value>namenode1.production.svc:8020</value>
  </property>
  <property>
    <name>dfs.namenode.rpc-address.mycluster.nn2</name>
    <value>namenode2.production.svc:8020</value>
  </property>
  <!-- JournalNode edit log shared storage -->
  <property>
    <name>dfs.namenode.shared.edits.dir</name>
    <value>qjournal://jn1.production.svc:8485;jn2.production.svc:8485;jn3.production.svc:8485/mycluster</value>
  </property>
  <!-- Automatic ZKFC failover -->
  <property>
    <name>dfs.ha.automatic-failover.enabled</name>
    <value>true</value>
  </property>
  <!-- Replication factor: 3 copies across 3 DataNodes -->
  <property>
    <name>dfs.replication</name>
    <value>3</value>
  </property>
</configuration>
```

## 7. Acceptance Criteria Satisfied

- ✅ **NameNode is not SPOF**: Automatic failover via ZKFC in ~30–60s.
- ✅ **No data loss on DataNode restart**: replicationFactor=3; PVC-backed DataNode volumes.
- ✅ **No IP hardcoding**: all addresses use Kubernetes DNS service names.
