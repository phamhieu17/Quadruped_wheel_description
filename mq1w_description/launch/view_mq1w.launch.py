"""The mq1w model in RViz, joints moved by sliders:  ros2 launch mq1w_description view_mq1w.launch.py [gui:=false] [rviz:=false]
As ur_description's view_ur.launch.py, it only includes view_mq1w.launch.xml, which holds the arguments
(rviz_config_file, description_file, gui, rviz) and the nodes; arguments given here reach it."""
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import FrontendLaunchDescriptionSource
from launch.substitutions import PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    return LaunchDescription([
        IncludeLaunchDescription(FrontendLaunchDescriptionSource(
            PathJoinSubstitution([FindPackageShare('mq1w_description'), 'launch', 'view_mq1w.launch.xml']))),
    ])
