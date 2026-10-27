#!/usr/bin/env python3
"""Consistency checks between <robot>_description/{urdf/<robot>.urdf, mjcf/<robot>.xml, config/actuators.yaml}.
   python3 validate_model.py <robot>      (mq1w | mq1; needs: mujoco, numpy, pyyaml) -> exit code 1 on any mismatch"""
import os, sys, xml.etree.ElementTree as ET, numpy as np, mujoco, yaml
if len(sys.argv) != 2: sys.exit(__doc__)
robot = sys.argv[1]
here = os.path.dirname(os.path.abspath(__file__)); root = os.path.join(here, '..', f'{robot}_description')
m = mujoco.MjModel.from_xml_path(os.path.join(root, 'mjcf', 'scene.xml')); d = mujoco.MjData(m)
urdf = ET.parse(os.path.join(root, 'urdf', f'{robot}.urdf')).getroot()
act = yaml.safe_load(open(os.path.join(root, 'config', 'actuators.yaml')))
wheels = 'wheel' in act['joints']
errors = []
def check(ok, msg):
    if not ok: errors.append(msg)
vec = lambda s: np.array([float(x) for x in s.split()])
bid = lambda n: mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, n)
jid = lambda n: mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_JOINT, n)

def mj_inertia(b):   # full inertia tensor of body b about its COM, in body frame
    R = np.zeros(9); mujoco.mju_quat2Mat(R, m.body_iquat[b]); R = R.reshape(3, 3)
    return R @ np.diag(m.body_inertia[b]) @ R.T

# links: mass, COM, inertia, physical validity
for link in urdf.findall('link'):
    ine = link.find('inertial'); name = link.get('name')
    if ine is None: continue
    b = bid(name); check(b >= 0, f'{name}: missing in MJCF')
    if b < 0: continue
    mass = float(ine.find('mass').get('value')); com = vec(ine.find('origin').get('xyz'))
    i = ine.find('inertia').attrib; I = np.array([[i['ixx'], i['ixy'], i['ixz']], [i['ixy'], i['iyy'], i['iyz']], [i['ixz'], i['iyz'], i['izz']]], float)
    check(abs(mass - m.body_mass[b]) < 1e-6, f'{name}: mass urdf {mass} mjcf {m.body_mass[b]}')
    check(np.allclose(com, m.body_ipos[b], atol=1e-6), f'{name}: COM urdf {com} mjcf {m.body_ipos[b]}')
    check(np.allclose(I, mj_inertia(b), atol=1e-7), f'{name}: inertia mismatch')
    ev = np.linalg.eigvalsh(I)
    check(ev.min() > 0 and ev[0] + ev[1] >= ev[2] - 1e-9, f'{name}: inertia not physical {ev}')

# joints: origin, axis, limits, effort, armature
cls = lambda n: n.split('_')[1]
for j in urdf.findall('joint'):
    name = j.get('name'); typ = j.get('type')
    if typ == 'fixed': continue
    k = jid(name); check(k >= 0, f'{name}: missing in MJCF')
    if k < 0: continue
    b = m.jnt_bodyid[k]
    check(np.allclose(vec(j.find('origin').get('xyz')), m.body_pos[b], atol=1e-6), f'{name}: origin mismatch')
    check(np.allclose(vec(j.find('axis').get('xyz')), m.jnt_axis[k], atol=1e-6), f'{name}: axis mismatch')
    lim = j.find('limit'); spec = act['joints'][cls(name)]
    if typ == 'revolute':
        check(np.allclose([float(lim.get('lower')), float(lim.get('upper'))], m.jnt_range[k], atol=1e-4), f'{name}: range mismatch')
    a = [i for i in range(m.nu) if m.actuator_trnid[i, 0] == k]
    check(len(a) == 1, f'{name}: expected one actuator')
    if a: check(abs(m.actuator_ctrlrange[a[0], 1] - float(lim.get('effort'))) < 1e-6 and abs(spec['effort'] - float(lim.get('effort'))) < 1e-6, f'{name}: effort mismatch')
    check(abs(spec['velocity'] - float(lim.get('velocity'))) < 1e-6, f'{name}: velocity mismatch')
    check(abs(m.dof_armature[m.jnt_dofadr[k]] - spec['armature']) < 1e-6, f'{name}: armature mjcf {m.dof_armature[m.jnt_dofadr[k]]} yaml {spec["armature"]}')
    dyn = j.find('dynamics')
    check(abs(m.dof_damping[m.jnt_dofadr[k]] - float(dyn.get('damping'))) < 1e-6, f'{name}: damping mismatch')
    check(abs(m.dof_frictionloss[m.jnt_dofadr[k]] - float(dyn.get('friction'))) < 1e-6, f'{name}: friction mismatch')

# collision geometry count per link (a link fixed to its parent, like *_foot, is merged into it as
# MuJoCo merges it: the foot sphere is a geom of the calf body)
fixed_children = {}
for j in urdf.findall('joint'):
    if j.get('type') == 'fixed':
        fixed_children.setdefault(j.find('parent').get('link'), []).append(j.find('child').get('link'))
links = {l.get('name'): l for l in urdf.findall('link')}
for link in urdf.findall('link'):
    b = bid(link.get('name'))
    if b < 0: continue
    n_urdf = len(link.findall('collision')) + sum(len(links[c].findall('collision')) for c in fixed_children.get(link.get('name'), [])
                                                  if bid(c) < 0)
    n_mj = sum(1 for g in range(m.ngeom) if m.geom_bodyid[g] == b and m.geom_contype[g])
    check(n_mj == n_urdf, f'{link.get("name")}: collisions urdf {n_urdf} mjcf {n_mj}')

# totals, keyframes: wheels (bodies *_wheel) or feet (geoms *_foot) touching the floor, nothing else in contact
check(abs(m.body_subtreemass[bid('base')] - sum(float(l.find('inertial/mass').get('value')) for l in urdf.findall('link') if l.find('inertial') is not None)) < 1e-6, 'total mass mismatch')
for k in range(m.nkey):
    mujoco.mj_resetDataKeyframe(m, d, k); mujoco.mj_forward(m, d)
    kname = mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_KEY, k)
    if wheels:
        touching = {mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_BODY, m.geom_bodyid[g]) for c in d.contact[:d.ncon] for g in (c.geom1, c.geom2) if m.geom_bodyid[g]}
        check(all(n.endswith('_wheel') for n in touching), f'key {kname}: non-wheel contact {touching}')
    else:
        touching = {mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_GEOM, g) or f'geom {g} of {m.body(m.geom_bodyid[g]).name}'
                    for c in d.contact[:d.ncon] for g in (c.geom1, c.geom2) if m.geom_bodyid[g]}
        check(all(n.endswith('_foot') for n in touching), f'key {kname}: non-foot contact {touching}')
    check(all(c.dist > -1e-3 for c in d.contact[:d.ncon]), f'key {kname}: penetration > 1 mm')

print(f'mass {m.body_subtreemass[bid("base")]:.2f} kg, {m.njnt - 1} joints, {m.nu} actuators')
print('\n'.join(['FAIL ' + e for e in errors]) or 'OK: URDF, MJCF and actuators.yaml are consistent')
sys.exit(1 if errors else 0)
