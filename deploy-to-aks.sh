#!/bin/bash

# Davinci Document Creator - AKS Deployment Script

set -e

echo "🚀 Starting deployment of Davinci Document Creator to AKS"

# Configuration
ACR_NAME="davinciregistry"
ACR_LOGIN_SERVER="${ACR_NAME}.azurecr.io"
RESOURCE_GROUP="davinci_can_cen_rg1"
AKS_CLUSTER="k8s-01"
NAMESPACE="doc-generator"

# Azure AD App Registration (You'll need to create this in Azure Portal)
TENANT_ID="953021b0-d492-4cc9-8551-e0b35080b03a"
CLIENT_ID="${AZURE_AD_CLIENT_ID:-your-app-registration-client-id}"
CLIENT_SECRET="${AZURE_AD_CLIENT_SECRET:-your-app-registration-secret}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Step 1: Login to Azure${NC}"
az account show &>/dev/null || az login

echo -e "${YELLOW}Step 2: Get AKS credentials${NC}"
az aks get-credentials --resource-group $RESOURCE_GROUP --name $AKS_CLUSTER --overwrite-existing

echo -e "${YELLOW}Step 3: Login to Azure Container Registry${NC}"
az acr login --name $ACR_NAME

echo -e "${YELLOW}Step 4: Build and push Docker images${NC}"

# Build backend
echo "Building backend image..."
docker build -t ${ACR_LOGIN_SERVER}/davinci-backend:latest ./backend
docker push ${ACR_LOGIN_SERVER}/davinci-backend:latest

# Build frontend
echo "Building frontend image..."
docker build -t ${ACR_LOGIN_SERVER}/davinci-frontend:latest ./frontend
docker push ${ACR_LOGIN_SERVER}/davinci-frontend:latest

echo -e "${YELLOW}Step 5: Create namespace${NC}"
kubectl create namespace $NAMESPACE --dry-run=client -o yaml | kubectl apply -f -

echo -e "${YELLOW}Step 6: Create secrets for Azure AD${NC}"
kubectl create secret generic davinci-doc-secrets \
  --namespace=$NAMESPACE \
  --from-literal=azure-tenant-id=$TENANT_ID \
  --from-literal=azure-client-id=$CLIENT_ID \
  --from-literal=azure-client-secret=$CLIENT_SECRET \
  --dry-run=client -o yaml | kubectl apply -f -

echo -e "${YELLOW}Step 7: Deploy to Kubernetes${NC}"
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/ingress.yaml

echo -e "${YELLOW}Step 8: Wait for deployment${NC}"
kubectl rollout status deployment/davinci-backend -n $NAMESPACE
kubectl rollout status deployment/davinci-frontend -n $NAMESPACE

echo -e "${YELLOW}Step 9: Get ingress IP${NC}"
echo "Waiting for ingress to get an IP address..."
for i in {1..60}; do
  INGRESS_IP=$(kubectl get ingress davinci-doc-ingress -n $NAMESPACE -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null)
  if [ ! -z "$INGRESS_IP" ]; then
    break
  fi
  echo -n "."
  sleep 5
done

echo ""
echo -e "${GREEN}✅ Deployment complete!${NC}"
echo ""
echo "Application details:"
echo "==================="
echo "Namespace: $NAMESPACE"
echo "Frontend: https://davinci-docs.davincisolutions.ai"
echo "Backend API: https://davinci-docs.davincisolutions.ai/api"

if [ ! -z "$INGRESS_IP" ]; then
  echo "Ingress IP: $INGRESS_IP"
  echo ""
  echo -e "${YELLOW}⚠️  Please update your DNS to point davinci-docs.davincisolutions.ai to $INGRESS_IP${NC}"
fi

echo ""
echo "To check pod status:"
echo "  kubectl get pods -n $NAMESPACE"
echo ""
echo "To view logs:"
echo "  kubectl logs -f deployment/davinci-backend -n $NAMESPACE"
echo "  kubectl logs -f deployment/davinci-frontend -n $NAMESPACE"
echo ""
echo "To set up Azure AD SSO:"
echo "  1. Create an App Registration in Azure Portal"
echo "  2. Set redirect URI to: https://davinci-docs.davincisolutions.ai/auth/callback"
echo "  3. Update the CLIENT_ID and CLIENT_SECRET in the script"
echo "  4. Re-run this deployment"