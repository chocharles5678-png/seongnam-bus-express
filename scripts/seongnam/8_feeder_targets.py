"""2단계: 노선이 닿지 않는 언덕 위 주거지 → 지선이 올라가야 할 목적지."""
import csv, glob, io, json, os, sys
import numpy as np
import shapefile
from scipy.spatial import cKDTree

sys.path.insert(0, os.path.dirname(__file__))
from tm import to_tm, to_latlon, UTMK

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
PROJ = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
LIMIT = 8.33
MAX_SEG = 500.0
CLUSTER = 250.0        # 언덕 위 주거지를 묶는 반경
TRUNK = 200            # 하루 이 이상 운행하면 간선으로 본다
BUS_MAX = 12.0         # 버스가 상시 운행 가능한 도로 종단경사 한계(%)

info = {}
for f in glob.glob(os.path.join(PROJ, 'data', 'raw', 'gg_busroute', 'getBusRouteInfoItemv2_*.json')):
    i = json.load(open(f, encoding='utf-8'))['response']['msgBody']['busRouteInfoItem']
    info[i['routeId']] = i
A, B = [], []
for f in glob.glob(os.path.join(PROJ, 'data', 'raw', 'gg_busroute', 'getBusRouteStationListv2_*.json')):
    rid = int(os.path.basename(f).split('_')[1].split('.')[0])
    if any(k in info.get(rid, {}).get('routeTypeName', '') for k in ('공항', '시외')):
        continue
    body = json.load(open(f, encoding='utf-8'))['response']['msgBody'] or {}
    S = body.get('busRouteStationList', [])
    S = sorted([s for s in (S if isinstance(S, list) else [S]) if s.get('x') and s.get('y')], key=lambda s: s['stationSeq'])
    pts = [to_tm(float(s['y']), float(s['x'])) for s in S]
    for p, q in zip(pts, pts[1:]):
        if np.hypot(q[0] - p[0], q[1] - p[1]) < MAX_SEG:
            A.append(p); B.append(q)
A, B = np.array(A), np.array(B)

r = shapefile.Reader(glob.glob(os.path.join(PROJ, 'data', 'raw', 'ngii_pop', '**', 'vl_blk.shp'), recursive=True)[0][:-4], encoding='utf-8')
XY, POP = [], []
for shp, rec in zip(r.shapes(), r.records()):
    if not rec['val']:
        continue
    xs = [p[0] for p in shp.points]; ys = [p[1] for p in shp.points]
    lat, lon = to_latlon((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2, **UTMK)
    XY.append(to_tm(lat, lon)); POP.append(rec['val'])
XY, POP = np.array(XY), np.array(POP)

d = np.load(os.path.join(PROJ, 'data', 'seongnam_dem10m.npz'))
dem, x0, y0, cell = d['dem'], float(d['x0']), float(d['y0']), float(d['cell'])


def z_at(x, y):
    i = np.round((y - y0) / cell).astype(int); j = np.round((x - x0) / cell).astype(int)
    ok = (i >= 0) & (i < dem.shape[0]) & (j >= 0) & (j < dem.shape[1])
    out = np.full(np.shape(x), np.nan); out[ok] = dem[i[ok], j[ok]]
    return out


Z = z_at(XY[:, 0], XY[:, 1])
stops = [s for s in csv.DictReader(open(os.path.join(PROJ, 'data', 'seongnam_stop_slope.csv'), encoding='utf-8-sig')) if s['미정차'] == 'N']
F = {s['정류장번호']: s for s in csv.DictReader(open(os.path.join(PROJ, 'data', 'seongnam_stop_frequency.csv'), encoding='utf-8-sig'))}
sxy = np.array([to_tm(float(F[s['정류장번호']]['위도']), float(F[s['정류장번호']]['경도'])) for s in stops])
sz = np.array([float(s['고도_m']) for s in stops])
sfq = np.array([int(s['도내노선_운행횟수']) for s in stops])
sd, si = cKDTree(sxy).query(XY)
g_stop = np.abs(Z - sz[si]) / np.maximum(sd, 1) * 100

AB = B - A; L2 = (AB ** 2).sum(1); L2[L2 == 0] = 1
near_d = np.full(len(XY), 1e9); near_p = np.zeros((len(XY), 2))
for i in range(0, len(XY), 200):
    P = XY[i:i + 200]
    t = np.clip(((P[:, None, :] - A[None]) * AB[None]).sum(2) / L2[None], 0, 1)
    proj = A[None] + t[:, :, None] * AB[None]
    dist = np.hypot(proj[:, :, 0] - P[:, None, 0], proj[:, :, 1] - P[:, None, 1])
    k = dist.argmin(1); idx = np.arange(len(P))
    near_d[i:i + 200] = dist[idx, k]; near_p[i:i + 200] = proj[idx, k]
g_route = np.abs(Z - z_at(near_p[:, 0], near_p[:, 1])) / np.maximum(near_d, 1) * 100

target = np.isfinite(g_stop) & np.isfinite(g_route) & (g_stop > LIMIT) & (g_route > LIMIT)
print(f'2단계 대상: 노선도 닿지 않는 언덕 위 노인 {POP[target].sum():,.0f}명 (격자 {target.sum()}개)')

# 간선 정류장 (접속점 후보)
trunk = sfq >= TRUNK
ttree = cKDTree(sxy[trunk]); tz = sz[trunk]
tname = [stops[i]['정류장명'] for i in np.where(trunk)[0]]

feats = json.load(open(os.path.join(PROJ, 'data', 'seongnam_admdong_20260701.geojson'), encoding='utf-8'))['features']


def in_ring(x, y, ring):
    inside = False; j = len(ring) - 1
    for i in range(len(ring)):
        if (ring[i][1] > y) != (ring[j][1] > y) and x < (ring[j][0] - ring[i][0]) * (y - ring[i][1]) / (ring[j][1] - ring[i][1]) + ring[i][0]:
            inside = not inside
        j = i
    return inside


order = np.argsort(-POP * target)
used = np.zeros(len(XY), bool)
rows = []
for k in order:
    if not target[k] or used[k]:
        continue
    m = target & ~used & (np.hypot(XY[:, 0] - XY[k, 0], XY[:, 1] - XY[k, 1]) <= CLUSTER)
    used |= m
    px, py = np.average(XY[m], axis=0, weights=POP[m])
    pz = float(z_at(np.array([px]), np.array([py]))[0])
    td, ti = ttree.query(np.array([[px, py]]))
    td, ti = float(td[0]), int(ti[0])
    climb = pz - float(tz[ti])                      # 간선 정류장에서 올라야 할 높이
    lat, lon = to_latlon(px, py)
    hit = next((f for f in feats if any(in_ring(lon, lat, p[0]) for p in f['geometry']['coordinates'])), None)
    p = hit['properties'] if hit else {}
    rows.append({'구': p.get('sggnm', '').replace('성남시', ''), '행정동': p.get('adm_nm', '').split()[-1] if hit else '',
                 '위도': round(lat, 6), '경도': round(lon, 6), '노인': round(float(POP[m].sum())), '격자수': int(m.sum()),
                 '고도_m': round(pz), '간선정류장': tname[ti], '간선까지_거리_m': round(td),
                 '올라야_할_높이_m': round(climb), '평균_등판경사_%': round(abs(climb) / max(td, 1) * 100, 1),
                 '버스운행_가능': 'O' if abs(climb) / max(td, 1) * 100 <= BUS_MAX else '△',
                 '현_도보경사_%': round(float(np.average(g_stop[m], weights=POP[m])), 1)})

rows.sort(key=lambda x: -x['노인'])
dst = os.path.join(PROJ, 'data', 'seongnam_feeder_targets.csv')
with open(dst, 'w', encoding='utf-8-sig', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
print(f'언덕 위 주거지 묶음 {len(rows)}개 | 상위 20개가 {sum(x["노인"] for x in rows[:20]):,}명 담당 | saved {dst}')
print(f"\n{'#':<3}{'구':<5}{'행정동':<8}{'노인':>6}{'고도':>6}{'등판높이':>7}{'거리':>6}{'등판경사':>7}{'가능':>4}  간선 접속점")
for i, x in enumerate(rows[:20], 1):
    print(f"{i:<3}{x['구']:<5}{x['행정동']:<8}{x['노인']:>6}{x['고도_m']:>5}m{x['올라야_할_높이_m']:>+6}m{x['간선까지_거리_m']:>5}m"
          f"{x['평균_등판경사_%']:>6}%{x['버스운행_가능']:>4}  {x['간선정류장'][:24]}")
ok = [x for x in rows if x['버스운행_가능'] == 'O']
print(f"\n버스 등판 가능(≤{BUS_MAX}%) 묶음 {len(ok)}개 / 노인 {sum(x['노인'] for x in ok):,}명 "
      f"({sum(x['노인'] for x in ok) / sum(x['노인'] for x in rows) * 100:.0f}%)")
