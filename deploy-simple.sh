#!/bin/bash

# Simple deployment script for Davinci Document Creator to AKS
# This version deploys without Azure AD authentication

set -e

echo "🚀 Deploying Davinci Document Creator to AKS (Simple version - no auth)"

# Configuration
ACR_NAME="davinciai"
ACR_LOGIN_SERVER="${ACR_NAME}.azurecr.io"
NAMESPACE="doc-generator"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}Step 1: Switch to k8s-01 context${NC}"
kubectl config use-context k8s-01

echo -e "${YELLOW}Step 2: Login to ACR${NC}"
az acr login --name $ACR_NAME

echo -e "${YELLOW}Step 3: Build and push images${NC}"
docker build -t ${ACR_LOGIN_SERVER}/davinci-backend:latest ./backend
docker push ${ACR_LOGIN_SERVER}/davinci-backend:latest

docker build -t ${ACR_LOGIN_SERVER}/davinci-frontend:latest ./frontend
docker push ${ACR_LOGIN_SERVER}/davinci-frontend:latest

echo -e "${YELLOW}Step 4: Create namespace${NC}"
kubectl create namespace $NAMESPACE --dry-run=client -o yaml | kubectl apply -f -

echo -e "${YELLOW}Step 5: Deploy application${NC}"
kubectl apply -f k8s/deployment.yaml

echo -e "${YELLOW}Step 6: Wait for pods${NC}"
kubectl wait --for=condition=ready pod -l app=davinci-backend -n $NAMESPACE --timeout=120s
kubectl wait --for=condition=ready pod -l app=davinci-frontend -n $NAMESPACE --timeout=120s

echo -e "${GREEN}✅ Deployment complete!${NC}"
echo ""
echo "Get the external IP with:"
echo "  kubectl get service davinci-frontend -n $NAMESPACE"
echo ""
echo "View logs with:"
echo "  kubectl logs -f -l app=davinci-backend -n $NAMESPACE"
echo "  kubectl logs -f -l app=davinci-frontend -n $NAMESPACE"