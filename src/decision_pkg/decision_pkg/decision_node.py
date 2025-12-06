#!/usr/bin/env python3
"""
Decision Node - State Machine for Autonomous Navigation
Manages states: SEARCH, APPROACH, INTERACT, AVOID_OBSTACLE, BACK_OFF
References: ucsd_robocar_hub2 for control patterns
"""

import rclpy
from rclpy.node import Node
from std_msgs.msg import String, Bool, Float32
from geometry_msgs.msg import Twist
from oakd_msgs.msg import PersonDetection


class DecisionNode(Node):
    """
    Decision node implementing state machine
    Subscribes:
        - /person_detection (oakd_msgs/PersonDetection)
        - /obstacle_ahead (std_msgs/Bool)
        - /game_done (std_msgs/Bool)
    Publishes:
        - /cmd_vel (geometry_msgs/Twist)
        - /current_state (std_msgs/String)
    """

    # State constants
    STATE_SEARCH = "SEARCH"
    STATE_APPROACH = "APPROACH"
    STATE_INTERACT = "INTERACT"
    STATE_AVOID_OBSTACLE = "AVOID_OBSTACLE"
    STATE_BACK_OFF = "BACK_OFF"
    STATE_IDLE = "IDLE"

    def __init__(self):
        super().__init__('decision_node')
        
        # State
        self.state = self.STATE_SEARCH
        
        # Publishers
        self.cmd_vel_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.state_pub = self.create_publisher(String, '/current_state', 10)
        
        # Subscribers
        self.person_detection_sub = self.create_subscription(
            PersonDetection, '/person_detection', self.person_detection_callback, 10
        )
        self.obstacle_ahead_sub = self.create_subscription(
            Bool, '/obstacle_ahead', self.obstacle_ahead_callback, 10
        )
        self.game_done_sub = self.create_subscription(
            Bool, '/game_done', self.game_done_callback, 10
        )
        
        # State variables
        self.person_found = False
        self.person_distance = 0.0
        self.person_bbox = None
        self.obstacle_ahead = False
        self.game_done = False
        
        # Parameters
        self.declare_parameter('target_distance', 1.0)  # meters
        self.declare_parameter('target_distance_tolerance', 0.2)  # meters
        self.declare_parameter('alignment_tolerance', 0.1)  # fraction of image width
        self.declare_parameter('max_linear_speed', 0.5)  # m/s
        self.declare_parameter('max_angular_speed', 1.0)  # rad/s
        self.declare_parameter('search_angular_speed', 0.5)  # rad/s
        self.declare_parameter('k_linear', 0.5)  # Proportional gain for distance
        self.declare_parameter('k_angular', 1.0)  # Proportional gain for angle
        self.declare_parameter('back_off_duration', 2.0)  # seconds
        self.declare_parameter('back_off_speed', -0.2)  # m/s (negative = backward)
        
        # Timer for state machine
        self.create_timer(0.1, self.state_machine_callback)  # 10 Hz
        
        # Back off timer
        self.back_off_start_time = None
        
        self.get_logger().info('Decision node initialized')
        self.get_logger().info(f'Initial state: {self.state}')

    def person_detection_callback(self, msg):
        """Callback for person detection updates"""
        self.person_found = msg.person_found.data
        self.person_distance = msg.distance.data
        self.person_bbox = msg.bbox

    def obstacle_ahead_callback(self, msg):
        """Callback for obstacle detection"""
        self.obstacle_ahead = msg.data

    def game_done_callback(self, msg):
        """Callback for game completion"""
        self.game_done = msg.data

    def state_machine_callback(self):
        """Main state machine loop"""
        cmd_vel = Twist()
        
        if self.state == self.STATE_SEARCH:
            cmd_vel = self.handle_search_state()
            
        elif self.state == self.STATE_APPROACH:
            cmd_vel = self.handle_approach_state()
            
        elif self.state == self.STATE_AVOID_OBSTACLE:
            cmd_vel = self.handle_avoid_obstacle_state()
            
        elif self.state == self.STATE_INTERACT:
            cmd_vel = self.handle_interact_state()
            
        elif self.state == self.STATE_BACK_OFF:
            cmd_vel = self.handle_back_off_state()
            
        elif self.state == self.STATE_IDLE:
            cmd_vel = Twist()  # Stop
        
        # Publish command
        self.cmd_vel_pub.publish(cmd_vel)
        
        # Publish current state
        state_msg = String(data=self.state)
        self.state_pub.publish(state_msg)

    def handle_search_state(self):
        """Handle SEARCH state - rotate to find person"""
        cmd_vel = Twist()
        
        if self.person_found:
            self.get_logger().info('Person found! Transitioning to APPROACH')
            self.state = self.STATE_APPROACH
        else:
            # Rotate slowly to search
            cmd_vel.angular.z = self.get_parameter('search_angular_speed').value
        
        return cmd_vel

    def handle_approach_state(self):
        """Handle APPROACH state - move towards person"""
        cmd_vel = Twist()
        
        # Check if person is still visible
        if not self.person_found:
            self.get_logger().warn('Person lost. Returning to SEARCH')
            self.state = self.STATE_SEARCH
            return cmd_vel
        
        # Check for obstacles
        if self.obstacle_ahead:
            self.get_logger().warn('Obstacle detected. Transitioning to AVOID_OBSTACLE')
            self.state = self.STATE_AVOID_OBSTACLE
            return cmd_vel
        
        # Check if we've reached target
        if self.is_at_target():
            self.get_logger().info('Reached target distance. Transitioning to INTERACT')
            self.state = self.STATE_INTERACT
            return cmd_vel
        
        # Compute control commands
        linear, angular = self.compute_follow_command()
        
        cmd_vel.linear.x = linear
        cmd_vel.angular.z = angular
        
        return cmd_vel

    def handle_avoid_obstacle_state(self):
        """Handle AVOID_OBSTACLE state - simple obstacle avoidance"""
        cmd_vel = Twist()
        
        # Simple strategy: stop, turn left for a bit, then return to search
        # In a more sophisticated version, you could check left/right depth
        # and turn toward the clearer side
        
        if not self.obstacle_ahead:
            # Obstacle cleared, return to search
            self.get_logger().info('Obstacle cleared. Returning to SEARCH')
            self.state = self.STATE_SEARCH
            return cmd_vel
        
        # Turn left
        cmd_vel.angular.z = self.get_parameter('search_angular_speed').value
        
        return cmd_vel

    def handle_interact_state(self):
        """Handle INTERACT state - stop and wait for game to complete"""
        cmd_vel = Twist()  # Stop
        
        if self.game_done:
            self.get_logger().info('Game completed. Transitioning to BACK_OFF')
            self.state = self.STATE_BACK_OFF
            self.back_off_start_time = self.get_clock().now()
            self.game_done = False  # Reset flag
        
        return cmd_vel

    def handle_back_off_state(self):
        """Handle BACK_OFF state - move backward after interaction"""
        cmd_vel = Twist()
        
        if self.back_off_start_time is None:
            self.back_off_start_time = self.get_clock().now()
        
        elapsed = (self.get_clock().now() - self.back_off_start_time).nanoseconds / 1e9
        duration = self.get_parameter('back_off_duration').value
        
        if elapsed < duration:
            # Move backward
            cmd_vel.linear.x = self.get_parameter('back_off_speed').value
        else:
            # Back off complete, return to search
            self.get_logger().info('Back off complete. Returning to SEARCH')
            self.state = self.STATE_SEARCH
            self.back_off_start_time = None
        
        return cmd_vel

    def compute_follow_command(self):
        """
        Compute linear and angular velocities to follow/approach person
        Returns: (linear, angular)
        """
        # Get parameters
        target_dist = self.get_parameter('target_distance').value
        k_linear = self.get_parameter('k_linear').value
        k_angular = self.get_parameter('k_angular').value
        max_linear = self.get_parameter('max_linear_speed').value
        max_angular = self.get_parameter('max_angular_speed').value
        
        # Distance control
        distance_error = self.person_distance - target_dist
        linear = k_linear * distance_error
        linear = max(0.0, min(linear, max_linear))  # Clamp and don't go backward
        
        # Angular control (based on bbox center)
        angular = 0.0
        if self.person_bbox is not None:
            # Assuming image width is normalized or we need to get actual width
            # For now, use bbox center x coordinate
            # In practice, you'd need to know the image width
            # This is a simplified version
            bbox_center_x = self.person_bbox.center.x
            
            # Normalize error (assuming image center is at 0.5)
            error_x = bbox_center_x - 0.5  # Normalized [-0.5, 0.5]
            
            angular = k_angular * error_x
            angular = max(-max_angular, min(angular, max_angular))
        
        return linear, angular

    def is_at_target(self):
        """Check if we're at target distance and aligned"""
        target_dist = self.get_parameter('target_distance').value
        tolerance = self.get_parameter('target_distance_tolerance').value
        alignment_tol = self.get_parameter('alignment_tolerance').value
        
        # Check distance
        distance_ok = abs(self.person_distance - target_dist) < tolerance
        
        # Check alignment
        alignment_ok = True
        if self.person_bbox is not None:
            bbox_center_x = self.person_bbox.center.x
            error_x = abs(bbox_center_x - 0.5)  # Distance from center
            alignment_ok = error_x < alignment_tol
        
        return distance_ok and alignment_ok


def main(args=None):
    rclpy.init(args=args)
    node = DecisionNode()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()

