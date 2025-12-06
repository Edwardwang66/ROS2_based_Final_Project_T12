"""
Full System Launch File
Launches all nodes for the OAK-D vision-based autonomous car system
References: ucsd_robocar_hub2 container structure
"""

from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    return LaunchDescription([
        # Launch arguments
        DeclareLaunchArgument(
            'use_mock_mode',
            default_value='false',
            description='Use mock mode (no OAK-D hardware)'
        ),
        DeclareLaunchArgument(
            'target_distance',
            default_value='1.0',
            description='Target distance to person in meters'
        ),
        DeclareLaunchArgument(
            'max_linear_speed',
            default_value='0.5',
            description='Maximum linear speed in m/s'
        ),
        DeclareLaunchArgument(
            'max_angular_speed',
            default_value='1.0',
            description='Maximum angular speed in rad/s'
        ),
        DeclareLaunchArgument(
            'total_rounds',
            default_value='3',
            description='Total rounds in RPS game'
        ),
        
        # Perception Node
        Node(
            package='oakd_vision_pkg',
            executable='perception_node',
            name='perception_node',
            parameters=[{
                'use_mock_mode': LaunchConfiguration('use_mock_mode'),
                'target_distance': LaunchConfiguration('target_distance'),
                'obstacle_threshold': 0.5,
            }],
            output='screen'
        ),
        
        # Decision Node
        Node(
            package='decision_pkg',
            executable='decision_node',
            name='decision_node',
            parameters=[{
                'target_distance': LaunchConfiguration('target_distance'),
                'max_linear_speed': LaunchConfiguration('max_linear_speed'),
                'max_angular_speed': LaunchConfiguration('max_angular_speed'),
                'search_angular_speed': 0.5,
                'k_linear': 0.5,
                'k_angular': 1.0,
            }],
            output='screen'
        ),
        
        # Game Node
        Node(
            package='game_pkg',
            executable='game_node',
            name='game_node',
            parameters=[{
                'total_rounds': LaunchConfiguration('total_rounds'),
            }],
            output='screen'
        ),
        
        # Control Node (optional - actuator package may subscribe directly to /cmd_vel)
        Node(
            package='control_pkg',
            executable='control_node',
            name='control_node',
            parameters=[{
                'max_linear_speed': LaunchConfiguration('max_linear_speed'),
                'max_angular_speed': LaunchConfiguration('max_angular_speed'),
                'enable_safety_limits': True,
            }],
            output='screen'
        ),
        
        # Note: The actuator package (ucsd_robocar_actuator2_pkg) should be launched separately
        # or included here if available. It typically subscribes to /cmd_vel directly.
    ])

