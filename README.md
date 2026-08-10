# DevOps 90-Minute Infrastructure Challenge

A minimal, production-style stack: Node.js/Express backend + PostgreSQL,
deployed to Kubernetes via a GitHub Actions CI/CD pipeline.

## Stack

- **Backend**: Node.js/Express, `backend/app.js` — REST API (`/todos`) backed by Postgres,
  plus `/health` (liveness) and `/ready` (readiness) endpoints.
- **Database**: PostgreSQL 16, single instance, `PersistentVolumeClaim`-backed.
- **Orchestration**: Kubernetes (tested against `kind`; works unmodified on
  minikube/k3s/EKS/GKE/AKS — only the `kubectl` context changes).
- **CI/CD**: GitHub Actions (`.github/workflows/ci-cd.yaml`) — builds the Docker
  image, pushes to GHCR, spins up an ephemeral `kind` cluster, applies manifests,
  rolls out the new image, and smoke-tests the live endpoint.

## Repo layout

```
backend/                  Express app + Dockerfile
k8s/00-namespace.yaml      Namespace
k8s/01-postgres-secret.yaml  DB credentials (Secret)
k8s/02-postgres.yaml        Postgres Deployment + PVC + headless Service
k8s/03-backend-configmap.yaml  Non-secret backend config (PGHOST, PGPORT, PORT)
k8s/04-backend.yaml          Backend Deployment (2 replicas) + NodePort Service
k8s/failure-demo/           Failure injection + fix manifests for the debugging demo
.github/workflows/ci-cd.yaml  CI/CD pipeline
```

## Local run (kind)

```bash
kind create cluster --name devops-challenge
kubectl apply -f k8s/00-namespace.yaml
kubectl apply -f k8s/01-postgres-secret.yaml
kubectl apply -f k8s/02-postgres.yaml
kubectl -n devops-challenge rollout status deployment/postgres
kubectl apply -f k8s/03-backend-configmap.yaml
kubectl apply -f k8s/04-backend.yaml
kubectl -n devops-challenge rollout status deployment/backend

kubectl -n devops-challenge port-forward svc/backend 3000:3000
curl localhost:3000/ready
curl -X POST localhost:3000/todos -H 'Content-Type: application/json' -d '{"title":"demo"}'
curl localhost:3000/todos
```

## Reliability improvement chosen: Readiness + Liveness Probes

**Why this, and not something else:** with only 90 minutes, the improvement had
to (a) be implementable *correctly* — not just present in a YAML file — and
(b) directly connect to the failure-simulation requirement, so the debugging
segment demonstrates a *real* mechanism rather than a staged one. Probes hit
both: they're the thing that actually detects and reacts to the injected
failure live, in front of the camera.

**Problem it solves:** without probes, Kubernetes' only signal for "is this
pod OK" is whether the container process is still running. A backend pod
that's alive but can't reach its database will happily keep receiving traffic
from the Service and returning 500s to every request — the cluster has no
idea anything is wrong. Two separate checks are needed because they answer
different questions:
- **Liveness** (`/health`) — "is the process wedged and needs a restart?"
  Deliberately does *not* touch the database, because a DB outage is not a
  reason to kill and restart the backend process (that would just
  restart-loop the backend for a problem the restart can't fix).
- **Readiness** (`/ready`) — "can this pod actually serve a request right
  now?" Checks the DB with `SELECT 1`. If it fails, Kubernetes removes the pod
  from the Service's endpoint list — traffic stops routing to it — without
  killing the pod, so it can self-heal the moment the DB is reachable again.

**Tradeoff introduced:** correctness depends on getting the split right. A
readiness check that's too strict (or too broad — e.g. checking downstream
services the DB check doesn't need) can pull healthy pods out of rotation
during a brief, self-recovering blip, reducing capacity when you least want
it. A liveness check that's too aggressive can restart-loop a pod that's
simply slow, not broken. There's also added latency/load per probe interval
(here, an extra `SELECT 1` every 5s per pod) and more moving parts to
misconfigure — the failure demo below is itself an example of a probe-adjacent
misconfiguration (a bad env var) that this setup is specifically designed to
surface quickly instead of silently.

## What's intentionally simplified (see DEMO_SCRIPT.md for the full discussion)

- Secrets are a plain K8s `Secret` (base64, not encrypted at rest) — fine for
  a demo, wrong for production (would use External Secrets Operator / Sealed
  Secrets / Vault).
- Single Postgres replica, no automated backups, no failover.
- CI/CD deploys to an ephemeral `kind` cluster it creates itself, so the
  pipeline is runnable by anyone without cloud credentials — a real pipeline
  would target a persistent cluster (EKS/GKE/AKS) via
  `aws eks update-kubeconfig` / OIDC federation, not `kind-action`.
- No ingress/TLS — `NodePort` for simplicity.
- No autoscaling (HPA) — fixed at 2 replicas.
