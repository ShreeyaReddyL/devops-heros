- https://github.com/Nency-Ravaliya/Kubernetes 

- k8s core objects: https://github.com/Nency-Ravaliya/Kubernetes/blob/main/core-objects.md

---

# Homework

Worked on core Kubernetes objects, pod lifecycle management, and rollout strategies. Tested everything on local minikube setup. Screenshots are in the `screenshots/` folder.

- `screenshots/01-rolling-update.png` — Deployed version 1 of the application, then performed a rolling update to version 2. Configured `maxSurge: 1` and `maxUnavailable: 0` in the deployment strategy, ensuring zero-downtime during the transition. New pods spin up before old ones terminate.
- `screenshots/02-rollout-undo.png` — Checked rollout history using `kubectl rollout history` and reverted to a previous version with `kubectl rollout undo`. The key insight: Kubernetes keeps the old ReplicaSet around with `DESIRED 0` replicas, so rollback is instant — no image re-pull is needed.
- `screenshots/03-troubleshooting.png` — Tested two intentionally broken manifests. `selector-mismatch.yaml` gets rejected immediately at apply time because the Deployment's selector must match the pod template labels. `broken-image.yaml` passes validation but fails at runtime with `ImagePullBackOff`, while existing pods continue running unaffected.
- `screenshots/04-troubleshooting-fix.png` — Used `kubectl describe pod` to inspect the Events section and identify the root cause, then ran `kubectl rollout undo` to restore working state. The workflow: describe to diagnose, undo to recover.
- `screenshots/05-blue-green-deployment.png` — Deployed Blue (v1) and Green (v2) environments simultaneously. Switched traffic instantly by updating the Service selector from `slot: blue` to `slot: green`. Demonstrated zero-downtime cutover and tested instant rollback capability.
- `screenshots/06-canary-deployment.png` — Deployed stable deployment (3 replicas) alongside canary deployment (1 replica) behind a common service. Tested traffic splitting verifying ~25% requests routed to the canary v2 release.
- `screenshots/07-pod-lifecycle.png` — Demonstrated Kubernetes pod lifecycle phases and failure states (`Pending`, `Running`, `CrashLoopBackOff`, `ImagePullBackOff`, `Completed/Succeeded`, and init containers). Checked status conditions (`PodScheduled`, `Initialized`, `ContainersReady`, `Ready`).