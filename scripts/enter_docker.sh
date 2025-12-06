#!/bin/bash
# Script to enter running Docker container

CONTAINER_NAME="oakd_vision_robocar"

if docker ps | grep -q $CONTAINER_NAME; then
    echo "Entering container: $CONTAINER_NAME"
    docker exec -it $CONTAINER_NAME bash
else
    echo "Container $CONTAINER_NAME is not running."
    echo "Start it first with: ./scripts/start_docker.sh"
    exit 1
fi

