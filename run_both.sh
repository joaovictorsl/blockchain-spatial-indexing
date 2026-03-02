#!/bin/bash

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

STORAGE_TYPE=${1:-mongo}
V1_LOGS="v1_api_logs.txt"
V2_LOGS="v2_api_logs.txt"

if [[ "$STORAGE_TYPE" != "mongo" && "$STORAGE_TYPE" != "psql" ]]; then
    echo "Usage: $0 [mongo|psql]"
    echo "Default: mongo"
    exit 1
fi

echo "================================================"
echo "Starting both API versions simultaneously"
echo "V1 Storage: $STORAGE_TYPE"
echo "V1 API logs: $V1_LOGS"
echo "V2 API logs: $V2_LOGS"
echo "================================================"

cleanup() {
    echo ""
    echo "Shutting down services..."
    cd "$SCRIPT_DIR/v1/api"
    if [ "$STORAGE_TYPE" = "mongo" ]; then
        docker compose -f docker-compose.mongo.yml -p tcc-v1 down
    else
        docker compose -f docker-compose.psql.yml -p tcc-v1 down
    fi
    cd "$SCRIPT_DIR/v2/api"
    docker compose -p tcc-v2 down
    echo "All services stopped."
}

trap cleanup EXIT INT TERM

echo ""
echo "Starting V1 API with $STORAGE_TYPE..."
cd "$SCRIPT_DIR/v1/api"
if [ "$STORAGE_TYPE" = "mongo" ]; then
    docker compose -f docker-compose.mongo.yml -p tcc-v1 up -d --build
else
    docker compose -f docker-compose.psql.yml -p tcc-v1 up -d --build
fi

echo ""
echo "Starting V2 API..."
cd "$SCRIPT_DIR/v2/api"
docker compose -p tcc-v2 up -d --build

cd "$SCRIPT_DIR"

echo ""
echo "================================================"
echo "Both services are running!"
echo "V1 API: Check your .env for API_PORT (default: 8000)"
echo "V2 API: Running on port 8000"
echo "================================================"
echo ""
echo "Streaming logs (Ctrl+C to stop)..."
echo ""

docker compose -p tcc-v1 -f "$SCRIPT_DIR/v1/api/docker-compose.$STORAGE_TYPE.yml" logs -f api > "$V1_LOGS" 2>&1 &
V1_PID=$!

docker compose -p tcc-v2 -f "$SCRIPT_DIR/v2/api/docker-compose.yml" logs -f api > "$V2_LOGS" 2>&1 &
V2_PID=$!

echo "V1 API logs -> $V1_LOGS (PID: $V1_PID)"
echo "V2 API logs -> $V2_LOGS (PID: $V2_PID)"
echo ""
echo "Press Ctrl+C to stop all services and exit..."

wait $V1_PID $V2_PID
