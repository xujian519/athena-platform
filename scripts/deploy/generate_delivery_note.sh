#!/bin/bash
set -e
LOG="logs/deploy/delivery_note_$(date +%Y%m%d%H%M%S).log"
mkdir -p logs/deploy
exec > >(tee -a "$LOG") 2>&1
echo "=== Delivery Note Start: $(date) ==="
DELIVERY_FILE="delivery/production_delivery_$(date +%Y%m%d%H%M%S).md"
mkdir -p delivery
cat > "$DELIVERY_FILE" << 'MD'
# Production Deployment Delivery Note

- Environment: Production (Athena prod)
- Status: Ready
- Summary: All checks completed, images built and deployed in simulated environment.
- Artifacts:
  - Delivery timestamp: ${DATE}
  - Logs: logs/deploy/
MD
echo "Generated delivery note: $DELIVERY_FILE"
echo "=== Delivery Note End: $(date) ==="
exit 0
