# prj01-linkpulse-app

LinkPulse: a small URL shortener with click analytics. Built to run on the EKS platform from [prj01-eks-gitops-platform](https://github.com/maorbrantz/prj01-eks-gitops-platform).

## Services

- `services/api`: FastAPI. Create short links, redirect and emit a click event to SQS, serve aggregated stats from DynamoDB. Exposes `/healthz`, `/readyz`, and Prometheus `/metrics`.
- `services/worker`: long-polls SQS, aggregates clicks per short code per day into DynamoDB, deletes handled messages, leaves failures on the queue for retry or the DLQ.
- `services/web`: static frontend served by nginx, talks to the api under `/api`.

Table and queue names plus the AWS endpoint come from environment variables, so the same code runs against localstack locally and against real AWS with IRSA on EKS.

## Local development

`make venv` creates a virtualenv and installs both service test suites. `make test` runs pytest with coverage (fails under 80%).

`make run-local` builds the images and starts api, worker, web, and localstack, with an init container that creates the tables and queue. The frontend is on http://localhost:8080 and the api on http://localhost:8000. `make stop-local` tears it down.

## Chart

`charts/linkpulse` is a plain Deployment-based Helm chart with values for image, tag, env, service account, and resources. Later phases convert the Deployment to an Argo Rollout.

Work in progress.
