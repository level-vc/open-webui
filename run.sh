#!/bin/bash

# Load environment variables from .env file if it exists
if [ -f .env ]; then
    echo "Loading environment variables from .env file..."
    set -a  # automatically export all variables
    source .env
    set +a  # stop automatically exporting
fi

image_name="open-webui"
container_name="open-webui"
host_port=3000
container_port=8080

docker build -t "$image_name" .
docker stop "$container_name" &>/dev/null || true
docker rm "$container_name" &>/dev/null || true

docker run -d -p "$host_port":"$container_port" \
    --add-host=host.docker.internal:host-gateway \
    -v "${image_name}:/app/backend/data" \
    --name "$container_name" \
    --restart always \
    -e OPENAI_API_BASE_URL="${OPENAI_API_BASE_URL}" \
    -e OPENAI_API_KEY="${OPENAI_API_KEY}" \
    -e DATABASE_URL="${DATABASE_URL}" \
    -e ENABLE_OAUTH_SIGNUP="${ENABLE_OAUTH_SIGNUP}" \
    -e OAUTH_CLIENT_ID="${OAUTH_CLIENT_ID}" \
    -e OAUTH_CLIENT_SECRET="${OAUTH_CLIENT_SECRET}" \
    -e OPENID_PROVIDER_URL="${OPENID_PROVIDER_URL}" \
    -e OAUTH_PROVIDER_NAME="${OAUTH_PROVIDER_NAME}" \
    -e OAUTH_SCOPES="${OAUTH_SCOPES}" \
    -e ENABLE_LOGIN_FORM="${ENABLE_LOGIN_FORM}" \
    -e ENABLE_OLLAMA_API=false \
    -e LANGFUSE_PUBLIC_KEY="${LANGFUSE_PUBLIC_KEY}" \
    -e LANGFUSE_SECRET_KEY="${LANGFUSE_SECRET_KEY}" \
    -e MCP_ENABLE=${MCP_ENABLE} \
    -e VECTOR_DB="${VECTOR_DB}" \
    -e PGVECTOR_DB_URL="${PGVECTOR_DB_URL}" \
    "$image_name"

docker image prune -f

echo "Open WebUI is running at http://localhost:3000"
