# DynamoDB & RDS — Database Services

## DynamoDB (NoSQL)

### What is DynamoDB?

Amazon DynamoDB is a fully managed NoSQL database service that provides fast and predictable performance with seamless scalability. It's a key-value and document database.

### Core Concepts

| Concept | Description |
|:---|:---|
| **Tables** | Top-level containers for data (similar to tables in RDBMS) |
| **Items** | Individual records in a table (similar to rows) |
| **Attributes** | Data elements within items (similar to columns, but schema-free) |
| **Partition Key** | Primary key used for data distribution across partitions |
| **Sort Key** | Optional secondary key enabling range queries within a partition |

### Data Model Example

```
Table: Users
├── Partition Key: user_id
├── Sort Key: created_at
│
├── Item: { user_id: "u001", created_at: "2026-01-15", name: "Alice", role: "admin" }
├── Item: { user_id: "u002", created_at: "2026-02-20", name: "Bob", email: "bob@example.com" }
└── Item: { user_id: "u003", created_at: "2026-03-10", name: "Charlie", age: 28 }
```

Note: Items can have different attributes — DynamoDB is schema-free.

### Key Features

- **Single-digit millisecond latency** at any scale
- **Auto-scaling** — capacity adjusts based on traffic
- **Global Tables** — multi-region, multi-active replication
- **DynamoDB Streams** — capture item-level changes for event-driven architectures
- **TTL (Time to Live)** — automatically delete expired items
- **DAX (DynamoDB Accelerator)** — in-memory cache for microsecond reads

### Access Patterns

| Operation | API | Description |
|:---|:---|:---|
| Create | `PutItem` | Insert a new item |
| Read (single) | `GetItem` | Retrieve by primary key |
| Read (multiple) | `Query` | Query by partition key + optional sort key |
| Read (scan) | `Scan` | Full table scan (expensive, avoid in production) |
| Update | `UpdateItem` | Modify specific attributes |
| Delete | `DeleteItem` | Remove an item |

### Use Cases

- **Real-time applications:** Leaderboards, session management
- **Gaming:** Player profiles, game state
- **IoT:** Sensor data, device telemetry
- **E-commerce:** Shopping carts, product catalogs
- **Ad tech:** Click-stream data, user activity tracking

---

## RDS (Relational Database Service)

### What is RDS?

Amazon RDS is a managed relational database service that makes it easy to set up, operate, and scale a relational database in the cloud.

### Supported Database Engines

| Engine | Description |
|:---|:---|
| **Amazon Aurora** | MySQL/PostgreSQL-compatible, 5x faster, auto-scaling |
| **MySQL** | Open-source relational database |
| **PostgreSQL** | Advanced open-source relational database |
| **MariaDB** | Community-developed MySQL fork |
| **Oracle** | Enterprise relational database |
| **SQL Server** | Microsoft's relational database |

### Core Concepts

| Concept | Description |
|:---|:---|
| **DB Instance** | An isolated database environment running in the cloud |
| **Instance Class** | CPU and memory configuration (e.g., `db.t3.micro`, `db.r5.large`) |
| **Storage** | EBS-backed storage (General Purpose SSD, Provisioned IOPS, Magnetic) |
| **Endpoint** | DNS name for connecting to the database |
| **Parameter Groups** | Database configuration settings |
| **Subnet Groups** | VPC subnets where RDS can place instances |

### High Availability

#### Multi-AZ Deployment

- Synchronous replication to a standby instance in a different Availability Zone
- Automatic failover if the primary instance fails (typically 1-2 minutes)
- Standby is NOT available for read traffic

```
Primary Instance (AZ-a) ←── Sync Replication ──→ Standby Instance (AZ-b)
        ↑
   Application
```

#### Read Replicas

- Asynchronous replication for scaling read workloads
- Can be in the same region or cross-region
- Can be promoted to standalone instance
- Up to 15 read replicas for Aurora, 5 for others

```
Primary Instance
    ├── Read Replica 1 (same region)    ← Read traffic
    ├── Read Replica 2 (same region)    ← Read traffic
    └── Read Replica 3 (cross-region)   ← Disaster recovery
```

### Security

- **Encryption at rest:** Using AWS KMS
- **Encryption in transit:** SSL/TLS connections
- **Network isolation:** VPC, Security Groups, private subnets
- **IAM authentication:** Token-based authentication for MySQL and PostgreSQL
- **Audit logging:** Database activity streams

### Backups

| Feature | Automated Backups | Manual Snapshots |
|:---|:---|:---|
| **Trigger** | Automatic daily | User-initiated |
| **Retention** | 0-35 days | Until deleted |
| **Point-in-time** | Yes (5-minute granularity) | No |
| **Cost** | Free (within retention period) | Storage costs |

### Use Cases

- **E-commerce:** Order management, inventory, user accounts
- **CRM:** Customer data, interactions, analytics
- **ERP:** Enterprise resource planning systems
- **Financial:** Transaction processing, reporting
- **Content management:** Blog platforms, CMS backends

---

## DynamoDB vs RDS Comparison

| Feature | DynamoDB | RDS |
|:---|:---|:---|
| **Type** | NoSQL (key-value, document) | Relational (SQL) |
| **Schema** | Schema-free | Fixed schema |
| **Scaling** | Horizontal (auto) | Vertical (manual) |
| **Queries** | Key-based access | Complex SQL joins |
| **Latency** | Single-digit milliseconds | Milliseconds to seconds |
| **Transactions** | Limited (TransactWriteItems) | Full ACID |
| **Best for** | High-volume, simple queries | Complex relationships, reporting |
| **Managed** | Fully serverless | Managed but needs instance sizing |
