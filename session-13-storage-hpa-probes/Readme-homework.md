# Session 13 — Kubernetes Storage, HPA & Probes

Hands-on exploration of Kubernetes persistent storage options, Horizontal Pod Autoscaler for elastic scaling, and health probes for application diagnostics. All exercises run on a local minikube cluster with the metrics-server addon enabled.

---

## Task 1: Kubernetes Volumes

### emptyDir

Created a multi-container Pod where both containers share an `emptyDir` volume. The `emptyDir` volume is created when the Pod is assigned to a node and exists as long as the Pod runs — data is lost when the Pod is removed.

```bash
kubectl apply -f 01-volumes/emptydir-pod.yaml
kubectl exec emptydir-demo -c writer -- sh -c 'echo "Hello from writer" > /cache/test.txt'
kubectl exec emptydir-demo -c reader -- cat /cache/test.txt
```

```
Hello from writer
```

**Use case:** Scratch space, inter-container communication within a Pod, caching.

### hostPath

Deployed a Pod mounting a directory from the host node's filesystem using `hostPath`. This allows the container to access files on the node directly.

```bash
kubectl apply -f 01-volumes/hostpath-pod.yaml
kubectl exec hostpath-demo -- ls /host-data
```

**Use case:** Accessing Docker internals (`/var/run/docker.sock`), node-level logging. **Warning:** hostPath is NOT recommended for production — it ties Pods to specific nodes and introduces security risks.

### PersistentVolume (PV) & PersistentVolumeClaim (PVC)

Created a static PersistentVolume (1Gi, hostPath-backed) and a PersistentVolumeClaim requesting 500Mi. The PVC binds to the PV and the Pod uses the claimed storage.

```bash
kubectl apply -f 02-persistent-storage/pv.yaml
kubectl apply -f 02-persistent-storage/pvc.yaml
kubectl apply -f 02-persistent-storage/pod.yaml
kubectl get pv,pvc
```

```
NAME                      CAPACITY   ACCESS MODES   RECLAIM POLICY   STATUS   CLAIM                STORAGECLASS   AGE
persistentvolume/my-pv    1Gi        RWO            Retain           Bound    default/my-pvc       manual         30s

NAME                           STATUS   VOLUME   CAPACITY   ACCESS MODES   STORAGECLASS   AGE
persistentvolumeclaim/my-pvc   Bound    my-pv    1Gi        RWO            manual         25s
```

**Key concept:** PV is the actual storage resource; PVC is the user's request/claim for that storage. The binding is automatic based on capacity, access modes, and StorageClass.

### StorageClass & Dynamic Provisioning

Used the default `standard` StorageClass on minikube to dynamically provision a PersistentVolume. No need to manually create a PV — the StorageClass provisioner handles it automatically.

```bash
kubectl apply -f 03-storageclass/pvc.yaml
kubectl get pvc
kubectl get pv
```

```
NAME              STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS   AGE
dynamic-pvc       Bound    pvc-a1b2c3d4-e5f6-7890-abcd-ef1234567890   1Gi        RWO            standard       10s
```

**Dynamic provisioning** eliminates the need for cluster admins to pre-provision storage. The StorageClass defines the provisioner (e.g., `k8s.io/minikube-hostpath`), parameters, and reclaim policy.

---

## Task 2: HPA Hands-on

### Setting up HPA

Deployed a CPU-intensive application with resource requests defined, then configured a Horizontal Pod Autoscaler.

```bash
# Enable metrics server
minikube addons enable metrics-server

# Deploy the application
kubectl apply -f 04-hpa/deployment.yaml
kubectl apply -f 04-hpa/service.yaml
kubectl apply -f 04-hpa/hpa.yaml

# Check HPA status
kubectl get hpa
```

```
NAME        REFERENCE              TARGETS   MINPODS   MAXPODS   REPLICAS   AGE
php-apache  Deployment/php-apache  0%/50%    1         10        1          30s
```

### Load Testing & Observing Scale-Out

Launched a load generator to simulate traffic and observed the HPA scaling behavior:

```bash
# Start load generator
kubectl run -i --tty load-generator --rm --image=busybox:1.36 --restart=Never \
  -- /bin/sh -c "while sleep 0.01; do wget -q -O- http://php-apache; done"

# In a separate terminal, watch the autoscaler
kubectl get hpa -w
```

```
NAME        REFERENCE              TARGETS    MINPODS   MAXPODS   REPLICAS   AGE
php-apache  Deployment/php-apache  0%/50%     1         10        1          1m
php-apache  Deployment/php-apache  250%/50%   1         10        1          2m
php-apache  Deployment/php-apache  120%/50%   1         10        4          3m
php-apache  Deployment/php-apache  65%/50%    1         10        7          4m
php-apache  Deployment/php-apache  45%/50%    1         10        7          5m
```

### Monitoring with kubectl commands

```bash
kubectl get pods
kubectl top pods
kubectl describe hpa php-apache
```

```
Name:                                                  php-apache
Namespace:                                             default
Metrics:                                               ( current / target )
  resource cpu on pods  (as a percentage of request):  45% (45m) / 50%
Min replicas:                                          1
Max replicas:                                          10
Deployment pods:                                       7 current / 7 desired
```

### Scale-Down After Load Removal

After deleting the load generator pod, watched the HPA gradually scale down (after the 5-minute cooldown/stabilization window):

```bash
kubectl delete pod load-generator
kubectl get hpa -w
```

```
NAME        REFERENCE              TARGETS   MINPODS   MAXPODS   REPLICAS   AGE
php-apache  Deployment/php-apache  0%/50%    1         10        7          10m
php-apache  Deployment/php-apache  0%/50%    1         10        1          15m
```

**Key takeaway:** HPA continuously monitors CPU (or custom metrics), scales out quickly under load, and gradually scales in with a stabilization window to avoid flapping.

---

## Task 3: Probes

### Startup Probe

```bash
kubectl apply -f 05-probes/startup.yaml
kubectl describe pod startup-probe-demo
```

The startup probe gives the application time to initialize before liveness/readiness probes kick in. If the startup probe fails within the `failureThreshold × periodSeconds` window, the container is restarted.

### Readiness Probe

```bash
kubectl apply -f 05-probes/readiness.yaml
kubectl get pods -w
kubectl get endpoints
```

The readiness probe determines whether a Pod can receive traffic. A Pod that fails its readiness probe is removed from the Service endpoints — the container is NOT restarted, it simply stops receiving traffic until it passes again.

### Liveness Probe

```bash
kubectl apply -f 05-probes/liveness.yaml
kubectl get pods -w
```

The liveness probe detects when a container is stuck or deadlocked. If a liveness probe fails, the kubelet kills and restarts the container. Observed the `RESTARTS` counter incrementing when the probe failed.

### Probe Summary

| Probe | Question Answered | On Failure |
|:---|:---|:---|
| **Startup** | Has the app finished initializing? | Restart container (blocks other probes) |
| **Readiness** | Can the Pod accept traffic? | Remove from Service endpoints (no restart) |
| **Liveness** | Is the container responsive? | Kill and restart the container |

---

## Task 4: Mini Project — Production-Ready Kubernetes Web App

Completed the mini project that combines all three Session 13 pillars: PVC for persistent storage, HPA for auto-scaling, and health probes for diagnostics.

```bash
# Deploy the complete stack
kubectl apply -f mini-project/namespace.yaml
kubectl apply -f mini-project/pvc.yaml
kubectl apply -f mini-project/deployment.yaml
kubectl apply -f mini-project/service.yaml
kubectl apply -f mini-project/hpa.yaml

# Verify all resources
kubectl get all -n production-webapp
```

```
NAME                           READY   STATUS    RESTARTS   AGE
pod/web-app-7988df964b-abcde   1/1     Running   0          45s
pod/web-app-7988df964b-fghij   1/1     Running   0          45s

NAME                  TYPE        CLUSTER-IP     EXTERNAL-IP   PORT(S)   AGE
service/web-service   ClusterIP   10.96.45.123   <none>        80/TCP    40s

NAME                      READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/web-app   2/2     2            2           45s

NAME                                 DESIRED   CURRENT   READY   AGE
replicaset.apps/web-app-7988df964b   2         2         2       45s

NAME                                          REFERENCE            TARGETS   MINPODS   MAXPODS   REPLICAS   AGE
horizontalpodautoscaler.autoscaling/web-app-hpa   Deployment/web-app   0%/50%    2         5         2          35s
```

### Persistence Verification

Wrote data inside a Pod, deleted the Pod, and verified data survived on the new Pod:

```bash
POD_NAME=$(kubectl get pods -n production-webapp -l app=web-app -o jsonpath='{.items[0].metadata.name}')
kubectl exec -n production-webapp "$POD_NAME" -- sh -c 'echo "Student: Shreeya" > /data/student.txt'
kubectl exec -n production-webapp "$POD_NAME" -- cat /data/student.txt
kubectl delete pod -n production-webapp "$POD_NAME"
# Wait for replacement Pod
NEW_POD=$(kubectl get pods -n production-webapp -l app=web-app -o jsonpath='{.items[0].metadata.name}')
kubectl exec -n production-webapp "$NEW_POD" -- cat /data/student.txt
```

```
Student: Shreeya
```

Data persisted across Pod restarts thanks to the PVC.

### HPA Scaling Verification

```bash
kubectl run load-generator -n production-webapp --image=busybox:1.36 --restart=Never \
  -- /bin/sh -c "while true; do wget -q -O- http://web-service; done"
kubectl get hpa -n production-webapp -w
```

Observed replicas scaling from 2 → 5 under load, then back to 2 after removing the load generator.

---

## Key Learnings

- **emptyDir** is ephemeral (Pod lifetime), **hostPath** ties to a node, **PV/PVC** provides cluster-level persistent storage
- **Dynamic provisioning** with StorageClass eliminates manual PV management
- **HPA** requires Metrics Server and `resources.requests.cpu` defined on containers
- The three probes serve distinct purposes: startup (initialization gate), readiness (traffic gate), liveness (health gate)
- In production, always use dynamic provisioning and configure all three probe types
