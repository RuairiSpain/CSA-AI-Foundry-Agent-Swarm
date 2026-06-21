# Guide: Deployment and CI/CD

---

## Docker

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY safe_framework/ ./safe_framework/
RUN pip install -e ./safe_framework

COPY routes/ ./routes/

ENV FOUNDRY_ENDPOINT=""
ENV FOUNDRY_API_KEY=""

EXPOSE 8000
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```bash
docker build -t safe-agent-api:latest .
docker run -p 8000:8000 \
  -e FOUNDRY_ENDPOINT=$FOUNDRY_ENDPOINT \
  -e FOUNDRY_API_KEY=$FOUNDRY_API_KEY \
  safe-agent-api:latest
```

---

## Azure Container Apps (Recommended)

```bash
# Deploy to Azure Container Apps
az containerapp create \
  --name safe-agent-api \
  --resource-group <rg> \
  --environment <aca-env> \
  --image <acr>.azurecr.io/safe-agent-api:latest \
  --target-port 8000 \
  --ingress external \
  --min-replicas 1 \
  --max-replicas 10 \
  --env-vars FOUNDRY_ENDPOINT=$FOUNDRY_ENDPOINT \
  --system-assigned   # Managed Identity
```

---

## GitHub Actions CI/CD

```yaml
# .github/workflows/deploy.yml
name: Deploy SAFE Agent API

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install -e ./safe_framework[dev]
      - run: pytest safe_framework/tests/ --cov=safe_core

  build-and-push:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: azure/docker-login@v1
        with:
          login-server: ${{ secrets.ACR_LOGIN_SERVER }}
          username: ${{ secrets.ACR_USERNAME }}
          password: ${{ secrets.ACR_PASSWORD }}
      - run: |
          docker build -t ${{ secrets.ACR_LOGIN_SERVER }}/safe-agent-api:${{ github.sha }} .
          docker push ${{ secrets.ACR_LOGIN_SERVER }}/safe-agent-api:${{ github.sha }}

  deploy:
    needs: build-and-push
    runs-on: ubuntu-latest
    steps:
      - uses: azure/login@v1
        with:
          creds: ${{ secrets.AZURE_CREDENTIALS }}
      - run: |
          az containerapp update \
            --name safe-agent-api \
            --resource-group ${{ secrets.RESOURCE_GROUP }} \
            --image ${{ secrets.ACR_LOGIN_SERVER }}/safe-agent-api:${{ github.sha }}
```

---

## AKS Deployment

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: safe-agent-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: safe-agent-api
  template:
    metadata:
      labels:
        app: safe-agent-api
    spec:
      serviceAccountName: safe-agent-sa   # workload identity
      containers:
        - name: safe-agent-api
          image: <acr>.azurecr.io/safe-agent-api:latest
          ports:
            - containerPort: 8000
          env:
            - name: FOUNDRY_ENDPOINT
              valueFrom:
                secretKeyRef:
                  name: safe-secrets
                  key: foundry-endpoint
          resources:
            requests:
              cpu: "250m"
              memory: "512Mi"
            limits:
              cpu: "1000m"
              memory: "2Gi"
          livenessProbe:
            httpGet:
              path: /health
              port: 8000
            initialDelaySeconds: 10
            periodSeconds: 30
```

---

## Environment Promotion Strategy

| Environment | Purpose | Approval Required |
|---|---|---|
| `dev` | Development and unit testing | None |
| `staging` | Integration testing with real Azure services | Auto (CI passes) |
| `production` | Live traffic | Manual approval from team lead |

Use the SAFE governance `ReleaseManager` to enforce promotion gates:

```python
from safe_framework.safe_core.release.manager import ReleaseManager

rm = ReleaseManager()
await rm.promote(
    route_name="contract-review",
    from_env="staging",
    to_env="production",
    approver="lead@company.com",
)
```

---

## Health Endpoint

Add a health endpoint to your API for ACA/AKS probes:

```python
@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "version": "1.0",
        "foundry_connected": bool(os.environ.get("FOUNDRY_ENDPOINT")),
    }
```
