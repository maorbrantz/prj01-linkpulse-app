FROM nginx:1.27-alpine

ENV WEB_PORT=8080 \
    API_UPSTREAM=http://api:8000

COPY html/ /usr/share/nginx/html/
COPY nginx.conf.template /etc/nginx/templates/default.conf.template

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget --quiet --tries=1 --spider "http://127.0.0.1:${WEB_PORT}/healthz" || exit 1
