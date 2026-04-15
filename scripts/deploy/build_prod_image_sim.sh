#!/bin/bash
set -e
LOG="logs/deploy/build_prod_image_sim_$(date +%Y%m%d%H%M%S).log"
mkdir -p logs/deploy
exec > >(tee -a "$LOG") 2>&1
echo "=== Prod Image Build (Sim) Start: $(date) ==="

IMAGE_TAG="athena-prod-sim-$(date +%Y%m%d%H%M%S)"
REGISTRY="private-registry.example.com"
IMAGE="$REGISTRY/athena:$IMAGE_TAG"
echo "Simulating build for image: $IMAGE"
echo "Note: No actual docker build executed in this environment."
echo "BUILD_STATUS: OK"
echo "=== Prod Image Build (Sim) End: $(date) ==="
exit 0
