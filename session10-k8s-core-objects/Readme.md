- https://github.com/Nency-Ravaliya/Kubernetes 

- k8s core objects: https://github.com/Nency-Ravaliya/Kubernetes/blob/main/core-objects.md

---

# Homework

Worked on core Kubernetes objects, pod lifecycle management, and rollout strategies. Tested everything on local minikube setup. Screenshots are in the screenshots folder.

01-rolling-update.png — Deployed version 1 of the application, then performed a rolling update to version 2. Configured `maxSurge: 1` and `maxUnavailable: 0` in the deployment strategy, ensuring zero-downtime during the transition. New pods spin up before old ones terminate.

02-rollout-undo.png — Checked rollout history using `kubectl rollout history` and reverted to a previous version with `kubectl rollout undo`. The key insight: Kubernetes keeps the old ReplicaSet around with `DESIRED 0` replicas, so rollback is instant — no image re-pull is needed.

03-troubleshooting.png — Tested two intentionally broken manifests. `selector-mismatch.yaml` gets rejected immediately at apply time because the Deployment's selector must match the pod template labels. `broken-image.yaml` passes validation but fails at runtime with `ImagePullBackOff`, while existing pods continue running unaffected.

04-troubleshooting-fix.png — Used `kubectl describe pod` to inspect the Events section and identify the root cause, then ran `kubectl rollout undo` to restore working state. The workflow: describe to diagnose, undo to recover.