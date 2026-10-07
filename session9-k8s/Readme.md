# Resources

- https://kubernetes.io/docs/tutorials/kubernetes-basics/
- https://minikube.sigs.k8s.io/docs/start/?arch=%2Fmacos%2Farm64%2Fstable%2Fbinary+download 

- https://kubernetes.io/docs/concepts/architecture/

- https://github.com/Nency-Ravaliya/Kubernetes

---

# Homework

Explored Kubernetes basics and pod creation. Used minikube on local setup. Screenshots are available in the `screenshots/` folder.

- `screenshots/01-minikube-status.png` — Checked minikube version, cluster status using `minikube status`, and verified nodes with `kubectl get nodes`. The cluster runs as a single Docker container on the host machine.
- `screenshots/02-handwritten-pod.png` — Created pod.yaml manually without referencing documentation. Every Kubernetes object requires four key fields: apiVersion, kind, metadata, and spec. Applied the manifest using `kubectl apply -f pod.yaml` and confirmed it was running.