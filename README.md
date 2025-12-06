# ROS2-based OAK-D Vision Autonomous Car Project

This project implements an autonomous car system using OAK-D camera and Raspberry Pi, built on ROS2 and integrated with UCSD Robocar Hub2 container.

## 🎯 Project Overview

The system enables a car to:
1. **Search** for people using OAK-D camera
2. **Approach** detected persons autonomously
3. **Avoid obstacles** using depth perception
4. **Interact** by playing Rock-Paper-Scissors (RPS) game
5. **Back off** after interaction and resume searching

## 📋 System Architecture

The system is organized into 4 main modules:

### 1. Perception Module (`oakd_vision_pkg`)
- **Human Detection**: Detects people in camera frames
- **Depth Estimation**: Calculates distance to detected persons
- **Obstacle Detection**: Identifies obstacles ahead using depth map
- **Gesture Recognition**: Recognizes hand gestures (rock, paper, scissors)

**Topics Published:**
- `/person_detection` (oakd_msgs/PersonDetection)
- `/obstacle_ahead` (std_msgs/Bool)
- `/hand_gesture` (std_msgs/String)
- `/oakd/rgb/image_raw` (sensor_msgs/Image)
- `/oakd/depth/image_raw` (sensor_msgs/Image)

### 2. Decision Module (`decision_pkg`)
- **State Machine**: Manages system states (SEARCH, APPROACH, INTERACT, AVOID_OBSTACLE, BACK_OFF)
- **Control Logic**: Computes high-level motion commands

**Topics:**
- Subscribes: `/person_detection`, `/obstacle_ahead`, `/game_done`
- Publishes: `/cmd_vel` (geometry_msgs/Twist), `/current_state` (std_msgs/String)

### 3. Game Module (`game_pkg`)
- **RPS Logic**: Handles Rock-Paper-Scissors game sessions
- **Score Tracking**: Manages game rounds and results

**Topics:**
- Subscribes: `/current_state`, `/hand_gesture`
- Publishes: `/game_result` (oakd_msgs/GameResult), `/game_done` (std_msgs/Bool)

### 4. Control Module (`control_pkg`)
- **Actuator Interface**: Interfaces with `ucsd_robocar_actuator2_pkg`
- **Safety Limits**: Applies velocity limits and safety checks

**Topics:**
- Subscribes: `/cmd_vel`
- Publishes: `/cmd_vel_out` (for monitoring)

## 🔧 Dependencies

### ROS2 Packages
- ROS2 Humble/Iron (recommended)
- `rclpy`
- `std_msgs`
- `geometry_msgs`
- `sensor_msgs`
- `vision_msgs`
- `cv_bridge`

### Python Packages
- `depthai` - OAK-D SDK (enables TPU acceleration)
- `depthai-blobconverter` - Convert models to OAK-D format
- `opencv-python` - Computer vision
- `numpy` - Numerical operations

### Models (TPU-accelerated)
- **Person Detection**: MobileNet-SSD (download via script)
- **RPS Gesture**: Hand gesture model (see [MODELS.md](MODELS.md))

### UCSD Robocar Hub2 Integration
- **Sensor Package**: `ucsd_robocar_sensor2_pkg`
  - Reference: https://gitlab.com/ucsd_robocar2/ucsd_robocar_hub2#ucsd-robocar-sensor2-pkg
- **Actuator Package**: `ucsd_robocar_actuator2_pkg`
  - Reference: https://gitlab.com/ucsd_robocar2/ucsd_robocar_hub2#ucsd-robocar-actuator2-pkg

## 📦 Installation

**This project uses Docker with UCSD Robocar Hub2 container as the primary setup method.**

### Option A: Docker Setup (Recommended) 🐳

This is the **recommended method** for UCSD Robocar Hub2 integration. All ROS2 dependencies are pre-configured in the Docker container.

**Quick Start:**
```bash
# 1. Pull Docker image (choose based on your architecture)
docker pull djnighti/ucsd_robocar:x86      # For X86 (laptops/desktops)
# OR
docker pull djnighti/ucsd_robocar:devel   # For ARM (Jetson)

# 2. Start container using provided script
./scripts/start_docker.sh

# 3. Enter container
./scripts/enter_docker.sh

# 4. Inside container: Download models and build
cd ~/ros2_ws
./scripts/download_models.sh  # Download TPU models
colcon build --packages-select oakd_msgs
source install/setup.bash
colcon build --symlink-install
source install/setup.bash

# 5. Launch system
ros2 launch full_system.launch.py
```

**For detailed Docker setup, see [DOCKER_SETUP.md](DOCKER_SETUP.md)**

**Key Benefits:**
- ✅ Pre-configured ROS2 environment
- ✅ All dependencies included
- ✅ Consistent across different machines
- ✅ Easy to share and reproduce
- ✅ Integrated with UCSD Robocar Hub2 packages

### Option B: Native ROS2 Installation (Advanced)

If you prefer not to use Docker, you can install ROS2 natively. See [SETUP.md](SETUP.md) for detailed instructions.

**Quick Steps:**
```bash
# 1. Install ROS2 Humble
# Follow: https://docs.ros.org/en/humble/Installation.html

# 2. Install Python dependencies
pip3 install depthai depthai-blobconverter opencv-python numpy

# 3. Setup workspace
cd ~/ros2_ws/src
git clone <your-repo-url> oakd_vision_project
cd ..

# 4. Download models
./scripts/download_models.sh

# 5. Build workspace
colcon build --packages-select oakd_msgs
source install/setup.bash
colcon build --symlink-install
source install/setup.bash
```

## 🚀 Usage

**Note**: All commands below should be run **inside the Docker container** (if using Docker method).

### Phase 1: Desktop Demo (No Car)

Test perception and game logic without hardware:

```bash
# Inside Docker container
ros2 launch oakd_vision_pkg perception.launch.py use_mock_mode:=true

# In another terminal (also inside container), check topics
docker exec -it <container_name> bash
ros2 topic echo /person_detection
ros2 topic echo /obstacle_ahead
ros2 topic echo /hand_gesture
```

### Phase 2: Full System (With Car)

Launch the complete system:

```bash
# Inside Docker container
ros2 launch full_system.launch.py

# Or with custom parameters
ros2 launch full_system.launch.py \
    target_distance:=1.5 \
    max_linear_speed:=0.3 \
    total_rounds:=5 \
    use_mock_mode:=false
```

### Individual Node Launch

```bash
# Perception only
ros2 launch oakd_vision_pkg perception.launch.py

# Decision only
ros2 launch decision_pkg decision.launch.py

# Game only
ros2 launch game_pkg game.launch.py
```

## 🔍 Monitoring

### View Topics

```bash
# List all topics
ros2 topic list

# Monitor specific topics
ros2 topic echo /current_state
ros2 topic echo /cmd_vel
ros2 topic echo /game_result
```

### Visualization (if RViz2 available)

```bash
ros2 run rviz2 rviz2
# Add displays for:
# - /oakd/rgb/image_raw (Image)
# - /oakd/depth/image_raw (DepthCloud)
# - /person_detection (BoundingBox2D)
```

## ⚙️ Configuration

### Perception Parameters

Edit `src/oakd_vision_pkg/config/perception_params.yaml`:

```yaml
perception_node:
  ros__parameters:
    target_distance: 1.0  # meters
    obstacle_threshold: 0.5  # meters
    person_confidence_threshold: 0.5
```

### Decision Parameters

Edit `src/decision_pkg/config/decision_params.yaml`:

```yaml
decision_node:
  ros__parameters:
    target_distance: 1.0
    max_linear_speed: 0.5  # m/s
    max_angular_speed: 1.0  # rad/s
    k_linear: 0.5  # Distance control gain
    k_angular: 1.0  # Angle control gain
```

## 🛠️ Development Phases

### Phase 1: OAK-D Desktop Demo ✅
- [x] Human detection
- [x] Depth estimation
- [x] Gesture recognition (RPS)
- [ ] Integrate actual detection models

### Phase 2: Car Integration
- [x] State machine implementation
- [x] Control interface
- [ ] Hardware integration with actuator package
- [ ] Testing on actual car

### Phase 3: Obstacle Avoidance
- [x] Depth-based obstacle detection
- [x] Avoid obstacle state
- [ ] Enhanced avoidance strategies
- [ ] LiDAR integration (future)

### Phase 4: Full Integration
- [x] Game interaction node
- [x] Complete state machine
- [ ] End-to-end testing
- [ ] Performance optimization

## 📝 TODO / Integration Points

### Models Running on OAK-D TPU

**All CV computations run on OAK-D Lite's TPU for acceleration!**

### Person Detection ✅
- **Status**: Implemented using MobileNet-SSD on TPU
- **Model**: `mobilenet-ssd_openvino_2021.4_6shave.blob`
- **Location**: Runs directly on OAK-D's TPU via NeuralNetwork node
- **Download**: Run `./scripts/download_models.sh`

### Gesture Recognition (RPS) 🔄
- **Status**: Framework ready, needs RPS model
- **To complete**:
  1. Download or train an RPS hand gesture model
  2. Convert to ONNX format
  3. Compile to `.blob` using `depthai_blobconverter`
  4. Place in `models/` directory
- **See**: [MODELS.md](MODELS.md) for detailed instructions

### Actuator Package Integration
The control node interfaces with `ucsd_robocar_actuator2_pkg`.
**Ensure:**
1. Actuator package is built and available
2. Actuator node subscribes to `/cmd_vel`
3. Hardware connections are properly configured

## 🐛 Troubleshooting

### OAK-D Not Detected (Inside Docker)
```bash
# Inside container, check USB connection
lsusb | grep Luxonis

# Test depthai
python3 -c "import depthai; print('OK')"

# If not detected, ensure container has device access:
# - Use --privileged flag
# - Mount /dev:/dev volume
# - Check USB permissions on host

# Run in mock mode for testing
ros2 launch full_system.launch.py use_mock_mode:=true
```

### Build Errors
```bash
# Clean and rebuild
rm -rf build install log
colcon build

# Build specific package
colcon build --packages-select oakd_msgs
```

### Topic Not Found
```bash
# Check if nodes are running
ros2 node list

# Check topic info
ros2 topic info /person_detection
ros2 topic hz /person_detection
```

## 🐳 Docker Support (Primary Method)

**This project is designed to run inside the UCSD Robocar Hub2 Docker container.**

### Docker Images
- **ARM (Jetson)**: `docker pull djnighti/ucsd_robocar:devel`
- **X86 (Laptops/Desktops)**: `docker pull djnighti/ucsd_robocar:x86`

### Quick Commands
```bash
# Start container
./scripts/start_docker.sh

# Enter container
./scripts/enter_docker.sh

# Stop container
./scripts/stop_docker.sh

# Or use Docker Compose
docker-compose up -d
docker-compose exec robocar bash
```

### Documentation
- **Detailed Docker Guide**: See [DOCKER_SETUP.md](DOCKER_SETUP.md)
- **Setup Instructions**: See [SETUP.md](SETUP.md)
- **Model Setup**: See [MODELS.md](MODELS.md)

## 📚 References

- **UCSD Robocar Hub2**: https://gitlab.com/ucsd_robocar2/ucsd_robocar_hub2
- **UCSD Docker Images**: 
  - ARM (Jetson): `docker pull djnighti/ucsd_robocar:devel`
  - X86: `docker pull djnighti/ucsd_robocar:x86`
- **OAK-D Documentation**: https://docs.luxonis.com/
- **ROS2 Documentation**: https://docs.ros.org/en/humble/
- **DepthAI Python API**: https://docs.luxonis.com/projects/api/en/latest/

## 📄 License

MIT License - See LICENSE file for details

## 👤 Author

Edward Wang

## 🙏 Acknowledgments

- UCSD Robocar Hub2 team for the ROS2 container framework
- Luxonis for OAK-D camera hardware and SDK
