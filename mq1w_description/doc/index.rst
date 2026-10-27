mq1w_description
================

The physical description of the MQ1W quadruped (wheel-legged) for ROS 2: its links and joints,
their masses and inertias, what they look like and what they collide with, its drives, and its
MuJoCo model. It holds data only; every other package of the control stack reads the robot from it.

.. toctree::
   :maxdepth: 2
   :caption: Contents

   robot_frames
   migration_notes
   vi/index

.. contents::
   :depth: 2
   :local:

The robot
---------

.. list-table::
   :widths: 30 70

   * - drives
     - 16 × Unitree GO-M8010-6 (4 legs × hip, thigh, calf, wheel)
   * - foot
     - a wheel (tyre cylinder) on each calf, turning without end
   * - mass
     - 20.27 kg (drives included)
   * - body height standing / lying
     - 0.3965 m / 0.2052 m (MJCF keyframes ``home`` / ``lie_down``)
   * - links / joints
     - 22 / 21, of which 16 move (:doc:`robot_frames`)

Why the package is laid out this way
------------------------------------

Two conventions, one outside and one inside:

- **One package per robot**, as Unitree's ``unitree_ros/robots`` (``go2_description``, ...). MQ1 and
  MQ1W differ in their legs (a foot sphere against a wheel), and the control stack finds a robot
  by the package name: each robot is ``<robot>_description`` → ``<robot>_control`` →
  ``<robot>_mujoco``.
- **Inside, as Universal Robots'** ``ur_description``: every number is in a config file, and the
  xacro only assembles them. A number is edited in one place; a calibrated robot is another config
  file, not another xacro.

.. image:: structure.svg
   :alt: Where each file of the package goes

Structure
---------

.. code-block:: text

   mq1w_description/
   ├── config/      every number (edit here)
   ├── urdf/        the xacro that assembles them, and the URDF it makes
   ├── meshes/      visual/: the parts; collision/: their convex pieces
   ├── mjcf/        the MuJoCo model
   ├── launch/      view_mq1w.launch.py / .xml: the model in RViz
   ├── rviz/        view_robot.rviz
   ├── test/        the checks
   └── doc/         this documentation

The configuration files
-----------------------

Values are given per joint or per link (not by a symmetry rule): the robot is not exactly
symmetric (the rear thighs turn through a range 60° further back than the front ones, and each
left / right part has its own measured inertia).

.. list-table::
   :header-rows: 1
   :widths: 32 68

   * - file
     - holds
   * - ``config/default_kinematics.yaml``
     - the origin of every joint in its parent link: x, y, z (m), roll, pitch, yaw (rad). As in
       UR, the nominal geometry; a calibrated robot gets its own copy (``kinematics_params:=``).
   * - ``config/joint_limits.yaml``
     - the position range of every revolute joint (rad)
   * - ``config/physical_parameters.yaml``
     - mass (kg), centre of mass (m) and inertia tensor (kg m², about the centre of mass) of every
       link, from the SolidWorks parts
   * - ``config/visual_parameters.yaml``
     - materials (rgba); per link its visual meshes and its collision geometry
   * - ``config/initial_positions.yaml``
     - the joint positions a ros2_control hardware starts at (the standing pose)
   * - ``config/actuators.yaml``
     - the drive per joint kind: effort, velocity, armature (rotor inertia), the transmission after
       the drive; joint damping and friction (ASSUMED). The keys of ``joints`` give the leg's
       joint kinds, which is how the control stack learns the joint layout.

Effort, velocity, damping and friction exist only in ``actuators.yaml``; the xacro reads them
there. The package test fails if a config entry is not used by the model.

The URDF files
--------------

.. list-table::
   :header-rows: 1
   :widths: 38 62

   * - file
     - role
   * - ``urdf/mq1w.urdf.xacro``
     - the robot (as ``ur.urdf.xacro``): its arguments, the config files, the call of the macro
   * - ``urdf/mq1w_macro.xacro``
     - the robot as a macro (as ``ur_macro.xacro``): ``base_link``, ``base``, the sensor frames,
       the four legs
   * - ``urdf/inc/mq1w_common.xacro``
     - the builders (as ``inc/ur_common.xacro``): a link or a joint by name, taking its numbers
       from the config files; it holds no number itself
   * - ``urdf/mq1w_mocked.urdf.xacro``
     - the robot plus a ros2_control system on mock hardware (as ``ur_mocked.urdf.xacro``)
   * - ``urdf/ros2_control_mock_hardware.xacro``
     - that system: ``mock_components/GenericSystem``, the joints of
       ``inc/mq1w_joint_control.xacro``, the IMU of ``inc/mq1w_sensors.xacro``
   * - ``urdf/mq1w.urdf``
     - the output of ``mq1w.urdf.xacro``, committed: the control stack's code generator reads it
       at build time. Never edited by hand.

Arguments of ``mq1w.urdf.xacro`` (an empty value means the file in ``config/``; another file is
given as an absolute path):

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - argument
     - file
   * - ``kinematics_params``
     - ``default_kinematics.yaml``
   * - ``joint_limit_params``
     - ``joint_limits.yaml``
   * - ``physical_params``
     - ``physical_parameters.yaml``
   * - ``visual_params``
     - ``visual_parameters.yaml``
   * - ``actuator_params``
     - ``actuators.yaml``

``mq1w_mocked.urdf.xacro`` takes these and ``initial_positions_file``, ``mock_sensor_commands``.

.. code-block:: bash

   cd mq1w_description
   xacro urdf/mq1w.urdf.xacro -o urdf/mq1w.urdf                          # after a config change
   xacro urdf/mq1w.urdf.xacro kinematics_params:=/abs/path/calibrated.yaml
   xacro urdf/mq1w_mocked.urdf.xacro                                     # with ros2_control

The robot runs no controller from this package: as in UR, running the robot is the driver's job,
here ``mq1w_control`` (``control_node``, over ``legged_msgs/LowCmd`` / ``LowState``).

Meshes
------

- ``meshes/visual/`` (26 STL files): the SolidWorks parts, coloured by the materials of
  ``visual_parameters.yaml``.
- ``meshes/collision/`` (140 STL files): each link's visual meshes split into convex
  pieces by ``scripts/make_collision_meshes.py`` (CoACD). MuJoCo collides a mesh as its convex
  hull, so a concave part (a thigh, the shell) needs several pieces.
- The contact element keeps its primitive: the wheel's tyre cylinder.
  It rolls smoothly (a hull is faceted), and the code generator reads its radius.

The MuJoCo model
----------------

``mjcf/mq1w.xml`` is the robot for MuJoCo, ``mjcf/scene.xml`` adds the floor. Besides what the URDF
holds, it has what only a simulator needs: the actuators (torque limits, rotor inertia), the IMU
sites, contact parameters, the keyframes ``home`` and ``lie_down``, the solver options
, and an ``<exclude>`` of each wheel with its own thigh (2.5 mm apart at the knee's stop).
It is used by ``episode_runner``, ``mujoco_node``, the control tests, ``make verify-model`` and
the RL training. Its shared numbers are kept equal to the URDF's by hand, and
``scripts/validate_model.py mq1w`` (in ``make verify-model``) checks them: masses, centres of mass,
inertias, joint origins, axes, ranges, efforts, armature, damping, friction, collision counts, and
that in each keyframe only the wheels touch the floor.

Viewing the model
-----------------

.. code-block:: bash

   ros2 launch mq1w_description view_mq1w.launch.py                 # or view_mq1w.launch.xml
   ros2 launch mq1w_description view_mq1w.launch.py gui:=false      # joint_state_publisher, no sliders
   ros2 launch mq1w_description view_mq1w.launch.py rviz:=false     # the nodes alone

``view_mq1w.launch.xml`` holds the arguments (``rviz_config_file``, ``description_file``, ``gui``,
``rviz``) and the nodes; the Python file only includes it, as UR's.

Tests
-----

``make test`` (or ``colcon test --packages-select mq1w_description``) runs:

- ``test/test_mq1w_urdf_xacro.py``: the xacro builds and equals ``urdf/mq1w.urdf``; one tree rooted at
  ``base_link``; every mesh exists; the mocked robot is the robot plus ros2_control, naming every
  moving joint within its limits; every config entry is used.
- ``test/test_view_mq1w_launch.py``: both view launches start (no window, ROS domain 77, their own
  namespace) and ``/tf`` with ``/tf_static`` carry every link.

Changing the model
------------------

.. list-table::
   :header-rows: 1
   :widths: 30 40 30

   * - to change
     - edit
     - then
   * - a number (an origin, a limit, a mass)
     - the file in ``config/``, and the same number in ``mjcf/mq1w.xml``
     - regenerate ``urdf/mq1w.urdf``; ``make verify-model``; ``make test``
   * - a part's shape
     - its STL in ``meshes/visual/``
     - ``scripts/make_collision_meshes.py mq1w``; regenerate the URDF; the checks above
   * - the drives
     - ``actuators.yaml`` and the MJCF
     - as for a number

The MJCF is not generated: apart from the collision meshes, a change to the model is made in the
config files and in the MJCF, and ``validate_model.py`` catches a side left behind.
