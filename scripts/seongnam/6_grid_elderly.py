"""100m 격자 고령인구 × 지형 → 노인이 실제로 언덕 위에 사는가."""
import csv, glob, io, json, os, sys
import numpy as np
import shapefile
from scipy.spatial import cKDTree

sys.path.insert(0, os.path.dirname(__file__))
from tm import to_tm, to_latlon, UTMK

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
PROJ = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
RADIUS = 300.0
LIMIT = 8.33

# 1) 격자 고령인구 (국토지리정보원 국토통계, 100m, 2025-10) → 지도 좌표계로
src = glob.glob(os.path.join(PROJ, 'data', 'raw', 'ngii_pop', '**', 'vl_blk.shp'), recursive=True)[0]
r = shapefile.Reader(src[:-4], encoding='utf-8')
cx, cy, pop = [], [], []
for shp, rec in zip(r.shapes(), r.records()):
    if not rec['val']:
        continue
    xs = [p[0] for p in shp.points]; ys = [p[1] for p in shp.points]
    lat, lon = to_latlon((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2, **UTMK)
    x, y = to_tm(lat, lon)
    cx.append(x); cy.append(y); pop.append(rec['val'])
cx, cy, pop = np.array(cx), np.array(cy), np.array(pop)
print(f'격자 {len(pop):,}개 | 고령인구 합계 {pop.sum():,.0f}명')

# 2) 격자마다 지형 고도
d = np.load(os.path.join(PROJ, 'data', 'seongnam_dem10m.npz'))
dem, x0, y0, cell = d['dem'], float(d['x0']), float(d['y0']), float(d['cell'])
gi = np.round((cy - y0) / cell).astype(int)
gj = np.round((cx - x0) / cell).astype(int)
inside = (gi >= 0) & (gi < dem.shape[0]) & (gj >= 0) & (gj < dem.shape[1])
z = np.full(len(pop), np.nan)
z[inside] = dem[gi[inside], gj[inside]]
ok = np.isfinite(z)
print(f'고도 확인된 격자 {ok.sum():,} ({pop[ok].sum() / pop.sum() * 100:.1f}%의 노인 인구)')

# 3) 행정동 부여
feats = json.load(open(os.path.join(PROJ, 'data', 'seongnam_admdong_20260701.geojson'), encoding='utf-8'))['features']


def in_ring(x, y, ring):
    inside = False
    j = len(ring) - 1
    for i in range(len(ring)):
        if (ring[i][1] > y) != (ring[j][1] > y) and x < (ring[j][0] - ring[i][0]) * (y - ring[i][1]) / (ring[j][1] - ring[i][1]) + ring[i][0]:
            inside = not inside
        j = i
    return inside


dong = []
for k in range(len(pop)):
    lat, lon = to_latlon(cx[k], cy[k])
    hit = next((f for f in feats if any(in_ring(lon, lat, poly[0]) for poly in f['geometry']['coordinates'])), None)
    p = hit['properties'] if hit else {}
    dong.append((p.get('sggnm', '').replace('성남시', ''), p.get('adm_nm', '').split()[-1] if hit else ''))

# 4) 정류장: 가장 가까운 정류장까지의 직선 경사
stops = [s for s in csv.DictReader(open(os.path.join(PROJ, 'data', 'seongnam_stop_slope.csv'), encoding='utf-8-sig'))
         if s['미정차'] == 'N']
latlon = {s['정류장번호']: (float(s['위도']), float(s['경도'])) for s in
          csv.DictReader(open(os.path.join(PROJ, 'data', 'seongnam_stop_frequency.csv'), encoding='utf-8-sig'))}
sxy = np.array([to_tm(*latlon[s['정류장번호']]) for s in stops])
sz = np.array([float(s['고도_m']) for s in stops])
tree = cKDTree(sxy)
dist, idx = tree.query(np.c_[cx, cy])
grade = np.abs(z - sz[idx]) / np.maximum(dist, 1) * 100

# 5) 집계
rows = []
for k in range(len(pop)):
    rows.append({'구': dong[k][0], '행정동': dong[k][1], '고령인구': pop[k],
                 '고도_m': round(float(z[k]), 1) if ok[k] else '',
                 '최근접정류장_거리_m': round(float(dist[k])),
                 '최근접정류장': stops[idx[k]]['정류장명'],
                 '정류장까지_경사_%': round(float(grade[k]), 1) if ok[k] else ''})
dst = os.path.join(PROJ, 'data', 'seongnam_grid_elderly.csv')
with open(dst, 'w', encoding='utf-8-sig', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
print('saved', dst)

steep = ok & (grade > LIMIT)
print(f'\n[성남 전체] 고도 확인된 노인 {pop[ok].sum():,.0f}명 중 '
      f'가장 가까운 정류장까지 {LIMIT}% 초과: {pop[steep].sum():,.0f}명 ({pop[steep].sum() / pop[ok].sum() * 100:.1f}%)')
print(f"{'구':<6}{'노인':>9}{'가파른곳 노인':>12}{'비율':>7}{'평균거리':>8}")
gu = np.array([d0 for d0, _ in dong])
for g in ['수정구', '중원구', '분당구']:
    m = ok & (gu == g)
    s = m & (grade > LIMIT)
    print(f'{g:<6}{pop[m].sum():>9,.0f}{pop[s].sum():>12,.0f}{pop[s].sum() / pop[m].sum() * 100:>6.1f}%{np.average(dist[m], weights=pop[m]):>8.0f}m')

print(f"\n[동별 상위 12]  {'동':<8}{'노인':>7}{'가파른곳':>8}{'비율':>7}")
dn = np.array([d1 for _, d1 in dong])
out = []
for name in set(dn):
    m = ok & (dn == name)
    if pop[m].sum() < 300:
        continue
    s = m & (grade > LIMIT)
    out.append((pop[s].sum() / pop[m].sum() * 100, name, pop[m].sum(), pop[s].sum(), gu[m][0]))
for ratio, name, tot, st, g in sorted(out, reverse=True)[:12]:
    print(f'  {g} {name:<8}{tot:>7,.0f}{st:>8,.0f}{ratio:>6.1f}%')
