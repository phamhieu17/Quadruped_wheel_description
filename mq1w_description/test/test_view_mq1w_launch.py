"""view_<robot>.launch.py and .launch.xml of this package (as ur_description's test_view_ur_launch.py):
each starts, and robot_state_publisher with the joint states publishes a transform for every link of
the URDF. Run with gui:=false rviz:=false (no window: joint_state_publisher instead of the sliders),
in ROS domain 77 so that a simulation open in domain 0 sees nothing of it, and in its own namespace
with /tf, /tf_static remapped into it: colcon tests the robots' packages at once, and one robot's
frames (MQ1's <leg>_foot) must not reach the other's test."""
import os
os.environ['ROS_DOMAIN_ID'] = '77'   # before rclpy and the launched nodes read it

import time
import unittest
import xml.etree.ElementTree as ET

import launch_testing
import launch_testing.actions
import launch_testing.asserts
import pytest
import rclpy
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import GroupAction, IncludeLaunchDescription
from launch.launch_description_sources import AnyLaunchDescriptionSource
from launch_ros.actions import PushRosNamespace, SetRemap
from rclpy.qos import DurabilityPolicy, QoSProfile
from tf2_msgs.msg import TFMessage

PKG = os.path.basename(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ROBOT = PKG.removesuffix('_description')
SHARE = get_package_share_directory(PKG)
NS = f'/test_{ROBOT}'
LINKS = {l.get('name') for l in ET.parse(os.path.join(SHARE, 'urdf', f'{ROBOT}.urdf')).getroot().findall('link')}


@pytest.mark.launch_test
@launch_testing.parametrize('launch_file', [f'view_{ROBOT}.launch.py', f'view_{ROBOT}.launch.xml'])
def generate_test_description(launch_file):
    view = IncludeLaunchDescription(AnyLaunchDescriptionSource(os.path.join(SHARE, 'launch', launch_file)),
                                    launch_arguments={'gui': 'false', 'rviz': 'false'}.items())
    isolated = GroupAction([PushRosNamespace(NS), SetRemap('/tf', f'{NS}/tf'), SetRemap('/tf_static', f'{NS}/tf_static'),
                            view])
    return LaunchDescription([isolated, launch_testing.actions.ReadyToTest()])


class TestEveryLinkHasATransform(unittest.TestCase):
    def test_tf_covers_the_urdf(self, launch_file):
        rclpy.init()
        node = rclpy.create_node('test_view_launch')
        frames = set()
        add = lambda msg: frames.update(t.child_frame_id for t in msg.transforms)
        node.create_subscription(TFMessage, f'{NS}/tf', add, 100)
        node.create_subscription(TFMessage, f'{NS}/tf_static', add,
                                 QoSProfile(depth=100, durability=DurabilityPolicy.TRANSIENT_LOCAL))
        try:
            end = time.time() + 15.0
            while time.time() < end and frames != LINKS - {'base_link'}:
                rclpy.spin_once(node, timeout_sec=0.1)
        finally:
            node.destroy_node()
            rclpy.shutdown()
        self.assertEqual(frames, LINKS - {'base_link'}, f'{launch_file}: links without a transform')


@launch_testing.post_shutdown_test()
class TestShutdown(unittest.TestCase):
    def test_nodes_exit_cleanly(self, proc_info, launch_file):
        launch_testing.asserts.assertExitCodes(proc_info, allowable_exit_codes=[0, -2, -15])
