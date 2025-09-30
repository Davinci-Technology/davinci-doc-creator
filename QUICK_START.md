# Quick Start - Deployment Cheat Sheet

## 🚀 I Want To Deploy Changes

### To Staging (for testing)

```bash
# 1. Make changes on staging branch or feature branch
git checkout staging
# ... make changes ...
git add .
git commit -m "Your changes"

# 2. Push to trigger deployment
git push origin staging

# 3. Watch deployment
# Go to: https://github.com/Davinci-Technology/davinci-doc-creator/actions

# 4. Test your changes
open https://staging-docs.davincisolutions.ai
```

### To Production (after staging testing)

```bash
# 1. Merge staging into main
git checkout main
git pull origin main
git merge staging

# 2. Push to trigger production deployment
git push origin main

# 3. Watch deployment
# Go to: https://github.com/Davinci-Technology/davinci-doc-creator/actions

# 4. Verify production
open https://docs.davincisolutions.ai
```

## 🧪 I Want To Test Changes Before Deploying

```bash
cd backend
source .venv/bin/activate

# Run all tests
./run_tests.sh

# If you changed PDF generation, save new baselines
./run_tests.sh --save-baseline
```

## 🐛 I Need To Rollback

### Staging

```bash
kubectl rollout undo deployment/davinci-backend-staging -n doc-generator-staging
kubectl rollout undo deployment/davinci-frontend-staging -n doc-generator-staging
```

### Production

```bash
kubectl rollout undo deployment/davinci-backend -n doc-generator
kubectl rollout undo deployment/davinci-frontend -n doc-generator
```

## 👀 I Want To Check What's Deployed

### View Current Deployments

```bash
# Staging
kubectl get pods -n doc-generator-staging

# Production
kubectl get pods -n doc-generator
```

### View Logs

```bash
# Staging
kubectl logs -f -l app=davinci-backend-staging -n doc-generator-staging

# Production
kubectl logs -f -l app=davinci-backend -n doc-generator
```

### Check Health

- Staging: https://staging-docs.davincisolutions.ai/api/health
- Production: https://docs.davincisolutions.ai/api/health

## 🔄 The Complete Flow

```
1. Create feature branch
   ↓
2. Make changes + commit
   ↓
3. Push to staging branch
   ↓
4. Auto-deploy to staging → https://staging-docs.davincisolutions.ai
   ↓
5. Test thoroughly on staging
   ↓
6. Merge staging → main
   ↓
7. Auto-deploy to production → https://docs.davincisolutions.ai
   ↓
8. Verify production works
```

## ❌ Deployment Failed?

### Check GitHub Actions

1. Go to https://github.com/Davinci-Technology/davinci-doc-creator/actions
2. Click on the failed workflow
3. Expand the failed step
4. Read error message

### Common Issues

**Tests failed:**
```bash
# Fix the tests or the code, then push again
./run_tests.sh  # Run locally first
```

**Build failed:**
```bash
# Check Docker build logs in GitHub Actions
# Usually means syntax error or missing dependency
```

**Deployment failed:**
```bash
# Check Kubernetes logs
kubectl get pods -n doc-generator-staging
kubectl describe pod <pod-name> -n doc-generator-staging
```

**Rollout timeout:**
```bash
# Pod might be crashlooping
kubectl logs <pod-name> -n doc-generator-staging
```

## 🎯 Common Tasks

### Force Redeploy (without code changes)

```bash
kubectl rollout restart deployment/davinci-backend-staging -n doc-generator-staging
```

### Deploy Specific Version

```bash
# Find the git SHA or image tag you want
IMAGE_TAG="staging-abc123"

kubectl set image deployment/davinci-backend-staging \
  backend=davinciai.azurecr.io/davinci-backend:$IMAGE_TAG \
  -n doc-generator-staging
```

### Delete Staging Environment

```bash
kubectl delete namespace doc-generator-staging
# Re-run deployment workflow to recreate
```

## 📊 Monitoring

### GitHub Actions Status

- Recent workflows: https://github.com/Davinci-Technology/davinci-doc-creator/actions
- Green check ✅ = Success
- Red X ❌ = Failed

### Kubernetes Status

```bash
# All resources at once
kubectl get all -n doc-generator-staging
kubectl get all -n doc-generator
```

## 🆘 Emergency Hotfix

```bash
# 1. Branch from main
git checkout main
git pull
git checkout -b hotfix/critical-bug

# 2. Fix the bug
# ... make changes ...

# 3. Commit and push directly to main
git checkout main
git merge hotfix/critical-bug
git push origin main
# → Deploys to production immediately

# 4. Backport to staging
git checkout staging
git merge main
git push origin staging
```

## 📚 Need More Info?

- Full deployment guide: [DEPLOYMENT.md](./DEPLOYMENT.md)
- Test suite docs: [backend/tests/README.md](./backend/tests/README.md)
- Project README: [README.md](./README.md)
