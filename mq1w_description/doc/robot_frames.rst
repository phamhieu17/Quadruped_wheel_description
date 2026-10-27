Robot frames
============

The frames of the MQ1W model, their conventions and the meaning of each joint's angle. The
numbers below are those of ``config/default_kinematics.yaml`` and ``config/joint_limits.yaml``,
which are the reference.

.. contents::
   :local:

Conventions
-----------

- Every frame follows `REP-103 <https://ros.org/reps/rep-0103.html>`_: **x forward, y left,
  z up**, right-handed; lengths in m, angles in rad.
- Legs are named by their corner: **FL** (front left), **FR** (front right), **RL** (rear left),
  **RR** (rear right). The control stack orders the joints FL, FR, RL, RR and, in each leg,
  hip, thigh, calf, wheel (the keys of ``actuators.yaml joints``).
- A positive joint angle turns the child link about the joint's axis by the right-hand rule.

The frame tree
--------------

.. code-block:: text

   base_link                     root, no mass
   └ base                        the body: mass, inertia, meshes
     ├ imu_link                  the IMU
     ├ lidar_link                the lidar
     ├ camera_link               the camera
     │ └ camera_optical_frame    the camera's optical frame
     ├ FL_hip
     │ └ FL_thigh
     │   └ FL_calf
     │     └ FL_wheel
     ├ FR_hip ...                (and RL, RR: the same chain)

- ``base_link`` is the root of the tree, at the body's origin, with nothing attached. As UR's
  ``base_link``, it carries no inertia because KDL (and so ``robot_state_publisher``) does not
  accept an inertia on the root link.
- ``base`` is the body itself, at the same place and orientation as ``base_link``. In MuJoCo it is
  the free-floating body; the control stack's state estimate (position, orientation, velocity) is
  that of ``base``.

Sensor frames
-------------

.. list-table::
   :header-rows: 1
   :widths: 26 28 46

   * - frame
     - position in ``base`` (m)
     - orientation
   * - ``imu_link``
     - (0, 0, 0)
     - as ``base``: the IMU's gyro and accelerometer are measured in it (MJCF site ``imu``)
   * - ``lidar_link``
     - (0.165, 0, 0.132)
     - as ``base``
   * - ``camera_link``
     - (0.2471, 0, 0.084)
     - as ``base`` (x forward)
   * - ``camera_optical_frame``
     - at ``camera_link``
     - REP-103 optical: **z forward, x right, y down** (roll −π/2, yaw −π/2)

The legs
--------

In the origins, ± is + on a front (x) or left (y) leg and − on a rear or right one: the right legs
mirror the left ones in y, the rear hips sit at −x.

.. list-table::
   :header-rows: 1
   :widths: 20 9 21 7 20 23

   * - joint
     - parent
     - origin (m)
     - axis
     - range (rad)
     - a positive angle
   * - ``<leg>_hip_joint``
     - base
     - (±0.2, ±0.05, 0)
     - x
     - [−0.6, 0.6]
     - moves the foot left (+y): out on a left leg, in on a right one
   * - ``<leg>_thigh_joint``
     - hip
     - (0, ±0.129, 0)
     - y
     - front [−1.5708, 3.4907], rear [−0.5236, 4.5379]
     - swings the leg back
   * - ``<leg>_calf_joint``
     - thigh
     - (0, 0, −0.22)
     - y
     - [−2.55, −0.84]
     - unfolds the knee (it is always negative: more negative folds it)
   * - ``<leg>_wheel_joint``
     - calf
     - (0, ±0.042, −0.22)
     - y
     - continuous
     - the wheel rolls forward (+x)

The thigh and the calf are 0.22 m long. The drives give 23.7 N·m, 30.1 rad/s at the hip, thigh and wheel and 35.6 N·m, 20.1 rad/s at the calf
(a further 1.5:1 transmission; ``actuators.yaml``).

The wheel
---------

``<leg>_wheel`` is the wheel's centre, at the end of the calf and 0.042 m outward. It turns about
its y axis without end; a positive velocity rolls the robot forward. Its collision is the tyre
cylinder (radius 0.075 m, width 0.044 m). The wheel touches the ground on its rim below the centre
*in the wheel plane*, so when the body rolls the contact point moves on the rim (the control
stack's ``FootContacts`` takes this into account).

Poses
-----

.. list-table::
   :header-rows: 1
   :widths: 18 22 60

   * - pose
     - hip, thigh, calf
     - what it is
   * - zero
     - 0, 0, 0
     - every leg straight down, the foot 0.44 m below the hip. A reference only: a calf angle of 0
       is outside its range.
   * - standing
     - 0, 0.8, −1.5
     - ``initial_positions.yaml``, MJCF keyframe ``home``. The foot is 0.016 m behind and 0.3215 m
       below the hip, the knee points back; the body stands 0.3965 m above the ground.
   * - lying
     - 0, 1.25, −2.55
     - MJCF keyframe ``lie_down`` (the calf at its stop); the body at 0.2052 m.

.. figure:: frames/standing_iso.png
   :alt: The standing robot with its frames

   The standing robot with every frame (x red, y green, z blue).

.. figure:: frames/standing_side.png
   :alt: The standing robot from its left side

   From the left side, the front to the left: the knees point back.
