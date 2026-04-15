#!/bin/bash
set -euo pipefail
LOG="logs/deploy/validate_certificates_$(date +%Y%m%d%H%M%S).log"
mkdir -p logs/deploy
exec > >(tee -a "$LOG") 2>&1
echo "=== Validate Certificates Start: $(date) ==="

CERT_DIRS=("configs/production/certs" "production/certs")
CERT_FOUND=0
for dir in "${CERT_DIRS[@]}"; do
  if [ -d "$dir" ]; then
    for cert in "$dir"/*.crt; do
      if [ -f "$cert" ]; then
        CERT_FOUND=1
        echo "FOUND_CERT: $(basename "$cert")"
        openssl x509 -in "$cert" -noout -dates || echo "INVALID_CERT: $(basename "$cert")"
      fi
    done
  fi
done

if [ "$CERT_FOUND" -eq 0 ]; then
  echo "No certificate files (.crt) found in known cert directories."
fi

echo "=== Validate Certificates End: $(date) ==="
exit 0
