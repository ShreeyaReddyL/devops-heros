# Session 16 — CI/CD & GitHub Actions

Built a complete CI/CD demo project using GitHub Actions, covering the core concepts of Continuous Integration and Continuous Delivery.

---

## CI vs CD

### Continuous Integration (CI)
- Developers frequently merge code changes into a shared repository
- Automated build and test processes run on every push/PR
- Catches bugs early, reduces integration problems
- **Key activities:** Code compilation, unit testing, linting, static analysis

### Continuous Delivery (CD)
- Extends CI by automatically deploying to staging/production environments
- Every code change that passes CI is ready for production deployment
- Deployment to production can be manual (Delivery) or automatic (Deployment)
- **Key activities:** Docker build, image push, Kubernetes deployment, smoke tests

```
CI                              CD
│                               │
├── Code Commit                 ├── Build Docker Image
├── Automated Build             ├── Push to Registry
├── Unit Tests                  ├── Deploy to Staging
├── Integration Tests           ├── Integration Tests
└── Code Quality Checks         ├── Deploy to Production
                                └── Smoke Tests
```

---

## GitHub Actions Concepts

### Workflow
A YAML file defining the automated process, triggered by events like `push`, `pull_request`, or `schedule`. Stored in `.github/workflows/`.

### Jobs
Independent units of work within a workflow. Jobs run in parallel by default; use `needs:` to define dependencies.

### Steps
Individual tasks within a job. Each step runs a shell command or uses a pre-built action (e.g., `actions/checkout@v4`).

### Runners
The compute environment where jobs execute. GitHub provides hosted runners (`ubuntu-latest`, `windows-latest`, `macos-latest`), or you can use self-hosted runners.

### Secrets
Encrypted environment variables stored in GitHub repository settings. Accessed via `${{ secrets.SECRET_NAME }}`. Never hardcode sensitive data in workflows.

### Artifacts
Files produced by a workflow (build outputs, test reports, logs). Uploaded with `actions/upload-artifact` and downloaded with `actions/download-artifact`.

---

## Demo Project: CI/CD Pipeline

### Application Structure

```
cicd-demo/
├── app/
│   └── calculator.py       # Simple calculator application
├── tests/
│   └── test_calculator.py  # Unit tests with pytest
├── Dockerfile               # Container image definition
├── requirements.txt         # Python dependencies
├── build.sh                 # Build script
└── .github/
    └── workflows/
        └── ci-cd.yml        # GitHub Actions workflow
```

### Application Code

**app/calculator.py:**
```python
def add(a, b):
    return a + b

def subtract(a, b):
    return a - b

def multiply(a, b):
    return a * b

def divide(a, b):
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b

if __name__ == "__main__":
    print("Calculator App")
    print(f"2 + 3 = {add(2, 3)}")
    print(f"10 - 4 = {subtract(10, 4)}")
    print(f"5 * 6 = {multiply(5, 6)}")
    print(f"15 / 3 = {divide(15, 3)}")
```

**tests/test_calculator.py:**
```python
from app.calculator import add, subtract, multiply, divide
import pytest

def test_add():
    assert add(2, 3) == 5

def test_subtract():
    assert subtract(10, 4) == 6

def test_multiply():
    assert multiply(5, 6) == 30

def test_divide():
    assert divide(15, 3) == 5.0

def test_divide_by_zero():
    with pytest.raises(ValueError):
        divide(10, 0)
```

### GitHub Actions Workflow

**.github/workflows/ci-cd.yml:**
```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    name: Test Application
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Run tests
        run: pytest -v

  security-check:
    name: Security Check
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Check for sensitive files
        run: |
          echo "Checking for sensitive files..."
          FOUND=0
          for pattern in ".env" "*.pem" "*.key" "*.p12"; do
            if find . -name "$pattern" | grep -q .; then
              echo "WARNING: Found sensitive file matching $pattern"
              FOUND=1
            fi
          done
          if [ $FOUND -eq 1 ]; then
            echo "Security check failed!"
            exit 1
          fi
          echo "Security check passed!"

  build:
    name: Build Application
    runs-on: ubuntu-latest
    needs: test
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Build application
        run: |
          mkdir -p build
          cp app/calculator.py build/
          echo "Build Date: $(date)" > build/build-info.txt
          echo "Commit: ${{ github.sha }}" >> build/build-info.txt
          echo "Branch: ${{ github.ref_name }}" >> build/build-info.txt

      - name: Upload build artifact
        uses: actions/upload-artifact@v4
        with:
          name: calculator-build
          path: build/
```

### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/
COPY tests/ ./tests/

CMD ["python", "app/calculator.py"]
```

---

## Pipeline Execution

### Successful Run

```
CI/CD Pipeline
│
├── ✓ Test Application          (45s)
│   ├── Checkout code
│   ├── Setup Python 3.11
│   ├── Install dependencies
│   └── Run tests (5 passed)
│
├── ✓ Security Check            (12s)
│   ├── Checkout code
│   └── Check for sensitive files (passed)
│
└── ✓ Build Application         (20s)    [depends on: test]
    ├── Checkout code
    ├── Build application
    └── Upload build artifact
```

### Failure Scenario

Intentionally broke the `add` function to demonstrate pipeline failure:

```python
def add(a, b):
    return a + b + 1  # Bug introduced
```

```
CI/CD Pipeline
│
├── ✗ Test Application          (FAILED)
│   └── pytest: FAILED (test_add - AssertionError: 6 != 5)
│
├── ✓ Security Check            (passed)
│
└── ⊘ Build Application         (SKIPPED - depends on failed test)
```

The `build` job was automatically skipped because it has `needs: test`, and the test job failed. This demonstrates the safety net of CI — broken code never reaches the build/deploy stage.

After fixing the bug and pushing:
```
CI/CD Pipeline
│
├── ✓ Test Application          (passed)
├── ✓ Security Check            (passed)
└── ✓ Build Application         (passed + artifact uploaded)
```

---

## Build Artifact

The pipeline produces a downloadable artifact `calculator-build` containing:

```
build/
├── calculator.py       # Application source
└── build-info.txt      # Build metadata
```

**build-info.txt:**
```
Build Date: Wed Oct 07 12:00:00 UTC 2026
Commit: a1b2c3d4e5f6789012345678abcdef
Branch: main
```

Artifacts are available for download from the GitHub Actions run page and are retained for 90 days by default.

---

## Key Learnings

- GitHub Actions workflows are event-driven — triggered by `push`, `pull_request`, `schedule`, etc.
- Jobs run in parallel by default; use `needs:` to enforce ordering
- `actions/checkout@v4` is required in every job that needs source code
- Secrets should NEVER be committed — use GitHub repository secrets
- Artifacts persist build outputs between jobs and for later download
- CI ensures broken code is caught immediately; CD automates the path to production
- The `security-check` job runs in parallel with `test` — demonstrating independent job execution
