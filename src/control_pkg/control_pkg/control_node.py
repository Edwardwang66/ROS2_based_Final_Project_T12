#!/usr/bin/env python3
"""
Control Node - Interface to UCSD Robocar Actuator Package
This node subscribes to /cmd_vel and forwards commands to the actuator package.
The actual hardware control is handled by ucsd_robocar_actuator2_pkg.

References:
- ucsd_robocar_actuator2_pkg: https://gitlab.com/ucsd_robocar2/ucsd_robocar_hub2#ucsd-robocar-actuator2-pkg
"""

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist


class ControlNode(Node):
    """
    Control node that interfaces with ucsd_robocar_actuator2_pkg
    This is a pass-through node that can add safety checks, logging, or
    coordinate transformations if needed.
    
    In most cases, the actuator package will directly subscribe to /cmd_vel,
    so this node may be optional. It's included for:
    - Safety limits
    - Coordinate frame transformations
    - Logging and monitoring
    - Future enhancements
    """

    def __init__(self):
        super().__init__('control_node')
        
        # Subscribe to high-level commands
        self.cmd_vel_sub = self.create_subscription(
            Twist, '/cmd_vel', self.cmd_vel_callback, 10
        )
        
        # Publish to actuator (if needed, otherwise actuator subscribes directly)
        # The actuator package typically subscribes to /cmd_vel directly,
        # so this might just be for monitoring/logging
        self.cmd_vel_out_pub = self.create_publisher(
            Twist, '/cmd_vel_out', 10
        )
        
        # Parameters for safety limits
        self.declare_parameter('max_linear_speed', 0.5)  # m/s
        self.declare_parameter('max_angular_speed', 1.0)  # rad/s
        self.declare_parameter('enable_safety_limits', True)
        
        self.get_logger().info('Control node initialized')
        self.get_logger().info(
            'Note: This node interfaces with ucsd_robocar_actuator2_pkg. '
            'Ensure the actuator package is running and subscribed to /cmd_vel'
        )

    def cmd_vel_callback(self, msg):
        """Callback for velocity commands"""
        # Apply safety limits if enabled
        if self.get_parameter('enable_safety_limits').value:
            msg = self.apply_safety_limits(msg)
        
        # Log command (optional, can be disabled for performance)
        # self.get_logger().debug(
        #     f'Cmd: linear={msg.linear.x:.2f}, angular={msg.angular.z:.2f}'
        # )
        
        # Forward to actuator (if needed)
        # In most setups, the actuator package subscribes directly to /cmd_vel
        # This publication is optional and can be used for monitoring
        self.cmd_vel_out_pub.publish(msg)

    def apply_safety_limits(self, msg):
        """Apply safety limits to velocity commands"""
        max_linear = self.get_parameter('max_linear_speed').value
        max_angular = self.get_parameter('max_angular_speed').value
        
        # Clamp linear velocity
        if msg.linear.x > max_linear:
            msg.linear.x = max_linear
        elif msg.linear.x < -max_linear:
            msg.linear.x = -max_linear
        
        # Clamp angular velocity
        if msg.angular.z > max_angular:
            msg.angular.z = max_angular
        elif msg.angular.z < -max_angular:
            msg.angular.z = -max_angular
        
        return msg


def main(args=None):
    rclpy.init(args=args)
    node = ControlNode()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()

