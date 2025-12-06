#!/bin/bash
# Script to stop UCSD Robocar Docker container

CONTAINER_NAME="oakd_vision_robocar"

if docker ps | grep -q $CONTAINER_NAME; then
    echo "Stopping container: $CONTAINER_NAME"
    docker stop $CONTAINER_NAME
    echo "Container stopped."
else
    echo "Container $CONTAINER_NAME is not running."
fi

# Disable X11 forwarding (security)
xhost -local:docker 2>/dev/null || true

echo "Done."

