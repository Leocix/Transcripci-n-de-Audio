#!/usr/bin/env bash
set -euo pipefail

# Script para Droplet Ubuntu 22.04+ que clona el repo y construye la imagen full
# Uso:
#   1. Copia este script al Droplet (scp scripts/build_and_push_on_droplet.sh user@droplet:~)
#   2. En el Droplet: chmod +x build_and_push_on_droplet.sh
#   3. Exporta variables: export DOCR_REGISTRY=registry.digitalocean.com/transcriptor
#      export DOCR_REPOSITORY=transcripcion-audio
#      export GIT_REF=master
#   4. Ejecuta: ./build_and_push_on_droplet.sh

# Variables configurables
DOCR_REGISTRY_DEFAULT="registry.digitalocean.com"
DOCR_REPOSITORY_DEFAULT="transcriptor/transcripcion-audio"
GIT_REF_DEFAULT="master"

DOCR_REGISTRY=${DOCR_REGISTRY:-$DOCR_REGISTRY_DEFAULT}
DOCR_REPOSITORY=${DOCR_REPOSITORY:-$DOCR_REPOSITORY_DEFAULT}
GIT_REF=${GIT_REF:-$GIT_REF_DEFAULT}

REPO_URL="https://github.com/Leocix/Transcripci-n-de-Audio.git"
WORKDIR="/tmp/transcripcion_build"

echo "Variables:\n  DOCR_REGISTRY=${DOCR_REGISTRY}\n  DOCR_REPOSITORY=${DOCR_REPOSITORY}\n  GIT_REF=${GIT_REF}\n  WORKDIR=${WORKDIR}"

# Preparar entorno
sudo apt-get update
sudo apt-get install -y git curl jq ca-certificates

# Instalar Docker si no está
if ! command -v docker >/dev/null 2>&1; then
  echo "Instalando Docker..."
  curl -fsSL https://get.docker.com -o get-docker.sh
  sudo sh get-docker.sh
  rm get-docker.sh
  sudo usermod -aG docker $USER || true
fi

# Crear workspace
rm -rf "$WORKDIR"
mkdir -p "$WORKDIR"
cd "$WORKDIR"

# Clonar repo
git clone --depth 1 --branch "$GIT_REF" "$REPO_URL" repo
cd repo

# Preparar requirements-full
cat config/requirements.txt config/requirements-optional.txt > config/requirements-full.txt

# Build usando buildx
IMAGE_TAG="${DOCR_REGISTRY}/${DOCR_REPOSITORY}:${GIT_REF}-full"
IMAGE_LATEST_TAG="${DOCR_REGISTRY}/${DOCR_REPOSITORY}:full-latest"

docker buildx create --use || true

echo "Construyendo imagen: $IMAGE_TAG"
# Try to use cache if available
docker buildx build --progress=plain --pull \
  --cache-from=type=registry,ref=${IMAGE_LATEST_TAG} \
  -t "$IMAGE_TAG" \
  --build-arg REQUIREMENTS=config/requirements-full.txt \
  --load . | tee build-full.log

# Tag and push
docker tag "$IMAGE_TAG" "$IMAGE_LATEST_TAG"

for i in 1 2 3; do
  echo "Intentando push ($i)..."
  if docker push "$IMAGE_TAG" | tee -a build-full.log; then
    echo "Push exitoso"
    break
  else
    echo "Push falló, reintentando en 10s..."
    sleep 10
  fi
done

# Push latest tag
docker push "$IMAGE_LATEST_TAG" | tee -a build-full.log

# Output digest
echo "Listando manifests en registry (requerirá doctl si quieres el digest exacto):"

echo "Build y push completados. Revisa build-full.log para detalles"
