#!/bin/bash
# Script to set up project in workspace (run inside Docker container)

set -e

WORKSPACE_DIR="$HOME/ros2_ws"
PROJECT_DIR="/home/ros/oakd_vision_project"

echo "Setting up project in workspace..."

# Check if project is mounted
if [ ! -d "$PROJECT_DIR" ]; then
    echo "Error: Project directory not found at $PROJECT_DIR"
    echo "Make sure you mounted the project when starting the container"
    exit 1
fi

# Create workspace src if it doesn't exist
mkdir -p $WORKSPACE_DIR/src

# Check if packages already exist
if [ -d "$WORKSPACE_DIR/src/oakd_vision_pkg" ]; then
    echo "Packages already exist in workspace. Skipping setup."
    echo "To re-setup, remove ~/ros2_ws/src/oakd_vision_pkg and related packages first."
    exit 0
fi

# Option 1: Create symlinks (recommended - allows editing on host)
echo "Creating symlinks from project to workspace..."
cd $WORKSPACE_DIR/src
for dir in $PROJECT_DIR/src/*/; do
    if [ -d "$dir" ]; then
        dirname=$(basename "$dir")
        echo "Linking $dirname..."
        ln -s "$dir" "$dirname"
    fi
done

# Option 2: Copy files (uncomment if you prefer copying)
# echo "Copying project files to workspace..."
# cp -r $PROJECT_DIR/src/* $WORKSPACE_DIR/src/

echo ""
echo "Setup complete!"
echo "Project packages are now in ~/ros2_ws/src"
echo ""
echo "Next steps:"
echo "  1. cd ~/ros2_ws"
echo "  2. colcon build --packages-select oakd_msgs"
echo "  3. source install/setup.bash"
echo "  4. colcon build --symlink-install"
echo "  5. source install/setup.bash"

