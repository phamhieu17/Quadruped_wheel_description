cmake_minimum_required(VERSION 3.8)
project(mq1w_description)
# The mq1w robot description, laid out as ur_description: urdf/ (xacro + its output), config/ (the numbers),
# meshes/{visual,collision}/, mjcf/ (MuJoCo), launch/, rviz/. Data only, no code.
find_package(ament_cmake REQUIRED)
install(DIRECTORY config launch meshes mjcf rviz urdf DESTINATION share/${PROJECT_NAME})
if(BUILD_TESTING)
  find_package(ament_cmake_pytest REQUIRED)
  ament_add_pytest_test(test_mq1w_urdf_xacro test/test_mq1w_urdf_xacro.py)
  # starts ROS nodes (no window): in domain 77, as every test that does (AGENTS.md)
  ament_add_pytest_test(test_view_mq1w_launch test/test_view_mq1w_launch.py ENV ROS_DOMAIN_ID=77 TIMEOUT 120)
endif()
ament_package()
