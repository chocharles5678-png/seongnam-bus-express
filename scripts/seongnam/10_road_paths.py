"""도로망 기반 재계산: 경사 기준을 넘지 않고 정류장에 닿을 수 있는가."""
import csv, glob, io, json, os, sys
import numpy as np
import shapefile
from scipy.spatial import cKDTree
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import dijkstra

sys.path.insert(0, os.path.dirname(__file__))
from tm import to_tm, to_latlon, UTMK

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
PROJ = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
CORRIDOR = 15.0     # 교통 레이어에서 이 거리 안이면 통행 가능
WALK_LIMIT = 8.33   # 보행 기준 경사(%)
BUS_LIMIT = 12.0    # 버스 등판 한계(%)
WALK_MAX = 600.0    # 도보로 받아들일 수 있는 우회 거리(m)
TRUNK = 200         # 간선 판정 기준(하루 운행)

dm = np.load(os.path.join(PROJ, 'data', 'seongnam_dem10m.npz'))
dem, x0, y0, cell = dm['dem'], float(dm['x0']), float(dm['y0']), float(dm['cell'])
H, W = dem.shape

# 1) 통행 가능 격자
cache = os.path.join(PROJ, 'data', 'seongnam_road_mask.npy')
if os.path.exists(cache):
    mask = np.load(cache)
else:
    pts = []
    for f in sorted(glob.glob(os.path.join(PROJ, 'data', 'raw', 'ngii', '*.dxf'))):
        lines = [l.strip() for l in open(f, encoding='cp949', errors='replace').read().splitlines()]
        layer, xs, ys, keep = '', [], [], False
        for code, val in list(zip(lines[0::2], lines[1::2])) + [('0', 'EOF')]:
            if code == '0':
                if keep and layer.startswith('A') and xs and min(xs) > 100000:
                    pts.extend(zip(xs, ys))
                keep, layer, xs, ys = val in ('LWPOLYLINE', 'POLYLINE', 'LINE'), '', [], []
            elif keep:
                if code == '8':
                    layer = val
                elif code == '10':
                    xs.append(float(val))
                elif code == '20':
                    ys.append(float(val))
    gy, gx = np.mgrid[0:H, 0:W]
    P = np.c_[x0 + gx.ravel() * cell, y0 + gy.ravel() * cell]
    dist, _ = cKDTree(np.array(pts)).query(P, distance_upper_bound=CORRIDOR)
    mask = np.isfinite(dist).reshape(H, W) & np.isfinite(dem)
    np.save(cache, mask)
print(f'통행 가능 격자 {mask.sum():,}개')

nid = np.full((H, W), -1, np.int32)
nid[mask] = np.arange(mask.sum())
N = int(mask.sum())

# 2) 간선 (8방향) + 경사
U, V, L, G = [], [], [], []
for di, dj in [(0, 1), (1, 0), (1, 1), (1, -1)]:
    a = nid[max(0, -di):H - max(0, di), max(0, -dj):W - max(0, dj)]
    b = nid[max(0, di):H - max(0, -di), max(0, dj):W - max(0, -dj)]
    za = dem[max(0, -di):H - max(0, di), max(0, -dj):W - max(0, dj)]
    zb = dem[max(0, di):H - max(0, -di), max(0, dj):W - max(0, -dj)]
    ok = (a >= 0) & (b >= 0)
    d = cell * np.hypot(di, dj)
    U.append(a[ok]); V.append(b[ok]); L.append(np.full(ok.sum(), d))
    G.append(np.abs(za[ok] - zb[ok]) / d * 100)
U, V, L, G = map(np.concatenate, (U, V, L, G))
print(f'간선 {len(U):,}개 | 경사 8.33% 초과 {np.mean(G > WALK_LIMIT) * 100:.0f}%')


def graph(limit):
    m = G <= limit
    g = coo_matrix((L[m], (U[m], V[m])), shape=(N, N)).tocsr()
    return g + g.T


# 3) 정류장 → 격자
stops = [s for s in csv.DictReader(open(os.path.join(PROJ, 'data', 'seongnam_stop_slope.csv'), encoding='utf-8-sig')) if s['미정차'] == 'N']
F = {s['정류장번호']: s for s in csv.DictReader(open(os.path.join(PROJ, 'data', 'seongnam_stop_frequency.csv'), encoding='utf-8-sig'))}
sxy = np.array([to_tm(float(F[s['정류장번호']]['위도']), float(F[s['정류장번호']]['경도'])) for s in stops])
sfq = np.array([int(s['도내노선_운행횟수']) for s in stops])
cellxy = np.c_[x0 + np.where(mask)[1] * cell, y0 + np.where(mask)[0] * cell]
ctree = cKDTree(cellxy)
sd, snode = ctree.query(sxy, distance_upper_bound=40)
valid = np.isfinite(sd)
print(f'도로망에 연결된 정류장 {valid.sum()}/{len(stops)}')

# 4) 고령인구 격자
r = shapefile.Reader(glob.glob(os.path.join(PROJ, 'data', 'raw', 'ngii_pop', '**', 'vl_blk.shp'), recursive=True)[0][:-4], encoding='utf-8')
PXY, POP = [], []
for shp, rec in zip(r.shapes(), r.records()):
    if not rec['val']:
        continue
    xs = [p[0] for p in shp.points]; ys = [p[1] for p in shp.points]
    lat, lon = to_latlon((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2, **UTMK)
    PXY.append(to_tm(lat, lon)); POP.append(rec['val'])
PXY, POP = np.array(PXY), np.array(POP)
pd_, pnode = ctree.query(PXY, distance_upper_bound=80)
pok = np.isfinite(pd_)
print(f'도로망에 연결된 격자 {pok.sum()}/{len(POP)} (노인 {POP[pok].sum():,.0f}명)')

# 5) 완만한 길만으로 정류장에 닿는가
res = {}
for name, limit, src in (('보행 8.33% 이하', WALK_LIMIT, snode[valid]),
                         ('보행 제한 없음', 100.0, snode[valid])):
    dist = dijkstra(graph(limit), indices=src.astype(int), min_only=True, unweighted=False)
    res[name] = dist
    reach = np.where(pok, dist[pnode.clip(0, N - 1)], np.inf)
    good = POP[pok & (reach <= WALK_MAX)].sum()
    print(f'{name}: {WALK_MAX:.0f}m 안에 정류장 도달 가능 노인 {good:,.0f}명 ({good / POP[pok].sum() * 100:.0f}%)')

flat = np.where(pok, res['보행 8.33% 이하'][pnode.clip(0, N - 1)], np.inf)
anyp = np.where(pok, res['보행 제한 없음'][pnode.clip(0, N - 1)], np.inf)
barred = pok & (anyp <= WALK_MAX) & (flat > WALK_MAX)
print(f'\n정류장은 가까우나 완만한 길이 없는 노인: {POP[barred].sum():,.0f}명')
np.savez_compressed(os.path.join(PROJ, 'data', 'seongnam_walk_paths.npz'),
                    pop=POP, xy=PXY, flat=flat, anyp=anyp, ok=pok)

# 6) 버스가 완만하게 올라갈 수 있는가 (간선 정류장 출발)
trunk = valid & (sfq >= TRUNK)
bus = dijkstra(graph(BUS_LIMIT), indices=snode[trunk].astype(int), min_only=True, unweighted=False)
busd = np.where(pok, bus[pnode.clip(0, N - 1)], np.inf)
for lim in (500, 1000, 1500):
    print(f'간선에서 {BUS_LIMIT:.0f}% 이하 도로로 {lim}m 안에 닿는 곳의 노인: {POP[pok & (busd <= lim)].sum():,.0f}명')
np.savez_compressed(os.path.join(PROJ, 'data', 'seongnam_bus_climb.npz'), pop=POP, xy=PXY, busd=busd, ok=pok)
