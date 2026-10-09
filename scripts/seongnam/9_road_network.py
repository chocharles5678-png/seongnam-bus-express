"""수치지도 도로선(A0013110) → 노드·간선 네트워크. 간선마다 지형 경사 부여."""
import glob, io, os, sys
import numpy as np

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
PROJ = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
ROAD_LAYER = 'A0013110'
SNAP = 1.0        # m, 이 격자로 반올림해 같은 점으로 취급
MAX_EDGE = 200.0  # 비정상적으로 긴 선분 제외


def segments(path):
    lines = [l.strip() for l in open(path, encoding='cp949', errors='replace').read().splitlines()]
    layer, xs, ys, keep = '', [], [], False
    for code, val in list(zip(lines[0::2], lines[1::2])) + [('0', 'EOF')]:
        if code == '0':
            if keep and layer == ROAD_LAYER and len(xs) > 1 and min(xs) > 100000:
                for i in range(len(xs) - 1):
                    yield xs[i], ys[i], xs[i + 1], ys[i + 1]
            keep, layer, xs, ys = val in ('LWPOLYLINE', 'POLYLINE', 'LINE'), '', [], []
        elif keep:
            if code == '8':
                layer = val
            elif code == '10':
                xs.append(float(val))
            elif code == '20':
                ys.append(float(val))


segs = []
files = sorted(glob.glob(os.path.join(PROJ, 'data', 'raw', 'ngii', '*.dxf')))
for f in files:
    segs.extend(segments(f))
segs = np.array(segs)
print(f'도엽 {len(files)}장 | 도로 선분 {len(segs):,}개')

# 노드 스냅
pts = np.r_[segs[:, :2], segs[:, 2:]]
key = np.round(pts / SNAP).astype(np.int64)
_, inv = np.unique(key, axis=0, return_inverse=True)
n = len(segs)
u, v = inv[:n], inv[n:]
node_xy = np.zeros((inv.max() + 1, 2))
node_xy[inv] = pts
length = np.hypot(segs[:, 2] - segs[:, 0], segs[:, 3] - segs[:, 1])

ok = (u != v) & (length <= MAX_EDGE) & (length > 0)
u, v, length = u[ok], v[ok], length[ok]
print(f'노드 {len(node_xy):,}개 | 간선 {len(u):,}개')

# 간선 경사 (지형)
d = np.load(os.path.join(PROJ, 'data', 'seongnam_dem10m.npz'))
dem, x0, y0, cell = d['dem'], float(d['x0']), float(d['y0']), float(d['cell'])
i = np.round((node_xy[:, 1] - y0) / cell).astype(int)
j = np.round((node_xy[:, 0] - x0) / cell).astype(int)
inside = (i >= 0) & (i < dem.shape[0]) & (j >= 0) & (j < dem.shape[1])
z = np.full(len(node_xy), np.nan)
z[inside] = dem[i[inside], j[inside]]
grade = np.abs(z[u] - z[v]) / length * 100

good = np.isfinite(grade)
print(f'경사 계산된 간선 {good.sum():,} ({good.mean() * 100:.0f}%) | '
      f'경사 중앙값 {np.nanmedian(grade):.1f}% | 8.33% 초과 {np.nanmean(grade > 8.33) * 100:.0f}% | 12% 초과 {np.nanmean(grade > 12) * 100:.0f}%')

np.savez_compressed(os.path.join(PROJ, 'data', 'seongnam_road_graph.npz'),
                    node_xy=node_xy, z=z, u=u, v=v, length=length, grade=grade)
print('saved data/seongnam_road_graph.npz')
