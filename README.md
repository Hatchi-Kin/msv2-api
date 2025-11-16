# For local development, you might port-forward the k3s postgres service:
```sh
kubectl port-forward service/postgres-service 5432:5432 -n glasgow-prod
```

# Then start the app
```sh
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```