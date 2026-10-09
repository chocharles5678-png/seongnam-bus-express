"""1단계: 기존 노선이 지나가지만 정류장이 없는 지점 → 정류장 신설 후보."""
import csv, glob, io, json, os, sys
import numpy as np
import shapefile
from scipy.spatial import cKDTree

sys.path.insert(0, os.path.dirname(__file__))
from tm import to_tm, to_latlon, UTMK

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
PROJ = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
LIMIT = 8.33
MIN_GAP = 150.0      # 기존 정류장과 이만큼은 떨어져야 신설 의미
CLUSTER = 150.0      # 후보 지점 묶는 반경
MAX_SEG = 500.0      # 이보다 긴 정류장 간 구간은 직선 근사 신뢰 불가

# 1) 노선 경로 복원 (정류장 순서를 직선으로 연결)
info = {}
for f in glob.glob(os.path.join(PROJ, 'data', 'raw', 'gg_busroute', 'getBusRouteInfoItemv2_*.json')):
    i = json.load(open(f, encoding='utf-8'))['response']['msgBody']['busRouteInfoItem']
    info[i['routeId']] = i
A, B, RID = [], [], []
for f in glob.glob(os.path.join(PROJ, 'data', 'raw', 'gg_busroute', 'getBusRouteStationListv2_*.json')):
    rid = int(os.path.basename(f).split('_')[1].split('.')[0])
    body = json.load(open(f, encoding='utf-8'))['response']['msgBody'] or {}
    S = body.get('busRouteStationList', [])
    S = sorted([s for s in (S if isinstance(S, list) else [S]) if s.get('x') and s.get('y')], key=lambda s: s['stationSeq'])
    pts = [to_tm(float(s['y']), float(s['x'])) for s in S]
    t = info.get(rid, {}).get('routeTypeName', '')
    if any(k in t for k in ('공항', '시외')):       # 동네 정류장에 서지 않는 노선 제외
        continue
    for p, q in zip(pts, pts[1:]):
        # 정류장 간격이 먼 구간은 직선 근사가 지형을 가로질러 버리므로 제외
        if np.hypot(q[0] - p[0], q[1] - p[1]) < MAX_SEG:
            A.append(p); B.append(q); RID.append(rid)
A, B, RID = np.array(A), np.array(B), np.array(RID)

# 2) 격자 고령인구
r = shapefile.Reader(glob.glob(os.path.join(PROJ, 'data', 'raw', 'ngii_pop', '**', 'vl_blk.shp'), recursive=True)[0][:-4], encoding='utf-8')
XY, POP = [], []
for shp, rec in zip(r.shapes(), r.records()):
    if not rec['val']:
        continue
    xs = [p[0] for p in shp.points]; ys = [p[1] for p in shp.points]
    lat, lon = to_latlon((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2, **UTMK)
    XY.append(to_tm(lat, lon)); POP.append(rec['val'])
XY, POP = np.array(XY), np.array(POP)

# 3) 지형
d = np.load(os.path.join(PROJ, 'data', 'seongnam_dem10m.npz'))
dem, x0, y0, cell = d['dem'], float(d['x0']), float(d['y0']), float(d['cell'])


def z_at(x, y):
    i = np.round((y - y0) / cell).astype(int); j = np.round((x - x0) / cell).astype(int)
    ok = (i >= 0) & (i < dem.shape[0]) & (j >= 0) & (j < dem.shape[1])
    out = np.full(np.shape(x), np.nan); out[ok] = dem[i[ok], j[ok]]
    return out


Z = z_at(XY[:, 0], XY[:, 1])

# 4) 기존 정류장까지 경사
stops = [s for s in csv.DictReader(open(os.path.join(PROJ, 'data', 'seongnam_stop_slope.csv'), encoding='utf-8-sig')) if s['미정차'] == 'N']
F = {s['정류장번호']: s for s in csv.DictReader(open(os.path.join(PROJ, 'data', 'seongnam_stop_frequency.csv'), encoding='utf-8-sig'))}
sxy = np.array([to_tm(float(F[s['정류장번호']]['위도']), float(F[s['정류장번호']]['경도'])) for s in stops])
sz = np.array([float(s['고도_m']) for s in stops])
stree = cKDTree(sxy)
sd, si = stree.query(XY)
g_stop = np.abs(Z - sz[si]) / np.maximum(sd, 1) * 100

# 5) 가장 가까운 노선 경로 위의 지점
AB = B - A; L2 = (AB ** 2).sum(1); L2[L2 == 0] = 1
near_d = np.full(len(XY), 1e9); near_p = np.zeros((len(XY), 2)); near_r = np.zeros(len(XY), int)
for i in range(0, len(XY), 200):
    P = XY[i:i + 200]
    t = np.clip(((P[:, None, :] - A[None]) * AB[None]).sum(2) / L2[None], 0, 1)
    proj = A[None] + t[:, :, None] * AB[None]
    dist = np.hypot(proj[:, :, 0] - P[:, None, 0], proj[:, :, 1] - P[:, None, 1])
    k = dist.argmin(1); idx = np.arange(len(P))
    near_d[i:i + 200] = dist[idx, k]; near_p[i:i + 200] = proj[idx, k]; near_r[i:i + 200] = RID[k]
g_route = np.abs(Z - z_at(near_p[:, 0], near_p[:, 1])) / np.maximum(near_d, 1) * 100

# 6) 대상: 정류장은 가파른데 노선 경로는 완만 + 기존 정류장과 충분히 떨어짐
target = np.isfinite(g_stop) & np.isfinite(g_route) & (g_stop > LIMIT) & (g_route <= LIMIT)
proj_stop_d, _ = stree.query(near_p)
steep = np.isfinite(g_stop) & np.isfinite(g_route) & (g_stop > LIMIT)
print(f'정류장 기준 언덕 위 노인 {POP[steep].sum():,.0f}명')
print(f'  ├ 노선 경로는 완만: {POP[steep & (g_route <= LIMIT)].sum():,.0f}명')
print(f'  └ 노선 경로도 가파름: {POP[steep & (g_route > LIMIT)].sum():,.0f}명')
target &= proj_stop_d >= MIN_GAP
print(f'그중 기존 정류장과 {MIN_GAP:.0f}m 이상 떨어져 신설 여지가 있는 대상: {POP[target].sum():,.0f}명 (격자 {target.sum()}개)')

# 7) 후보 지점 묶기
order = np.argsort(-POP * target)
used = np.zeros(len(XY), bool)
cands = []
for k in order:
    if not target[k] or used[k]:
        continue
    m = target & ~used & (np.hypot(near_p[:, 0] - near_p[k, 0], near_p[:, 1] - near_p[k, 1]) <= CLUSTER)
    if POP[m].sum() <= 0:
        continue
    used |= m
    px, py = near_p[m].mean(0)
    lat, lon = to_latlon(px, py)
    routes = sorted({str(info[r_]['routeName']) for r_ in near_r[m] if r_ in info})
    types = {info[r_]['routeTypeName'] for r_ in near_r[m] if r_ in info}
    cands.append({'위도': round(lat, 6), '경도': round(lon, 6), '담당_노인': round(float(POP[m].sum())),
                  '격자수': int(m.sum()), '고도_m': round(float(z_at(np.array([px]), np.array([py]))[0]), 1),
                  '현_정류장까지_경사': round(float(np.average(g_stop[m], weights=POP[m])), 1),
                  '후보까지_경사': round(float(np.average(g_route[m], weights=POP[m])), 1),
                  '후보까지_거리_m': round(float(np.average(near_d[m], weights=POP[m]))),
                  '기존정류장_거리_m': round(float(stree.query(np.array([[px, py]]))[0][0])),
                  '경유노선': ' '.join(routes[:6]), '노선유형': '·'.join(sorted(types))})

# 8) 행정동 부여
feats = json.load(open(os.path.join(PROJ, 'data', 'seongnam_admdong_20260701.geojson'), encoding='utf-8'))['features']


def in_ring(x, y, ring):
    inside = False; j = len(ring) - 1
    for i in range(len(ring)):
        if (ring[i][1] > y) != (ring[j][1] > y) and x < (ring[j][0] - ring[i][0]) * (y - ring[i][1]) / (ring[j][1] - ring[i][1]) + ring[i][0]:
            inside = not inside
        j = i
    return inside


for c in cands:
    hit = next((f for f in feats if any(in_ring(c['경도'], c['위도'], p[0]) for p in f['geometry']['coordinates'])), None)
    p = hit['properties'] if hit else {}
    c['구'] = p.get('sggnm', '').replace('성남시', ''); c['행정동'] = p.get('adm_nm', '').split()[-1] if hit else ''

cands.sort(key=lambda c: -c['담당_노인'])
dst = os.path.join(PROJ, 'data', 'seongnam_new_stop_candidates.csv')
cols = ['구', '행정동', '위도', '경도', '담당_노인', '고도_m', '현_정류장까지_경사', '후보까지_경사',
        '후보까지_거리_m', '기존정류장_거리_m', '경유노선', '노선유형', '격자수']
with open(dst, 'w', encoding='utf-8-sig', newline='') as f:
    w = csv.DictWriter(f, fieldnames=cols, extrasaction='ignore'); w.writeheader(); w.writerows(cands)
print(f'후보 지점 {len(cands)}곳 | 상위 20곳이 {sum(c["담당_노인"] for c in cands[:20]):,}명 담당 | saved {dst}')
print(f"\n{'#':<3}{'구':<5}{'행정동':<8}{'담당노인':>6}{'현경사':>7}{'후보경사':>7}{'기존정류장':>8}  경유노선")
for i, c in enumerate(cands[:20], 1):
    print(f"{i:<3}{c['구']:<5}{c['행정동']:<8}{c['담당_노인']:>6}{c['현_정류장까지_경사']:>6}%{c['후보까지_경사']:>6}%{c['기존정류장_거리_m']:>7}m  {c['경유노선'][:34]} ({c['노선유형'][:14]})")
