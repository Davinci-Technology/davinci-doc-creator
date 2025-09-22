# GitHub Actions CI/CD Setup

## Overview
This project has automated CI/CD deployment to Azure Kubernetes Service (AKS) using GitHub Actions.

## Pipeline Configuration

### Workflow Trigger
The deployment pipeline triggers automatically on:
- Push to `main` branch
- Pull requests to `main` branch
- Manual workflow dispatch

### Pipeline Stages

1. **Build and Push** (`build-and-push` job)
   - Builds Docker images for backend and frontend
   - Tags images with commit SHA and `latest`
   - Pushes to Azure Container Registry (ACR)

2. **Deploy** (`deploy` job)
   - Deploys to AKS cluster `k8s-01`
   - Updates deployments with new image tags
   - Waits for successful rollout
   - Reports deployment status

## Azure Resources

- **Resource Group:** `davinci_can_cen_rg1`
- **AKS Cluster:** `k8s-01`
- **Container Registry:** `davinciai.azurecr.io`
- **Namespace:** `doc-generator`

## Service Principal

A dedicated service principal `github-actions-davinci-doc` has been created with:
- Contributor access to the subscription
- ACR push permissions to `davinciai` registry

## GitHub Repository Secret

The following secret is configured in the repository:
- `AZURE_CREDENTIALS`: Contains the service principal credentials for Azure authentication

## Deployment URLs

- **Production:** http://docs.davincisolutions.ai
- **Health Check:** http://docs.davincisolutions.ai/api/health

## Image Versioning

- Each deployment creates images tagged with the commit SHA
- Additionally updates the `latest` tag for rollback capability
- Example: `davinciai.azurecr.io/davinci-backend:4a6d4626f6076ad1e22e90e09c5f118e7db3b23c`

## Monitoring Deployments

### GitHub Actions
View deployment status at: https://github.com/Davinci-Technology/davinci-doc-creator/actions

### Kubernetes
```bash
# Check deployment status
kubectl get deployments -n doc-generator

# Check pod status
kubectl get pods -n doc-generator

# View logs
kubectl logs -f deployment/davinci-backend -n doc-generator
kubectl logs -f deployment/davinci-frontend -n doc-generator
```

## Rollback Procedure

If a deployment fails or causes issues:

```bash
# Rollback to previous version
kubectl rollout undo deployment/davinci-backend -n doc-generator
kubectl rollout undo deployment/davinci-frontend -n doc-generator

# Or deploy a specific image tag
kubectl set image deployment/davinci-backend backend=davinciai.azurecr.io/davinci-backend:<TAG> -n doc-generator
kubectl set image deployment/davinci-frontend frontend=davinciai.azurecr.io/davinci-frontend:<TAG> -n doc-generator
```

## Local Development

The application continues to run locally for development:
- Frontend: http://localhost:3000
- Backend: http://localhost:5001

## Security Notes

- Service principal credentials expire in 2 years (2027)
- Azure AD authentication is configured but currently disabled (`REQUIRE_AUTH=false`)
- Secrets are stored securely in GitHub repository secrets
- No credentials are committed to the repository