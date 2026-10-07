# Session 12 — Ingress, ConfigMaps & Secrets

Explored Ingress routing, ConfigMaps for externalized configuration, and Secrets for sensitive data. All exercises on local minikube with the Ingress addon enabled. Screenshots in the screenshots folder.

## Ingress

01-ingress-setup.png — Enabled the NGINX Ingress controller on minikube using `minikube addons enable ingress`, then verified it was running in the `ingress-nginx` namespace.

02-host-path-routing.png — Created an Ingress resource with both host-based and path-based routing rules. Host-based routes traffic based on the domain name (e.g., `app.local` → svc-a, `api.local` → svc-b). Path-based splits routes within the same host (e.g., `/app` → frontend, `/api` → backend). Updated `/etc/hosts` to map the minikube IP to custom hostnames.

03-default-backend.png — Configured a default backend to handle unmatched routes, returning a custom 404 page instead of the NGINX default. Any request that doesn't match a defined host or path rule falls through to this backend.

## ConfigMaps

04-configmap-env-vol.png — Created a ConfigMap with application settings and consumed it two ways:
- **Environment variables** — Injected using `envFrom` or individual `valueFrom` references. Simple for flat key-value pairs, but changes require a pod restart.
- **Volume mount** — Mounted the ConfigMap as files in the container filesystem. Kubernetes automatically updates the files when the ConfigMap changes (within ~60 seconds), enabling live config refresh without restarting.

05-configmap-update.png — Demonstrated live update: modified the ConfigMap data, then watched the mounted file update automatically inside the running pod. The kubelet sync loop picks up changes at the configured interval. Environment variable approach does NOT get live updates — pods must be restarted.

## Secrets

06-secrets-types.png — Worked with different Secret types:
- **Opaque** — General-purpose, base64-encoded values. Default type for `kubectl create secret generic`.
- **kubernetes.io/tls** — TLS certificates stored as `tls.crt` and `tls.key`. Used by Ingress for HTTPS termination.
- **kubernetes.io/dockerconfigjson** — Docker registry credentials for pulling private images.

07-secret-vs-configmap.png — Key differences: Secrets are base64-encoded (not encrypted by default), stored separately in etcd, and can be encrypted at rest with EncryptionConfiguration. ConfigMaps are plain text. Both can be consumed as environment variables or volume mounts. In production, use an external secrets manager (Vault, AWS Secrets Manager) and the External Secrets Operator.

08-tls-ingress.png — Generated a self-signed TLS certificate, stored it as a TLS Secret, and attached it to the Ingress resource. Verified HTTPS worked by curling with `--insecure` flag. The Ingress controller terminates TLS and forwards plain HTTP to the backend service.
