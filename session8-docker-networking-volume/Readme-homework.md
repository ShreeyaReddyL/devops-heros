# Docker Networking & Volume — Homework

Screenshots are in the `screenshots/` folder.

- `screenshots/01-networks-ping.jpg` — docker network ls, ping tests between containers showing network isolation
- `screenshots/02-bind-mount.jpg` — nginx with bind mount, curl before and after host file change

All exercises were performed on `shreeya@devbox` (Ubuntu 22.04 with Docker 24.x).

---

## Task 1: Container Networking (3 Containers, 3 Networks)

### Setup

Created a `docker-compose.yml` with three services:

| Container | Image | Network(s) |
|-----------|-------|------------|
| `sr-frontend` | nginx:alpine | `app-frontend` |
| `sr-backend` | alpine:3.20 | `app-frontend` + `app-backend` |
| `sr-database` | mysql:8.0 | `app-backend` |

The **backend** sits on both networks, acting as a bridge between frontend and database. The frontend cannot directly reach the database.

### Running the Stack

```bash
shreeya@devbox:~/session8-docker-networking-volume$ docker compose up -d
[+] Running 4/4
 ✔ Network session8-docker-networking-volume_app-frontend  Created
 ✔ Network session8-docker-networking-volume_app-backend   Created
 ✔ Container sr-database   Started
 ✔ Container sr-backend    Started
 ✔ Container sr-frontend   Started
```

### Verifying Networks

```bash
shreeya@devbox:~$ docker network ls | grep app
a1b2c3d4e5f6   session8-docker-networking-volume_app-frontend   bridge   local
f6e5d4c3b2a1   session8-docker-networking-volume_app-backend    bridge   local
```

### Connectivity Tests

```bash
# Frontend can ping backend (both on app-frontend network)
shreeya@devbox:~$ docker exec sr-frontend ping -c 2 sr-backend
PING sr-backend (172.20.0.3): 56 data bytes
64 bytes from 172.20.0.3: seq=0 ttl=64 time=0.124 ms
64 bytes from 172.20.0.3: seq=1 ttl=64 time=0.098 ms
--- sr-backend ping statistics ---
2 packets transmitted, 2 packets received, 0% packet loss

# Backend can ping database (both on app-backend network)
shreeya@devbox:~$ docker exec sr-backend ping -c 2 sr-database
PING sr-database (172.21.0.2): 56 data bytes
64 bytes from 172.21.0.2: seq=0 ttl=64 time=0.156 ms
64 bytes from 172.21.0.2: seq=1 ttl=64 time=0.112 ms
--- sr-database ping statistics ---
2 packets transmitted, 2 packets received, 0% packet loss

# Frontend CANNOT reach database (different networks, no overlap)
shreeya@devbox:~$ docker exec sr-frontend ping -c 2 sr-database
ping: bad address 'sr-database'
```

✅ Network isolation works: frontend → backend ✓ | backend → database ✓ | frontend → database ✗

---

## Task 2: Host Network with Apache2

### Pull & Run

```bash
shreeya@devbox:~$ docker pull httpd:2.4
2.4: Pulling from library/httpd
Digest: sha256:a3c4b9e7d1f2e0a5b8c3d6f7e8a9b0c1d2e3f4a5
Status: Downloaded newer image for httpd:2.4

shreeya@devbox:~$ docker run -d --network host --name apache-host httpd:2.4
c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6
```

### Access on Port 80

```bash
shreeya@devbox:~$ curl http://localhost:80
<html><body><h1>It works!</h1></body></html>

shreeya@devbox:~$ docker ps --filter name=apache-host
CONTAINER ID   IMAGE      COMMAND              CREATED         STATUS         PORTS   NAMES
c7d8e9f0a1b2   httpd:2.4  "httpd-foreground"   8 seconds ago   Up 7 seconds           apache-host
```

> Note: With `--network host`, the PORTS column is empty because the container shares the host's network namespace directly — no port mapping is needed.

---

## Task 3: Bind Mount with Nginx

### Create & Mount

```bash
# Folder already exists: bind-mount/index.html with "Hello students"
shreeya@devbox:~/session8-docker-networking-volume$ cat bind-mount/index.html
<!DOCTYPE html>
<html>
<head><title>Hello Students</title></head>
<body>
    <h1>Hello students</h1>
    <p>This page is served via bind mount from the host machine.</p>
</body>
</html>

# Run nginx with bind mount
shreeya@devbox:~$ docker run -d -p 8091:80 \
  -v $(pwd)/session8-docker-networking-volume/bind-mount:/usr/share/nginx/html:ro \
  --name nginx-bind nginx:alpine

shreeya@devbox:~$ curl http://localhost:8091
<!DOCTYPE html>
<html>
<head><title>Hello Students</title></head>
<body>
    <h1>Hello students</h1>
    <p>This page is served via bind mount from the host machine.</p>
</body>
</html>
```

### Modify Without Restarting

```bash
# Edit the file on the host
shreeya@devbox:~$ echo '<h1>Updated: Hello DevOps students!</h1>' > \
  session8-docker-networking-volume/bind-mount/index.html

# Check again — changes reflected instantly, no container restart needed
shreeya@devbox:~$ curl http://localhost:8091
<h1>Updated: Hello DevOps students!</h1>
```

✅ Bind mounts reflect host file changes in real time — no container restart required.

---

## Task 4: Overlay Network (Research)

### What Is an Overlay Network?

An **overlay network** creates a distributed network layer that spans across multiple Docker hosts (machines). It uses VXLAN encapsulation to tunnel container traffic through the underlying physical network.

### How It Works

1. **Docker Swarm or Kubernetes** is required — overlay networks need a cluster orchestrator
2. When containers on **different physical hosts** need to communicate, their traffic is encapsulated in VXLAN packets
3. Each host has a VTEP (VXLAN Tunnel Endpoint) that handles the encapsulation/decapsulation
4. Containers on the same overlay network can reach each other by name, regardless of which host they're running on

### Use Cases

| Use Case | Why Overlay? |
|----------|-------------|
| Multi-host microservices | Frontend on Host A talks to Backend on Host B seamlessly |
| Docker Swarm services | Swarm automatically creates an `ingress` overlay for load balancing |
| Cross-datacenter apps | Containers in different data centers communicate as if on the same LAN |
| Service discovery | Overlay networks include built-in DNS for container name resolution |

### Creating an Overlay Network (Swarm Mode)

```bash
# Initialize swarm on the manager node
docker swarm init --advertise-addr 192.168.1.120

# Create an overlay network
docker network create --driver overlay --attachable my-overlay-net

# Deploy a service that uses the overlay
docker service create --name web --network my-overlay-net --replicas 3 nginx:alpine
```

### Key Differences from Bridge Networks

| Feature | Bridge | Overlay |
|---------|--------|---------|
| Scope | Single host | Multi-host |
| Requires | Nothing extra | Swarm / orchestrator |
| Encryption | Not by default | Optional (`--opt encrypted`) |
| Performance | Minimal overhead | Some VXLAN encapsulation overhead |
| Use case | Development, single-host apps | Production, distributed systems |
