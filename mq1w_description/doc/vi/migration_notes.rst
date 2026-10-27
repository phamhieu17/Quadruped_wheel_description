Ghi chú chuyển đổi
==================

Những gì thay đổi so với bố cục cũ của mô tả robot MQ1: một gói duy nhất,
``quadruped_description``, chứa cả hai robot trong `Quadruped_description
<https://github.com/phamhieu17/Quadruped_description>`_. Giờ mỗi robot có repo riêng:
``mq1w_description`` nằm ở `Quadruped_wheel_description <https://github.com/phamhieu17/Quadruped_wheel_description>`_, ``mq1_description`` ở
`Quadruped_description <https://github.com/phamhieu17/Quadruped_description>`_ (hai robot khác nhau về chân và động học). Trong
stack điều khiển, chúng là các submodule ``robots/mq1w`` và ``robots/mq1``.

.. contents::
   :local:

Cấu trúc
--------

Bố cục cũ có một gói duy nhất, ``quadruped_description``, chia thư mục theo robot
(``config/mq1w/``, ``meshes/mq1w/``, ``mjcf/mq1w/``, ``urdf/mq1w.urdf``). Giờ mỗi robot là một gói riêng,
``mq1w_description``, bên trong tổ chức như ``ur_description``.

.. list-table::
   :header-rows: 1
   :widths: 45 55

   * - trước
     - bây giờ
   * - ``urdf/mq1w.urdf.xacro`` (một file, số ghi thẳng trong đó)
     - ``urdf/mq1w.urdf.xacro`` + ``mq1w_macro.xacro`` + ``inc/mq1w_common.xacro``, số nằm trong ``config/``
   * - ``xacro ... use_ros2_control:=true hardware_plugin:=...``
     - ``urdf/mq1w_mocked.urdf.xacro`` (chỉ phần cứng giả lập)
   * - ``meshes/mq1w/*.stl``
     - ``meshes/visual/*.stl``; ``meshes/collision/`` là mới
   * - ``config/mq1w/joint_defaults.yaml``
     - ``config/initial_positions.yaml`` (tư thế đứng); tư thế nằm là keyframe ``lie_down`` của
       MJCF; bỏ các gain dùng cho demo
   * - ``config/mq1w/inertials.json``
     - ``config/physical_parameters.yaml``
   * - ``config/mq1w/ros2_controllers.yaml``, ``launch/control.launch.py``
     - đã xoá: không gì dùng; robot được điều khiển bởi ``mq1w_control``
   * - ``launch/display.launch.py``
     - ``launch/view_mq1w.launch.py`` và ``view_mq1w.launch.xml`` (thêm arg ``rviz_config_file``,
       ``description_file``, ``rviz``)
   * - ``rviz/display.rviz``
     - ``rviz/view_robot.rviz``
   * - ``scripts/mujoco_stand.py``
     - đã xoá (``make sim`` làm việc đó bằng stack điều khiển)
   * - –
     - ``test/``, ``doc/``, ``scripts/make_collision_meshes.py``

Mô hình
-------

- URDF bằng đúng bản cũ về mặt số (so từng con số, không dung sai).
- **Collision**: các hình hộp và hình trụ đơn giản được thay bằng các mảnh lồi cắt từ mesh của chi
  tiết; hình trụ bánh xe được giữ nguyên. Trong MJCF, file mesh
  nằm trong ``visual/`` và ``collision/``, và mỗi bánh xe không va chạm với thigh của chính nó.
- Ảnh hưởng: mọi episode bắt đầu từ tư thế nằm thay đổi nhẹ (robot nằm lên các mảnh mới);
  MuJoCo trên GPU chạy chậm hơn khoảng 26%.

Cập nhật bản clone
------------------

Submodule ``robots/`` đã thành ``robots/mq1w`` và ``robots/mq1``; cách đơn giản nhất là clone lại:

.. code-block:: bash

   git clone --recursive https://github.com/phamhieu17/Quadrupped.git quadruped
   cd quadruped && make build && make test
