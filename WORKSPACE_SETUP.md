# Workspace Setup Guide

This guide explains how to add your project to the ROS2 workspace inside the Docker container.

## Understanding the Setup

- **Host Machine**: Where you edit code
- **Docker Container**: Where ROS2 runs
- **Workspace**: `~/ros2_ws` inside container (mounted from host)
- **Project**: Your `ROS2_based_Final_Project_T12` directory

## Method 1: Mount Project and Link to Workspace (Recommended)

This allows you to edit files on your host machine and have them available in the container.

### Step 1: Start Container with Project Mounted

The `start_docker.sh` script automatically mounts your project:

```bash
# From project root directory
./scripts/start_docker.sh
```

Or manually:
```bash
docker run -it --rm \
  --privileged \
  --network host \
  -e DISPLAY=$DISPLAY \
  -v /tmp/.X11-unix:/tmp/.X11-unix \
  -v /dev:/dev \
  -v ~/ros2_ws:/home/ros/ros2_ws \
  -v $(pwd):/home/ros/oakd_vision_project \
  djnighti/ucsd_robocar:x86 \
  bash
```

### Step 2: Link Project to Workspace (Inside Container)

```bash
# Enter container
./scripts/enter_docker.sh

# Run setup script
./scripts/setup_workspace.sh

# Or manually:
cd ~/ros2_ws/src
ln -s /home/ros/oakd_vision_project/src/* ./
```

### Step 3: Build Workspace

```bash
cd ~/ros2_ws
colcon build --packages-select oakd_msgs
source install/setup.bash
colcon build --symlink-install
source install/setup.bash
```

**Benefits:**
- ✅ Edit files on host, changes reflect in container
- ✅ No need to copy files
- ✅ Easy to version control

## Method 2: Git Clone Inside Container

If you prefer a clean setup or want to keep container separate from host.

### Step 1: Start Container

```bash
./scripts/start_docker.sh
./scripts/enter_docker.sh
```

### Step 2: Clone Project Inside Container

```bash
cd ~/ros2_ws/src
git clone <your-repo-url> oakd_vision_project
# Or clone directly
git clone <your-repo-url> .
```

### Step 3: Build Workspace

```bash
cd ~/ros2_ws
colcon build --packages-select oakd_msgs
source install/setup.bash
colcon build --symlink-install
source install/setup.bash
```

**Benefits:**
- ✅ Clean separation
- ✅ Easy to update with git pull
- ✅ No host dependencies

## Method 3: Copy Project to Workspace on Host

If you want files physically in the workspace directory.

### Step 1: Copy on Host Machine

```bash
# On host
mkdir -p ~/ros2_ws/src
cp -r /path/to/ROS2_based_Final_Project_T12/src/* ~/ros2_ws/src/
```

### Step 2: Start Container

```bash
./scripts/start_docker.sh
./scripts/enter_docker.sh
```

### Step 3: Build (Files Already in Workspace)

```bash
cd ~/ros2_ws
colcon build --packages-select oakd_msgs
source install/setup.bash
colcon build --symlink-install
source install/setup.bash
```

**Benefits:**
- ✅ Simple setup
- ✅ No linking needed
- ❌ Changes on host don't automatically reflect (need to copy again)

## Recommended Workflow

For development, use **Method 1** (mount + link):

1. Edit code on host machine
2. Changes automatically available in container (via symlink)
3. Build and test in container
4. Commit changes from host

## Quick Setup Script

Use the provided script for automatic setup:

```bash
# Inside container
cd /home/ros/oakd_vision_project
./scripts/setup_workspace.sh
```

This script:
- Checks if project is mounted
- Creates symlinks from project to workspace
- Provides next steps

## Troubleshooting

### Issue: Packages Not Found

```bash
# Check if packages are in workspace
ls ~/ros2_ws/src/

# If empty, run setup script or manually link
cd ~/ros2_ws/src
ln -s /home/ros/oakd_vision_project/src/* ./
```

### Issue: Changes Not Reflecting

If using symlinks, changes should be immediate. If using copies:
```bash
# Re-copy files
cp -r /home/ros/oakd_vision_project/src/* ~/ros2_ws/src/
```

### Issue: Build Errors

```bash
# Clean and rebuild
cd ~/ros2_ws
rm -rf build install log
colcon build --symlink-install
```

## Directory Structure

After setup, your workspace should look like:

```
~/ros2_ws/
├── src/
│   ├── oakd_msgs/          # Symlink or copy
│   ├── oakd_vision_pkg/    # Symlink or copy
│   ├── decision_pkg/       # Symlink or copy
│   ├── game_pkg/           # Symlink or copy
│   └── control_pkg/        # Symlink or copy
├── build/
├── install/
└── log/
```

## Next Steps

After workspace setup:
1. Download models: `./scripts/download_models.sh`
2. Build workspace: `colcon build`
3. Launch system: `ros2 launch full_system.launch.py`

