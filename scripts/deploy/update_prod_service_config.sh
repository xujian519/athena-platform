#!/bin/bash
set -e
LOG="logs/deploy/update_prod_service_config_$(date +%Y%m%d%H%M%S).log"
mkdir -p logs/deploy
exec > >(tee -a "$LOG") 2>&1
echo "=== Update Prod Service Config Start: $(date) ==="

CONFIG_FILE="configs/production/k8s-prod.yaml"
UPDATED_FILE="configs/production/k8s-prod.yaml.updated"
if [ -f "$CONFIG_FILE" ]; then
  cp "$CONFIG_FILE" "$UPDATED_FILE"
  echo "UPDATED: ${UPDATED_FILE}"
  echo "STATUS: OK"
else
  echo "CONFIG_MISSING: ${CONFIG_FILE}"
  echo "STATUS: FAIL"
  exit 1
fi
echo "=== Update Prod Service Config End: $(date) ==="
exit 0
