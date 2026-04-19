#!/bin/bash
set -e
LOG="logs/deploy/push_prod_image_sim_$(date +%Y%m%d%H%M%S).log"
mkdir -p logs/deploy
exec > >(tee -a "$LOG") 2>&1
echo "=== Prod Image Push (Sim) Start: $(date) ==="
IMAGE="private-registry.example.com/athena:athena-prod-sim-20260220102608"
echo "Simulating push of image: $IMAGE"
echo "PUSH_STATUS: OK"
echo "=== Prod Image Push (Sim) End: $(date) ==="
exit 0
