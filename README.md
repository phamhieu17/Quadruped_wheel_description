# Quadruped_wheel_description

The robot description of the **MQ1W** quadruped: one ROS 2 package, `mq1w_description`
(`ament_cmake`, data only), as Unitree's [`unitree_ros/robots`](https://github.com/unitreerobotics/unitree_ros)
(`go2_description`, ...). Inside, it is laid out as Universal Robots'
[`ur_description`](https://github.com/UniversalRobots/Universal_Robots_ROS2_Description): the
xacro is a macro built from config files, and every number is in `config/`. The control stack
[`quadruped`](https://github.com/phamhieu17/Quadrupped) holds this repository as the submodule
`robots/mq1w`; its sibling MQ1 (point feet) is [`Quadruped_description`](https://github.com/phamhieu17/Quadruped_description)
(`robots/mq1`). The two robots share the GO-M8010-6 drives and the base, hip and thigh parts,
but differ in their legs and kinematics.

| package | | joints per leg | foot |
|---|---|---|---|
| `mq1w_description` | wheel-legged, 20.3 kg | hip, thigh, calf, wheel | wheel (cylinder) |

```
mq1w_description/
├── urdf/mq1w.urdf.xacro        the robot (as ur.urdf.xacro): arguments, loads config/, calls the macro
│        mq1w_macro.xacro       the robot macro (as ur_macro.xacro): base, sensor frames, four legs
│        mq1w_mocked.urdf.xacro the robot + ros2_control on mock hardware (as ur_mocked.urdf.xacro)
│        ros2_control_mock_hardware.xacro  that ros2_control system (mock_components/GenericSystem)
│        inc/mq1w_common.xacro  builders: a link or a joint by name, from the config files
│            mq1w_joint_control.xacro  the joints' ros2_control interfaces (as ur_joint_control.xacro)
│            mq1w_sensors.xacro  the IMU's                                  (as ur_sensors.xacro)
│        mq1w.urdf              the robot's output (the control stack's codegen reads it)
├── config/default_kinematics.yaml joint origins                         (as ur_description)
│          joint_limits.yaml       position range of each joint
│          physical_parameters.yaml  mass, centre of mass, inertia of each link
│          visual_parameters.yaml  materials, visual meshes, collision geometry of each link
│          initial_positions.yaml  the joint positions a ros2_control hardware starts at
│          actuators.yaml          GO-M8010-6 per joint kind: effort, velocity, armature; the ASSUMED friction
├── meshes/visual/*.stl            the parts (SolidWorks)
│          collision/<link>_<i>.stl  convex pieces of each link (scripts/make_collision_meshes.py)
├── mjcf/mq1w.xml, scene.xml    MuJoCo model, and the scene (floor + robot)
├── launch/view_mq1w.launch.py  RViz + joint sliders     (as view_ur.launch.py)
│          view_mq1w.launch.xml the same in XML         (as view_ur.launch.xml)
├── rviz/view_robot.rviz
├── test/test_mq1w_urdf_xacro.py  the xacro builds and is urdf/mq1w.urdf; one tree; meshes exist;
│                                   every config entry is used
│        test_view_mq1w_launch.py  both view launches start (gui:=false rviz:=false, domain 77, own
│                                   namespace) and /tf + /tf_static cover every link   (as UR's)
└── doc/                             the documentation (as ur_description's doc/), English + vi/ (Tiếng Việt):
                                     index, robot_frames (frames, axes, joint signs, poses), migration_notes
scripts/validate_model.py mq1w          URDF, MJCF and actuators.yaml consistent; keyframes touch only the wheels
        make_collision_meshes.py mq1w   collision pieces from the visual meshes (CoACD)
```

**Documentation** (English, with a Vietnamese translation in `doc/vi/`): `mq1w_description/doc/`,
in reStructuredText, readable on GitHub as is, or built as a site with Sphinx:

```
pip install -r doc_requirements.txt
sphinx-build -W mq1w_description/doc mq1w_description/doc/_build/html
```

## Building

In a ROS 2 Jazzy workspace (alone, or inside `quadruped`):

```
git clone https://github.com/phamhieu17/Quadruped_wheel_description.git src/Quadruped_wheel_description
rosdep install --from-paths src --ignore-src -y
colcon build && colcon test
ros2 launch mq1w_description view_mq1w.launch.py [gui:=false] [rviz:=false]   # or view_mq1w.launch.xml
python3 scripts/validate_model.py mq1w                                       # needs mujoco, numpy, pyyaml
```

## Changing the model

- **A number** (an origin, a limit, a mass): edit it in `config/`, then regenerate the URDF:
  `cd mq1w_description && xacro urdf/mq1w.urdf.xacro -o urdf/mq1w.urdf`. The MJCF carries
  the same numbers by hand: change it too; `validate_model.py` checks they agree. The xacro reads
  effort, velocity, damping and friction from `actuators.yaml` (one source per number).
  Another file for one robot (a calibration): `xacro ... kinematics_params:=/abs/path.yaml` (also
  `joint_limit_params`, `physical_params`, `visual_params`, `actuator_params`; the mocked robot also
  `initial_positions_file`).
- **A part's shape** (a visual mesh): replace it in `meshes/visual/`, then
  `python3 scripts/make_collision_meshes.py mq1w` (needs `pip install coacd trimesh`). It splits
  each link's visual meshes into convex pieces (MuJoCo collides a mesh as its convex hull) and
  rewrites the `collision` lists of `visual_parameters.yaml` and the collision geoms of the MJCF.
  The contact element keeps its primitive: the wheel's cylinder (smooth rolling; the codegen reads its radius). Then regenerate the URDF.
- **A collision pair that cannot happen** is excluded in the MJCF `<contact>`: a wheel and its own
  thigh, 2.5 mm apart at the knee's stop, but the cylinder's square edge reaches the thigh.

As in UR, the description says how the robot meets ros2_control (`mq1w_mocked.urdf.xacro`: the
robot with its joints and IMU on mock hardware) but runs no controller: running the robot is the
driver's job, here `mq1w_control` (`control_node`, over `legged_msgs/LowCmd` / `LowState`).

Everything numeric in the control stack is generated from these files at build time
(`control/tools/codegen` of `quadruped`, reading the installed `mq1w_description`). The joint
layout comes from them too: the keys of `config/actuators.yaml joints` give the leg's joint kinds.

Check after an edit, in `quadruped`: `make build && make verify-model && make test` (the
description packages' tests run in `make test`).
