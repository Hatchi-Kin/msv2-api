# For local development
## you might port-forward the k3s postgres services:
```sh
kubectl port-forward service/postgres-service 5432:5432 -n glasgow-prod
```
and
```sh
kubectl port-forward -n glasgow-prod svc/minio-service 9000:9000
```

# or maybe just port forward the prod api directly
```sh
kubectl port-forward -n glasgow-prod svc/fastapi-msv2-api-service 8000:8010
```


# Then start the app
```sh
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```
