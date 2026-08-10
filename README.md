# DevOps Engineer - 90 Minute Infrastructure Challenge

Minimal production-style Kubernetes application stack demonstrating:

- Docker containerization
- Kubernetes deployment
- PostgreSQL dependency
- GitHub Actions CI/CD
- Readiness and liveness probes
- Resource requests and limits
- Operational debugging
- Intentional CPU failure simulation

## 1. Local test

```bash
pip install -r app/requirements.txt
pytest app/ -v
```

## 2. Build Docker image

```bash
docker build -t shashikanthchary/devops-demo:latest .
docker push shashikanthchary/devops-demo:latest
```

## 3. Deploy to Kubernetes

```bash
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/postgres.yaml
kubectl apply -f k8s/backend.yaml
```

Verify:

```bash
kubectl get pods -n devops-demo
kubectl get svc -n devops-demo
kubectl rollout status deployment/backend -n devops-demo
```

Test:

```bash
curl http://<NODE-IP>:30898/health
```

## 4. CI/CD

GitHub Actions performs:

1. Checkout
2. Python setup
3. Tests
4. Docker build
5. Docker push
6. AWS authentication using OIDC
7. EKS kubeconfig
8. Kubernetes apply
9. Image update
10. Rollout verification

Required GitHub secrets:

- `DOCKER_USERNAME`
- `DOCKER_PASSWORD`
- `AWS_REGION`
- `AWS_ROLE_ARN`
- `EKS_CLUSTER_NAME`

## 5. Reliability improvement

Readiness and liveness probes are implemented.

Readiness prevents traffic from reaching a pod that is not ready.

Liveness allows Kubernetes to restart an unhealthy application container.

Tradeoff: badly tuned probes can cause unnecessary restarts or remove healthy pods from service.

## 6. Intentional CPU failure

Get the backend pod:

```bash
kubectl get pods -n devops-demo -l app=backend
```

Enter the pod:

```bash
kubectl exec -it <backend-pod> -n devops-demo -- sh
```

Generate CPU pressure:

```bash
yes > /dev/null &
```

Observe:

```bash
kubectl top pods -n devops-demo
```

Debug:

```bash
kubectl describe pod <backend-pod> -n devops-demo
kubectl logs <backend-pod> -n devops-demo
kubectl get events -n devops-demo --sort-by=.metadata.creationTimestamp
curl http://<NODE-IP>:30898/health
```

Stop the stress:

```bash
kill <PID>
```

If necessary, restart the pod:

```bash
kubectl delete pod <backend-pod> -n devops-demo
```

Verify recovery:

```bash
kubectl get pods -n devops-demo
kubectl top pods -n devops-demo
curl http://<NODE-IP>:30898/health
```

## Production tradeoffs

This challenge intentionally avoids over-engineering.

For production I would consider:

- Amazon RDS instead of PostgreSQL Deployment
- Kubernetes Secrets / AWS Secrets Manager
- ALB Ingress with TLS
- HPA
- PodDisruptionBudget
- Multi-AZ node groups
- Persistent storage for stateful workloads
- Prometheus/Grafana
- Centralized logging
- Container image scanning
- Network policies
- GitHub Actions OIDC instead of long-lived AWS credentials
