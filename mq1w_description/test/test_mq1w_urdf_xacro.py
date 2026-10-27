"""The description package of this directory (<robot>_description), as ur_description's test/:
the xacro builds (and <robot>_mocked, with ros2_control), urdf/<robot>.urdf is its output, the model is one
tree whose meshes exist, and every entry of the config files is used by it."""
import os
import xml.etree.ElementTree as ET

import pytest
import xacro
import yaml

PKG = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROBOT = os.path.basename(PKG).removesuffix('_description')
XACRO = os.path.join(PKG, 'urdf', f'{ROBOT}.urdf.xacro')
MOCKED = os.path.join(PKG, 'urdf', f'{ROBOT}_mocked.urdf.xacro')
URDF = os.path.join(PKG, 'urdf', f'{ROBOT}.urdf')


def config(name):
    with open(os.path.join(PKG, 'config', f'{name}.yaml')) as f:
        return yaml.safe_load(f)


def build(path=XACRO, **args):
    return ET.fromstring(xacro.process_file(path, mappings=args).toxml())


def canonical(e):
    """An element as nested tuples; numbers as floats, compared exactly; comments, whitespace left out."""
    def value(s):
        try:
            return tuple(float(t) for t in s.split())
        except ValueError:
            return s.strip()
    return (e.tag, tuple(sorted((k, value(v)) for k, v in e.attrib.items())), value(e.text or ''),
            tuple(canonical(c) for c in e if isinstance(c.tag, str)))


@pytest.fixture(scope='module')
def urdf():
    return build()


def test_committed_urdf_is_the_xacro_output(urdf):
    assert canonical(urdf) == canonical(ET.parse(URDF).getroot()), (
        f'urdf/{ROBOT}.urdf is out of date: cd {ROBOT}_description && xacro urdf/{ROBOT}.urdf.xacro -o urdf/{ROBOT}.urdf')


def test_one_tree_rooted_at_base_link(urdf):
    links = [l.get('name') for l in urdf.findall('link')]
    assert len(links) == len(set(links))
    children = [j.find('child').get('link') for j in urdf.findall('joint')]
    assert len(children) == len(set(children)), 'a link with two parents'
    for j in urdf.findall('joint'):
        assert j.find('parent').get('link') in links and j.find('child').get('link') in links, j.get('name')
    assert set(links) - set(children) == {'base_link'}


def test_every_mesh_exists(urdf):
    prefix = f'package://{ROBOT}_description/'
    for m in urdf.iter('mesh'):
        f = m.get('filename')
        assert f.startswith(prefix) and os.path.isfile(os.path.join(PKG, f[len(prefix):])), f


def test_ros2_control_names_every_moving_joint_within_its_limits(urdf):
    assert urdf.find('ros2_control') is None, 'the robot file has no ros2_control (as ur.urdf.xacro)'
    mocked = build(MOCKED)
    assert [canonical(c) for c in mocked if c.tag != 'ros2_control'] == [canonical(c) for c in urdf], \
        'the mocked robot is the robot plus ros2_control'
    rc = mocked.find('ros2_control')
    moving = {j.get('name'): j for j in urdf.findall('joint') if j.get('type') != 'fixed'}
    names = [j.get('name') for j in rc.findall('joint')]
    assert sorted(names) == sorted(moving)
    for j in rc.findall('joint'):
        init = j.find("state_interface[@name='position']/param[@name='initial_value']")
        lim = moving[j.get('name')].find('limit')
        if init is not None and lim.get('lower') is not None:
            assert float(lim.get('lower')) <= float(init.text) <= float(lim.get('upper')), j.get('name')
    assert rc.find("sensor[@name='imu_sensor']/param[@name='frame_id']").text in [l.get('name') for l in urdf.findall('link')]


def test_every_config_entry_is_used(urdf):
    joints = {j.get('name'): j.get('type') for j in urdf.findall('joint')}
    links = {l.get('name'): l for l in urdf.findall('link')}
    assert set(config('default_kinematics')['kinematics']) == set(joints)
    assert set(config('joint_limits')['joint_limits']) == {n for n, t in joints.items() if t == 'revolute'}
    assert set(config('physical_parameters')['inertia_parameters']) == {n for n, l in links.items() if l.find('inertial') is not None}
    visual = config('visual_parameters')
    assert set(visual['mesh_files']) == {n for n, l in links.items() if l.find('visual') is not None or l.find('collision') is not None}
    assert set(visual['materials']) == {v.find('material').get('name') for v in urdf.iter('visual')}
    assert set(config('initial_positions')) == {n for n, t in joints.items() if t == 'revolute'}
