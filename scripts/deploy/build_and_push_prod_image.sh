#!/bin/bash
set -e
IMAGE_TAG="athena-prod-$(date +%Y%m%d%H%M%S)"
REGISTRY="private-registry.example.com"
IMAGE="$REGISTRY/athena:$IMAGE_TAG"
LOG="logs/deploy/docker_build_${IMAGE_TAG}.log"
mkdir -p logs/deploy
exec > >(tee -a "$LOG") 2>&1
echo "=== Docker Build & Push Start: $(date) ==="
echo "IMAGE_TAG=$IMAGE_TAG"
echo "IMAGE=$IMAGE"

if ! command -v docker >/dev/null 2>&1; then
  echo "ERROR: docker not installed"
  exit 1
fi

echo "[Docker] Building image..."
DOCKERFILE=$(ls Dockerfile.* 2>/dev/null | head -n 1)
if [ -z "$DOCKERFILE" ]; then
  if [ -f Dockerfile ]; then
    DOCKERFILE="Dockerfile"
  else
    echo "ERROR: No Dockerfile found (Dockerfile or Dockerfile.*). Skipping image build."; exit 0
  fi
fi
echo "Using Dockerfile: $DOCKERFILE"
set +e
docker build -t "$IMAGE" -f "$DOCKERFILE" .
BUILD_STATUS=$?
set -e
if [ $BUILD_STATUS -ne 0 ]; then
  echo "Docker build failed with status $BUILD_STATUS, skipping push attempt.";
  exit 0
fi

echo "[Docker] Pushing image to registry..."
docker push "$IMAGE"

echo "=== Docker Build & Push End: $(date) ==="
exit 0
