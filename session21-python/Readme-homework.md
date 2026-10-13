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

> **Important:** the previous version of this report described a Linux
> "devbox" with "10/10 passed" tests, "0 High/Critical CVEs", a live AWS
> deployment and working Grafana panels. Those claims were inherited from the
> starter repository. They were **not reproducible** on this machine and are
> listed in §11 as UNVERIFIED rather than restated as accomplishments.

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

Validation ran on **Windows 11**, PowerShell, **not** the Ubuntu devbox the
earlier report described.

| Tool | Version | How obtained |
|---|---|---|
| Git | 2.50.1.windows.1 | pre-installed |
| Python | **3.12.10** | installed per-user from python.org (no admin) |
| Node.js | v22.17.0 | pre-installed |
| npm | 10.9.2 | pre-installed |
| Helm | v3.16.3 | single binary, no admin |
| Terraform | v1.9.8 | single binary, no admin |

> **Why Python 3.12:** the machine's default `python` is 3.14.3, for which
> `psycopg-binary==3.2.3` publishes no wheel (PyPI lists cp38–cp313 only), so
> `pip install -r requirements.txt` would fall back to a source build and fail.
> 3.12 is also what `backend/Dockerfile` and the CI workflow use, so local,
> container and CI runs are consistent. 3.12.10 is the last 3.12 release that
> ships a Windows installer; 3.12.11+ are source-only security releases.

**Not installed:** Docker, WSL, AWS CLI, kubectl, Minikube. This report does not
assume any of them.

---

## 3. Verification log

All commands below were run in PowerShell from
`C:\Users\Dell\OneDrive\Desktop\devops`. Exit codes are the real ones.

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

---

## 5. Rubric checklist

| Module | Criterion | Status | Evidence |
|---|---|---|---|
| **M1** (10) | FastAPI starts, `/health` responds | **VERIFIED** | §3.5 live HTTP |
| | ≥ 4 REST endpoints (GET/POST/PUT/DELETE) | **VERIFIED** | §3.5 CRUD |
| | PostgreSQL + ≥ 1 Alembic migration | **VERIFIED** (schema) / **NOT TESTED** (Postgres runtime) | §3.4; Postgres needs Docker |
| | React frontend renders, calls API | **VERIFIED** | §9a real browser round trip |
| | Responsive usable UI | **VERIFIED** | §9a + screenshots 09/10 |
| **M2** (10) | pytest runs without errors | **VERIFIED** | 25 passed, exit 0 |
| | ≥ 5 tests over ≥ 3 endpoints | **VERIFIED** | 25 tests, 7 endpoints |
| | Test DB, not production | **VERIFIED** | §3.3 isolation |
| | `pytest.ini` / `conftest.py` correct | **VERIFIED** | both present |
| **M3** (5) | Public repo linked | **VERIFIED** | header |
| | Meaningful commit messages | **VERIFIED** | 2 milestone commits |
| | `.gitignore` covers `.env`, `__pycache__`, `node_modules`, `.venv` | **VERIFIED** | §3.10 |
| **M4** (10) | `backend/Dockerfile` builds | **NOT TESTED** | Docker not installed |
| | `frontend/Dockerfile` multi-stage | **VERIFIED** (Dockerfile content) | build-stage → Nginx |
| | Images run as non-root | **VERIFIED** (config) / **NOT TESTED** (runtime) | `USER 10001`, `USER nginx` |
| | `docker compose up --build` starts 3 services | **BLOCKED** | Docker not installed |
| **M5** (15) | Workflow exists, triggers on `main` | **VERIFIED** (config) | YAML parsed |
| | pytest job fails the build | **VERIFIED** (config) | `needs: test` |
| | Frontend built in pipeline | **VERIFIED** (config) | `npm run build` |
| | Both images built | **VERIFIED** (config) | build-push-action ×2 |
| | Pushed to GHCR | **NOT TESTED** | needs push + repo run |
| | SHA image tags | **VERIFIED** (config) | `:${github.sha}` |
| **M6** (5) | Trivy scans both images | **VERIFIED** (config) | 2 scan steps |
| | Fails on HIGH/CRITICAL | **VERIFIED** (config) | `exit-code: "1"` |
| | Explain a CVE / clean scan | **NOT TESTED** | needs a real pipeline run |
| **M7** (15) | Valid HCL | **VERIFIED** | §9 |
| | `terraform init` | **VERIFIED** | §9, exit 0 |
| | `terraform validate` | **VERIFIED** | §9, Success |
| | `terraform plan` non-empty, no errors | **BLOCKED** | no AWS credentials |
| | VPC with ≥ 2 public subnets | **VERIFIED** (config) / **BLOCKED** (provisioned) | 2 public + 2 private |
| | EKS + ≥ 1 node group | **VERIFIED** (config) / **BLOCKED** (provisioned) | managed node group |
| | `terraform destroy` clean | **NOT TESTED** | nothing was applied |
| | `terraform.tfvars.example`, no creds | **VERIFIED** | §3.10 |
| **M8** (15) | `k8s/namespace.yaml` applies | **BLOCKED** | no cluster |
| | Chart with Chart.yaml/values/templates | **VERIFIED** | `helm lint` exit 0 |
| | `helm upgrade --install` | **BLOCKED** | no cluster |
| | ≥ 2 replicas each | **VERIFIED** (rendered) | both `replicas: 2` |
| | ClusterIP Services | **VERIFIED** (rendered) | 8000 / 8080 |
| | Ingress `/`→frontend, `/api`→backend | **VERIFIED** (rendered) | §3.7 |
| | All pods Running | **BLOCKED** | no cluster |
| **M9** (10) | `/metrics` Prometheus format | **VERIFIED** | 13 597 bytes live |
| | Prometheus installed & scraping | **BLOCKED** | no cluster |
| | Grafana accessible | **BLOCKED** | no cluster |
| | Live Grafana panel | **BLOCKED** | no cluster |
| **M10** (5) | README explains the application | **VERIFIED** | `README.md` |
| | Live demo of a pipeline run | **NOT TESTED** | requires push + run |

---

## 6. Blockers

| Blocker | Reason | Unlocks |
|---|---|---|
| **Docker Desktop not installed** | requires an administrator UAC prompt; WSL 2 is also not installed | M4 runtime, M8 cluster, M9 |
| **No Kubernetes cluster** | depends on Docker Desktop | M8, M9, troubleshooting lab |
| **No AWS credentials / AWS CLI** | not configured on this machine | M7 `plan` / `apply` / `destroy` |
| **Not pushed to GitHub yet** | no push performed in this session | real Actions run, GHCR packages, Trivy results |

---

## 7. Repository hygiene

- Work is on `capstone/campusfix-session21`; `main` is untouched.
- No history was rewritten, no force-push, no previous session modified.
- One pre-existing uncommitted change (`session-11-kubernetes-services/README.md`)
  was found on entry and deliberately left untouched and uncommitted.
- No secrets were added.

---

## 8. Screenshots

Existing files in `screenshots/` (`01-`…`08-`) are earlier coursework and are
preserved untouched. Several depict a Linux devbox and results that could not be
reproduced here; they are **not** used as evidence for any claim in §5.

Two new screenshots were captured from the **actually running** application
during this session (see §9a):

| File | What it proves |
|---|---|
| [`09-campusfix-browser-ui.png`](screenshots/09-campusfix-browser-ui.png) | Dashboard rendering live data from the API |
| [`10-campusfix-ticket-created.png`](screenshots/10-campusfix-ticket-created.png) | Ticket created through the UI form, success state shown |

No screenshot has been fabricated, and none exists for Docker, AWS,
Kubernetes, GitHub Actions, Trivy or Grafana, because none of those ran here.

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

## 9a. Browser evidence — **VERIFIED**

Docker was unavailable, but the **production build** was verified end-to-end in
a real browser without it:

1. `npm run build` produced `dist/`.
2. `frontend/serve-dist.mjs` served `dist/` on `127.0.0.1:3000` and proxied
   `/api` to the FastAPI backend on `:8000` — the same split Nginx performs in
   the container.
3. Six realistic tickets were created and three were moved through the workflow
   (`POST` + `PUT`).
4. The CampusFix dashboard was opened at <http://127.0.0.1:3000>.

Observed in the rendered DOM:

```text
document.title = "CampusFix — Campus Maintenance & IT Support"
brand           = "CampusFix"
stats           = Total 6, Open 3, In progress 2, Resolved 1, Critical 1
categories      = Campus Wi-Fi 2, Projector/AV 1, Plumbing 1,
                  Lab Equipment 1, Electrical & Lighting 1
```

5. The **"Report issue"** form was filled in and submitted through the UI:

```text
notice        = "✓ Ticket #7 submitted."
form closed   = true
total tickets = 7   (was 6)
critical      = 2   (was 1)
first row     = "#7 Wi-Fi dead zone in the Central Library reading room"
```

That is a genuine full round trip — React form → `POST /api/tickets` → FastAPI →
SQLAlchemy → database → refetch → re-render.

Screenshots captured from the running application:

| File | Content |
|---|---|
| [`screenshots/09-campusfix-browser-ui.png`](screenshots/09-campusfix-browser-ui.png) | Dashboard with 6 live tickets, stats and category breakdown |
| [`screenshots/10-campusfix-ticket-created.png`](screenshots/10-campusfix-ticket-created.png) | After creating ticket #7 through the UI form |

> These were produced against a local SQLite database, not PostgreSQL, because
> Docker was not available. They prove the **application layer** (M1). They are
> not evidence of the Docker Compose stack (M4).

---

## 10. Exact next steps

### 10.1 Install Docker Desktop (needs administrator)

```powershell
# PowerShell, elevated
wsl --install
# reboot, then:
winget install -e --id Docker.DockerDesktop
```

After install, verify (PowerShell):

```powershell
docker version
docker compose version
```

Then run the stack:

```powershell
cd C:\Users\Dell\OneDrive\Desktop\devops\session21-python
docker compose up --build
docker compose ps
curl.exe http://localhost:8000/health
curl.exe http://localhost:3000
```

### 10.2 Push and watch a real pipeline

```powershell
cd C:\Users\Dell\OneDrive\Desktop\devops
git push -u origin capstone/campusfix-session21
```

Then open the Actions tab, confirm the green run, and record the Trivy output
and the GHCR package pages as real evidence.

### 10.3 Terraform (needs AWS credentials + cost approval)

```powershell
$env:PATH="$env:LOCALAPPDATA\DevOpsTools;$env:PATH"
cd C:\Users\Dell\OneDrive\Desktop\devops\session21-python\terraform
aws sts get-caller-identity
terraform plan
```

**Do not run `terraform apply` without explicit cost approval.** An EKS control
plane, two `t3.medium` nodes and a NAT gateway all bill hourly. Always finish
with `terraform destroy`.

---

## 11. Claims from the previous report that could not be verified

These appear in the earlier version of this file and are **not** restated as
achievements:

| Previous claim | Status |
|---|---|
| Environment "Ubuntu 22.04 LTS (`shreeya@devbox`)" | **UNVERIFIED** — this machine is Windows 11 with no WSL installed |
| "10/10 passed" tests | **SUPERSEDED** — the suite is now 25 tests and genuinely passes |
| "0 High/Critical CVEs" | **UNVERIFIED** — no Trivy run has executed on this machine |
| AWS VPC + EKS deployed | **UNVERIFIED** — no Terraform apply has run |
| Kubernetes v1.30/v1.31 cluster | **UNVERIFIED** — no cluster exists here |
| Grafana dashboard with live panels | **UNVERIFIED** — no monitoring stack has been installed |
| Screenshots of the above | **UNVERIFIED** — preserved as historical material only |