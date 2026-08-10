# DevOps Engineer — Kubernetes Infrastructure Challenge

A minimal production-style application stack demonstrating containerization, Kubernetes deployment, CI/CD automation, reliability engineering, observability, and operational debugging.

## Architecture

```text
Developer
    |
    | git push
    v
GitHub Repository
    |
    v
GitHub Actions
    |
    +--> Run Tests
    |
    +--> Build Docker Image
    |
    +--> Push Image to Docker Hub
    |
    +--> Deploy to Kubernetes
             |
             v
        k3s Kubernetes
             |
       +-----+------+
       |            |
       v            v
    Backend      PostgreSQL
    Flask API    Database
       |
       v
    Kubernetes Service
```

## Technology Stack

| Component          | Technology                                |
| ------------------ | ----------------------------------------- |
| Application        | Python Flask                              |
| Containerization   | Docker                                    |
| Orchestration      | Kubernetes / k3s                          |
| Database           | PostgreSQL                                |
| CI/CD              | GitHub Actions                            |
| Container Registry | Docker Hub                                |
| Monitoring         | Kubernetes health checks, logs and events |
| Infrastructure     | AWS EC2                                   |
| Testing            | Pytest                                    |

## Project Structure

```text
devops-k8s-challenge/
│
├── app/
│   ├── app.py
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .dockerignore
│
├── tests/
│   └── test_app.py
│
├── k8s/
│   ├── namespace.yaml
│   │
│   ├── database/
│   │   ├── postgres-secret.yaml
│   │   ├── postgres-deployment.yaml
│   │   └── postgres-service.yaml
│   │
│   └── backend/
│       ├── backend-deployment.yaml
│       └── backend-service.yaml
│
├── .github/
│   └── workflows/
│       └── deploy.yaml
│
├── .gitignore
└── README.md
```

## Application

The application is a simple Flask REST API backed by PostgreSQL.

### Endpoints

```text
GET /
GET /health
GET /ready
GET /api
```

### Health Endpoint

```text
/health
```

Used by the Kubernetes liveness probe to determine whether the application process is healthy.

### Readiness Endpoint

```text
/ready
```

Checks application availability and PostgreSQL connectivity before allowing the pod to receive traffic.

### API Endpoint

```text
/api
```

Connects to PostgreSQL and creates a sample request record.

---

# Kubernetes Deployment

## 1. Create the namespace

```bash
kubectl apply -f k8s/namespace.yaml
```

## 2. Deploy PostgreSQL

```bash
kubectl apply -f k8s/database/
```

## 3. Deploy the backend

```bash
kubectl apply -f k8s/backend/
```

## 4. Verify resources

```bash
kubectl get all -n devops-demo
```

Check pods:

```bash
kubectl get pods -n devops-demo -o wide
```

Check services:

```bash
kubectl get svc -n devops-demo
```

Check endpoints:

```bash
kubectl get endpoints -n devops-demo
```

---

# Docker

Build the application image:

```bash
docker build -t <dockerhub-username>/devops-demo:latest ./app
```

Run locally:

```bash
docker run -p 8080:8080 \
  -e DB_HOST=<database-host> \
  -e DB_NAME=appdb \
  -e DB_USER=appuser \
  -e DB_PASSWORD=<password> \
  <dockerhub-username>/devops-demo:latest
```

Test:

```bash
curl http://localhost:8080/health
```

---

# CI/CD Pipeline

The GitHub Actions pipeline is triggered whenever code is pushed to the `main` branch.

```text
Git Push
   |
   v
Run Tests
   |
   v
Build Docker Image
   |
   v
Push Image to Docker Hub
   |
   v
Deploy to Kubernetes
   |
   v
kubectl rollout status
```

## Pipeline stages

### 1. Test

Runs Python tests using Pytest.

```bash
python -m pytest
```

### 2. Build

Creates the Docker image.

```bash
docker build
```

### 3. Push

Pushes the image to Docker Hub.

Images are tagged using the Git commit SHA to provide an immutable deployment reference.

```text
<dockerhub-username>/devops-demo:<git-sha>
```

### 4. Deploy

Updates the Kubernetes deployment:

```bash
kubectl set image deployment/backend
```

Then verifies the rollout:

```bash
kubectl rollout status deployment/backend
```

---

# GitHub Secrets

The following GitHub Actions secrets are required:

```text
DOCKERHUB_USERNAME
DOCKERHUB_TOKEN
K8S_HOST
K8S_USER
K8S_SSH_KEY
```

Secrets are not stored in the Git repository.

---

# Reliability Improvement

## Readiness and Liveness Probes

The primary reliability improvement implemented in this challenge is Kubernetes health probing.

### Liveness Probe

The backend exposes:

```text
/health
```

Kubernetes uses this endpoint to determine whether the application process is alive.

If the application becomes unhealthy, Kubernetes can restart the container.

### Readiness Probe

The backend exposes:

```text
/ready
```

The readiness check verifies PostgreSQL connectivity.

If PostgreSQL is unavailable:

```text
Backend Pod
     |
     v
/ready
     |
     X
PostgreSQL unavailable
     |
     v
Pod becomes NotReady
     |
     v
Service stops sending traffic
```

### Why this was chosen

The application depends on PostgreSQL. A running container does not necessarily mean that the application can serve requests successfully.

The readiness probe prevents Kubernetes from sending traffic to a backend that cannot access its database.

### Tradeoff

Health checks add additional requests and poorly designed probes can cause unnecessary restarts.

Therefore:

* Liveness checks only application health.
* Readiness checks dependency availability.
* Liveness does not directly depend on PostgreSQL.

---

# Deployment Strategy

The backend uses Kubernetes `RollingUpdate`.

```yaml
strategy:
  type: RollingUpdate
  rollingUpdate:
    maxUnavailable: 0
    maxSurge: 1
```

This ensures that an existing healthy pod remains available while the new version is being deployed.

Check rollout status:

```bash
kubectl rollout status deployment/backend -n devops-demo
```

Check rollout history:

```bash
kubectl rollout history deployment/backend -n devops-demo
```

Rollback if required:

```bash
kubectl rollout undo deployment/backend -n devops-demo
```

---

# Observability and Debugging

The challenge uses Kubernetes-native observability capabilities.

## Pod status

```bash
kubectl get pods -n devops-demo
```

## Pod details

```bash
kubectl describe pod <pod-name> -n devops-demo
```

## Application logs

```bash
kubectl logs deployment/backend -n devops-demo
```

## Previous container logs

```bash
kubectl logs <pod-name> --previous -n devops-demo
```

## Kubernetes events

```bash
kubectl get events -n devops-demo --sort-by=.lastTimestamp
```

## Service endpoints

```bash
kubectl get endpoints -n devops-demo
```

---

# Intentional Failure Scenario

For the operational debugging demonstration, database connectivity is intentionally broken.

The backend database hostname is changed from:

```text
postgres
```

to:

```text
postgres-wrong
```

The expected symptoms are:

```text
Pod running
     |
     v
Readiness probe fails
     |
     v
Pod remains NotReady
     |
     v
Application logs show database connection failure
```

## Debugging Process

### Step 1 — Check pods

```bash
kubectl get pods -n devops-demo
```

### Step 2 — Inspect pod events

```bash
kubectl describe pod <backend-pod> -n devops-demo
```

### Step 3 — Check application logs

```bash
kubectl logs deployment/backend -n devops-demo
```

### Step 4 — Check PostgreSQL service

```bash
kubectl get svc -n devops-demo
```

### Step 5 — Check endpoints

```bash
kubectl get endpoints postgres -n devops-demo
```

### Step 6 — Test DNS from the backend

```bash
kubectl exec -it deployment/backend -n devops-demo -- \
  getent hosts postgres-wrong
```

The hostname fails to resolve.

### Root Cause

The backend was configured with an incorrect Kubernetes Service hostname.

```text
postgres-wrong
```

instead of:

```text
postgres
```

### Fix

Restore the correct environment variable:

```yaml
- name: DB_HOST
  value: postgres
```

Apply the configuration:

```bash
kubectl apply -f k8s/backend/
```

Verify:

```bash
kubectl rollout status deployment/backend -n devops-demo
```

Finally:

```bash
curl http://<EC2-IP>:<NODEPORT>/api
```

---

# Production Improvements

This challenge intentionally keeps the infrastructure small enough to build and demonstrate within 90 minutes.

For a real production environment, I would improve the architecture in the following areas:

### Kubernetes

Move from single-node k3s to a multi-node managed Kubernetes cluster such as EKS, GKE, or AKS.

### Database

Move PostgreSQL from Kubernetes to a managed database service such as Amazon RDS or Cloud SQL.

This provides:

* Automated backups
* High availability
* Replication
* Point-in-time recovery
* Managed upgrades

### Secrets

Replace Kubernetes Secrets with a dedicated secrets-management solution such as AWS Secrets Manager with External Secrets.

### CI/CD

Move from direct `kubectl` deployment to a GitOps approach using Argo CD.

### Observability

Add:

* Prometheus
* Grafana
* Centralized logging
* Alerting
* Distributed tracing

### Infrastructure as Code

Provision AWS infrastructure and Kubernetes dependencies using Terraform.

### Security

Add:

* Image vulnerability scanning
* SAST
* Dependency scanning
* Container security scanning
* RBAC
* Network policies
* Pod security controls
* Non-root containers

---

# Key Design Decisions

| Decision               | Reason                                                  |
| ---------------------- | ------------------------------------------------------- |
| k3s                    | Lightweight Kubernetes for a time-constrained challenge |
| Flask                  | Minimal application complexity                          |
| PostgreSQL             | Demonstrates service dependency                         |
| Readiness probe        | Prevents traffic to unhealthy dependencies              |
| Liveness probe         | Enables automatic container recovery                    |
| 2 backend replicas     | Demonstrates basic availability                         |
| RollingUpdate          | Reduces deployment downtime                             |
| Git SHA image tag      | Provides deployment traceability                        |
| Kubernetes Service     | Provides stable internal DNS                            |
| Kubernetes logs/events | Enables operational debugging                           |

---

# Validation Checklist

Before recording the video, verify:

```text
[ ] Kubernetes node is Ready
[ ] PostgreSQL pod is Running
[ ] Backend has 2 replicas
[ ] Backend readiness probe passes
[ ] Backend liveness probe passes
[ ] API endpoint works
[ ] Database connection works
[ ] Docker image is pushed
[ ] GitHub Actions pipeline passes
[ ] Automatic deployment works
[ ] Rollout history is available
[ ] Intentional failure can be reproduced
[ ] Failure can be debugged
[ ] Root cause can be explained
[ ] Failure can be fixed
[ ] Final application is healthy
```

---

# Demo Commands

Useful commands for the final recording:

```bash
kubectl get nodes

kubectl get all -n devops-demo

kubectl get pods -n devops-demo -o wide

kubectl get svc -n devops-demo

kubectl get endpoints -n devops-demo

kubectl get events -n devops-demo --sort-by=.lastTimestamp

kubectl logs deployment/backend -n devops-demo

kubectl describe deployment backend -n devops-demo

kubectl rollout status deployment/backend -n devops-demo

kubectl rollout history deployment/backend -n devops-demo
```

Application validation:

```bash
curl http://<EC2-IP>:<NODEPORT>/

curl http://<EC2-IP>:<NODEPORT>/health

curl http://<EC2-IP>:<NODEPORT>/ready

curl http://<EC2-IP>:<NODEPORT>/api
```

---

# Challenge Outcome

The completed solution demonstrates:

* Containerization with Docker
* Kubernetes orchestration
* Application and database deployment
* CI/CD automation
* Immutable image tagging
* Kubernetes health probes
* Rolling deployments
* Resource configuration
* Service discovery
* Application logging
* Kubernetes troubleshooting
* Intentional failure simulation
* Root-cause analysis
* Recovery and validation

The focus is on demonstrating reliable infrastructure and operational debugging rather than application complexity.
