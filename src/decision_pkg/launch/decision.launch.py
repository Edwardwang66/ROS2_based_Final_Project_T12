from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    return LaunchDescription([
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
        
        Node(
            package='decision_pkg',
            executable='decision_node',
            name='decision_node',
            parameters=[{
                'target_distance': LaunchConfiguration('target_distance'),
                'max_linear_speed': LaunchConfiguration('max_linear_speed'),
                'max_angular_speed': LaunchConfiguration('max_angular_speed'),
            }],
            output='screen'
        ),
    ])

