# Kubernetes deployment

Apply:
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/postgres.yaml
kubectl apply -f k8s/backend.yaml

Check:
kubectl get pods -n devops-demo
kubectl get svc -n devops-demo
kubectl rollout status deployment/backend -n devops-demo

Test:
curl http://<NODE-IP>:30898/health

Observability:
kubectl top pods -n devops-demo
kubectl describe pod <pod> -n devops-demo
kubectl logs <pod> -n devops-demo
kubectl get events -n devops-demo --sort-by=.metadata.creationTimestamp

Failure simulation:
kubectl exec -it <backend-pod> -n devops-demo -- sh
yes > /dev/null &

Then inspect CPU with:
kubectl top pods -n devops-demo

Stop the stress process:
kill <PID>
