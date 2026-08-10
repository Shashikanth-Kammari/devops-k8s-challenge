# Video Walkthrough Script (target: 8–12 min total)

Record your terminal + a browser tab on the GitHub Actions run. Suggested
window layout: terminal full-screen, alt-tab to the Actions tab when needed.

Before recording, push this repo to GitHub so the Actions workflow is real
(not a dry run). Everything below has been tested locally against a live
Postgres instance and the app behaves exactly as scripted.

---

## 1. Live Demo (3–4 min)

**Say:** "This is a Node/Express backend and Postgres, deployed to Kubernetes,
with CI/CD that builds, pushes, and deploys automatically on every push."

```bash
# Show the cluster and namespace
kubectl get nodes
kubectl get all -n devops-challenge

# Show the app is actually working end-to-end
kubectl -n devops-challenge port-forward svc/backend 3000:3000 &
curl -s localhost:3000/ready
curl -s -X POST localhost:3000/todos -H 'Content-Type: application/json' \
     -d '{"title":"ship the demo"}'
curl -s localhost:3000/todos
```

**Say:** "Now watch this deploy through the pipeline." Push a trivial change
(e.g. bump a comment in `app.js`), `git push`, then switch to the GitHub
Actions tab and narrate live:

- `build-and-push` job: Docker image built, tagged with the git SHA (not
  `latest` — immutable, traceable), pushed to GHCR.
- `deploy` job: spins up an ephemeral `kind` cluster, applies manifests,
  `kubectl set image` to the new SHA tag, waits on `rollout status`, then
  runs a smoke test hitting `/ready` and `/todos`.

When it goes green:

```bash
kubectl -n devops-challenge get pods -o wide
kubectl -n devops-challenge rollout history deployment/backend
```

**Say:** "Two replicas, rolling update with `maxUnavailable: 0`, so there's
zero-downtime capacity during every deploy."

---

## 2. Architecture Walkthrough (2–3 min)

**Say, while pointing at `kubectl get all -n devops-challenge` output:**

- "Cluster: `kind` locally / any managed K8s in real deployment — nothing
  here is cloud-specific, it's plain manifests, no Helm/Kustomize magic
  hiding what's actually applied."
- "Backend Deployment: 2 replicas, config split into a ConfigMap for
  non-secret values (`PGHOST`, `PGPORT`, `PORT`) and a Secret for credentials
  — so the two have different blast radii and different handling."
- "Postgres: single Deployment with a PersistentVolumeClaim, `Recreate`
  strategy — I don't want two Postgres pods racing for the same volume during
  a rollout."
- "CI/CD flow: push → build → tag with git SHA → push to GHCR → spin up a
  disposable cluster → apply manifests → set the new image → wait for
  rollout → smoke test. If the smoke test fails, the job fails loudly instead
  of silently leaving a broken deploy live."
- "Reliability choice: readiness + liveness probes — explained in depth in
  the next section since it's also what powers the failure demo."

---

## 3. Failure Debugging Walkthrough (2–3 min) — the main event

**Say:** "I'm going to break DB connectivity the way it actually happens in
production — someone edits a ConfigMap and it drifts from the real Service
name."

```bash
# 1. Inject the failure
kubectl apply -f k8s/failure-demo/break-db-host.yaml
kubectl -n devops-challenge rollout restart deployment/backend
```

**Symptom — show it live:**

```bash
kubectl -n devops-challenge get pods
# READY column: pods show 0/1 or flip to NotReady — NOT CrashLoopBackOff.
# That distinction is the whole point of splitting liveness from readiness.

kubectl -n devops-challenge get endpoints backend
# Endpoint list is empty/short — Kubernetes has already pulled the pod
# out of the Service because readiness is failing.
```

**Say (narrate the reasoning, including a wrong-assumption beat — this is
what graders are told to look for):**

> "First instinct might be 'the pod is crashing' — but `kubectl get pods`
> shows it's Running, just not Ready. So it's not a crash, it's a probe
> failure. Let's check *which* probe."

```bash
kubectl -n devops-challenge describe pod -l app=backend | grep -A5 Readiness
kubectl -n devops-challenge describe pod -l app=backend | tail -20
# Events show: "Readiness probe failed: HTTP probe failed with statuscode: 503"
```

**Say:** "Liveness is fine — process didn't restart — so it's specifically
the readiness check, which only checks the DB. Let's check application logs
directly instead of guessing further."

```bash
kubectl -n devops-challenge logs -l app=backend --tail=30
# Look for: "DB init failed, retrying in 3s: getaddrinfo ENOTFOUND postgres-db"
```

**Root cause:** `PGHOST` in the ConfigMap is `postgres-db`, but the actual
Service is named `postgres`.

```bash
kubectl -n devops-challenge get configmap backend-config -o yaml
kubectl -n devops-challenge get svc -n devops-challenge
# Compare the two — mismatch is now obvious
```

**Fix and verify — including the second wrong-assumption beat:**

> "Fixing the ConfigMap alone won't fix running pods — env vars from a
> ConfigMap aren't hot-reloaded into a live container. You have to roll the
> pods after fixing the source."

```bash
kubectl apply -f k8s/failure-demo/fix-db-host.yaml
kubectl -n devops-challenge rollout restart deployment/backend
kubectl -n devops-challenge rollout status deployment/backend

# Confirm recovery
kubectl -n devops-challenge get pods
curl -s localhost:3000/ready
```

**Say:** "Back to `{"status":"ready","db":"connected"}`, pods Ready 1/1,
endpoints populated again — and at no point did the process crash or lose
requests it could still legitimately serve; readiness just correctly
withheld traffic the whole time it couldn't."

---

## 4. Tradeoff Discussion (1–2 min)

**Say:**

- "Intentionally simplified: plaintext K8s Secret instead of Vault/Sealed
  Secrets/External Secrets; single Postgres instance with no backup/failover;
  no ingress or TLS — NodePort only; CI/CD deploys to a disposable cluster it
  creates itself so it's runnable without cloud creds, rather than a real
  persistent EKS/GKE cluster."
- "What breaks at scale: single Postgres instance is a single point of
  failure and a write bottleneck — no read replicas, no automated failover.
  Fixed replica count means no response to real traffic spikes. Rolling
  update with only 2 replicas means a bad rollout only has one healthy pod
  covering traffic during the transition."
- "What I'd improve in real production: managed Postgres (RDS/Cloud SQL) or
  an operator-managed HA setup, External Secrets Operator against a real
  secrets manager, HPA on CPU/latency, an Ingress with TLS instead of
  NodePort, and a persistent cluster with the CI/CD job authenticating via
  OIDC instead of spinning up its own throwaway cluster."
