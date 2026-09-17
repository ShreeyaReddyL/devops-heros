# Session 11 — Kubernetes Services

Covered Kubernetes service types, DNS resolution, and deployment strategies. All exercises done on local minikube cluster. Screenshots in the screenshots folder.

## Service Types

01-five-service-types.png — Deployed all five Kubernetes service types and verified them with `kubectl get svc` and endpoint inspection. Services solve a fundamental problem: pod IPs are ephemeral and change on every restart, so a Service provides a stable DNS name and virtual IP that discovers pods via label selectors.

- **ClusterIP** — Default type, only reachable within the cluster. Used for internal microservice communication.
- **NodePort** — Exposes the service on a static port (range 30000-32767) on each node. Useful for development and quick testing.
- **LoadBalancer** — Provisions a cloud-provided external IP. Sits on top of NodePort under the hood.
- **ExternalName** — A DNS CNAME alias pointing to an external hostname. No ClusterIP, no endpoints, no proxying.
- **Headless** — Set `clusterIP: None`. Instead of load-balancing to one virtual IP, DNS returns individual pod IPs. Essential for StatefulSets where clients need direct pod access.

## DNS and Service Discovery

02-service-dns-proof.png — Demonstrated the key difference between ClusterIP and Headless services. A regular ClusterIP service resolves to a single virtual IP address, while a Headless service returns all pod IPs directly — one A record per pod.

03-externalname-loadbalancer.png — ExternalName correctly returns its CNAME alias without any endpoints. LoadBalancer shows `<pending>` for external IP because minikube doesn't have a cloud controller to provision one, but it still works through the NodePort fallback. The CNAME target doesn't need to resolve — ExternalName is purely a DNS-level alias.

04-coredns-fqdn.png — Explored CoreDNS configuration, examined `/etc/resolv.conf` inside a pod, and tested both short and fully-qualified lookups. The full form is `svc-name.namespace.svc.cluster.local`. Short names resolve within the same namespace thanks to the search domain list. The `ndots:5` setting means names with fewer than 5 dots try all search domains first, which can slow down external DNS lookups.

## Deployment Strategies

05-blue-green.png — Ran both v1 (blue) and v2 (green) deployments simultaneously, then switched the Service selector from `slot: blue` to `slot: green`. Traffic cuts over immediately with zero restarts. The tradeoff: you need double the resources while both versions are running.

06-canary.png — Deployed 9 stable replicas and 1 canary replica behind the same Service. Ran 30 curl requests — got 29 from stable and 1 from canary. The traffic split is purely based on replica ratio, not any routing configuration.

07-recreate.png — The only strategy that causes downtime. All old pods terminate before new ones start. Pod count goes from 3/3 ready → 0/3 (curl fails) → new version comes up. Use when two different versions cannot coexist (e.g., database schema conflicts).

## Workload Controllers

08-rs-vs-deployment.png — `kubectl rollout history` works on Deployments but errors on bare ReplicaSets. A ReplicaSet only maintains the desired pod count with no versioning or rollback. A Deployment wraps ReplicaSets and adds revision tracking and undo capability.

**Deployment vs StatefulSet vs DaemonSet:**
- **Deployment** — Stateless workloads. Pods get random names and can land on any node.
- **StatefulSet** — Ordered, stable pod names (e.g., `db-0`, `db-1`) with persistent storage. Used for databases and stateful applications.
- **DaemonSet** — No replica count. Runs exactly one pod per node. Used for monitoring agents, log collectors, and node-level daemons.
