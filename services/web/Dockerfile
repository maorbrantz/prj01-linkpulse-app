# unprivileged variant runs as a non-root uid and listens on 8080 by default,
# which is what the cluster policy requires and what the chart probes expect.
FROM nginxinc/nginx-unprivileged:1.27-alpine

# patch the base os packages so the image scan does not trip on fixed cves.
USER root
RUN apk upgrade --no-cache
# numeric uid (nginx) so the kubelet can verify non-root under the cluster policy.
USER 101

ENV WEB_PORT=8080 \
    API_UPSTREAM=http://api:8000

COPY html/ /usr/share/nginx/html/
COPY nginx.conf.template /etc/nginx/templates/default.conf.template

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget --quiet --tries=1 --spider "http://127.0.0.1:${WEB_PORT}/healthz" || exit 1
