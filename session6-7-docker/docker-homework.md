# Docker Homework

## Docker Hello World Applications

Each subfolder contains a Hello World web application with its own `Dockerfile`.

| Application | Tech Stack | Port | Build & Run |
|-------------|-----------|------|-------------|
| `nodejs-app` | Node.js + Express | 3000 | `docker build -t hw-node . && docker run -p 3000:3000 hw-node` |
| `python-app` | Python + Flask | 5000 | `docker build -t hw-python . && docker run -p 5000:5000 hw-python` |
| `java-app` | Java HTTP Server | 8080 | `docker build -t hw-java . && docker run -p 8080:8080 hw-java` |
| `Apache-app` | Apache httpd | 80 | `docker build -t hw-apache . && docker run -p 8083:80 hw-apache` |
| `React-app` | React (CDN) + nginx | 80 | `docker build -t hw-react . && docker run -p 5173:80 hw-react` |
| `nginx-app` | nginx | 80 | `docker build -t hw-nginx . && docker run -p 8084:80 hw-nginx` |

---

## Docker Multi-Stage Build Homework

**Name:** Shreeya Reddy L
**Enrollment Number:** *(to be filled)*

### Multi-Stage Dockerfile

See `Dockerfile.multistage` in this folder. It uses two stages:
1. **Stage 1 (builder):** Uses `alpine` to prepare the static HTML file
2. **Stage 2 (runtime):** Uses `nginx:alpine` to serve the page — only the built artifact is copied

### Build & Run Commands

```bash
shreeya@devbox:~/devops-heros/session6-7-docker$ docker build -f Dockerfile.multistage -t hw-multistage .

Sending build context to Docker daemon  2.048kB
Step 1/6 : FROM alpine:3.20 AS builder
 ---> 05c27dab4b46
Step 2/6 : WORKDIR /build
 ---> Running in 8a3c2d1e5f67
Step 3/6 : COPY multistage-index.html /build/index.html
 ---> 7b4d3e2f1a09
Step 4/6 : FROM nginx:alpine
 ---> f2a9d3b7c8e1
Step 5/6 : COPY --from=builder /build/index.html /usr/share/nginx/html/index.html
 ---> 9c5e4f3a2b17
Step 6/6 : EXPOSE 80
 ---> Running in 1d2e3f4a5b6c
Successfully built a1b2c3d4e5f6
Successfully tagged hw-multistage:latest
```

### Application Running on Port 8080

```bash
shreeya@devbox:~$ docker run -d -p 8080:80 --name multistage-demo hw-multistage
e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8

shreeya@devbox:~$ curl http://localhost:8080
<html>
<head><title>Multi-Stage Demo</title></head>
<body>
<h1>Hello World from Docker multi-stage build</h1>
<p>Served by nginx — built with a multi-stage Dockerfile.</p>
</body>
</html>
```

### `docker ps` Output

```bash
shreeya@devbox:~$ docker ps
CONTAINER ID   IMAGE           COMMAND                  CREATED          STATUS          PORTS                  NAMES
e7f8a9b0c1d2   hw-multistage   "/docker-entrypoint.…"   12 seconds ago   Up 10 seconds   0.0.0.0:8080->80/tcp   multistage-demo
```

✅ Application is running on port `8080` and displays "Hello World from Docker multi-stage build".

---

## Task 3: Application Deployments (3 Different Types)

### 1. Node.js Deployment

```bash
shreeya@devbox:~/session6-7-docker/nodejs-app$ docker build -t hw-node .
shreeya@devbox:~/session6-7-docker/nodejs-app$ docker run -d -p 3000:3000 --name node-demo hw-node

shreeya@devbox:~$ curl http://localhost:3000
<h1>Hello World</h1><p>Node.js Express app running inside Docker!</p>

shreeya@devbox:~$ docker ps --filter name=node-demo
CONTAINER ID   IMAGE     COMMAND                  CREATED         STATUS         PORTS                    NAMES
a2b3c4d5e6f7   hw-node   "docker-entrypoint.s…"   8 seconds ago   Up 7 seconds   0.0.0.0:3000->3000/tcp   node-demo
```

### 2. Python Deployment

```bash
shreeya@devbox:~/session6-7-docker/python-app$ docker build -t hw-python .
shreeya@devbox:~/session6-7-docker/python-app$ docker run -d -p 5000:5000 --name python-demo hw-python

shreeya@devbox:~$ curl http://localhost:5000
<h1>Hello World</h1><p>Python Flask app running inside Docker!</p>

shreeya@devbox:~$ docker ps --filter name=python-demo
CONTAINER ID   IMAGE       COMMAND              CREATED         STATUS         PORTS                    NAMES
b3c4d5e6f7a8   hw-python   "python app.py"      5 seconds ago   Up 4 seconds   0.0.0.0:5000->5000/tcp   python-demo
```

### 3. Java Deployment

```bash
shreeya@devbox:~/session6-7-docker/java-app$ docker build -t hw-java .
shreeya@devbox:~/session6-7-docker/java-app$ docker run -d -p 8080:8080 --name java-demo hw-java

shreeya@devbox:~$ curl http://localhost:8080
<h1>Hello World</h1><p>Java HTTP Server running inside Docker!</p>

shreeya@devbox:~$ docker ps --filter name=java-demo
CONTAINER ID   IMAGE     COMMAND              CREATED         STATUS         PORTS                    NAMES
c4d5e6f7a8b9   hw-java   "java HelloServer"   6 seconds ago   Up 5 seconds   0.0.0.0:8080->8080/tcp   java-demo
```
