# Session 15 — Helm

Hands-on exploration of Helm — the Kubernetes package manager. Covered Helm commands, chart structure, installation, upgrade, rollback workflows, and the mini project.

---

## Task 1: Helm Commands

### helm create

Creates a new Helm chart with the default template structure.

```bash
helm create my-webapp
```

```
Creating my-webapp
```

Generated structure:
```
my-webapp/
├── Chart.yaml          # Chart metadata (name, version, appVersion)
├── values.yaml         # Default configuration values
├── charts/             # Dependency charts
├── templates/          # Kubernetes manifest templates
│   ├── deployment.yaml
│   ├── service.yaml
│   ├── serviceaccount.yaml
│   ├── hpa.yaml
│   ├── ingress.yaml
│   ├── _helpers.tpl    # Template helper functions
│   ├── NOTES.txt       # Post-install instructions
│   └── tests/
│       └── test-connection.yaml
└── .helmignore
```

### helm install

Installs a chart to the cluster, creating a release.

```bash
helm install my-release my-webapp/
```

```
NAME: my-release
LAST DEPLOYED: Wed Oct 07 2026 10:15:30
NAMESPACE: default
STATUS: deployed
REVISION: 1
```

### helm list

Lists all installed releases.

```bash
helm list
helm list --all-namespaces
```

```
NAME            NAMESPACE   REVISION    UPDATED                                 STATUS      CHART             APP VERSION
my-release      default     1           2026-10-07 10:15:30.123456 +0530 IST    deployed    my-webapp-0.1.0   1.16.0
```

### helm status

Shows the current status of a release.

```bash
helm status my-release
```

```
NAME: my-release
LAST DEPLOYED: Wed Oct 07 2026 10:15:30
NAMESPACE: default
STATUS: deployed
REVISION: 1
```

### helm get

Retrieves extended information about a release.

```bash
# Get all information
helm get all my-release

# Get only values
helm get values my-release

# Get computed manifest
helm get manifest my-release

# Get release notes
helm get notes my-release

# Get hooks
helm get hooks my-release
```

### helm upgrade

Upgrades a release with new values or chart version.

```bash
# Upgrade with new values
helm upgrade my-release my-webapp/ --set replicaCount=3

# Upgrade with values file
helm upgrade my-release my-webapp/ -f custom-values.yaml
```

```
Release "my-release" has been upgraded. Happy Helming!
NAME: my-release
LAST DEPLOYED: Wed Oct 07 2026 10:30:00
NAMESPACE: default
STATUS: deployed
REVISION: 2
```

### helm history

Shows the revision history of a release.

```bash
helm history my-release
```

```
REVISION    UPDATED                     STATUS       CHART             APP VERSION    DESCRIPTION
1           Wed Oct 07 10:15:30 2026    superseded   my-webapp-0.1.0   1.16.0         Install complete
2           Wed Oct 07 10:30:00 2026    deployed     my-webapp-0.1.0   1.16.0         Upgrade complete
```

### helm rollback

Rolls back a release to a previous revision.

```bash
helm rollback my-release 1
```

```
Rollback was a success! Happy Helming!
```

### helm uninstall

Removes a release from the cluster.

```bash
helm uninstall my-release
```

```
release "my-release" uninstalled
```

### helm repo

Manages chart repositories.

```bash
# Add a repo
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo add stable https://charts.helm.sh/stable

# Update repos
helm repo update

# List repos
helm repo list

# Remove repo
helm repo remove stable
```

```
NAME        URL
bitnami     https://charts.bitnami.com/bitnami
```

### helm search

Searches for charts in repos or the Artifact Hub.

```bash
# Search in added repos
helm search repo nginx
helm search repo bitnami/mysql

# Search Artifact Hub
helm search hub wordpress
```

```
NAME                    CHART VERSION   APP VERSION   DESCRIPTION
bitnami/nginx           15.3.5          1.25.3        NGINX is a high-performance web server...
bitnami/nginx-ingress   9.9.4           1.9.4         NGINX Ingress Controller...
```

---

## Task 2: Helm Rollback Workflow

Performed the complete install → upgrade → verify → upgrade → verify → rollback → verify workflow:

### Step 1: Install (Revision 1)

```bash
helm install webapp my-webapp/ --set image.tag=1.24
helm list
kubectl get pods
```

```
NAME            NAMESPACE   REVISION   STATUS     CHART             APP VERSION
webapp          default     1          deployed   my-webapp-0.1.0   1.16.0
```

Pods running with `nginx:1.24`.

### Step 2: Upgrade to v1.25 (Revision 2)

```bash
helm upgrade webapp my-webapp/ --set image.tag=1.25
kubectl get pods -w
```

```
Release "webapp" has been upgraded.
REVISION: 2
```

Verified new Pods are running `nginx:1.25`:
```bash
kubectl describe pod <pod-name> | grep Image
```
```
Image: nginx:1.25
```

### Step 3: Upgrade to v1.26 (Revision 3)

```bash
helm upgrade webapp my-webapp/ --set image.tag=1.26
helm history webapp
```

```
REVISION   UPDATED                    STATUS       CHART             DESCRIPTION
1          Wed Oct 07 10:15:30 2026   superseded   my-webapp-0.1.0   Install complete
2          Wed Oct 07 10:30:00 2026   superseded   my-webapp-0.1.0   Upgrade complete
3          Wed Oct 07 10:45:00 2026   deployed     my-webapp-0.1.0   Upgrade complete
```

### Step 4: Rollback to Revision 1

```bash
helm rollback webapp 1
helm history webapp
```

```
REVISION   UPDATED                    STATUS       CHART             DESCRIPTION
1          Wed Oct 07 10:15:30 2026   superseded   my-webapp-0.1.0   Install complete
2          Wed Oct 07 10:30:00 2026   superseded   my-webapp-0.1.0   Upgrade complete
3          Wed Oct 07 10:45:00 2026   superseded   my-webapp-0.1.0   Upgrade complete
4          Wed Oct 07 11:00:00 2026   deployed     my-webapp-0.1.0   Rollback to 1
```

Verified Pods reverted to `nginx:1.24`:
```bash
kubectl describe pod <pod-name> | grep Image
```
```
Image: nginx:1.24
```

**Key takeaway:** Rolling back creates a NEW revision (Revision 4) that matches the state of the target revision (Revision 1). Helm never modifies history — it only appends.

---

## Task 3: Mini Project

Completed the Helm mini project — deployed a complete application using a custom Helm chart with:

```bash
# Deploy the application
helm install demo-app mini-project/

# Verify
kubectl get all
helm status demo-app
```

The chart included:
- **Deployment** with configurable replicas, image, and resource limits
- **Service** (ClusterIP) exposing the application
- **HPA** for autoscaling based on CPU utilization
- **ConfigMap** for application configuration
- **Values files** for different environments (dev, staging, prod)

### Chart Structure

```
mini-project/
├── Chart.yaml
├── values.yaml
└── templates/
    ├── deployment.yaml
    ├── service.yaml
    ├── hpa.yaml
    └── _helpers.tpl
```

### Testing Different Configurations

```bash
# Install with custom values
helm install demo-app mini-project/ -f mini-project/values-prod.yaml

# Dry-run to preview manifests
helm install demo-app mini-project/ --dry-run --debug

# Template rendering
helm template demo-app mini-project/
```

---

## Chart.yaml vs values.yaml

| File | Purpose | Example Content |
|:---|:---|:---|
| **Chart.yaml** | Chart metadata — name, version, description, dependencies | `name: my-webapp`, `version: 0.1.0` |
| **values.yaml** | Default configuration values consumed by templates | `replicaCount: 2`, `image.tag: 1.25` |

---

## Key Learnings

- Helm charts package Kubernetes manifests with Go templates for configurability
- `values.yaml` provides defaults; overrides via `--set` or `-f custom-values.yaml`
- `helm history` tracks all revisions; `helm rollback` creates a new revision
- Always use `--dry-run` before applying changes to production
- Helm repos like Bitnami provide production-ready charts for common applications
- Template functions (`{{ .Values.replicaCount }}`, `{{ include "chart.name" . }}`) enable DRY manifests
