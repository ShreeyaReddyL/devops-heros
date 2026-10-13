# Session 21 — DevOps Final Capstone: CampusFix

> [!NOTE]
> **Capstone submission report, validation evidence and screenshots:**
> [Readme-homework.md](Readme-homework.md).

## 1. What this is

**CampusFix** is a campus maintenance and IT support ticketing system. Staff and
students report issues — dead Wi-Fi, burnt-out projectors, leaking taps, broken
lab equipment, electrical faults — and track them from `OPEN` through
`IN_PROGRESS` to `RESOLVED`.

It is a custom application built for this capstone. The rubric requires the
submitted domain to be the student's own, so this is not the reference
TaskBoard starter with renamed labels: the data model, validation rules, ticket
workflow, statistics, API surface, UI and tests are all campus-specific.

| Layer | Technology |
|---|---|
| Frontend | React 18 + Vite, CSS, Nginx (unprivileged, port 8080) |
| Backend | Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2.0 |
| Database | PostgreSQL 16, Alembic migrations |
| Tests | pytest 8, isolated SQLite |
| Local | Docker + Docker Compose |
| CI/CD | GitHub Actions |
| Registry | GitHub Container Registry (GHCR), commit-SHA tags |
| Security | Trivy image scanning, HIGH/CRITICAL gate |
| IaC | Terraform, AWS VPC + EKS |
| Orchestration | Kubernetes, Helm, Ingress, HPA |
| Observability | Prometheus (`/metrics`) + Grafana |

---

## 2. Architecture

```text
Browser  →  :3000  →  frontend (Nginx :8080)
                          │  proxies /api
                          ▼
                     backend (FastAPI :8000)  ──►  PostgreSQL 16
                          │
                          └── /metrics ──► Prometheus ──► Grafana

Git push → GitHub Actions → pytest → frontend build → docker build
         → Trivy gate → GHCR (:SHA) → (optional) Helm deploy to EKS
```

### Ticket model

| Field | Type | Notes |
|---|---|---|
| `id` | int | primary key |
| `title` | str(200) | required, min 5 chars, non-blank |
| `description` | text | optional |
| `category` | enum | `WI_FI`, `PROJECTOR`, `ELECTRICAL`, `PLUMBING`, `HOSTEL`, `LAB_EQUIPMENT`, `IT_SUPPORT`, `OTHER` |
| `building` | str(120) | campus location |
| `reporter` | str(120) | who reported it |
| `priority` | enum | `LOW`, `MEDIUM`, `HIGH`, `CRITICAL` |
| `status` | enum | `OPEN`, `IN_PROGRESS`, `RESOLVED` |
| `created_at` | timestamptz | set on insert |

### Ticket workflow

Transitions are enforced server-side in `ALLOWED_TRANSITIONS`
(`backend/app/schemas.py`); an illegal move returns **409**.

```text
OPEN ──► IN_PROGRESS ──► RESOLVED
  ▲            │              │
  └────────────┴──────────────┘   (reopen)
```

---

## 3. API

```text
GET    /                       service metadata
GET    /health                 liveness  (no DB access)
GET    /ready                  readiness (executes a real query)
GET    /metrics                Prometheus exposition

GET    /api/tickets            list; ?status= &category= &priority=
GET    /api/tickets/stats      counts by status, priority and category
GET    /api/tickets/{id}       read one            (404 if missing)
POST   /api/tickets            create              (201, 422 if invalid)
PUT    /api/tickets/{id}       update              (404 missing, 409 illegal transition)
DELETE /api/tickets/{id}       delete              (204, 404 if missing)
```

Interactive docs: <http://localhost:8000/docs>

---

## 4. Run it locally

### Option A — Docker Compose (recommended)

```bash
docker compose up --build
```

| URL | What |
|---|---|
| <http://localhost:3000> | CampusFix UI |
| <http://localhost:8000/docs> | Swagger UI |
| <http://localhost:8000/health> | liveness |
| <http://localhost:8000/metrics> | Prometheus metrics |

PostgreSQL has a health check and the backend waits for it, so `alembic upgrade
head` never races the database.

```bash
docker compose down       # stop
docker compose down -v    # stop and delete the database volume
```

### Option B — backend only (no Docker)

Requires Python 3.12+.

```bash
cd backend
python -m venv .venv
source .venv/bin/activate        # Windows PowerShell: .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
cp .env.example .env             # Windows: copy .env.example .env

export DATABASE_URL='postgresql+psycopg://campusfix:campusfix@localhost:5432/campusfix'
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

### Option C — frontend dev server

```bash
cd frontend
npm install
npm run dev        # http://localhost:5173, proxies /api to :8000
```

### Option D — serve the production build without Docker

Useful when you want to check the real bundle but have no container runtime.
`serve-dist.mjs` reproduces what Nginx does in the container — it serves `dist/`
and proxies `/api` to the backend:

```bash
cd frontend
npm run build
node serve-dist.mjs 3000 8000     # UI on :3000, API on :8000
```

---

## 5. Tests

```bash
cd backend
python -m pytest -v
```

The suite is fully isolated. `backend/conftest.py` points `DATABASE_URL` at a
temporary SQLite file **before** any `app.*` module is imported (the engine is
built at import time), truncates `tickets` before every test, and deletes the
file at the end of the session. The PostgreSQL database is never touched and
results do not depend on test ordering.

Covered: `/`, `/health`, `/ready`, `/metrics`, ticket create/read/list/filter/
update/delete, validation rejections (422), missing records (404), illegal
workflow transitions (409), and statistics.

---

## 6. CI/CD

`.github/workflows/ci-cd.yml` runs on pushes to `main` and on pull requests:

1. **test** — pytest, then `npm run build`. Failure stops the pipeline.
2. **build-scan-push** — builds both images, runs **Trivy with
   `exit-code: 1` on HIGH/CRITICAL**, then pushes to GHCR tagged with the
   commit SHA. The GHCR owner is lowercased because the registry rejects
   uppercase in image paths. Pull requests from forks build and scan but never
   publish.
3. **deploy** — optional. Requires a `KUBE_CONFIG_DATA` repository secret
   (base64 kubeconfig). **Without that secret the job logs a notice and exits
   cleanly instead of failing CI.** Documented in the workflow itself.

---

## 7. Terraform (AWS)

```bash
cd terraform
terraform init
terraform validate
terraform plan      # requires AWS credentials
terraform apply     # creates chargeable resources — see cost note
terraform destroy   # required after the evaluation
```

- Region defaults to `ap-south-1`.
- 2 public + 2 private subnets across 2 AZs, one NAT gateway.
- EKS cluster plus one managed node group (2 × `t3.medium` by default).
- Kubernetes version defaults to `1.35`, which is in Amazon EKS **standard**
  support. Versions 1.31–1.33 have moved to extended support, which bills at a
  higher hourly rate.
- `terraform.tfvars.example` contains no credentials. State, `.terraform/` and
  lock files are git-ignored.

> **Cost warning.** `terraform apply` creates an EKS control plane, EC2 worker
> nodes and a NAT gateway, all of which bill hourly. Always run
> `terraform destroy` when finished.

---

## 8. Kubernetes + Helm

```bash
kubectl apply -f k8s/namespace.yaml

helm upgrade --install campusfix ./helm/campusfix \
  -n campusfix --create-namespace \
  -f ./helm/campusfix/values-prod.yaml \
  --set backend.tag=<commit-sha> \
  --set frontend.tag=<commit-sha>
```

| Resource | Name pattern | Detail |
|---|---|---|
| Deployment | `campusfix-backend` | 2+ replicas, initContainer runs `alembic upgrade head` |
| Deployment | `campusfix-frontend` | 2+ replicas, Nginx on 8080 |
| Service | `campusfix-backend` | ClusterIP :8000 |
| Service | `campusfix-frontend` | ClusterIP :8080 |
| Ingress | `campusfix` | `/api` → backend, `/` → frontend |
| HPA | `campusfix-backend` | CPU 60%, 2–6 replicas |
| ServiceMonitor | `campusfix-backend` | scrapes `/metrics` every 15s |

Both Deployments run with `runAsNonRoot`. The frontend learns the backend
address from the `BACKEND_UPSTREAM` environment variable, so the same image
works under Docker Compose and under Kubernetes.

Database credentials come from a Kubernetes Secret. Set
`postgres.existingSecret` in production so the password is not stored in the
chart.

---

## 9. Observability

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm upgrade --install monitoring prometheus-community/kube-prometheus-stack \
  -n monitoring --create-namespace \
  -f monitoring/prometheus-values.yaml
```

The ServiceMonitor carries `release: kube-prometheus-stack`; keep that in sync
with `monitoring.release` in the chart values.

---

## 10. Troubleshooting lab

```bash
kubectl apply -f troubleshooting/broken-image.yaml     # ImagePullBackOff
kubectl apply -f troubleshooting/broken-service.yaml    # Service with no endpoints
```

Each manifest documents the expected symptom, the diagnostic commands and the
recovery step in its header.

---

## 11. Load generation

Useful for populating the Grafana panels and giving the HPA something to scale
against. Both scripts target the same URL and report the same figures.

```bash
# Linux / macOS / Git Bash
URL=http://localhost:3000/api/tickets REQUESTS=500 ./scripts/load-test.sh

# Windows PowerShell
.\scripts\load-test.ps1 -Url http://localhost:3000/api/tickets -Requests 500
```

Both exit non-zero if any request fails, so they double as CI smoke tests.

---

## 12. Repository layout

```text
session21-python/
├── backend/
│   ├── app/                    # main, models, schemas, db, config
│   ├── alembic/versions/       # 0001_create_tasks, 0002_campusfix_tickets
│   ├── tests/test_api.py       # 25 tests
│   ├── conftest.py             # database isolation fixtures
│   └── Dockerfile
├── frontend/
│   ├── src/main.jsx            # CampusFix dashboard
│   ├── nginx.conf.template     # envsubst upstream
│   └── Dockerfile              # Node build → unprivileged Nginx
├── helm/campusfix/             # Helm chart
├── k8s/                        # namespace
├── monitoring/                 # kube-prometheus-stack values
├── terraform/                  # AWS VPC + EKS
├── troubleshooting/            # deliberately broken manifests
└── .github/workflows/ci-cd.yml
```