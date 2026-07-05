# prj01-linkpulse-app

[![ci](https://github.com/maorbrantz/prj01-linkpulse-app/actions/workflows/ci.yml/badge.svg)](https://github.com/maorbrantz/prj01-linkpulse-app/actions/workflows/ci.yml)
[![release](https://github.com/maorbrantz/prj01-linkpulse-app/actions/workflows/release.yml/badge.svg)](https://github.com/maorbrantz/prj01-linkpulse-app/actions/workflows/release.yml)

LinkPulse is a small URL shortener with click analytics. Create a short link, follow it, and the click is counted; the api serves aggregated stats per short code per day. It exists to be a realistic thing to deploy, scale, canary, and roll back on the platform in [prj01-eks-gitops-platform](https://github.com/maorbrantz/prj01-eks-gitops-platform), where it runs live at **https://linkpulse.prj1.maorbrantz.com**.

This repo holds the application code, its container images, the Helm chart, and the CI and release pipelines. It does not hold any cluster or infrastructure state; that lives in the platform repo, and the two meet at an image tag.

## Services

| Service | Stack | Role |
|---|---|---|
| `services/api` | FastAPI | Create short links, redirect and emit a click event to SQS, serve aggregated stats from DynamoDB. Exposes `/healthz`, `/readyz`, and Prometheus `/metrics`. |
| `services/worker` | Python, boto3 | Long-polls SQS, aggregates clicks per short code per day into DynamoDB, deletes handled messages, and leaves failures on the queue for retry or the DLQ. Exposes a `/metrics` port. |
| `services/web` | nginx | Static frontend that talks to the api under `/api`. |

Table and queue names, the AWS region, and the AWS endpoint all come from environment variables, so the same code runs against localstack locally and against real AWS on EKS. On the cluster each service account is bound to an IAM role through EKS Pod Identity, so no service carries static AWS credentials.

## Local development

`make venv` creates a virtualenv and installs both service test suites. `make test` runs pytest with coverage on the api and the worker, and fails under 80 percent (the gate is set in each service's `pyproject.toml`).

`make run-local` starts the whole thing under Docker Compose: api, worker, web, and localstack, with an init container that creates the DynamoDB tables and the SQS queue before the services start. The frontend comes up on http://localhost:8080 and the api on http://localhost:8000. `make stop-local` tears it down and removes the volumes.

## Tests

Both services have pytest suites covering the happy paths, the error paths, and the units (short-code generation, aggregation math, config and logging). Coverage is enforced at 80 percent per service in CI, so a change that drops coverage does not merge.

## How deployment works

Deployment is GitOps, and it is driven from the platform repo, not from here. A merge to `main` triggers the `release` workflow, which builds and pushes the three service images to ECR (through GitHub OIDC, no stored AWS keys) tagged with the short git SHA, then opens a pull request on the platform repo bumping the image tag in `gitops/apps/dev/linkpulse/values.yaml`. Merging that pull request is the deploy: ArgoCD syncs and Argo Rollouts runs the canary. The full walk is in the platform repo's [gitops-flow.md](https://github.com/maorbrantz/prj01-eks-gitops-platform/blob/main/docs/gitops-flow.md). Nobody runs `kubectl apply`.

Before any of that, the `ci` workflow runs on every pull request: `ruff` lint and pytest with the coverage gate on the api and worker, a `trivy` image scan that fails on HIGH or CRITICAL, and a `gitleaks` secret scan.

## Chart

`charts/linkpulse` is the Helm chart the platform renders. Its values (image tag, env, service account names, resources) are supplied per environment from the platform repo through an ArgoCD multi-source app, so the image tag lives there and the chart stays environment-agnostic.

The api is not a plain Deployment. It runs as an Argo Rollouts `Rollout` with a replica-ratio canary (20 percent, analysis, 50 percent, analysis, then full) and a CPU-based HPA that owns the replica count. Between the weight steps the rollout runs two Prometheus `AnalysisTemplate`s against the canary pods only: success rate (target at or above 99 percent) and p95 latency (under 500ms). A release that fails either one aborts back to stable. The chart also carries a `failRate` value used to inject 500s on purpose for the auto-rollback demo; it is zero in normal operation.

The pod and container security contexts (run as non-root, drop all capabilities, no privilege escalation, seccomp runtime default) are set in the chart so the workloads satisfy the cluster's Kyverno policies. A ServiceMonitor per service points Prometheus at the `/metrics` endpoints, and the ingress terminates TLS with an ACM certificate and redirects HTTP to HTTPS when a certificate ARN is supplied.
