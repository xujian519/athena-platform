#!/bin/bash
set -e
LOG="logs/deploy/k8s_deploy_$(date +%Y%m%d%H%M%S).log"
mkdir -p logs/deploy
exec > >(tee -a "$LOG") 2>&1
echo "=== Kubernetes Prod Deploy Start: $(date) ==="

NAMESPACE="athena-prod"
if ! kubectl get ns "$NAMESPACE" >/dev/null 2>&1; then
  echo "Creating namespace $NAMESPACE"
  kubectl create ns "$NAMESPACE"
fi

echo "Applying manifests for production in namespace $NAMESPACE"
kubectl apply -f configs/k8s/prod/ -n "$NAMESPACE" || true

echo "Checking rollout status for deployments in $NAMESPACE"
kubectl rollout status deployment -n "$NAMESPACE" --timeout=600s || true

echo "Listing pods in $NAMESPACE"
kubectl get pods -n "$NAMESPACE" || true

echo "=== Kubernetes Prod Deploy End: $(date) ==="
exit 0
