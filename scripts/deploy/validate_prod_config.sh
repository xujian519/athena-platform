#!/bin/bash
set -euo pipefail
LOG="logs/deploy/validate_prod_config_$(date +%Y%m%d%H%M%S).log"
mkdir -p logs/deploy
exec > >(tee -a "$LOG") 2>&1
echo "=== Validate Prod Config Start: $(date) ==="

CONFIG_DIR="configs/production"
if [ ! -d "$CONFIG_DIR" ]; then
  if [ -d "production" ]; then
    CONFIG_DIR="production"
  else
    echo "ERROR: Production config directory not found: $CONFIG_DIR"; exit 1
  fi
fi

MISSING_VARS=()
REQUIRED_FILES=("hosts.txt" "k8s-prod.yaml" "app-secrets.yaml")
for f in "${REQUIRED_FILES[@]}"; do
  if [ ! -f "$CONFIG_DIR/$f" ]; then
    MISSING_VARS+=("$f")
  fi
done

if command -v yq >/dev/null 2>&1; then
  echo "YAML check: yq installed (skipping detailed validation)"
fi

if [ ${#MISSING_VARS[@]} -gt 0 ]; then
  echo "Missing required config files: ${MISSING_VARS[*]}"
  echo "STATUS: FAIL"
  exit 2
fi

echo "All required production config files are present."
echo "STATUS: OK"
echo "=== Validate Prod Config End: $(date) ==="
exit 0
