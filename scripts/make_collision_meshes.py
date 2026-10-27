#!/usr/bin/env python3
"""Collision meshes of <robot>_description, made from its visual meshes (as ur_description's
meshes/<type>/collision/), and the model files rewritten to use them.

    python3 make_collision_meshes.py <robot>      (mq1 | mq1w; needs: coacd, trimesh, numpy, pyyaml)

For every link with visual meshes, the meshes are placed in the link frame (their xyz, rpy) and split
into convex pieces by CoACD: MuJoCo collides a mesh as its convex hull, so a concave part (a thigh, the
shell) needs several. The pieces go to meshes/collision/<link>_<i>.stl, and the link's collision in
config/visual_parameters.yaml (-> URDF, by the xacro) and in mjcf/<robot>.xml becomes those meshes.

The contact elements keep their primitive: the wheel's cylinder and the foot's sphere roll and touch
smoothly (a hull is faceted), and the codegen reads their radius (kFootRadius). So:
  - a wheel link (<leg>_wheel) and a foot link (<leg>_foot) are left as they are;
  - the visual meshes of a foot (FOOT_MESHES) are left out of the link that carries them (MQ1's calf);
  - a link holding a foot sphere (fixed child <leg>_foot) is cut at the top of the sphere, so that the
    sphere alone touches the ground there.
Run it again after a visual mesh changes; then rebuild urdf/<robot>.urdf (xacro) and run
validate_model.py <robot> and the package test.
"""
import glob
import os
import re
import sys

import coacd
import numpy as np
import trimesh
import yaml

# CoACD: concavity threshold (fraction of the part's size: lower = more pieces, closer fit), at most
# this many pieces per link and vertices per piece (MuJoCo's collision cost grows with both), seed for
# a reproducible result.
THRESHOLD = 0.03
MAX_PIECES = 16
MAX_PIECE_VERTICES = 64
SEED = 0
FOOT_MESHES = {'foot.stl'}

if len(sys.argv) != 2:
    sys.exit(__doc__)
robot = sys.argv[1]
pkg = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', f'{robot}_description')
visual_file = os.path.join(pkg, 'config', 'visual_parameters.yaml')
mjcf_file = os.path.join(pkg, 'mjcf', f'{robot}.xml')
out_dir = os.path.join(pkg, 'meshes', 'collision')
visual = yaml.safe_load(open(visual_file))
kinematics = yaml.safe_load(open(os.path.join(pkg, 'config', 'default_kinematics.yaml')))['kinematics']


def pose(entry):
    """4x4 transform of an entry's xyz, rpy (URDF fixed-axis roll, pitch, yaw)."""
    T = trimesh.transformations.euler_matrix(*entry.get('rpy', [0, 0, 0]), axes='sxyz')
    T[:3, 3] = entry.get('xyz', [0, 0, 0])
    return T


def cut_below(piece, z):
    """The convex piece where it is above the plane z (None if nothing is): still convex."""
    if piece.bounds[0][2] >= z:
        return piece
    if piece.bounds[1][2] <= z:
        return None
    v = piece.vertices
    a, b = v[piece.edges_unique[:, 0]], v[piece.edges_unique[:, 1]]
    crossing = (a[:, 2] - z) * (b[:, 2] - z) < 0
    t = ((z - a[crossing, 2]) / (b[crossing, 2] - a[crossing, 2]))[:, None]
    points = np.vstack([v[v[:, 2] >= z], a[crossing] + t * (b[crossing] - a[crossing])])
    return trimesh.convex.convex_hull(points) if len(points) >= 4 else None


def foot_top(link):
    """z of the top of the foot sphere fixed to this link, or None."""
    leg = link.split('_')[0]
    foot = visual['mesh_files'].get(f'{leg}_foot')
    if not link.endswith('_calf') or foot is None:
        return None
    sphere = next(c['sphere'] for c in foot['collision'] if 'sphere' in c)
    return kinematics[f'{leg}_foot_joint']['z'] + sphere['radius']


def pieces_of(link, entries):
    parts = []
    for v in entries:
        if v['mesh'] in FOOT_MESHES:
            continue
        m = trimesh.load(os.path.join(pkg, 'meshes', 'visual', v['mesh']), force='mesh')
        m.apply_transform(pose(v))
        parts.append(m)
    whole = trimesh.util.concatenate(parts)
    result = coacd.run_coacd(coacd.Mesh(whole.vertices, whole.faces), threshold=THRESHOLD, max_convex_hull=MAX_PIECES,
                             decimate=True, max_ch_vertex=MAX_PIECE_VERTICES, seed=SEED)
    pieces = [trimesh.Trimesh(vs, fs) for vs, fs in result]
    z = foot_top(link)
    if z is not None:
        pieces = [p for p in (cut_below(p, z) for p in pieces) if p is not None]
    return pieces


links = [n for n, m in visual['mesh_files'].items()
         if m.get('visual') and not n.endswith(('_wheel', '_foot'))]
os.makedirs(out_dir, exist_ok=True)
files = {}
for link in links:
    for old in glob.glob(os.path.join(out_dir, f'{link}_*.stl')):
        os.remove(old)
    pieces = pieces_of(link, visual['mesh_files'][link]['visual'])
    files[link] = []
    for i, p in enumerate(pieces):
        name = f'{link}_{i}.stl'
        p.export(os.path.join(out_dir, name))
        files[link].append(name)
    print(f'{link}: {len(pieces)} pieces, {sum(len(p.vertices) for p in pieces)} vertices')

# visual_parameters.yaml: the link's collision list becomes its meshes (text edit: keeps the comments)
lines = open(visual_file).read().split('\n')
out, i = [], 0
current = None
while i < len(lines):
    line = lines[i]
    m = re.match(r'^  (\w+):$', line)
    if m:
        current = m.group(1)
    if current in files and line == '    collision:':
        out.append(line)
        out += [f'      - {{mesh: {f}}}' for f in files[current]]
        i += 1
        while i < len(lines) and lines[i].startswith('      - '):
            i += 1
        continue
    out.append(line)
    i += 1
open(visual_file, 'w').write('\n'.join(out))

# MJCF: collision mesh assets after the visual ones; each link's class="collision" geoms become its meshes
x = open(mjcf_file).read().split('\n')
x = [l for l in x if 'file="collision/' not in l]
last_asset = max(k for k, l in enumerate(x) if re.search(r'<mesh name="[^"]+" file="visual/', l))
indent = re.match(r'\s*', x[last_asset]).group(0)
assets = [f'{indent}<mesh name="{f[:-4]}" file="collision/{f}"/>' for link in links for f in files[link]]
x = x[:last_asset + 1] + assets + x[last_asset + 1:]
for link in links:
    start = next(k for k, l in enumerate(x) if f'<body name="{link}"' in l)
    end = next(k for k in range(start + 1, len(x)) if '<body ' in x[k] or '</body>' in x[k])
    geoms = [k for k in range(start + 1, end) if 'class="collision"' in x[k]]
    if not geoms:
        sys.exit(f'{link}: no class="collision" geom in {mjcf_file}')
    gindent = re.match(r'\s*', x[geoms[0]]).group(0)
    new = [f'{gindent}<geom class="collision" type="mesh" mesh="{f[:-4]}"/>' for f in files[link]]
    x = x[:geoms[0]] + new + [l for k, l in enumerate(x[geoms[0]:end], geoms[0]) if k not in geoms] + x[end:]
open(mjcf_file, 'w').write('\n'.join(x))
print(f'wrote {sum(len(v) for v in files.values())} meshes to {out_dir}; updated {visual_file} and {mjcf_file}')
