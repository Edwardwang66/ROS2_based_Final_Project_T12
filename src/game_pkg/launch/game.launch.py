from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument(
            'total_rounds',
            default_value='3',
            description='Total rounds in RPS game'
        ),
        
        Node(
            package='game_pkg',
            executable='game_node',
            name='game_node',
            parameters=[{
                'total_rounds': LaunchConfiguration('total_rounds'),
            }],
            output='screen'
        ),
    ])

