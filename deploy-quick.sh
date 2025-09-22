#!/bin/bash

# Quick deployment without building images
# We'll deploy first, then update images later

echo "🚀 Quick deployment to AKS (using placeholder images)"

NAMESPACE="doc-generator"

echo "Creating namespace..."
kubectl create namespace $NAMESPACE --dry-run=client -o yaml | kubectl apply -f -

echo "Deploying application..."
kubectl apply -f k8s/deployment.yaml

echo "Getting service status..."
kubectl get pods -n $NAMESPACE
kubectl get service -n $NAMESPACE

echo ""
echo "✅ Deployment started!"
echo ""
echo "Watch pod status with:"
echo "  kubectl get pods -n $NAMESPACE -w"
echo ""
echo "Once pods are running, get the external IP with:"
echo "  kubectl get service davinci-frontend -n $NAMESPACE"