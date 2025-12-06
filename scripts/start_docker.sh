#!/bin/bash
# Script to start UCSD Robocar Docker container with OAK-D support

set -e

# Configuration
IMAGE_X86="djnighti/ucsd_robocar:x86"
IMAGE_ARM="djnighti/ucsd_robocar:devel"
CONTAINER_NAME="oakd_vision_robocar"

# Detect architecture
ARCH=$(uname -m)
if [ "$ARCH" = "aarch64" ] || [ "$ARCH" = "arm64" ]; then
    IMAGE=$IMAGE_ARM
    echo "Detected ARM architecture, using: $IMAGE"
else
    IMAGE=$IMAGE_X86
    echo "Detected X86 architecture, using: $IMAGE"
fi

# Check if image exists
if ! docker images | grep -q "$(echo $IMAGE | cut -d: -f1)"; then
    echo "Image $IMAGE not found. Pulling..."
    docker pull $IMAGE
fi

# Enable X11 forwarding
xhost +local:docker 2>/dev/null || echo "Note: xhost command failed, X11 may not work"

# Check if container already exists
if docker ps -a | grep -q $CONTAINER_NAME; then
    echo "Container $CONTAINER_NAME already exists."
    read -p "Start existing container? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker start $CONTAINER_NAME
        echo "Container started. Access with: docker exec -it $CONTAINER_NAME bash"
        exit 0
    else
        echo "Removing existing container..."
        docker rm -f $CONTAINER_NAME
    fi
fi

# Create workspace directory if it doesn't exist
WORKSPACE_DIR="$HOME/ros2_ws"
if [ ! -d "$WORKSPACE_DIR" ]; then
    echo "Creating workspace directory: $WORKSPACE_DIR"
    mkdir -p $WORKSPACE_DIR/src
fi

# Get project directory (assume script is run from project root)
PROJECT_DIR=$(pwd)

# Start container
echo "Starting container: $CONTAINER_NAME"
echo "Mounting workspace: $WORKSPACE_DIR -> /home/ros/ros2_ws"
echo "Mounting project: $PROJECT_DIR -> /home/ros/oakd_vision_project"
docker run -d \
    --name $CONTAINER_NAME \
    --privileged \
    --network host \
    -e DISPLAY=$DISPLAY \
    -v /tmp/.X11-unix:/tmp/.X11-unix \
    -v /dev:/dev \
    -v $WORKSPACE_DIR:/home/ros/ros2_ws \
    -v $PROJECT_DIR:/home/ros/oakd_vision_project \
    $IMAGE \
    tail -f /dev/null

echo ""
echo "=========================================="
echo "Container started successfully!"
echo "Container name: $CONTAINER_NAME"
echo ""
echo "To access the container, run:"
echo "  docker exec -it $CONTAINER_NAME bash"
echo ""
echo "Inside the container, set up your project:"
echo ""
echo "Option 1: Link mounted project to workspace"
echo "  cd ~/ros2_ws/src"
echo "  ln -s /home/ros/oakd_vision_project/src/* ./"
echo ""
echo "Option 2: Git clone into workspace"
echo "  cd ~/ros2_ws/src"
echo "  git clone <your-repo-url> oakd_vision_project"
echo ""
echo "Then build and run:"
echo "  1. cd ~/ros2_ws"
echo "  2. ./scripts/download_models.sh  # (if in project dir)"
echo "  3. colcon build --packages-select oakd_msgs"
echo "  4. source install/setup.bash"
echo "  5. colcon build --symlink-install"
echo "  6. source install/setup.bash"
echo "  7. ros2 launch full_system.launch.py"
echo "=========================================="

