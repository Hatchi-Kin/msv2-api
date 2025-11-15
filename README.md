# For local development, you might port-forward the k3s postgres service:
```sh
kubectl port-forward service/postgres-service 5432:5432 -n glasgow-prod
```