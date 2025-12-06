from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    return LaunchDescription([
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
            'obstacle_threshold',
            default_value='0.5',
            description='Obstacle detection threshold in meters'
        ),
        
        Node(
            package='oakd_vision_pkg',
            executable='perception_node',
            name='perception_node',
            parameters=[{
                'use_mock_mode': LaunchConfiguration('use_mock_mode'),
                'target_distance': LaunchConfiguration('target_distance'),
                'obstacle_threshold': LaunchConfiguration('obstacle_threshold'),
            }],
            output='screen'
        ),
    ])

