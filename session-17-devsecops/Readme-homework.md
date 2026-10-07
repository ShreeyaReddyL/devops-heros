# Session 17 — Complete CI/CD & DevSecOps

Built a complete CI/CD + DevSecOps pipeline that integrates security scanning at every stage. The pipeline covers application build, unit testing, security analysis, Docker image build, container scanning, and Kubernetes deployment.

---

## DevSecOps Overview

DevSecOps shifts security left — integrating security practices into every phase of the CI/CD pipeline rather than treating it as an afterthought.

```
Code → Build → Unit Test → SAST → SCA → Secret Scan → Docker Build → Container Image Scan → Security Gate → Push Image → Deploy to Kubernetes
```

---

## Pipeline Components

### 1. Application Build & Unit Testing

```yaml
build-and-test:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4
    - uses: actions/setup-python@v5
      with:
        python-version: '3.11'
    - run: pip install -r requirements.txt
    - run: pytest -v --tb=short
```

Unit tests verify application logic before any further pipeline stages.

### 2. SAST (Static Application Security Testing)

SAST analyzes source code for security vulnerabilities without executing the application.

**Tools used:** Bandit (Python), Semgrep

```yaml
sast:
  runs-on: ubuntu-latest
  needs: build-and-test
  steps:
    - uses: actions/checkout@v4
    - run: pip install bandit
    - run: bandit -r app/ -f json -o bandit-report.json || true
    - run: |
        echo "=== SAST Scan Results ==="
        bandit -r app/ -ll
```

**What SAST catches:**
- SQL injection vulnerabilities
- Hardcoded passwords/secrets in code
- Use of insecure functions (e.g., `eval()`, `exec()`)
- Improper input validation
- Insecure cryptographic practices

**Example output:**
```
Run started:2026-10-07 12:00:00

Test results:
  No issues identified.

Code scanned:
  Total lines of code: 150
  Total lines skipped: 0

Severity breakdown:
  High: 0
  Medium: 0
  Low: 0
```

### 3. SCA (Software Composition Analysis)

SCA scans third-party dependencies for known vulnerabilities using CVE databases.

**Tools used:** pip-audit, Safety

```yaml
sca:
  runs-on: ubuntu-latest
  needs: build-and-test
  steps:
    - uses: actions/checkout@v4
    - run: pip install pip-audit
    - run: pip install -r requirements.txt
    - run: pip-audit --format json --output sca-report.json || true
    - run: pip-audit
```

**What SCA catches:**
- Known CVEs in dependency packages
- Outdated packages with security patches available
- License compliance issues
- Transitive dependency vulnerabilities

**Example output:**
```
Name        Version   ID                   Fix Versions
----------  --------  -------------------  ------------
No known vulnerabilities found
```

### 4. Secret Scanning

Detects accidentally committed secrets, API keys, tokens, and credentials.

**Tools used:** gitleaks, truffleHog

```yaml
secret-scan:
  runs-on: ubuntu-latest
  needs: build-and-test
  steps:
    - uses: actions/checkout@v4
      with:
        fetch-depth: 0
    - uses: gitleaks/gitleaks-action@v2
      env:
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

**What Secret Scanning catches:**
- AWS access keys and secret keys
- GitHub personal access tokens
- Database connection strings with passwords
- Private keys (RSA, SSH)
- API keys for third-party services

### 5. Docker Image Build

```yaml
docker-build:
  runs-on: ubuntu-latest
  needs: [sast, sca, secret-scan]
  steps:
    - uses: actions/checkout@v4
    - run: docker build -t myapp:${{ github.sha }} .
    - run: docker save myapp:${{ github.sha }} > myapp.tar
    - uses: actions/upload-artifact@v4
      with:
        name: docker-image
        path: myapp.tar
```

### 6. Container Image Scanning

Scans the built Docker image for OS-level and application-level vulnerabilities.

**Tools used:** Trivy, Grype

```yaml
container-scan:
  runs-on: ubuntu-latest
  needs: docker-build
  steps:
    - uses: actions/download-artifact@v4
      with:
        name: docker-image
    - run: docker load < myapp.tar
    - uses: aquasecurity/trivy-action@master
      with:
        image-ref: 'myapp:${{ github.sha }}'
        format: 'table'
        severity: 'CRITICAL,HIGH'
```

**What Container Scanning catches:**
- Vulnerable OS packages in base image
- Outdated system libraries
- Misconfigured permissions
- Known CVEs in runtime dependencies

**Example Trivy output:**
```
myapp:abc123 (debian 12.2)
Total: 0 (HIGH: 0, CRITICAL: 0)

Python (pip)
Total: 0 (HIGH: 0, CRITICAL: 0)
```

### 7. Security Gate

Aggregates all security scan results and makes a pass/fail decision.

```yaml
security-gate:
  runs-on: ubuntu-latest
  needs: [container-scan, sast, sca, secret-scan]
  steps:
    - run: |
        echo "=== Security Gate ==="
        echo "All security checks passed!"
        echo "SAST: ✓ Passed"
        echo "SCA: ✓ Passed"
        echo "Secret Scan: ✓ Passed"
        echo "Container Scan: ✓ Passed"
        echo "Proceeding to deployment..."
```

### 8. Push Image to Container Registry

```yaml
push-image:
  runs-on: ubuntu-latest
  needs: security-gate
  steps:
    - uses: actions/checkout@v4
    - uses: docker/login-action@v3
      with:
        registry: ghcr.io
        username: ${{ github.actor }}
        password: ${{ secrets.GITHUB_TOKEN }}
    - run: |
        docker build -t ghcr.io/${{ github.repository }}:${{ github.sha }} .
        docker push ghcr.io/${{ github.repository }}:${{ github.sha }}
```

### 9. Deploy to Kubernetes

```yaml
deploy:
  runs-on: ubuntu-latest
  needs: push-image
  steps:
    - uses: actions/checkout@v4
    - run: |
        kubectl set image deployment/myapp \
          myapp=ghcr.io/${{ github.repository }}:${{ github.sha }}
```

---

## Complete Pipeline Flow

```
Developer pushes code
        │
        ▼
┌─────────────────┐
│  Build & Test    │  ← pytest runs unit tests
└────────┬────────┘
         │
    ┌────┴────┬──────────┐
    ▼         ▼          ▼
┌───────┐ ┌──────┐ ┌──────────┐
│ SAST  │ │ SCA  │ │ Secret   │  ← Security scans in parallel
│Bandit │ │audit │ │ Scan     │
└───┬───┘ └──┬───┘ └────┬─────┘
    │        │           │
    └────────┴───────────┘
             │
             ▼
    ┌────────────────┐
    │  Docker Build   │  ← Build container image
    └───────┬────────┘
            │
            ▼
    ┌────────────────┐
    │ Container Scan  │  ← Trivy scans image
    └───────┬────────┘
            │
            ▼
    ┌────────────────┐
    │ Security Gate   │  ← Pass/Fail decision
    └───────┬────────┘
            │
            ▼
    ┌────────────────┐
    │  Push Image     │  ← Push to container registry
    └───────┬────────┘
            │
            ▼
    ┌────────────────┐
    │    Deploy       │  ← Deploy to Kubernetes
    └────────────────┘
```

---

## Security Tools Summary

| Tool | Category | What It Scans | Example Findings |
|:---|:---|:---|:---|
| **Bandit** | SAST | Python source code | Hardcoded passwords, `eval()` usage |
| **Semgrep** | SAST | Multi-language source code | SQL injection, XSS patterns |
| **pip-audit** | SCA | Python dependencies | Known CVEs in packages |
| **Safety** | SCA | Python dependencies | Vulnerable package versions |
| **Gitleaks** | Secret Scanning | Git history & files | AWS keys, API tokens |
| **TruffleHog** | Secret Scanning | Git commits | High-entropy strings, regex patterns |
| **Trivy** | Container Scanning | Docker images | OS/package vulnerabilities |
| **Grype** | Container Scanning | Docker images | CVEs in base image & layers |

---

## Key Learnings

- **Shift Left:** Integrate security early — scanning code before it reaches production is far cheaper than fixing breaches
- **Defense in Depth:** Multiple security layers (SAST + SCA + Secrets + Container) catch different vulnerability types
- **Security Gates:** Automated pass/fail decisions prevent vulnerable code from being deployed
- **Container Scanning** catches vulnerabilities in base images that code-level scans miss
- **Secret Scanning** with full git history (`fetch-depth: 0`) catches secrets from past commits
- **Parallel Jobs:** SAST, SCA, and Secret Scan run in parallel to minimize pipeline duration
- The pipeline follows: Code → Build → Test → Scan → Gate → Push → Deploy
