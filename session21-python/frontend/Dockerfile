# syntax=docker/dockerfile:1

# ---- Stage 1: build the Vite bundle -----------------------------------------
FROM node:22-alpine AS build

WORKDIR /app

COPY package.json ./
RUN npm install --no-audit --no-fund

COPY . .
RUN npm run build

# ---- Stage 2: serve the static bundle with unprivileged Nginx ---------------
FROM nginx:1.27-alpine

# The stock image starts as root and writes its pid file to /var/run. Running as
# the unprivileged `nginx` user (uid 101) requires the pid file and every scratch
# directory to live somewhere writable, so retarget them into /tmp.
#
# /etc/nginx/conf.d must ALSO be writable by that user: the image entrypoint
# renders /etc/nginx/templates/*.template into conf.d via envsubst before
# nginx starts. If conf.d stays root-owned the render is skipped, nginx comes
# up with no server block at all, and every incoming connection is closed.
RUN set -eux; \
    sed -i 's,^pid .*,pid /tmp/nginx.pid;,' /etc/nginx/nginx.conf; \
    sed -i '/^user /d' /etc/nginx/nginx.conf; \
    rm -f /etc/nginx/conf.d/default.conf; \
    mkdir -p /tmp/client_temp /tmp/proxy_temp /tmp/fastcgi_temp /tmp/uwsgi_temp /tmp/scgi_temp; \
    chown -R nginx:nginx /tmp /etc/nginx/conf.d

# envsubst template: ${BACKEND_UPSTREAM} is resolved at container start, which
# lets the same image talk to the Compose service name or the Helm Service name.
# Copied before the chown below so /etc/nginx/templates exists first.
ENV BACKEND_UPSTREAM=backend:8000
COPY nginx.conf.template /etc/nginx/templates/default.conf.template
RUN chown -R nginx:nginx /etc/nginx/templates

COPY --from=build /app/dist /usr/share/nginx/html
RUN chown -R nginx:nginx /usr/share/nginx/html

USER nginx

EXPOSE 8080

# Actually fetch the liveness endpoint. `nginx -t` only validates syntax and
# still succeeds when no server block exists, which hides a broken config.
HEALTHCHECK --interval=10s --timeout=5s --start-period=10s --retries=5 \
    CMD ["wget", "--spider", "-q", "http://127.0.0.1:8080/healthz"]

CMD ["nginx", "-g", "daemon off;"]