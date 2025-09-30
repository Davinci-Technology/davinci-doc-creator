# Deployment Guide - Davinci Document Creator

This project uses a **two-environment deployment strategy** with automated CI/CD pipelines.

## 🏗️ Architecture Overview

```
staging branch → Tests → Build → Deploy to Staging (doc-generator-staging)
                                  ↓
                              Test manually
                                  ↓
                           Merge to main
                                  ↓
main branch    → Tests → Build → Deploy to Production (doc-generator)
```

## 🌍 Environments

| Environment | Branch | Namespace | URL | Auth |
|------------|--------|-----------|-----|------|
| **Staging** | `staging` | `doc-generator-staging` | https://staging-docs.davincisolutions.ai | Disabled |
| **Production** | `main` | `doc-generator` | https://docs.davincisolutions.ai | Optional |

## 🚀 Deployment Workflows

### Staging Deployment

**Triggers:** Push to `staging` branch or manual dispatch

**Pipeline Steps:**
1. ✅ Run unit tests (`test_html_parser.py`)
2. ✅ Run integration tests (`test_pdf_generation.py`)
3. 🏗️ Build Docker images
4. 📦 Push to ACR with `staging-{sha}` and `staging` tags
5. 🚀 Deploy to `doc-generator-staging` namespace
6. ⏱️ Wait for rollout (5 min timeout)
7. 📊 Report deployment status

**Workflow File:** `.github/workflows/deploy-staging.yml`

### Production Deployment

**Triggers:** Push to `main` branch or manual dispatch

**Pipeline Steps:**
1. ✅ Run unit tests
2. ✅ Run integration tests
3. ✅ Run regression tests (if baselines exist)
4. 🏗️ Build Docker images
5. 📦 Push to ACR with `prod-{sha}` and `latest` tags
6. 🚀 Deploy to `doc-generator` namespace
7. ⏱️ Wait for rollout (5 min timeout)
8. ✔️ Verify deployment health
9. 📊 Report deployment status

**Workflow File:** `.github/workflows/deploy-production.yml`

## 📝 Development Workflow

### Standard Flow

```bash
# 1. Create feature branch from staging
git checkout staging
git pull origin staging
git checkout -b feature/your-feature-name

# 2. Make your changes and commit
git add .
git commit -m "Add feature X"

# 3. Push and create PR to staging
git push origin feature/your-feature-name
# Create PR: feature/your-feature-name → staging

# 4. Merge PR to staging
# → Automatically deploys to staging environment

# 5. Test on staging
open https://staging-docs.davincisolutions.ai

# 6. If everything works, promote to production
git checkout main
git pull origin main
git merge staging
git push origin main
# → Automatically deploys to production
```

### Hotfix Flow (Emergency Production Fix)

```bash
# 1. Create hotfix branch from main
git checkout main
git pull origin main
git checkout -b hotfix/urgent-fix

# 2. Make the fix
git add .
git commit -m "Fix critical bug X"

# 3. Push directly to main (skip staging)
git checkout main
git merge hotfix/urgent-fix
git push origin main
# → Deploys directly to production

# 4. Backport to staging
git checkout staging
git merge main
git push origin staging
```

## 🧪 Testing Before Deployment

All deployments run automated tests first. **If tests fail, deployment is blocked.**

### Run Tests Locally

```bash
cd backend
source .venv/bin/activate

# Run all tests
./run_tests.sh

# Run specific test suites
./run_tests.sh --unit          # Parser tests only
./run_tests.sh --integration   # PDF generation tests
./run_tests.sh --regression    # Compare to baselines
```

### Create Test Baselines (Important!)

Before making changes to PDF generation logic:

```bash
cd backend
./run_tests.sh --save-baseline
```

This captures current PDF output as the "correct" baseline for regression testing.

## 🔧 Manual Deployment

### Deploy Staging Manually

```bash
# Set context
kubectl config use-context k8s-01

# Create namespace
kubectl apply -f k8s/staging/namespace.yaml

# Deploy application
kubectl apply -f k8s/staging/deployment.yaml
kubectl apply -f k8s/staging/ingress.yaml

# Check status
kubectl get pods -n doc-generator-staging
kubectl get ingress -n doc-generator-staging
```

### Deploy Production Manually

```bash
# Set context
kubectl config use-context k8s-01

# Deploy application
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/ingress.yaml

# Check status
kubectl get pods -n doc-generator
kubectl get ingress -n doc-generator
```

## 🐛 Troubleshooting Deployments

### Check Pipeline Status

Visit: https://github.com/Davinci-Technology/davinci-doc-creator/actions

### View Logs

**Staging:**
```bash
kubectl logs -f -l app=davinci-backend-staging -n doc-generator-staging
kubectl logs -f -l app=davinci-frontend-staging -n doc-generator-staging
```

**Production:**
```bash
kubectl logs -f -l app=davinci-backend -n doc-generator
kubectl logs -f -l app=davinci-frontend -n doc-generator
```

### Check Pod Status

```bash
# Staging
kubectl get pods -n doc-generator-staging
kubectl describe pod <pod-name> -n doc-generator-staging

# Production
kubectl get pods -n doc-generator
kubectl describe pod <pod-name> -n doc-generator
```

### Rollback Deployment

**Staging:**
```bash
kubectl rollout undo deployment/davinci-backend-staging -n doc-generator-staging
kubectl rollout undo deployment/davinci-frontend-staging -n doc-generator-staging
```

**Production:**
```bash
kubectl rollout undo deployment/davinci-backend -n doc-generator
kubectl rollout undo deployment/davinci-frontend -n doc-generator
```

### Deploy Specific Version

```bash
# Find the image tag you want (from ACR or git SHA)
IMAGE_TAG="prod-abc123def456"

# Update deployment
kubectl set image deployment/davinci-backend \
  backend=davinciai.azurecr.io/davinci-backend:$IMAGE_TAG \
  -n doc-generator

kubectl set image deployment/davinci-frontend \
  frontend=davinciai.azurecr.io/davinci-frontend:$IMAGE_TAG \
  -n doc-generator
```

## 📊 Monitoring Deployments

### GitHub Actions Summary

After each deployment, GitHub creates a summary showing:
- Environment deployed to
- Image tags used
- Deployment URL
- Next steps

### Kubernetes Dashboard

```bash
# Get all resources in staging
kubectl get all -n doc-generator-staging

# Get all resources in production
kubectl get all -n doc-generator
```

### Health Checks

**Staging:** https://staging-docs.davincisolutions.ai/api/health
**Production:** https://docs.davincisolutions.ai/api/health

## 🔐 Secrets Management

Secrets are stored in Kubernetes secrets:

**Staging:**
```bash
kubectl create secret generic davinci-doc-secrets-staging \
  --namespace=doc-generator-staging \
  --from-literal=azure-tenant-id=$TENANT_ID \
  --from-literal=azure-client-id=$CLIENT_ID \
  --from-literal=azure-client-secret=$CLIENT_SECRET
```

**Production:**
```bash
kubectl create secret generic davinci-doc-secrets \
  --namespace=doc-generator \
  --from-literal=azure-tenant-id=$TENANT_ID \
  --from-literal=azure-client-id=$CLIENT_ID \
  --from-literal=azure-client-secret=$CLIENT_SECRET
```

## 🌐 DNS Configuration

Ensure DNS records point to the AKS ingress IP:

```bash
# Get ingress IP
kubectl get ingress -n doc-generator-staging
kubectl get ingress -n doc-generator
```

Add A records:
- `staging-docs.davincisolutions.ai` → Staging Ingress IP
- `docs.davincisolutions.ai` → Production Ingress IP

## 📦 Image Tags

| Environment | Tags | Description |
|------------|------|-------------|
| **Staging** | `staging-{sha}` | Unique tag per commit |
|  | `staging` | Always points to latest staging |
| **Production** | `prod-{sha}` | Unique tag per commit |
|  | `latest` | Always points to latest production |

## ⚠️ Important Notes

### Testing First
- **All** code changes should go through staging first
- Test thoroughly on staging before promoting to production
- Use regression tests to catch unintended changes

### Branch Protection
Consider adding these branch protection rules on GitHub:
- **staging**: Require PR reviews, run tests
- **main**: Require PR reviews, require status checks to pass

### Deployment Frequency
- **Staging**: Deploy frequently, multiple times per day
- **Production**: Deploy after thorough staging testing

### Rollback Strategy
- Keep at least 3 previous image versions in ACR
- Document rollback procedures
- Test rollback process periodically

## 🎯 Quick Commands

```bash
# Check what's deployed
kubectl get deploy,svc,ing -n doc-generator-staging
kubectl get deploy,svc,ing -n doc-generator

# Force new deployment (without code changes)
kubectl rollout restart deployment/davinci-backend-staging -n doc-generator-staging
kubectl rollout restart deployment/davinci-backend -n doc-generator

# Watch rollout
kubectl rollout status deployment/davinci-backend-staging -n doc-generator-staging --watch

# Scale deployment
kubectl scale deployment/davinci-backend-staging --replicas=2 -n doc-generator-staging

# Delete staging environment (cleanup)
kubectl delete namespace doc-generator-staging
```

## 📞 Support

For deployment issues:
1. Check GitHub Actions logs
2. Check Kubernetes pod logs
3. Verify DNS configuration
4. Check ingress status
5. Review recent commits for breaking changes

## 🔄 CI/CD Pipeline Diagram

```
┌─────────────────────────────────────────────────────────────┐
│  Feature Development                                         │
│  feature/* → PR → staging branch                            │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  Staging Pipeline (.github/workflows/deploy-staging.yml)    │
│  ✅ Unit Tests                                              │
│  ✅ Integration Tests                                       │
│  🏗️  Build & Push (staging tags)                           │
│  🚀 Deploy to doc-generator-staging                         │
│  🌐 https://staging-docs.davincisolutions.ai               │
└────────────────────────┬────────────────────────────────────┘
                         │
                         │ Manual testing passes
                         │
                         ▼
                    Merge staging → main
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  Production Pipeline (.github/workflows/deploy-production.yml)│
│  ✅ Unit Tests                                              │
│  ✅ Integration Tests                                       │
│  ✅ Regression Tests                                        │
│  🏗️  Build & Push (prod tags)                              │
│  🚀 Deploy to doc-generator                                 │
│  🌐 https://docs.davincisolutions.ai                        │
└─────────────────────────────────────────────────────────────┘
```
