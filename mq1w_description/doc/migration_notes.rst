Migration notes
===============

What changed against the earlier layout of the MQ1 descriptions: one package,
``quadruped_description``, holding both robots in `Quadruped_description
<https://github.com/phamhieu17/Quadruped_description>`_. Each robot now has its own repository:
``mq1w_description`` is in `Quadruped_wheel_description <https://github.com/phamhieu17/Quadruped_wheel_description>`_, ``mq1_description`` in
`Quadruped_description <https://github.com/phamhieu17/Quadruped_description>`_ (the two robots differ in their legs and
kinematics). In the control stack they are the submodules ``robots/mq1w`` and ``robots/mq1``.

.. contents::
   :local:

Layout
------

The earlier layout held one package, ``quadruped_description``, with a folder per robot
(``config/mq1w/``, ``meshes/mq1w/``, ``mjcf/mq1w/``, ``urdf/mq1w.urdf``). Each robot is now its own
package, ``mq1w_description``, laid out inside as ``ur_description``.

.. list-table::
   :header-rows: 1
   :widths: 45 55

   * - before
     - now
   * - ``urdf/mq1w.urdf.xacro`` (one file, numbers written in it)
     - ``urdf/mq1w.urdf.xacro`` + ``mq1w_macro.xacro`` + ``inc/mq1w_common.xacro``, numbers in ``config/``
   * - ``xacro ... use_ros2_control:=true hardware_plugin:=...``
     - ``urdf/mq1w_mocked.urdf.xacro`` (mock hardware only)
   * - ``meshes/mq1w/*.stl``
     - ``meshes/visual/*.stl``; ``meshes/collision/`` is new
   * - ``config/mq1w/joint_defaults.yaml``
     - ``config/initial_positions.yaml`` (the standing pose); the lying pose is the MJCF keyframe
       ``lie_down``; the demo gains were dropped
   * - ``config/mq1w/inertials.json``
     - ``config/physical_parameters.yaml``
   * - ``config/mq1w/ros2_controllers.yaml``, ``launch/control.launch.py``
     - removed: nothing used them; the robot is driven by ``mq1w_control``
   * - ``launch/display.launch.py``
     - ``launch/view_mq1w.launch.py`` and ``view_mq1w.launch.xml`` (new arguments ``rviz_config_file``,
       ``description_file``, ``rviz``)
   * - ``rviz/display.rviz``
     - ``rviz/view_robot.rviz``
   * - ``scripts/mujoco_stand.py``
     - removed (``make sim`` does it with the control stack)
   * - –
     - ``test/``, ``doc/``, ``scripts/make_collision_meshes.py``

The model
---------

- The URDF is numerically identical to the earlier one (every number compared exactly).
- **Collision**: the box and cylinder primitives became convex pieces of the parts' meshes; the
  wheels' cylinders stay. In the MJCF the mesh files are under
  ``visual/`` and ``collision/`` and each wheel is excluded from colliding with its own thigh.
- Effects: every episode that starts lying down changed slightly (the robot rests on the new
  pieces); MuJoCo on the GPU makes ~26% fewer steps per second.

Updating a checkout
-------------------

The submodule ``robots/`` became ``robots/mq1w`` and ``robots/mq1``; the simplest is a fresh clone:

.. code-block:: bash

   git clone --recursive https://github.com/phamhieu17/Quadrupped.git quadruped
   cd quadruped && make build && make test
