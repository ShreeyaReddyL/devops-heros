# CampusFix — DevOps Capstone

CampusFix is a campus maintenance and IT-support ticketing application. Students
and staff can report Wi-Fi, classroom equipment, electrical, plumbing, hostel,
and lab issues, then track them through an `OPEN` → `IN_PROGRESS` → `RESOLVED`
workflow.

This repository contains the course session material and the capstone project
in [`session21-python/`](session21-python/). The project uses a custom campus
support domain rather than copying the TaskBoard reference application.

## Run the application

From the repository root, run:

```bash
cd session21-python
docker compose up --build
```

Then open <http://localhost:3000>. The API is available at
<http://localhost:8000/docs>, with health and metrics at `/health` and
`/metrics`.

Run the isolated backend test suite with:

```bash
cd session21-python/backend
python -m pytest -v
```

## Project documentation

- [CampusFix architecture, APIs, local setup, Kubernetes, and observability](session21-python/README.md)
- [Instructor grading rubric](session21-python/GRADING.md)
- [Capstone validation report and evidence status](session21-python/Readme-homework.md)
- [Screenshots](session21-python/screenshots/)

GitHub Actions builds and scans the frontend and backend images. Terraform
configuration for AWS VPC and EKS is included; AWS resources are not deployed
yet.

## Course links

- DevOps homework: <https://docs.google.com/document/d/1cjXFYf2Thm8cBEN-0C48B-v02cj3jGLd47lcO18prHE/edit?usp=sharing>
- Submission form, Section A: <https://forms.gle/ydjAJcwxjpjBXgxB8>
- Submission form, Section B: <https://forms.gle/pAuXQaokwVzhRzit6>

