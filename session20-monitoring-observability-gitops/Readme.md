# Session 20 — Monitoring, Observability & GitOps

Explored the three pillars of observability, hands-on monitoring with Prometheus and Grafana, and GitOps principles with ArgoCD.

---

## Task 1: Monitoring

### What is Monitoring?

Monitoring is the practice of collecting, analyzing, and displaying real-time data about the health and performance of systems. It answers: **"Is my system working?"**

### Key Monitoring Concepts

#### Metrics

Numerical measurements collected over time. Metrics are the foundation of monitoring.

| Metric Type | Description | Example |
|:---|:---|:---|
| **Counter** | Monotonically increasing value | Total HTTP requests: 15,432 |
| **Gauge** | Value that can go up and down | Current CPU usage: 45% |
| **Histogram** | Distribution of values in buckets | Request latency: p50=10ms, p99=200ms |
| **Summary** | Similar to histogram with pre-calculated quantiles | Response time: avg=50ms |

#### Logs

Timestamped records of discrete events. Logs provide detailed context about what happened.

```
2026-10-07T12:00:01Z INFO  [main] Application started on port 8080
2026-10-07T12:00:15Z WARN  [db] Slow query detected: 2500ms
2026-10-07T12:00:30Z ERROR [api] Connection refused: database unreachable
```

**Log levels:** DEBUG < INFO < WARN < ERROR < FATAL

#### Alerts

Notifications triggered when metrics cross predefined thresholds.

```yaml
# Example Prometheus alert rule
groups:
  - name: application-alerts
    rules:
      - alert: HighCPUUsage
        expr: node_cpu_seconds_total{mode="idle"} < 20
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High CPU usage detected"
          description: "CPU idle is below 20% for more than 5 minutes"

      - alert: HighMemoryUsage
        expr: (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes) * 100 < 15
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Memory usage above 85%"
```

### Monitoring Demo

#### CPU Utilization

```bash
# Kubernetes - check CPU usage
kubectl top nodes
kubectl top pods

# Linux - system metrics
top
htop
vmstat 1
```

```
NAME       CPU(cores)   CPU%   MEMORY(bytes)   MEMORY%
minikube   250m         12%    1200Mi           62%
```

#### Memory Utilization

```bash
# Check memory usage
kubectl top pods --sort-by=memory
free -h
```

#### Application Health

```bash
# Check Pod health
kubectl get pods
kubectl describe pod <pod-name>

# Health endpoint
curl http://localhost:8080/health
```

```json
{
  "status": "healthy",
  "uptime": "2h 45m",
  "version": "1.0.0"
}
```

---

## Task 2: Observability

### The Three Pillars of Observability

Observability is the ability to understand a system's internal state by examining its outputs. It answers: **"Why is my system broken?"**

```
                    Observability
                         │
           ┌─────────────┼─────────────┐
           │             │             │
        Metrics         Logs         Traces
           │             │             │
     "What happened"  "Why it      "Where it
      numerically"    happened"     happened"
```

### Pillar 1: Metrics

**What:** Aggregated numerical data over time.
**Why:** Fast anomaly detection, trend analysis, alerting.
**Tools:** Prometheus, Datadog, CloudWatch, InfluxDB.

```
CPU Usage Over Time:
100% ┤
 80% ┤         ╭─╮
 60% ┤    ╭───╯   ╰──╮
 40% ┤───╯            ╰──────
 20% ┤
  0% ┼──────────────────────
     0h   1h   2h   3h   4h
```

### Pillar 2: Logs

**What:** Timestamped text records of discrete events.
**Why:** Detailed debugging, audit trails, error context.
**Tools:** ELK Stack (Elasticsearch, Logstash, Kibana), Loki, Fluentd, CloudWatch Logs.

```
[2026-10-07 12:00:01] INFO  Request received: GET /api/users
[2026-10-07 12:00:01] DEBUG Database query: SELECT * FROM users WHERE id=42
[2026-10-07 12:00:02] INFO  Response sent: 200 OK (45ms)
[2026-10-07 12:00:15] ERROR Database connection timeout after 30s
[2026-10-07 12:00:15] ERROR Request failed: GET /api/orders - 500 Internal Server Error
```

### Pillar 3: Traces

**What:** End-to-end request flow across microservices.
**Why:** Identify bottlenecks, understand service dependencies, debug distributed systems.
**Tools:** Jaeger, Zipkin, OpenTelemetry, AWS X-Ray.

```
Request: GET /api/checkout
│
├── API Gateway (5ms)
│   └── Auth Service (15ms)
│       └── Token validation
├── Order Service (120ms)
│   ├── Inventory Check (30ms)
│   │   └── Database query (25ms) ← BOTTLENECK
│   └── Payment Processing (80ms)
│       └── External API call (75ms)
└── Notification Service (10ms)
    └── Send email (async)

Total: 150ms
```

### Why Observability is Required

1. **Microservices complexity** — Distributed systems are harder to debug than monoliths
2. **Unknown unknowns** — Can't predict all failure modes in advance
3. **Mean Time to Recovery (MTTR)** — Faster root cause identification
4. **Performance optimization** — Identify bottlenecks across service boundaries
5. **Compliance and auditing** — Maintain records of system behavior

### Common Tools Landscape

| Category | Tools |
|:---|:---|
| **Metrics** | Prometheus, Grafana, Datadog, CloudWatch |
| **Logs** | ELK Stack, Loki, Fluentd, CloudWatch Logs |
| **Traces** | Jaeger, Zipkin, OpenTelemetry, X-Ray |
| **All-in-one** | Datadog, New Relic, Dynatrace |
| **Kubernetes** | Prometheus + Grafana, Lens, k9s |

### Kubernetes Observability

```bash
# Metrics
kubectl top nodes
kubectl top pods
kubectl get --raw /apis/metrics.k8s.io/v1beta1/pods

# Logs
kubectl logs <pod-name>
kubectl logs <pod-name> -f --tail=100
kubectl logs -l app=myapp --all-containers

# Events (traces of cluster operations)
kubectl get events --sort-by='.lastTimestamp'
kubectl describe pod <pod-name>
```

#### Prometheus in Kubernetes

```yaml
# docker-compose.yml for Prometheus
version: '3.8'
services:
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml

# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'kubernetes-pods'
    kubernetes_sd_configs:
      - role: pod
```

#### Grafana Dashboard

```yaml
# docker-compose.yml for Grafana
version: '3.8'
services:
  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
```

Access Grafana at `http://localhost:3000` (admin/admin), add Prometheus as a data source, and import dashboard ID `3662` for Kubernetes monitoring.

---

## Task 3: GitOps

### What is GitOps?

GitOps is an operational framework where **Git is the single source of truth** for declarative infrastructure and application configuration. Changes are applied to production through Git commits, not manual `kubectl apply`.

### Core Principles

| Principle | Description |
|:---|:---|
| **Declarative** | Entire system described declaratively (YAML, HCL) |
| **Versioned** | Desired state stored in Git (version control) |
| **Automated** | Approved changes auto-applied to the system |
| **Reconciled** | Software agents ensure actual state matches desired state |

### Git as the Source of Truth

```
Developer → Git Commit → Git Repository → GitOps Agent → Kubernetes Cluster
                                              ↑                    │
                                              └── Continuous ──────┘
                                                  Reconciliation
```

**Traditional workflow:**
```
Developer → kubectl apply → Cluster
  (manual, error-prone, no audit trail)
```

**GitOps workflow:**
```
Developer → Git push → Merge → ArgoCD detects change → Auto-deploy to Cluster
  (automated, auditable, rollback = git revert)
```

### Declarative Configuration

All infrastructure and application state is defined in YAML files stored in Git:

```yaml
# gitops-repo/app/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web-app
  namespace: production
spec:
  replicas: 3
  selector:
    matchLabels:
      app: web-app
  template:
    metadata:
      labels:
        app: web-app
    spec:
      containers:
        - name: web-app
          image: myapp:v2.1.0
          ports:
            - containerPort: 80
```

### Continuous Reconciliation

The GitOps agent continuously compares the desired state (in Git) with the actual state (in the cluster). If they differ, the agent reconciles automatically.

```
Desired State (Git)          Actual State (Cluster)
replicas: 3          vs      replicas: 2
image: v2.1.0        vs      image: v2.1.0
                                   │
                              DRIFT DETECTED
                                   │
                              Auto-reconcile
                                   │
                              replicas: 3 ✓
```

### GitOps Workflow

```
1. Developer creates a Pull Request to change deployment.yaml
2. PR is reviewed and approved
3. PR is merged to main branch
4. ArgoCD detects the change in Git
5. ArgoCD compares desired state with cluster state
6. ArgoCD applies the changes to the cluster
7. If deployment fails → ArgoCD shows "Degraded" status
8. To rollback → git revert the commit → ArgoCD auto-reconciles
```

### Kubernetes + GitOps (ArgoCD)

#### Installing ArgoCD

```bash
# Create namespace
kubectl create namespace argocd

# Install ArgoCD
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# Access ArgoCD UI
kubectl port-forward svc/argocd-server -n argocd 8080:443

# Get initial admin password
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d
```

#### ArgoCD Application Definition

```yaml
# argocd-application.yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: web-app
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/ShreeyaReddyL/devops-heros.git
    targetRevision: main
    path: gitops/app
  destination:
    server: https://kubernetes.default.svc
    namespace: production
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
      - CreateNamespace=true
```

**Key fields:**
- `source.repoURL` — Git repository containing manifests
- `source.path` — Directory within the repo
- `syncPolicy.automated` — Auto-sync on Git changes
- `selfHeal: true` — Auto-fix manual cluster changes (drift detection)
- `prune: true` — Delete resources removed from Git

#### GitOps Benefits

| Benefit | Description |
|:---|:---|
| **Auditability** | Every change is a Git commit with author, timestamp, and message |
| **Rollback** | `git revert` instantly rolls back production |
| **Consistency** | Cluster state always matches Git — no configuration drift |
| **Security** | No direct cluster access needed — only Git access |
| **Disaster Recovery** | Rebuild entire cluster from Git repository |
| **Collaboration** | Changes go through PR review process |

---

## Key Learnings

- **Monitoring** tells you WHAT is happening (metrics, alerts)
- **Observability** tells you WHY something is happening (metrics + logs + traces together)
- **Three pillars:** Metrics (numeric), Logs (text events), Traces (request flow)
- **Prometheus** scrapes metrics; **Grafana** visualizes them
- **GitOps** makes Git the single source of truth for infrastructure
- **ArgoCD** watches Git and auto-reconciles cluster state
- Continuous reconciliation prevents configuration drift
- Rollback in GitOps = `git revert` (no kubectl commands needed)
