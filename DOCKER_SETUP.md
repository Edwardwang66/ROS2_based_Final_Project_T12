# Docker Setup Guide for ROS2 OAK-D Vision Project

This guide explains how to run the project inside the UCSD Robocar Hub2 Docker container.

## Prerequisites

1. **Docker installed** on your system
2. **UCSD Robocar Docker image** pulled from Docker Hub
3. **X11 forwarding** set up (for GUI applications)

## Step 1: Pull UCSD Robocar Docker Image

### For ARM Architecture (Jetson)
```bash
docker pull djnighti/ucsd_robocar:devel
```

### For X86 Architecture (Most laptops/desktops)
```bash
docker pull djnighti/ucsd_robocar:x86
```

## Step 2: Enable X11 Forwarding (if needed)

### On Host Machine
```bash
# Enable X11 forwarding
xhost +local:docker

# SSH with X11 forwarding (if connecting to Jetson)
ssh -X jetson@ip_address
```

### Verify X11 Forwarding
```bash
# Inside container, test with:
xeyes
```

**Note**: Remember to disable X11 forwarding when done:
```bash
xhost -local:docker
```

## Step 3: Start Docker Container

### Option A: Using Existing UCSD Container Scripts

The UCSD Robocar Hub2 container should have helper scripts. Check the container's `~/.bashrc` for functions like:
```bash
# Example function (may vary)
create_robocar_container
```

### Option B: Manual Container Start

```bash
# For X86
docker run -it --rm \
  --privileged \
  --network host \
  -e DISPLAY=$DISPLAY \
  -v /tmp/.X11-unix:/tmp/.X11-unix \
  -v /dev:/dev \
  -v ~/ros2_ws:/home/ros/ros2_ws \
  djnighti/ucsd_robocar:x86 \
  bash

# For ARM (Jetson)
docker run -it --rm \
  --privileged \
  --network host \
  -e DISPLAY=$DISPLAY \
  -v /tmp/.X11-unix:/tmp/.X11-unix \
  -v /dev:/dev \
  -v ~/ros2_ws:/home/ros/ros2_ws \
  djnighti/ucsd_robocar:devel \
  bash
```

**Explanation of flags:**
- `--privileged`: Required for hardware access (cameras, USB devices)
- `--network host`: Use host network (for ROS2 communication)
- `-e DISPLAY=$DISPLAY`: Forward display for GUI
- `-v /tmp/.X11-unix:/tmp/.X11-unix`: X11 socket for display
- `-v /dev:/dev`: Access to devices (OAK-D camera, etc.)
- `-v ~/ros2_ws:/home/ros/ros2_ws`: Mount your workspace

## Step 4: Access Running Container

If container is already running:
```bash
# List running containers
docker ps

# Access container (replace CONTAINER_NAME with actual name)
docker exec -it CONTAINER_NAME bash
```

## Step 5: Setup Project Inside Container

Once inside the container:

```bash
# Navigate to workspace
cd ~/ros2_ws  # or wherever you mounted it

# Install Python dependencies (if not already in image)
pip3 install depthai opencv-python numpy

# Build workspace
colcon build --packages-select oakd_msgs
source install/setup.bash
colcon build --symlink-install
source install/setup.bash
```

## Step 6: Connect OAK-D Camera

### Check Camera Access
```bash
# Inside container, check if OAK-D is detected
lsusb | grep Luxonis

# Test depthai
python3 -c "import depthai as dai; print('OK')"
```

### If Camera Not Detected
```bash
# Check USB permissions
ls -l /dev/bus/usb/

# May need to add user to dialout group (if not already)
sudo usermod -a -G dialout $USER
```

## Step 7: Run Project

### Launch Full System
```bash
# Inside container
ros2 launch full_system.launch.py

# Or with mock mode (no hardware)
ros2 launch full_system.launch.py use_mock_mode:=true
```

### Monitor Topics
```bash
# In another terminal (access container again)
docker exec -it CONTAINER_NAME bash
ros2 topic list
ros2 topic echo /current_state
```

## Step 8: Save Container Changes

If you want to save changes made in the container:

```bash
# From host machine
docker commit CONTAINER_NAME your_username/oakd_vision:latest

# Tag it
docker tag your_username/oakd_vision:latest your_username/oakd_vision:v1.0

# Push to Docker Hub (optional)
docker push your_username/oakd_vision:latest
```

## Troubleshooting

### Issue: Display Not Working
```bash
# Check X11 forwarding
echo $DISPLAY
xhost +local:docker

# Restart container with proper X11 setup
```

### Issue: OAK-D Not Detected
```bash
# Check USB devices
lsusb

# Ensure container has device access
docker run ... --device=/dev/bus/usb ...
```

### Issue: Permission Denied
```bash
# Add user to docker group (on host)
sudo usermod -a -G docker $USER
# Log out and back in
```

### Issue: Network Issues
```bash
# Use host network mode
docker run ... --network host ...
```

## Integration with UCSD Robocar Packages

The container should already have:
- `ucsd_robocar_sensor2_pkg`
- `ucsd_robocar_actuator2_pkg`

Your project packages will be built alongside these. Ensure they're in the same workspace:

```
~/ros2_ws/src/
├── ucsd_robocar_hub2/          # UCSD packages
├── oakd_vision_pkg/            # Your packages
├── decision_pkg/
├── game_pkg/
└── control_pkg/
```

## Docker Compose (Optional)

For easier management, you can create a `docker-compose.yml`:

```yaml
version: '3.8'
services:
  robocar:
    image: djnighti/ucsd_robocar:x86  # or :devel for ARM
    container_name: oakd_vision_robocar
    privileged: true
    network_mode: host
    environment:
      - DISPLAY=${DISPLAY}
    volumes:
      - /tmp/.X11-unix:/tmp/.X11-unix
      - /dev:/dev
      - ~/ros2_ws:/home/ros/ros2_ws
    stdin_open: true
    tty: true
```

Then use:
```bash
docker-compose up -d
docker-compose exec robocar bash
```

## Notes

- **X86 Image**: Use for development and testing on your computer
- **ARM Image (devel)**: Use on Jetson for actual robot deployment
- **File Sharing**: Mount your workspace as a volume to persist changes
- **Display**: X11 forwarding required for RViz2 and image displays

## References

- UCSD Robocar Hub2: https://gitlab.com/ucsd_robocar2/ucsd_robocar_hub2
- Docker Documentation: https://docs.docker.com/

