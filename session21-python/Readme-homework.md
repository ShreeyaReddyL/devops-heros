# Session 21 — DevOps Final Capstone: CampusFix

**Student:** Shreeya Reddy
**Repository:** https://github.com/ShreeyaReddyL/devops-heros
**Project folder:** [`session21-python/`](.)
**Rubric:** [GRADING.md](GRADING.md)
**Working branch:** `capstone/campusfix-session21`

---

## 0. Evidence status legend

Every claim in this document is tagged. Nothing is asserted without a command
that was actually run and an observed exit status.

| Tag | Meaning |
|---|---|
| **VERIFIED** | Command was executed; the recorded exit status and output are real. |
| **BLOCKED** | Could not run in this environment; the exact blocker is named. |
| **NOT TESTED** | Deliberately not attempted, with the reason stated. |
| **UNVERIFIED** | A pre-existing claim in the repository that I could not reproduce and have **not** repeated as fact. |

> **State as of 2026-10-16:** the current validation below supersedes earlier
> snapshots in this report. CampusFix has been rebuilt and run locally with
> Docker Compose and Minikube in WSL; real Trivy scans and live Prometheus /
> Grafana checks were performed. Commit `ba32c7a60b82d2491e867ef2e420a60842caefb9`
> was pushed to `capstone/campusfix-session21`; GitHub Actions run #4 succeeded,
> published both SHA-tagged images to public GHCR packages, and passed both
> configured Trivy gates. The optional deploy job was skipped because this
> workflow currently deploys only from `main`. AWS infrastructure has not been provisioned.
> Historical output is identified as such. Local terminal evidence 19–25 and
> GitHub evidence 26–29 were captured on 2026-10-16; AWS evidence remains.

---

## 1. The application: CampusFix

**CampusFix** is a campus maintenance and IT support ticketing system. It was
built as a custom application, not a relabelled copy of the reference
TaskBoard starter — the rubric (`GRADING.md` §Grading Policy) assigns zero to a
direct clone, so the domain, data model, workflow, API, UI and tests are all
campus-specific.

### 1.1 Domain

Reported issues include campus Wi-Fi failures, broken classroom projectors,
electrical and lighting faults, hostel maintenance, plumbing leaks and lab
equipment problems.

### 1.2 Ticket model

| Field | Type | Constraint |
|---|---|---|
| `id` | int | PK |
| `title` | str(200) | required, 5–200 chars, non-blank |
| `description` | text | optional, ≤ 4000 chars |
| `category` | enum | `WI_FI`, `PROJECTOR`, `ELECTRICAL`, `PLUMBING`, `HOSTEL`, `LAB_EQUIPMENT`, `IT_SUPPORT`, `OTHER` |
| `building` | str(120) | campus location |
| `reporter` | str(120) | who reported the issue |
| `priority` | enum | `LOW`, `MEDIUM`, `HIGH`, `CRITICAL` |
| `status` | enum | `OPEN`, `IN_PROGRESS`, `RESOLVED` |
| `created_at` | timestamptz | set on insert |

### 1.3 Workflow

Enforced server-side in `backend/app/schemas.py`; illegal moves return **409**.

```text
OPEN ──► IN_PROGRESS ──► RESOLVED
  ▲            │              │
  └────────────┴──────────────┘  (reopen)
```

### 1.4 API

```text
GET    /                       GET    /api/tickets?status=&category=&priority=
GET    /health                 GET    /api/tickets/stats
GET    /ready                  GET    /api/tickets/{id}
GET    /metrics                POST   /api/tickets
                                PUT    /api/tickets/{id}
                                DELETE /api/tickets/{id}
```

### 1.5 Architecture

```text
Browser ─► :3000 ─► frontend (unprivileged Nginx :8080)
                        │ proxies /api
                        ▼
                   backend (FastAPI :8000) ──► PostgreSQL 16
                        └── /metrics ──► Prometheus ──► Grafana
```

---

## 2. Environment actually used

All validation for this session ran on a **real Linux environment**.

### 2.1 Host

| Layer | Detail |
|---|---|
| Host OS | Windows 11 (build 26200.9457) |
| Linux | **WSL 2 — Ubuntu 24.04.5 LTS (noble)** |
| Linux user | **`shreeya`** (matches the `shreeya@devbox` account used in Sessions 2–3) |
| Kernel | `6.18.54.1-microsoft-standard-WSL2` |
| WSL | v3.0.3.0, default version 2, WSLg 1.0.79 |

### 2.2 Toolchain

| Tool | Version | How obtained |
|---|---|---|
| Git | 2.50.1.windows.1 | pre-installed on Windows |
| Python | 3.12.10 | installed per-user from python.org (no admin) |
| Node.js | v22.17.0 | pre-installed on Windows + installed in Ubuntu |
| **Docker Engine (CE)** | **29.9.0** | **installed inside Ubuntu** — used for Compose builds and Minikube |
| kubectl | v1.37.1 | `~/.local/bin` in Ubuntu |
| **minikube** | **v1.39.0** | Kubernetes **v1.34.0**, docker driver |
| helm | v3.16.3 | `~/.local/bin` in Ubuntu |
| terraform | v1.9.8 | `~/.local/bin` in Ubuntu |
| metrics-server | v0.9.0 | minikube addon |
| kube-prometheus-stack | 92.4.0 / Prometheus v0.94.1 | Helm |
| Grafana | 13.2.4 | via kube-prometheus-stack |

> **Why Python 3.12:** the Windows `python` is 3.14.3, for which
> `psycopg-binary==3.2.3` publishes no wheel (PyPI lists cp38–cp313 only), so
> `pip install -r requirements.txt` would fall back to a source build and fail.
> 3.12 is also what `backend/Dockerfile` and the CI workflow use, so local,
> container and CI runs are consistent. 3.12.10 is the last 3.12 release that
> ships a Windows installer.

### 2.3 A note on the Linux environment

The course is taught on Linux and the starter report described an Ubuntu
"devbox". That environment now genuinely exists: Ubuntu 24.04 runs **inside
WSL 2**, hosts its own Docker Engine, and runs the whole Kubernetes stack.

The validated workflow uses Docker Engine inside Ubuntu WSL. Windows-side
Docker Desktop's named pipe was unavailable in this session, so Compose,
Minikube, Helm, and Trivy commands ran in the Linux shell:

| Runtime | Used for |
|---|---|
| Docker CE 29.9.0 **inside Ubuntu** | `docker compose up --build`, image builds, Minikube and local Trivy scans |
| Windows Docker Desktop | Not used; its Docker pipe was unavailable |

The images deployed to Kubernetes were **built natively on Ubuntu Linux**
(`campusfix-backend:local`, `campusfix-frontend:local`) and loaded into the
minikube node, so the cluster evidence is produced by Linux tooling end to end.

Git for Windows also provides **GNU bash 5.2.37**, so the repository's `.sh`
scripts remain runnable — verified in §3.11.

**Not installed:** AWS CLI, and no AWS credentials are configured.

---

## 3. Verification log

All commands were run in PowerShell (Windows) or Bash inside Ubuntu
`shreeya@DESKTOP-G7A7T8M`, as noted per section. Exit codes are real.

### 3.1 Dependency install — **VERIFIED**

```powershell
cd session21-python\backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

`EXITCODE=0`. Installed at the exact pinned versions:
`fastapi 0.115.6`, `uvicorn 0.34.0`, `SQLAlchemy 2.0.36`, `psycopg 3.2.3`,
`psycopg-binary 3.2.3`, `alembic 1.14.0`, `pytest 8.3.4`, `httpx 0.28.1`,
`pydantic 2.14.1`.

### 3.2 Import/compile check — **VERIFIED**

```powershell
.\.venv\Scripts\python.exe -m compileall -q app tests conftest.py
```

`COMPILE EXIT=0`.

### 3.3 Test suite — **VERIFIED**

```powershell
.\.venv\Scripts\python.exe -m pytest -v
```

```text
platform win32 -- Python 3.12.10, pytest-8.3.4
collected 25 items
...
============================= 25 passed, 1 warning in 0.66s ========================
PYTEST EXITCODE=0
```

The single warning originates in `starlette/testclient.py` (third-party
`BlockingPortal` alias deprecation), not in project code.

**Re-run to prove order-independence:** `25 passed`, exit 0, and the temporary
database was confirmed deleted afterwards.

Coverage across 7 endpoints: `/`, `/health`, `/ready`, `/metrics`, ticket
create / list / filter / read / update / delete, `/api/tickets/stats`, plus
422 validation, 404 not-found, 409 illegal-transition and empty-payload cases.

**Test isolation.** `backend/conftest.py` sets `DATABASE_URL` to a temporary
SQLite file *above* the `app.*` imports (the SQLAlchemy engine is constructed
at import time), truncates `tickets` before every test via an autouse fixture,
and deletes the file when the session ends. PostgreSQL is never touched.

**Current Linux-container recheck (2026-10-16):** the same 25 tests passed in
the rebuilt backend image under WSL Docker Engine. Two third-party deprecation
warnings were printed; there were no test failures. The genuine terminal
capture is saved as [`19-pytest-terminal.png`](screenshots/19-pytest-terminal.png).

### 3.4 Migrations — **VERIFIED**

```powershell
$env:DATABASE_URL="sqlite:///./alembic_check.db"
.\.venv\Scripts\python.exe -m alembic upgrade head
```

```text
Running upgrade  -> 0001_create_tasks
Running upgrade 0001_create_tasks -> 0002_campusfix_tickets
UPGRADE EXIT=0
```

Resulting schema (queried directly from SQLite):

```text
tables: ['alembic_version', 'tickets']
alembic_version: ['0002_campusfix_tickets']
tickets columns:
  id INTEGER NOT NULL | title VARCHAR(200) | description TEXT
  priority VARCHAR(20) default 'MEDIUM' | status VARCHAR(30) default 'OPEN'
  created_at DATETIME | category VARCHAR(30) default 'IT_SUPPORT'
  building VARCHAR(120) default 'Unspecified' | reporter VARCHAR(120) default 'Unknown'
```

`alembic downgrade base` → `EXIT=0`.

**Data preservation proven.** Two legacy TaskBoard rows were inserted at
revision `0001`, then migrated to head. Result:

```text
(1, 'Old wifi task', 'RESOLVED', 'HIGH', 'IT_SUPPORT', 'Imported from TaskBoard', 'Shreeya Reddy')
(2, 'Old todo task', 'OPEN',    'LOW',  'IT_SUPPORT', 'Imported from TaskBoard', 'Unknown')
```

`DONE→RESOLVED`, `TODO→OPEN`, `assignee→reporter`; no rows lost.

> **Defect found and fixed during this check:** the first run left
> `status` with `server_default 'TODO'` inherited from migration 0001 —
> a value that is not a valid `TicketStatus`. Migration 0002 now alters it to
> `'OPEN'` using `batch_alter_table` so it works on SQLite as well as Postgres.

### 3.5 Live HTTP smoke test — **VERIFIED**

The app was started with `uvicorn app.main:app` and driven over real HTTP
(not through `TestClient`).

| Check | Result |
|---|---|
| `GET /health` | 200 `{"status":"UP","service":"CampusFix API","version":"1.0.0"}` |
| `GET /` | 200 `{"service":"CampusFix API",...}` |
| `GET /ready` | 200 `{"status":"READY"}` |
| `POST /api/tickets` | 201, `status=OPEN`, `category=WI_FI` |
| `GET /api/tickets` | 200, list returned |
| `GET /api/tickets/{id}` | 200 |
| `GET /api/tickets?status=OPEN` | 200, filtered correctly |
| `PUT .../status=IN_PROGRESS` | 200 |
| `PUT .../status=RESOLVED,priority=CRITICAL` | 200 |
| `PUT` RESOLVED→IN_PROGRESS | **409** (as designed) |
| `POST` invalid title | **422** (as designed) |
| `GET` missing ticket | **404** (as designed) |
| `GET /api/tickets/stats` | 200, `total=1 open=0 in_progress=0 resolved=1 critical=1` |
| `GET /metrics` | 200, 13 597 bytes; families `http_requests_total`, `http_request_duration_seconds_count`, `http_request_size_bytes_count` |
| `DELETE /api/tickets/{id}` | **204**, empty body; subsequent GET → 404 |
| `GET /docs` | 200 |
| `GET /openapi.json` | `title: CampusFix API`, 7 paths, enums correct |

### 3.6 Frontend build — **VERIFIED**

```powershell
cd session21-python\frontend
npm install --no-audit --no-fund   # 62 packages, NPM INSTALL EXIT=0
npm run build
```

```text
vite v5.4.11 building for production...
✓ 30 modules transformed.
dist/index.html                 0.56 kB
dist/assets/index-*.css         6.63 kB
dist/assets/index-*.js        151.56 kB
✓ built in 1.54s
BUILD EXIT=0
```

All npm dependencies are now pinned to exact versions; previously every
dependency was `"latest"`, which is a reproducibility hazard.

### 3.7 Helm chart — **VERIFIED**

```powershell
helm lint .\helm\campusfix
#==> Linting .\helm\campusfix
#1 chart(s) linted, 0 chart(s) failed
#LINT EXIT=0
```

```powershell
helm template campusfix .\helm\campusfix -n campusfix --set ingress.enabled=true
#TEMPLATE EXIT=0 -> 11 resources
```

Rendered resources: `Secret`, `PersistentVolumeClaim`, `Service` ×3,
`Deployment` ×3, `HorizontalPodAutoscaler`, `Ingress`, `ServiceMonitor`.

A wiring verification script then asserted the rendered YAML against the
rubric. It **failed on the first run** and exposed a genuine bug — see §4.

After the fix, all checks passed:

```text
== Ingress routing ==            /api -> campusfix-backend (http) | / -> campusfix-frontend (http)
== Services ==                   both ClusterIP; backend 8000, frontend 8080
== Selector/pod-label match ==   backend PASS, frontend PASS
== Replicas ==                   backend 2, frontend 2
== Nginx upstream ==             BACKEND_UPSTREAM=campusfix-backend:8000
== Migrations ==                 initContainer ['alembic','upgrade','head']
== Probes ==                     /ready, /health, /healthz
== Non-root ==                   runAsNonRoot true on both
== HPA ==                        targets campusfix-backend, 2-6 replicas, cpu
== DB credentials ==             secretKeyRef on backend and postgres
== ServiceMonitor ==             selector matches backend Service labels
RESULT: ALL HELM WIRING CHECKS PASSED
```

### 3.8 Terraform — **VERIFIED (fmt / init / validate)**

```powershell
terraform fmt -check    # FIRST RUN: EXIT=3, main.tf unformatted
terraform fmt           # reformatted
terraform fmt -check    # RE-RUN: EXIT=0
```

`terraform init` result is recorded in §9. `terraform plan` requires AWS
credentials and is **BLOCKED** (§10).

### 3.9 Workflow and Compose syntax — **VERIFIED**

```python
yaml.safe_load(open('.github/workflows/ci-cd.yml'))
# YAML parses OK; jobs: ['test', 'build-scan-push', 'deploy']
```

Compose parsed and asserted:

```text
postgres   ports=['5432:5432']  healthcheck=yes
backend    ports=['8000:8000']  healthcheck=yes  depends_on=postgres:service_healthy
frontend   ports=['3000:8080']  healthcheck=yes  depends_on=backend:service_healthy
```

### 3.10 Secret and ignore audit — **VERIFIED**

A regex sweep for `AKIA*`, `ASIA*`, private-key headers, `ghp_*`,
`github_pat_*`, `xox*` and `aws_secret_access_key` across all tracked
Session 21 files produced **one** hit — `terraform.tfvars.example:3`, which is
the comment *"AWS authentication comes from the environment … not from this
file."* A documentation reference, not a credential. No `.env`, `*.tfstate`,
kubeconfig or `*.pem` is tracked anywhere in the repository.

`git check-ignore` confirms `.venv/`, `test.db`, `.terraform/`,
`node_modules/` and `__pycache__/` are all ignored. Seven stale
`__pycache__/*.pyc` files and one `.DS_Store` that had been committed were
untracked.

---

### 3.11 Load generators — **VERIFIED**

`scripts/load-test.sh` was **broken**: it pointed at
`http://taskboard.local/api/health`, a stale TaskBoard URL that is not a
CampusFix route, and nothing in the repository referenced it. It now defaults
to the CampusFix API, reports success/failure counts and latency percentiles,
and exits non-zero when requests fail. A PowerShell equivalent
(`scripts/load-test.ps1`) was added so the tool works on either platform.

Both were executed against the live backend:

```text
# Git Bash 5.2.37 (MSys) — proves .sh still runs here
URL=http://127.0.0.1:8000/api/tickets REQUESTS=25 ./scripts/load-test.sh
  elapsed 2s | successful 25 | failed 0 | avg 0.0045s | max 0.0076s
  BASH EXIT=0

# PowerShell
.\scripts\load-test.ps1 -Url http://127.0.0.1:8000/api/tickets -Requests 25
  elapsed 0.6s | successful 25 | failed 0 | avg 0.0247s | max 0.0541s

# Failure detection
.\scripts\load-test.ps1 -Url .../api/tickets/999999 -Requests 3
  successful 0 | failed 3  ->  exit 1  (correctly reported 404)
```

The generated traffic is visible in `/metrics`, which is the point of the tool:

```text
http_requests_total{handler="/api/tickets",method="GET",status="2xx"} 50.0
http_requests_total{handler="/health",method="GET",status="2xx"}       2.0
http_requests_total{handler="none",method="GET",status="4xx"}           1.0
```

---

## 3.12 Docker Compose on Linux containers — **VERIFIED (current WSL run)**

```bash
# Ubuntu 24.04 inside WSL 2
docker compose config
docker compose up --build -d
docker compose ps
```

```text
SERVICE    STATUS                    PORTS
backend    Up (healthy)             0.0.0.0:8000->8000/tcp
frontend   Up (healthy)             0.0.0.0:3000->8080/tcp
postgres   Up (healthy)             0.0.0.0:5432->5432/tcp
```

The `condition: service_healthy` chain worked exactly as designed —
`postgres Healthy → backend Healthy → frontend Started`.

**Non-root verified at runtime, not just declared:**

```text
backend    uid=10001  user=appuser
frontend   uid=101    user=nginx     (nginx -t passes)
```

**Database:** PostgreSQL 16.15, `alembic_version = 0002_campusfix_tickets`,
tables `tickets` + `alembic_version`, `tickets_pkey`, `tickets_id_seq`, and
`select count(*) from pg_class where relname like 'tasks%'` → **0**.

**Full CRUD through `http://localhost:3000` (nginx → FastAPI → PostgreSQL):**

| Request | Result |
|---|---|
| `POST /api/tickets` | **201** |
| `GET /api/tickets` | **200** |
| `PUT .../status=IN_PROGRESS` then `RESOLVED` | 200, 200 |
| `PUT` RESOLVED → IN_PROGRESS | **409** |
| `POST` invalid title | **422** |
| `GET` missing ticket | **404** |
| `DELETE /api/tickets/1` | **204** (empty body) |
| `GET` after delete | **404** |
| `GET /metrics` | 200, ~13 KB |

Current Compose browser evidence: [`14-campusfix-compose-app.png`](screenshots/14-campusfix-compose-app.png).
The older [`11-docker-compose-ui.png`](screenshots/11-docker-compose-ui.png)
is retained as historical evidence. Current terminal evidence of
`docker compose up --build` and all three healthy services is saved in
[`21-compose-build-terminal.png`](screenshots/21-compose-build-terminal.png),
[`21-compose-services-running.png`](screenshots/21-compose-services-running.png),
and [`21-compose-health-status.png`](screenshots/21-compose-health-status.png).

---

## 3.13 Kubernetes cluster + Helm deploy — **VERIFIED**

> **Current-state note (2026-10-16):** the historical command/output below
> records an earlier `campusfix.local` run and HPA scale test. The current
> deployment is Helm release `campusfix` revision 4 with two backend replicas,
> two frontend replicas and one PostgreSQL pod; the Ingress host is `localhost`.
> Current browser evidence is [`15-campusfix-kubernetes-ingress.png`](screenshots/15-campusfix-kubernetes-ingress.png).

All commands below ran inside **Ubuntu** as `shreeya@DESKTOP-G7A7T8M`.

```bash
minikube start --driver=docker --cpus=2 --memory=4096 --kubernetes-version=v1.34.0
kubectl apply -f k8s/namespace.yaml
helm lint ./helm/campusfix
helm upgrade --install campusfix ./helm/campusfix -n campusfix \
  --set backend.image=campusfix-backend --set backend.tag=local \
  --set backend.imagePullPolicy=IfNotPresent \
  --set frontend.image=campusfix-frontend --set frontend.tag=local \
  --set frontend.imagePullPolicy=IfNotPresent \
  --set ingress.enabled=true --set ingress.className=nginx --set ingress.host=campusfix.local
```

```text
* minikube v1.39.0 on Ubuntu 24.04 (kvm/amd64)
* Using the docker driver
* Preparing Kubernetes v1.34.0 on containerd 2.3.4
minikube start exit=0

namespace/campusfix created
==> Linting ./helm/campusfix
1 chart(s) linted, 0 chart(s) failed        # exit 0

NAME     	NAMESPACE	REVISION	STATUS   	CHART
campusfix	campusfix	4       	deployed	campusfix-1.0.0
```

```text
NAME                                  READY   STATUS    RESTARTS
campusfix-backend-6b56cbf8db-2sgpf    1/1     Running   0
campusfix-backend-6b56cbf8db-6h4nw    1/1     Running   0
campusfix-frontend-76c87fcc48-bsmg8   1/1     Running   0
campusfix-frontend-76c87fcc48-zstng   1/1     Running   0
campusfix-postgres-565bc89bdd-wvdvt   1/1     Running   0

NAME                         TYPE        CLUSTER-IP      PORT(S)
service/campusfix-backend    ClusterIP   10.103.119.122  8000/TCP
service/campusfix-frontend   ClusterIP   10.105.157.253  8080/TCP
service/campusfix-postgres   ClusterIP   10.97.159.123   5432/TCP

endpoints/campusfix-backend    10.244.0.6:8000,10.244.0.9:8000
endpoints/campusfix-frontend   10.244.0.10:8080,10.244.0.7:8080
endpoints/campusfix-postgres   10.244.0.8:5432

ingress/campusfix   CLASS=nginx   HOSTS=campusfix.local   ADDRESS=192.168.49.2   PORT=80
```

**Routing through the Ingress (port-forwarded controller, `Host: campusfix.local`):**

| Request | Result |
|---|---|
| `POST /api/tickets` | **201** `{"id":1,...,"category":"PLUMBING","status":"OPEN"}` |
| `GET /api/tickets` | **200** |
| `GET /api/tickets/stats` | **200** `{"total":1,"open":1,...}` |
| `GET /` | **200** `<title>CampusFix — Campus Maintenance & IT Support</title>` |
| `GET /metrics` | **200** |
| `DELETE /api/tickets/1` | **204** |

This is the proof that the original chart's broken routing
(`taskboard-backend` on port 8080, a Service that never existed) is fixed.

The backend `migrate` initContainer ran on **both** replicas
(`Started container migrate`).

---

## 3.14 Horizontal Pod Autoscaler — **VERIFIED (it really scaled)**

```bash
minikube addons enable metrics-server    # metrics-server v0.9.0, 1/1 Running
helm upgrade campusfix ... --set hpa.enabled=true \
  --set hpa.targetCPUUtilizationPercentage=50
```

Real load was applied (3 parallel loops hammering `/api/tickets` and
`/api/tickets/stats` from a `curlimages/curl` pod for 90 s):

```text
NAME                TARGETS        MINPODS  MAXPODS  REPLICAS
campusfix-backend   cpu: 61%/50%   2        6        3

campusfix-backend-6b56cbf8db-2sgpf   1/1  Running   0  13m
campusfix-backend-6b56cbf8db-6h4nw   1/1  Running   0  13m
campusfix-backend-6b56cbf8db-l95w4   1/1  Running   0  32s   <-- created by the HPA
```

A longer run reached the ceiling:

```text
campusfix-backend   cpu: 173%/50%   2   6   6
```

After the load generator was deleted, CPU fell to `5%/50%`. Replicas stayed at
6 across the following 160 s because the HPA's **default 5-minute scale-down
stabilisation window** had not elapsed; this is expected Kubernetes behaviour,
not a fault.

---

## 3.15 Prometheus and Grafana — **VERIFIED (current local deployment)**

The `monitoring` Helm release is installed in Minikube. CampusFix's
ServiceMonitor uses the matching `release: monitoring` label and Prometheus
discovers the two active backend replicas. Both targets were observed `UP`
(`2 / 2`) on the current Prometheus Targets page.

The current provisioned Grafana dashboard, `CampusFix API observability`, has
five populated panels: API requests over 15 minutes, ready CampusFix app pods,
request rate by route, p95 request latency, and responses by status. Its JSON
is in `monitoring/campusfix-dashboard.json`, and
`monitoring/campusfix-dashboard-configmap.yaml` provisions it through the
Grafana dashboard sidecar.

Current screenshots:

- [`16-campusfix-prometheus-targets.png`](screenshots/16-campusfix-prometheus-targets.png) — both backend scrape targets UP.
- [`17-campusfix-grafana-dashboard.png`](screenshots/17-campusfix-grafana-dashboard.png) — five live panels populated with app metrics.
- [`18-campusfix-metrics-endpoint.png`](screenshots/18-campusfix-metrics-endpoint.png) — Prometheus-formatted metrics from `/metrics`.

Screenshots 12 and 13 show a legitimate earlier Grafana/Prometheus state, but
their counts and panels are stale; use 16–18 for submission.

---

## 3.16 Troubleshooting lab — **VERIFIED (both reproduced and recovered)**

### Exercise 1 — invalid image tag

```text
$ kubectl apply -f troubleshooting/broken-image.yaml
deployment.apps/broken-image created

$ kubectl get pods -n campusfix -l app=broken-image
NAME                            READY   STATUS             RESTARTS   AGE
broken-image-6597b5b77f-6vdp9   0/1     ImagePullBackOff   0          20s

$ kubectl describe pod
Warning  Failed  kubelet  spec.containers{backend}: Failed to pull image
   "ghcr.io/example/campusfix-backend:does-not-exist": failed to resolve
   reference ...: failed to authorize: failed to fetch anonymous token:
   unexpected status from GET request to
   https://ghcr.io/token?...: 403 Forbidden
Warning  Failed  kubelet  spec.containers{backend}: Error: ErrImagePull
Normal   BackOff kubelet  spec.containers{backend}: Back-off pulling image ...
Warning  Failed  kubelet  spec.containers{backend}: Error: ImagePullBackOff
```

**Root cause:** the tag `:does-not-exist` does not exist in the registry, so the
kubelet cannot pull it and retries with exponential backoff.

**Recovery:**

```text
$ kubectl delete deployment broken-image -n campusfix
deployment.apps "broken-image" deleted from campusfix namespace
```

### Exercise 2 — Service selector matching no pods

```text
$ kubectl apply -f troubleshooting/broken-service.yaml
$ kubectl get svc broken-service -n campusfix
NAME             TYPE        CLUSTER-IP    PORT(S)
broken-service   ClusterIP   10.103.34.1   8080/TCP

$ kubectl get endpoints broken-service -n campusfix      # symptom
NAME             ENDPOINTS   AGE
broken-service   <none>      5s

$ kubectl get endpoints campusfix-frontend -n campusfix  # working contrast
NAME                 ENDPOINTS
campusfix-frontend   10.244.0.10:8080,10.244.0.7:8080

$ kubectl get pods -n campusfix --show-labels
campusfix-frontend-76c87fcc48-bsmg8  1/1  Running  0  45m
   app.kubernetes.io/component=frontend,app.kubernetes.io/instance=campusfix,
   app.kubernetes.io/name=campusfix,app=campusfix-frontend,pod-template-hash=76c87fcc48
```

**Root cause:** the Service selector `app: label-that-does-not-exist` matches no
pod, so no endpoints are created and traffic returns 503 — even though the pods
are `Running`. A Service selects pods by label; no matching label = no endpoints.

**Recovery:** `kubectl delete service broken-service -n campusfix`

### Final state — not left broken

```text
campusfix-backend    2/2   2   2     (current local deployment)
campusfix-frontend   2/2   2   2
campusfix-postgres   1/1   1   1
campusfix            campusfix  4  deployed
```

---

## 3.17 Local image security scans — **VERIFIED**

Trivy 0.76.0 scanned the rebuilt local backend and frontend images for HIGH and
CRITICAL findings, ignoring vulnerabilities without a fix available. Both
scans returned zero findings:

```bash
trivy image --ignore-unfixed --severity HIGH,CRITICAL session21-python-backend:latest
trivy image --ignore-unfixed --severity HIGH,CRITICAL session21-python-frontend:latest
```

This is local scan evidence only. The rubric asks for the Trivy output from a
GitHub Actions run as well. Run #4 passed both backend and frontend Trivy steps;
the configured gate scans HIGH and CRITICAL findings (ignoring unfixed issues)
and fails on a match. The backend report table showed zero vulnerabilities for
the listed OS and Python package targets. See §3.18 and screenshot 27.

## 3.18 GitHub Actions, Trivy, and GHCR — **VERIFIED**

Commit `ba32c7a60b82d2491e867ef2e420a60842caefb9` was pushed to
`capstone/campusfix-session21`. The real workflow run completed successfully
in 2m 14s:

| Job or result | Outcome |
|---|---|
| Backend tests and frontend build | **Success** |
| Build, scan, and publish images | **Success** |
| Trivy backend scan | **Success**; no HIGH/CRITICAL findings matched the configured gate; report table showed 0 vulnerabilities for listed targets |
| Trivy frontend scan | **Success**; no HIGH/CRITICAL findings matched the configured gate |
| GHCR publication | **Success**; backend and frontend images published with the full commit SHA tag |
| Deploy to Kubernetes via Helm | **Skipped**; the job condition permits deployment only on `main`, while this run was on `capstone/campusfix-session21` |

Run: [CampusFix CI/CD #4](https://github.com/ShreeyaReddyL/devops-heros/actions/runs/38886639159)

Published package pages: [campusfix-backend](https://github.com/users/ShreeyaReddyL/packages/container/package/campusfix-backend) and [campusfix-frontend](https://github.com/users/ShreeyaReddyL/packages/container/package/campusfix-frontend). Both packages are public. The tag is `ba32c7a60b82d2491e867ef2e420a60842caefb9`.

The workflow uses `severity: HIGH,CRITICAL`, `ignore-unfixed: true`, and
`exit-code: "1"`; a successful scan therefore means no findings matched that
configured gate. It does not mean the images have no vulnerabilities at every
severity. Screenshots 26–29 show the run, backend scan output, package list, and
backend tag page.

The run also completed with non-blocking maintenance annotations: the current
action versions emitted Node.js 20 deprecation warnings, `ubuntu-latest` emitted
an upcoming runner-image migration notice, and checkout post-cleanup reported
`git` exit 128. Neither job nor the workflow failed; review these annotations
when updating the Actions versions.

The workflow has not deployed this image to Kubernetes or AWS. Its deploy job
is `main`-only and currently consumes `KUBE_CONFIG_DATA`; AWS OIDC/EKS
deployment is a separate follow-up step.

## 4. Defects found and fixed

These were found by the checks above, not assumed.

| # | Component | Defect | Impact | Fix |
|---|---|---|---|---|
| 1 | CI/CD | `ghcr.io/${{ github.repository_owner }}/…` renders `ShreeyaReddyL`, and GHCR rejects uppercase in image paths | every push would fail at `docker push` | lowercase the owner in a dedicated step |
| 2 | CI/CD | `deploy` job had no secret guard | pipeline red whenever `KUBE_CONFIG_DATA` is unset | detect the secret, emit a notice, exit cleanly |
| 3 | Helm | Ingress pointed at Service `taskboard-backend` port **8080**; the real Service was `<release>-taskboard-backend` port **8000** | `/api` routing impossible | route through the `fullname` helper, port `8000` |
| 4 | Helm | Frontend Nginx proxied to `backend:8000`, a Service that does not exist in-cluster | frontend→backend calls fail on k8s | pass `BACKEND_UPSTREAM` env, envsubst template |
| 5 | Helm | **ServiceMonitor selected on `app.kubernetes.io/component: backend`, which the backend Service never set** | **Prometheus would never have scraped `/metrics`** | add the label to the Service (found by the wiring script) |
| 6 | Helm | Backend Deployment never ran migrations | schema not migrated on deploy | `initContainer: alembic upgrade head` |
| 7 | Helm | DB password hardcoded in `values.yaml` and rendered into a Secret | rubric flags hardcoded secrets | `postgres.existingSecret` support |
| 8 | Terraform | All `.tf` files were 1–3 lines of compressed inline HCL | `terraform fmt -check` fails | reformatted, documented |
| 9 | Terraform | EKS `1.31` | now **extended support**, billed at a higher hourly rate | `1.35` (standard support) |
| 10 | Terraform | `aws ~> 5.0` vs EKS module needing `>= 6.59` | module/provider incompatibility | modules `eks 21.29.0`, `vpc 6.7.3`, `aws ~> 6.0` (resolved to 6.68.0) |
| 11 | Docker Compose | no health checks, `depends_on` without a condition | migrations race PostgreSQL startup | health checks + `condition: service_healthy` |
| 12 | Docker | frontend Nginx ran as **root** | fails rubric M4 non-root criterion | unprivileged uid 101, port 8080, `/tmp` scratch |
| 13 | Migration 0002 | `status` kept `server_default 'TODO'` | invalid value outside the `TicketStatus` enum | `batch_alter_table` → `'OPEN'` |
| 14 | Tests | no cleanup; `test.db` persisted between runs | order-dependent results | autouse truncate fixture + temp-file teardown |
| 15 | Repo | 7 `.pyc` + 1 `.DS_Store` committed; `.gitignore` missing `__pycache__`, `.pyc`, `.venv`, `test.db` | rubric M3 | extended `.gitignore`, untracked the files |
| 16 | Frontend | all npm deps pinned to `"latest"` | non-reproducible builds; CI could break on any upstream release | exact versions pinned |
| 17 | Terraform | EKS module v21 removed the v20 argument names (`cluster_name`, `cluster_version`, `cluster_endpoint_public_access`, `cluster_addons`) | `terraform validate` failed; the stack would never apply | renamed to `name`, `kubernetes_version`, `endpoint_public_access`, `addons` |
| 18 | `scripts/load-test.sh` | pointed at `http://taskboard.local/api/health`, a stale TaskBoard URL and not a CampusFix route; referenced by nothing | rewrote against the CampusFix API, added latency/failure reporting, added a PowerShell equivalent |
| 19 | Frontend image | `/etc/nginx/conf.d` was root-owned, so the entrypoint's envsubst step could not render `default.conf`; nginx started with **no server block** and closed every connection. `nginx -t` still passed, so the healthcheck missed it | chown `conf.d`/`templates` to `nginx`; healthcheck now fetches `/healthz` instead of only validating syntax |
| 20 | Frontend image | `USER nginx` is a **name**; the kubelet cannot verify a username is non-root and refused to start every frontend pod (`CreateContainerConfigError`) | changed to `USER 101` (the nginx uid) so `runAsNonRoot: true` is satisfied |
| 21 | Migration 0002 | PostgreSQL does not follow a table rename, so `tasks_id_seq` and `tasks_pkey` survived — the schema still looked like the TaskBoard start | rename both in `upgrade()` and reverse in `downgrade()` |
| 22 | CI deploy | rollout verification referenced `campusfix-campusfix-backend`, but the Helm fullname helper renders `campusfix-backend` for this release | corrected the rollout check to use the rendered Deployment name; workflow has not yet run on GitHub |

---

## 5. Rubric checklist

| Module | Criterion | Status | Evidence |
|---|---|---|---|
| **M1** (10) | FastAPI starts, `/health` responds | **VERIFIED** | §3.5, §3.12 |
| | ≥ 4 REST endpoints (GET/POST/PUT/DELETE) | **VERIFIED** | §3.5, §3.12, §3.13 |
| | PostgreSQL + ≥ 1 Alembic migration | **VERIFIED** | §3.4, §3.12 (PostgreSQL 16.15, alembic_version 0002) |
| | React frontend renders, calls API | **VERIFIED** | §3.6, §3.12, §3.13, §9a |
| | Responsive usable UI | **VERIFIED** | §9a screenshots |
| **M2** (10) | pytest runs without errors | **VERIFIED** | 25 passed, exit 0 |
| | ≥ 5 tests over ≥ 3 endpoints | **VERIFIED** | 25 tests, 7 endpoints |
| | Test DB, not production | **VERIFIED** | §3.3 isolation |
| | `pytest.ini` / `conftest.py` correct | **VERIFIED** | both present |
| **M3** (5) | Public repo linked | **VERIFIED** | header |
| | At least 10 meaningful commits | **VERIFIED** | 64 commits in local history; current head is `cc7ec87` |
| | `.gitignore` covers `.env`, `__pycache__`, `node_modules`, `.venv` | **VERIFIED** | §3.10 |
| **M4** (10) | `backend/Dockerfile` builds | **VERIFIED** | §3.12 exit 0 |
| | `frontend/Dockerfile` multi-stage | **VERIFIED** | Node build → Nginx runtime |
| | Images run as non-root | **VERIFIED** | uid 10001 / uid 101 at runtime, §3.12 |
| | `docker compose up --build` starts 3 services | **VERIFIED** | all 3 healthy, §3.12 |
| **M5** (15) | Workflow exists, triggers on `main` | **VERIFIED** (config) | YAML parsed |
| | pytest job fails the build | **VERIFIED** (config) | `needs: test` |
| | Frontend built in pipeline | **VERIFIED** (config) | `npm run build` |
| | Both images built | **VERIFIED** (config) | build-push-action ×2 |
| | Pushed to GHCR | **VERIFIED** | Actions run #4 published both public packages, §3.18 |
| | SHA image tags | **VERIFIED** (config) | `:${github.sha}` |
| **M6** (5) | Trivy scans both images | **VERIFIED** (config) | 2 scan steps |
| | Fails on HIGH/CRITICAL | **VERIFIED** (config) | `exit-code: "1"` |
| | Explain a CVE / clean scan | **VERIFIED** | both Actions scans passed the configured HIGH/CRITICAL gate; backend report table is in screenshot 27, §3.18 |
| **M7** (15) | Valid HCL | **VERIFIED** | §3.8 |
| | `terraform init` | **VERIFIED** | §9, exit 0 |
| | `terraform validate` | **VERIFIED** | §9, Success |
| | `terraform plan` non-empty, no errors | **BLOCKED** | no AWS credentials |
| | VPC with ≥ 2 public subnets | **VERIFIED** (config) / **BLOCKED** (provisioned) | 2 public + 2 private |
| | EKS + ≥ 1 node group | **VERIFIED** (config) / **BLOCKED** (provisioned) | managed node group |
| | `terraform destroy` clean | **NOT TESTED** | nothing was applied |
| | `terraform.tfvars.example`, no creds | **VERIFIED** | §3.10 |
| **M8** (15) | `k8s/namespace.yaml` applies | **VERIFIED** | §3.13 |
| | Chart with Chart.yaml/values/templates | **VERIFIED** | `helm lint` exit 0 |
| | `helm upgrade --install` deploys | **VERIFIED** | §3.13, revision 4 deployed |
| | ≥ 2 replicas each | **VERIFIED** | current deployment: backend 2, frontend 2 |
| | ClusterIP Services | **VERIFIED** | 8000 / 8080 / 5432 |
| | Ingress `/`→frontend, `/api`→backend | **VERIFIED** | §3.13 routing table |
| | Pods Running | **VERIFIED** | current CampusFix namespace: 5/5 app/database pods Running |
| **M9** (10) | `/metrics` Prometheus format | **VERIFIED** | browser screenshot 18 and genuine terminal `curl` screenshot 25 |
| | Prometheus installed and scraping | **VERIFIED** | both current backend targets UP, screenshot 16 |
| | Grafana installed and accessible | **VERIFIED** | local Grafana dashboard screenshot 17 |
| | ≥ 1 live Grafana panel | **VERIFIED** | five populated panels, screenshot 17 |
| **M10** (5) | README explains the application | **VERIFIED** | `README.md` |
| | Live demo of a pipeline run and deployment update | **PIPELINE VERIFIED; DEPLOYMENT PENDING** | run #4 is green; deployment was skipped because the workflow is `main`-only and no AWS EKS deploy integration is configured |

---

## 6. Blockers

| Blocker | Reason | Unlocks |
|---|---|---|
| **AWS account credentials / CLI not configured** | No AWS credentials are connected to this workspace and no resources have been provisioned; the user plans to use a personal account with introductory credits | M7 plan/apply/destroy and AWS evidence |
| **Workflow deployment is not enabled for this branch** | `deploy` is restricted to `main` and still uses `KUBE_CONFIG_DATA`; run #4 on the capstone branch skipped it | AWS EKS deployment after the workflow is wired to AWS authentication |

The application, tests, Docker, local Kubernetes and observability layers were
verified in WSL. Genuine terminal captures are saved as screenshots 19–25;
GitHub Actions, CI Trivy, and GHCR evidence are saved as screenshots 26–29.
AWS evidence remains incomplete. This report does not claim that the whole
rubric is complete.

---

## 7. Repository hygiene

- Work is on `capstone/campusfix-session21`; `main` is untouched.
- No history was rewritten, no force-push, no previous session modified.
- One pre-existing uncommitted change (`session-11-kubernetes-services/README.md`)
  was found on entry and deliberately left untouched and uncommitted.
- No secrets were added.

---

## 8. Screenshots

The earlier `01-`…`08-` images were from TaskBoard/coursework, not CampusFix,
so they were removed from this capstone evidence folder on 2026-10-16. Images
in the individual earlier-session folders were left untouched. The current
screenshots below were captured from the actual application, observability
stack, and Ubuntu terminal. Use 14–25 for current evidence; 09–13 are earlier
CampusFix captures.

| File | What it proves |
|---|---|
| [`09-campusfix-browser-ui.png`](screenshots/09-campusfix-browser-ui.png) | Dashboard rendering live API data |
| [`10-campusfix-ticket-created.png`](screenshots/10-campusfix-ticket-created.png) | Ticket created through the UI form (round trip) |
| [`11-docker-compose-ui.png`](screenshots/11-docker-compose-ui.png) | Earlier Compose browser capture |
| [`12-grafana-dashboard.png`](screenshots/12-grafana-dashboard.png) | Earlier dashboard capture; superseded by 17 |
| [`13-prometheus-targets-up.png`](screenshots/13-prometheus-targets-up.png) | Earlier targets capture; superseded by 16 |
| [`14-campusfix-compose-app.png`](screenshots/14-campusfix-compose-app.png) | Current browser app served by the healthy Compose stack |
| [`15-campusfix-kubernetes-ingress.png`](screenshots/15-campusfix-kubernetes-ingress.png) | Current app served through Minikube Ingress |
| [`16-campusfix-prometheus-targets.png`](screenshots/16-campusfix-prometheus-targets.png) | Prometheus showing 2/2 CampusFix targets UP |
| [`17-campusfix-grafana-dashboard.png`](screenshots/17-campusfix-grafana-dashboard.png) | Current Grafana dashboard with five populated panels |
| [`18-campusfix-metrics-endpoint.png`](screenshots/18-campusfix-metrics-endpoint.png) | Prometheus metrics returned by `/metrics` |
| [`19-pytest-terminal.png`](screenshots/19-pytest-terminal.png) | Ubuntu Docker run: 25 pytest tests passed; two third-party deprecation warnings |
| [`20-git-history-terminal.png`](screenshots/20-git-history-terminal.png) | Recent Git history and current capstone branch |
| [`21-compose-build-terminal.png`](screenshots/21-compose-build-terminal.png) | `docker compose up --build` build output |
| [`21-compose-services-running.png`](screenshots/21-compose-services-running.png) | Compose images built and all three containers running |
| [`21-compose-health-status.png`](screenshots/21-compose-health-status.png) | `docker compose ps`: backend, frontend, and PostgreSQL healthy |
| [`22-kubernetes-pods-terminal.png`](screenshots/22-kubernetes-pods-terminal.png) | Five CampusFix pods are `1/1 Running` |
| [`23-kubernetes-services-terminal.png`](screenshots/23-kubernetes-services-terminal.png) | Backend, frontend, and PostgreSQL ClusterIP Services and ports |
| [`24-helm-release-terminal.png`](screenshots/24-helm-release-terminal.png) | Helm release `campusfix`, revision 4, deployed |
| [`25-metrics-curl-terminal.png`](screenshots/25-metrics-curl-terminal.png) | `curl` response from the Prometheus-format `/metrics` endpoint |
| [`26-github-actions-success.jpg`](screenshots/26-github-actions-success.jpg) | Actions run #4: test/build and image publish jobs succeeded; deploy job skipped on the capstone branch |
| [`27-github-actions-trivy-backend.jpg`](screenshots/27-github-actions-trivy-backend.jpg) | Backend Trivy report output from the successful CI scan |
| [`28-ghcr-packages-list.jpg`](screenshots/28-ghcr-packages-list.jpg) | Public backend and frontend GHCR packages created by run #4 |
| [`29-ghcr-backend-package-tag.jpg`](screenshots/29-ghcr-backend-package-tag.jpg) | Public backend package and full commit-SHA image tag |

**Completed:** the seven local terminal evidence items requested by the
instructor are captured above. The three Compose images complement the build
output with container and health status.

**Completed:** the green Actions run, the CI backend Trivy report, and the GHCR
package/tag screenshots are captured above. The frontend Trivy step also
passed in the same run.

**Still required:** AWS plan, VPC/EKS deployment, and destroy screenshots.
Those remain pending until AWS setup and deployment are completed. A local scan
or browser screenshot cannot substitute for AWS evidence.

The local terminal captures were taken from the real Ubuntu session on
2026-10-16; they are not rendered or reconstructed terminal output.

---

## 9. Terraform `init` / `validate` result — **VERIFIED**

```powershell
terraform init -no-color
```

```text
- Installing hashicorp/aws v6.68.0...   Installed (signed by HashiCorp)
- Installing hashicorp/tls v4.4.1...    Installed
- Installing hashicorp/time v0.14.2...  Installed
- Installing hashicorp/cloudinit v2.4.1, hashicorp/null v3.3.2
Terraform has been successfully initialized!
INIT EXIT=0
```

The AWS provider resolved to **6.68.0**, satisfying the EKS module's
`>= 6.59` constraint.

> **Defect found and fixed here.** The first `terraform validate` **failed**
> (exit 1) with five `Unsupported argument` errors. The
> `terraform-aws-modules/eks` module was **restructured in v21**: `cluster_name`
> → `name`, `cluster_version` → `kubernetes_version`,
> `cluster_endpoint_public_access` → `endpoint_public_access`,
> `cluster_addons` → `addons`. The original configuration used the removed v20
> names and would never have applied. After correcting them:

```powershell
terraform fmt            # no further changes
terraform validate       # Success! The configuration is valid.
terraform fmt -check     # EXIT=0
```

**`terraform validate` → Success, exit 0. `terraform fmt -check` → exit 0.**

`terraform plan` and `terraform apply` were **not run** — no AWS credentials are
configured on this machine, and `apply` creates billable resources (§10.3).

---

## 9a. Current browser evidence — **VERIFIED**

The current Compose browser capture at
[`screenshots/14-campusfix-compose-app.png`](screenshots/14-campusfix-compose-app.png)
shows the React frontend served by the Compose Nginx container on port 3000,
calling FastAPI and PostgreSQL. The current Kubernetes capture at
[`screenshots/15-campusfix-kubernetes-ingress.png`](screenshots/15-campusfix-kubernetes-ingress.png)
shows the same application through the Minikube Nginx Ingress via a localhost
port-forward. These are separate local database instances.

Screenshots 09 and 10 are older CampusFix UI captures from the earlier local
SQLite run. They are genuine but do not prove the current PostgreSQL-backed
Compose or Kubernetes deployments; use 14 and 15 for those claims.

Screenshots 19–25 now provide the separate real-terminal evidence for Compose,
pytest, Kubernetes pods/services, Helm, Git history, and `/metrics`. The
terminal images are original captures from the live Ubuntu session; no output
was fabricated into an image.

---

## 10. Remaining submission work

The non-AWS application work is in place and locally validated. The terminal
evidence for pytest, Git history, Compose startup, Kubernetes pods/services,
Helm, and `/metrics` is complete in §8. The real Actions/GHCR/CI Trivy evidence
is now captured in screenshots 26–29. AWS evidence remains outstanding.

GitHub Actions and GHCR have been demonstrated by run #4. For the M10
deployment update, the workflow still needs an AWS EKS deployment path: the
current job runs only on `main` and expects `KUBE_CONFIG_DATA`. The capstone
branch run therefore skipped deployment.

AWS is the next work phase. The user's personal AWS account and advertised
introductory credits have not yet been connected to this workspace, and no
resources have been provisioned. M7 plan/apply/destroy and AWS console evidence
remain outstanding. Review the actual account pricing and projected resources
before applying Terraform; a credit balance does not guarantee every
EKS-related charge will be covered.

---

## 11. Earlier claims and screenshots that are superseded

| Previous claim | Status |
|---|---|
| Environment `Ubuntu 22.04` on a hosted devbox | **SUPERSEDED** — current environment is Ubuntu 24.04.5 under WSL 2 |
| `10/10 passed` tests | **SUPERSEDED** — current suite has 25 passing tests |
| Zero HIGH/CRITICAL findings under configured Trivy gate | **VERIFIED** locally and in Actions run #4; see §3.17–§3.18 |
| AWS VPC + EKS deployed | **NOT TRUE / NOT DONE** — no AWS account credentials or Terraform apply exist |
| Kubernetes v1.30/v1.31 cluster | **SUPERSEDED** — local Minikube v1.34.0 was used |
| Six CampusFix scrape targets and seven dashboard panels | **HISTORICAL** — current run scrapes 2 backend targets and displays five current panels |
| Local terminal screenshots | **CAPTURED** — screenshots 19–25 in §8 |
| Actions and GHCR screenshots | **CAPTURED** — screenshots 26–29; run #4 succeeded |
| AWS screenshots | **MISSING** — account setup and AWS deployment remain pending |

---

## 12. Presentation and recording

The editable nine-slide deck is saved in `submission/CampusFix-Capstone-Deck.pptx`.
Its speaker notes include a short talk track and a suggested order for recording
the working application, Compose stack, tests, Minikube Ingress, Prometheus,
and Grafana. The final slide and speaker notes now report run #4 as green,
state that deployment was skipped on this branch, and leave AWS deployment as
the next phase. The slide deck is a guide, not a substitute for the
instructor's M10 live or recorded demo of a pushed change, pipeline run, and
deployment update.
