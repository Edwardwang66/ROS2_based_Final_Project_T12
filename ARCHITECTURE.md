# System Architecture Documentation

## Overview

This document describes the system architecture for the ROS2-based OAK-D vision autonomous car project, integrated with UCSD Robocar Hub2.

## System Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    OAK-D Camera (Hardware)                   │
│              RGB Image + Depth Map Stream                   │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│              Perception Node (oakd_vision_pkg)               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Human        │  │ Obstacle     │  │ Gesture      │      │
│  │ Detection    │  │ Detection    │  │ Recognition  │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│         │                 │                    │              │
│         └─────────────────┴────────────────────┘            │
│                    Publish Topics                             │
└───────────────────────┬─────────────────────────────────────┘
                        │
        ┌───────────────┼───────────────┐
        │               │               │
        ▼               ▼               ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ /person_     │ │ /obstacle_   │ │ /hand_       │
│ detection    │ │ ahead        │ │ gesture      │
└──────────────┘ └──────────────┘ └──────────────┘
        │               │               │
        └───────────────┼───────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│            Decision Node (decision_pkg)                       │
│                    State Machine                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ SEARCH   │→ │ APPROACH │→ │ INTERACT │→ │ BACK_OFF  │   │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘   │
│       │             │              │             │          │
│       └─────────────┴──────────────┴─────────────┘          │
│                    AVOID_OBSTACLE                            │
│                                                               │
│              Computes: /cmd_vel                              │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│         Control Node (control_pkg)                            │
│         Safety Limits + Monitoring                           │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│   UCSD Robocar Actuator Package                              │
│   (ucsd_robocar_actuator2_pkg)                               │
│   Subscribes to /cmd_vel                                     │
│   Controls: Motors, Servos, etc.                             │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│              Game Node (game_pkg)                            │
│  Subscribes: /current_state, /hand_gesture                   │
│  Publishes: /game_result, /game_done                         │
│                                                               │
│  ┌─────────────────────────────────────────────┐            │
│  │  RPS Game Logic                              │            │
│  │  - Round Management                          │            │
│  │  - Score Tracking                           │            │
│  │  - Result Calculation                       │            │
│  └─────────────────────────────────────────────┘            │
└─────────────────────────────────────────────────────────────┘
```

## Node Communication

### Topic Flow

1. **Perception → Decision**
   - `/person_detection` → Decision uses for state transitions
   - `/obstacle_ahead` → Decision uses for obstacle avoidance

2. **Decision → Control → Actuator**
   - `/cmd_vel` → Control applies safety limits → Actuator executes

3. **Decision → Game**
   - `/current_state` → Game activates when state = "INTERACT"

4. **Perception → Game**
   - `/hand_gesture` → Game uses for RPS recognition

5. **Game → Decision**
   - `/game_done` → Decision transitions to BACK_OFF state

## State Machine Details

### State: SEARCH
- **Trigger**: Initial state or person lost
- **Action**: Rotate slowly (angular velocity only)
- **Transition**: Person detected → APPROACH

### State: APPROACH
- **Trigger**: Person detected
- **Action**: 
  - Compute linear velocity from distance error
  - Compute angular velocity from bbox center error
  - Publish `/cmd_vel`
- **Transitions**:
  - Person lost → SEARCH
  - Obstacle detected → AVOID_OBSTACLE
  - At target distance + aligned → INTERACT

### State: INTERACT
- **Trigger**: Reached target position
- **Action**: Stop (zero velocity), activate game
- **Transition**: Game done → BACK_OFF

### State: AVOID_OBSTACLE
- **Trigger**: Obstacle detected during APPROACH
- **Action**: Stop, turn left/right
- **Transition**: Obstacle cleared → SEARCH

### State: BACK_OFF
- **Trigger**: Game completed
- **Action**: Move backward for fixed duration
- **Transition**: Duration elapsed → SEARCH

## Message Definitions

### PersonDetection (oakd_msgs/PersonDetection)
```yaml
person_found: bool
bbox: vision_msgs/BoundingBox2D
distance: float32  # meters
confidence: float32  # 0.0-1.0
```

### GameResult (oakd_msgs/GameResult)
```yaml
player_gesture: string  # "rock", "paper", "scissors"
robot_gesture: string
result: string  # "win", "loss", "tie"
round_number: int32
total_rounds: int32
game_done: bool
```

## Integration with UCSD Robocar Hub2

### Sensor Package Integration
- **Reference**: `ucsd_robocar_sensor2_pkg`
- **Usage**: This project extends sensor functionality with OAK-D specific perception
- **Pattern**: Follow sensor package conventions for topic naming and message types

### Actuator Package Integration
- **Reference**: `ucsd_robocar_actuator2_pkg`
- **Interface**: `/cmd_vel` topic (geometry_msgs/Twist)
- **Pattern**: Actuator package subscribes directly to `/cmd_vel` or via control node

## Control Algorithm

### Distance Control (Proportional)
```
linear_velocity = k_linear * (distance - target_distance)
linear_velocity = clamp(linear_velocity, 0, max_linear_speed)
```

### Angle Control (Proportional)
```
error_x = bbox_center_x - image_center_x  # normalized
angular_velocity = k_angular * error_x
angular_velocity = clamp(angular_velocity, -max_angular, max_angular)
```

## Obstacle Detection Algorithm

1. Extract ROI from depth map (center region)
2. Filter invalid depth values (0, outliers)
3. Calculate 10th percentile depth
4. Compare with threshold (default: 0.5m)
5. Publish `/obstacle_ahead` boolean

## Future Enhancements

### LiDAR Integration
- Replace depth-based obstacle detection with LiDAR `/scan` topic
- Subscribe to `sensor_msgs/LaserScan` in decision node
- More accurate obstacle detection and mapping

### Path Planning
- Integrate with `ucsd_robocar_path_planning2_pkg`
- Add waypoint navigation
- Dynamic obstacle avoidance

### Localization
- Integrate with `ucsd_robocar_localization2_pkg`
- Add SLAM capabilities
- Map-based navigation

## Performance Considerations

- **Perception Rate**: 10 Hz (configurable via timer)
- **Decision Rate**: 10 Hz
- **Control Rate**: 10 Hz (matches decision)
- **Game Rate**: 10 Hz (event-driven)

## Safety Features

1. **Velocity Limits**: Enforced in control node
2. **Obstacle Avoidance**: Automatic state transition
3. **Timeout Handling**: Gesture recognition timeout
4. **Emergency Stop**: Can be added via service call

