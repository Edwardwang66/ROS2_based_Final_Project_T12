# Setup Guide - ROS2 OAK-D Vision Project

This guide provides step-by-step instructions for setting up the project using Docker (recommended) or native ROS2 installation.

## Prerequisites

### Hardware
- OAK-D camera (Luxonis)
- Raspberry Pi 4 / Jetson (or development machine)
- ROS2-compatible robot chassis
- USB 3.0 cable for OAK-D

### Software (Docker Method - Recommended)
- Docker installed on your system
- X11 forwarding set up (for GUI applications)
- Access to UCSD Robocar Hub2 Docker container

### Software (Native Method - Optional)
- Ubuntu 22.04 (for ROS2 Humble) or Ubuntu 20.04 (for ROS2 Foxy)
- ROS2 Humble/Iron installed
- Python 3.8+

## Method A: Docker Setup (Recommended)

This is the recommended method for UCSD Robocar Hub2 integration.

### Step 1: Install Docker

**On Linux:**
```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
# Log out and back in for group changes to take effect
```

**On Windows/Mac:**
- Download Docker Desktop from https://www.docker.com/products/docker-desktop

### Step 2: Pull UCSD Robocar Docker Image

**For ARM Architecture (Jeston/Pi 5):**
```bash
docker pull djnighti/ucsd_robocar:devel
```

**For X86 Architecture (Most laptops/desktops):**
```bash
docker pull djnighti/ucsd_robocar:x86
```

### Step 3: Enable X11 Forwarding (for GUI)

**On Host Machine:**
```bash
# Enable X11 forwarding
xhost +local:docker

# SSH with X11 forwarding (if connecting to Jetson)
ssh -X jetson@ip_address
```

**Verify X11:**
```bash
# Inside container, test with:
xeyes
```

**Note**: Remember to disable when done: `xhost -local:docker`

### Step 4: Add Project to Workspace

You have several options to get your project into the container workspace:

**Option A: Mount Local Project Directory (Recommended for Development)**

This allows you to edit files on your host machine and see changes in the container.

```bash
# On host machine, navigate to your project root
cd /path/to/ROS2_based_Final_Project_T12

# The start_docker.sh script automatically mounts the project
# Or manually specify the mount:
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

# Inside container, create symlink or copy to workspace
cd ~/ros2_ws/src
ln -s /home/ros/oakd_vision_project/src/* ./
# OR
cp -r /home/ros/oakd_vision_project/src/* ./
```

**Option B: Git Clone Inside Container (Recommended for Clean Setup)**

```bash
# Start container first
./scripts/start_docker.sh
./scripts/enter_docker.sh

# Inside container
cd ~/ros2_ws/src
git clone <your-repo-url> oakd_vision_project
# Or clone directly into workspace
git clone <your-repo-url> .
```

**Option C: Copy Project Files into Workspace**

```bash
# On host machine
mkdir -p ~/ros2_ws/src
cp -r /path/to/ROS2_based_Final_Project_T12/src/* ~/ros2_ws/src/

# Then start container (workspace is already mounted)
./scripts/start_docker.sh
```

### Step 5: Start Docker Container

**Option 1: Using Provided Scripts (Easiest)**
```bash
# Make scripts executable (if on Linux/Mac)
chmod +x scripts/*.sh

# Start container (workspace should already have your project)
./scripts/start_docker.sh

# Enter container
./scripts/enter_docker.sh
```

**Option 2: Using Docker Compose**
```bash
# Edit docker-compose.yml to mount your project if needed
docker-compose up -d
docker-compose exec robocar bash
```

**Option 3: Manual Docker Command**
```bash
# For X86 - Mount your project directory
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

# For ARM (Jetson/Pi 5)
docker run -it --rm \
  --privileged \
  --network host \
  -e DISPLAY=$DISPLAY \
  -v /tmp/.X11-unix:/tmp/.X11-unix \
  -v /dev:/dev \
  -v ~/ros2_ws:/home/ros/ros2_ws \
  -v $(pwd):/home/ros/oakd_vision_project \
  djnighti/ucsd_robocar:devel \
  bash
```

### Step 6: Setup Project Inside Container

Once inside the container, you need to add your project packages to the workspace:

**Quick Setup (Recommended):**
```bash
# Use the provided setup script
cd /home/ros/oakd_vision_project
chmod +x scripts/setup_workspace.sh
./scripts/setup_workspace.sh
```

**Manual Setup:**
```bash
# Navigate to workspace
cd ~/ros2_ws/src

# Create symlinks from mounted project (allows editing on host)
ln -s /home/ros/oakd_vision_project/src/* ./

# Verify packages are linked
ls -la
# Should see: oakd_msgs, oakd_vision_pkg, decision_pkg, game_pkg, control_pkg
```

**Alternative: If you cloned inside container:**
```bash
# If you git cloned into ~/ros2_ws/src, packages are already there
cd ~/ros2_ws/src
ls  # Verify packages exist
```

Then continue with:

Once inside the container:

```bash
# Navigate to workspace
cd ~/ros2_ws

# If you mounted project separately, link it to workspace
# (Skip if you already cloned/copied into ~/ros2_ws/src)
if [ ! -d "src/oakd_vision_project" ]; then
    cd src
    # Option 1: Create symlink from mounted directory
    ln -s /home/ros/oakd_vision_project/src/* ./
    # Option 2: Or copy files
    # cp -r /home/ros/oakd_vision_project/src/* ./
    cd ..
fi

# Install Python dependencies (if not already in image)
pip3 install depthai depthai-blobconverter opencv-python numpy

# Download models (if not already done)
# Navigate to project root (adjust path based on your setup)
if [ -d "/home/ros/oakd_vision_project" ]; then
    cd /home/ros/oakd_vision_project
    ./scripts/download_models.sh
    cd ~/ros2_ws
elif [ -d "src/oakd_vision_project" ]; then
    cd src/oakd_vision_project
    ./scripts/download_models.sh
    cd ~/ros2_ws
fi

# Build workspace
colcon build --packages-select oakd_msgs
source install/setup.bash
colcon build --symlink-install
source install/setup.bash
```

### Step 7: Test OAK-D Connection (Inside Container)

```bash
# Check if OAK-D is detected
lsusb | grep Luxonis

# Test depthai
python3 -c "import depthai as dai; print('OK')"
```

### Step 8: Launch System (Inside Container)

```bash
# Launch full system
ros2 launch full_system.launch.py

# Or in mock mode (for testing)
ros2 launch full_system.launch.py use_mock_mode:=true
```

For detailed Docker setup, see [DOCKER_SETUP.md](DOCKER_SETUP.md).

---

## Method B: Native ROS2 Installation (Optional)

If you prefer not to use Docker, you can install ROS2 natively.

### Step 1: Install ROS2

### Ubuntu 22.04 (ROS2 Humble)
```bash
sudo apt update
sudo apt install software-properties-common
sudo add-apt-repository universe
sudo apt update && sudo apt install curl -y
sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.asc | sudo apt-key add -
sudo sh -c 'echo "deb [arch=$(dpkg --print-architecture)] http://packages.ros.org/ros2/ubuntu $(lsb_release -cs) main" > /etc/apt/sources.list.d/ros2-latest.list'
sudo apt update
sudo apt install ros-humble-desktop
sudo apt install python3-colcon-common-extensions
```

### Source ROS2
```bash
source /opt/ros/humble/setup.bash
echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc
```

### Step 2: Install Python Dependencies

```bash
pip3 install depthai depthai-blobconverter opencv-python numpy
sudo apt install python3-opencv python3-numpy
```

### Step 3: Install CV Bridge

```bash
sudo apt install ros-humble-cv-bridge
```

### Step 4: Setup Workspace

```bash
# Create workspace
mkdir -p ~/ros2_ws/src
cd ~/ros2_ws/src

# Clone this project
git clone <your-repo-url> oakd_vision_project

# Clone UCSD Robocar Hub2 (if needed)
git clone https://gitlab.com/ucsd_robocar2/ucsd_robocar_hub2.git

cd ..
```

### Step 5: Download Models

```bash
# Download required models for TPU acceleration
cd ~/ros2_ws/src/oakd_vision_project
./scripts/download_models.sh
```

### Step 6: Build Workspace

```bash
# Build custom messages first
colcon build --packages-select oakd_msgs
source install/setup.bash

# Build all packages
colcon build --symlink-install

# Source workspace
source install/setup.bash
echo "source ~/ros2_ws/install/setup.bash" >> ~/.bashrc
```

### Step 7: Test OAK-D Connection

```bash
# Test depthai installation
python3 -c "import depthai; dai.Device(dai.OpenVINO.VERSION_2021_4); print('OAK-D detected!')"

# Or run a simple test
python3 << EOF
import depthai as dai
pipeline = dai.Pipeline()
device = dai.Device(pipeline)
print(f"Device name: {device.getDeviceName()}")
print("OAK-D connected successfully!")
EOF
```

### Step 8: Test in Mock Mode

```bash
# Launch perception node in mock mode
ros2 launch oakd_vision_pkg perception.launch.py use_mock_mode:=true

# In another terminal, check topics
ros2 topic list
ros2 topic echo /person_detection
```

### Step 9: Integrate with UCSD Robocar Actuator

### Option A: Actuator Package Already Running
If `ucsd_robocar_actuator2_pkg` is already running and subscribed to `/cmd_vel`, you can skip the control node or use it for monitoring.

### Option B: Launch Actuator Package
```bash
# Follow UCSD Robocar Hub2 instructions to launch actuator package
# Ensure it subscribes to /cmd_vel topic
```

### Step 10: Launch Full System

```bash
# With OAK-D hardware
ros2 launch full_system.launch.py

# In mock mode (for testing)
ros2 launch full_system.launch.py use_mock_mode:=true
```

### Step 11: Verify System

### Check Nodes
```bash
ros2 node list
# Should see:
# - perception_node
# - decision_node
# - game_node
# - control_node
```

### Check Topics
```bash
ros2 topic list
# Key topics:
# - /person_detection
# - /obstacle_ahead
# - /cmd_vel
# - /current_state
# - /game_result
```

### Monitor State Machine
```bash
ros2 topic echo /current_state
# Should cycle through: SEARCH -> APPROACH -> INTERACT -> BACK_OFF
```

## Troubleshooting

### Docker-Specific Issues

#### Issue: Display Not Working in Container
```bash
# Check X11 forwarding
echo $DISPLAY
xhost +local:docker

# Restart container with proper X11 setup
docker stop <container_name>
./scripts/start_docker.sh
```

#### Issue: OAK-D Not Detected in Container
```bash
# Inside container, check USB devices
lsusb | grep Luxonis

# Ensure container has device access
# Use --privileged flag and -v /dev:/dev when starting container
```

#### Issue: Permission Denied in Container
```bash
# On host, add user to docker group
sudo usermod -a -G docker $USER
# Log out and back in
```

#### Issue: Container Can't Access Workspace
```bash
# Check volume mounts
docker inspect <container_name> | grep Mounts

# Ensure workspace is mounted correctly
# Use absolute paths in docker run command
```

### General Issues

#### Issue: OAK-D Not Found
```bash
# Check USB permissions (on host)
sudo usermod -a -G dialout $USER
# Log out and back in

# Check USB connection
lsusb | grep Luxonis

# Test with depthai examples
python3 -m depthai
```

#### Issue: Build Errors
```bash
# Clean build
rm -rf build install log

# Rebuild
colcon build --symlink-install

# Check for missing dependencies
rosdep install --from-paths src --ignore-src -r -y
```

#### Issue: Import Errors
```bash
# Ensure workspace is sourced
source install/setup.bash

# Check Python path
echo $PYTHONPATH

# Reinstall Python packages (inside container)
pip3 install --upgrade depthai depthai-blobconverter opencv-python numpy
```

#### Issue: Models Not Found
```bash
# Download models
./scripts/download_models.sh

# Check model paths in config files
# Update paths if models are in different location
```

## Next Steps

1. **Download Models**: Run `./scripts/download_models.sh` to get TPU-accelerated models
2. **Get RPS Model**: See [MODELS.md](MODELS.md) for RPS gesture model setup
3. **Tune Parameters**: Adjust control gains and thresholds in config files
4. **Test on Hardware**: Deploy to Jetson/Raspberry Pi and test with actual car

## Additional Resources

- **Docker Setup**: See [DOCKER_SETUP.md](DOCKER_SETUP.md) for detailed Docker instructions
- **Model Setup**: See [MODELS.md](MODELS.md) for model download and configuration
- **Architecture**: See [ARCHITECTURE.md](ARCHITECTURE.md) for system architecture details

