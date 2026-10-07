# Session 14 — Kubernetes Troubleshooting

Comprehensive hands-on practice with Kubernetes troubleshooting commands and common issues. Learned systematic debugging workflows for identifying, investigating, and resolving cluster issues.

---

## Task 1: Kubernetes Troubleshooting Commands

### kubectl get

The most basic command for listing resources. Used various flags to get richer information.

```bash
# List pods with extra details
kubectl get pods -o wide

# List all resources in all namespaces
kubectl get all --all-namespaces

# Watch for real-time changes
kubectl get pods -w

# Custom columns output
kubectl get pods -o custom-columns=NAME:.metadata.name,STATUS:.status.phase,NODE:.spec.nodeName
```

```
NAME                         STATUS    NODE
nginx-deploy-7fb96c846b-x1   Running   minikube
nginx-deploy-7fb96c846b-x2   Running   minikube
```

### kubectl describe

Provides detailed information about a resource, including events, conditions, and configuration.

```bash
kubectl describe pod nginx-deploy-7fb96c846b-x1
kubectl describe node minikube
kubectl describe svc my-service
```

Key sections to look at:
- **Events** — Shows scheduling, pulling, starting, and error events in chronological order
- **Conditions** — Pod conditions like `Initialized`, `Ready`, `ContainersReady`, `PodScheduled`
- **Containers** — Image, ports, resource requests/limits, probe configuration

### kubectl logs

Retrieves container logs for debugging application-level issues.

```bash
# Current container logs
kubectl logs nginx-deploy-7fb96c846b-x1

# Previous container logs (after a crash)
kubectl logs nginx-deploy-7fb96c846b-x1 --previous

# Follow logs in real-time
kubectl logs -f nginx-deploy-7fb96c846b-x1

# Logs from a specific container in a multi-container Pod
kubectl logs nginx-deploy-7fb96c846b-x1 -c sidecar

# Last 50 lines
kubectl logs nginx-deploy-7fb96c846b-x1 --tail=50

# Logs since last 5 minutes
kubectl logs nginx-deploy-7fb96c846b-x1 --since=5m
```

### kubectl exec

Executes commands inside a running container for interactive debugging.

```bash
# Run a single command
kubectl exec nginx-deploy-7fb96c846b-x1 -- cat /etc/nginx/nginx.conf

# Interactive shell
kubectl exec -it nginx-deploy-7fb96c846b-x1 -- /bin/sh

# Inside the container:
# Check networking
nslookup kubernetes.default
wget -qO- http://my-service:80
cat /etc/resolv.conf

# Check filesystem
ls -la /data
df -h

# Check environment
env | grep MY_
```

### kubectl events

Shows cluster-wide events sorted by timestamp.

```bash
kubectl get events --sort-by='.lastTimestamp'
kubectl get events --field-selector type=Warning
kubectl get events -n kube-system
```

```
LAST SEEN   TYPE      REASON              OBJECT                              MESSAGE
2m          Normal    Scheduled           pod/nginx-deploy-7fb96c846b-x1      Successfully assigned default/nginx to minikube
2m          Normal    Pulling             pod/nginx-deploy-7fb96c846b-x1      Pulling image "nginx:1.25"
1m          Normal    Pulled              pod/nginx-deploy-7fb96c846b-x1      Successfully pulled image "nginx:1.25"
1m          Normal    Created             pod/nginx-deploy-7fb96c846b-x1      Created container nginx
1m          Normal    Started             pod/nginx-deploy-7fb96c846b-x1      Started container nginx
```

### kubectl explain

Describes the schema and fields of a resource — invaluable for writing YAML manifests.

```bash
kubectl explain pod.spec.containers.livenessProbe
kubectl explain deployment.spec.strategy
kubectl explain service.spec.type
```

### kubectl top

Shows resource consumption (requires Metrics Server).

```bash
kubectl top nodes
kubectl top pods
kubectl top pods --sort-by=cpu
kubectl top pods --sort-by=memory
```

```
NAME                             CPU(cores)   MEMORY(bytes)
nginx-deploy-7fb96c846b-x1      1m           5Mi
nginx-deploy-7fb96c846b-x2      1m           5Mi
```

### kubectl get -o wide

Extended output with additional columns (Node, IP, etc.).

```bash
kubectl get pods -o wide
```

```
NAME                             READY   STATUS    RESTARTS   AGE   IP           NODE       NOMINATED NODE   READINESS GATES
nginx-deploy-7fb96c846b-x1      1/1     Running   0          5m    172.17.0.3   minikube   <none>           <none>
nginx-deploy-7fb96c846b-x2      1/1     Running   0          5m    172.17.0.4   minikube   <none>           <none>
```

---

## Task 2: Troubleshoot Common Issues

### CrashLoopBackOff

**Symptom:** Pod keeps restarting with increasing backoff delays.

```bash
kubectl get pods
```
```
NAME              READY   STATUS             RESTARTS      AGE
crash-demo-pod    0/1     CrashLoopBackOff   5 (2m ago)    8m
```

**Investigation:**
```bash
kubectl describe pod crash-demo-pod
kubectl logs crash-demo-pod --previous
```

**Root causes identified:**
1. Application error — missing config file or environment variable
2. Wrong command or entrypoint in container spec
3. Liveness probe misconfiguration causing premature kills
4. OOMKilled — container exceeding memory limits

**Fix:** Corrected the container command/args and ensured all required environment variables were set.

### ImagePullBackOff / ErrImagePull

**Symptom:** Pod stuck unable to pull container image.

```bash
kubectl get pods
```
```
NAME                READY   STATUS             RESTARTS   AGE
image-err-pod       0/1     ImagePullBackOff   0          3m
```

**Investigation:**
```bash
kubectl describe pod image-err-pod
```
Events show: `Failed to pull image "nginx:nonexistent": rpc error: code = NotFound`

**Root causes identified:**
1. Typo in image name or tag
2. Private registry without imagePullSecrets configured
3. Network connectivity issues to registry

**Fix:** Corrected the image tag from `nginx:nonexistent` to `nginx:1.25`.

### Pending Pods

**Symptom:** Pod stuck in `Pending` state indefinitely.

```bash
kubectl get pods
```
```
NAME             READY   STATUS    RESTARTS   AGE
pending-pod      0/1     Pending   0          5m
```

**Investigation:**
```bash
kubectl describe pod pending-pod
```
Events show: `0/1 nodes are available: 1 Insufficient cpu.`

**Root causes identified:**
1. Insufficient cluster resources (CPU/memory)
2. Node selector or affinity rules that can't be satisfied
3. Taints and tolerations mismatch
4. PVC not bound (no matching PV or StorageClass)

**Fix:** Reduced the resource requests to fit within available cluster capacity, or added additional nodes.

### ContainerCreating

**Symptom:** Pod stuck in `ContainerCreating` state.

**Root causes identified:**
1. Volume mount failing (PVC not bound, ConfigMap/Secret not found)
2. Image still being pulled (large image on slow connection)
3. Network plugin issues

**Fix:** Verified the referenced ConfigMap existed and created the missing resource.

### Service Connectivity Issues

**Investigation workflow:**
```bash
# Check Service exists and has endpoints
kubectl get svc my-service
kubectl get endpoints my-service

# Verify labels match
kubectl get pods --show-labels
kubectl get svc my-service -o yaml | grep selector -A 5

# Test DNS resolution
kubectl run dns-test --image=busybox:1.36 --rm -it --restart=Never -- nslookup my-service
```

**Common fixes:**
- Ensure Pod labels match Service selector
- Verify target port matches container port
- Check if Pods are in `Ready` state (readiness probe passing)

### DNS Issues

```bash
# Check CoreDNS pods are running
kubectl get pods -n kube-system -l k8s-app=kube-dns

# Test DNS from within a Pod
kubectl exec -it debug-pod -- nslookup kubernetes.default.svc.cluster.local
kubectl exec -it debug-pod -- cat /etc/resolv.conf
```

### Pod Networking Issues

```bash
# Check Pod IP
kubectl get pod my-pod -o wide

# Test connectivity between Pods
kubectl exec -it pod-a -- ping <pod-b-ip>
kubectl exec -it pod-a -- wget -qO- http://<pod-b-ip>:80
```

### Configuration Issues

```bash
# Verify ConfigMap/Secret data
kubectl get configmap my-config -o yaml
kubectl get secret my-secret -o yaml

# Check volume mounts
kubectl describe pod my-pod | grep -A 10 "Mounts"

# Check environment variables
kubectl exec my-pod -- env
```

---

## Task 3: Mini Project — Kubernetes Troubleshooting

Completed the troubleshooting mini-project scenarios:

### Scenario 1: Broken Deployment

**Problem:** Deployment Pods stuck in `ImagePullBackOff`.

```bash
kubectl apply -f scenarios/broken-deployment.yaml
kubectl get pods
kubectl describe pod <pod-name>
```

**Root Cause:** Image name had a typo — `ngingx:1.25` instead of `nginx:1.25`.

**Fix:**
```bash
kubectl set image deployment/broken-deploy nginx=nginx:1.25
kubectl get pods -w
```

**After fix:** All Pods transitioned to `Running` state.

### Scenario 2: Service Not Reachable

**Problem:** Service exists but returns no response.

**Root Cause:** Service selector `app: webapp` didn't match Pod labels `app: web-app` (dash vs no dash).

**Fix:** Updated Service selector to match Pod labels.

### Scenario 3: Resource Limits

**Problem:** Pods getting OOMKilled.

**Root Cause:** Memory limit set to 64Mi for an application requiring ~128Mi.

**Fix:** Increased memory limit to 256Mi with a request of 128Mi.

---

## Troubleshooting Flowchart

```
Pod Issue Detected
        │
        ├── Status: Pending
        │     └── kubectl describe pod → Check events
        │           ├── Insufficient resources → Scale nodes / reduce requests
        │           ├── Unschedulable → Check taints/tolerations
        │           └── PVC pending → Check StorageClass / PV
        │
        ├── Status: ImagePullBackOff
        │     └── kubectl describe pod → Check image name
        │           ├── Wrong image/tag → Fix image reference
        │           └── Private registry → Add imagePullSecrets
        │
        ├── Status: CrashLoopBackOff
        │     └── kubectl logs --previous → Check application logs
        │           ├── Config error → Fix ConfigMap/Secret/env
        │           ├── OOMKilled → Increase memory limits
        │           └── Probe failing → Fix probe configuration
        │
        └── Status: Running but not working
              └── kubectl get endpoints → Check Service connectivity
                    ├── No endpoints → Fix label selector mismatch
                    ├── DNS failure → Check CoreDNS pods
                    └── Port mismatch → Fix targetPort
```

---

## Key Learnings

- Always start with `kubectl get` → `kubectl describe` → `kubectl logs` workflow
- Events are the most informative source for scheduling and runtime errors
- `--previous` flag on `kubectl logs` captures logs from crashed containers
- Label selector mismatches between Pods and Services are a very common issue
- Resource limits (OOMKill) and probe misconfigurations are frequent causes of CrashLoopBackOff
