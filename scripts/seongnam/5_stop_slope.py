"""정류장 반경 300m 안의 건물(=사람 사는 곳) 기준 경사 지표."""
import csv, glob, io, os, sys
import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
from tm import to_tm

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
PROJ = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
RADIUS = 300.0       # m, 교통약자 도보권
LIMIT = 8.33         # %, 경사로 기준 1/12

d = np.load(os.path.join(PROJ, 'data', 'seongnam_dem10m.npz'))
dem, x0, y0, cell = d['dem'], float(d['x0']), float(d['y0']), float(d['cell'])
gy, gx = np.gradient(dem, cell)
slope = np.hypot(gx, gy) * 100

# 건물 위치: 수치지도 B001(건물) 폴리곤 중심 → 격자 셀 표시
built = np.zeros(dem.shape, bool)
for path in glob.glob(os.path.join(PROJ, 'data', 'raw', 'ngii', '*.dxf')):
    lines = [l.strip() for l in open(path, encoding='cp949', errors='replace').read().splitlines()]
    layer, xs, ys, in_poly = '', [], [], False
    for code, val in list(zip(lines[0::2], lines[1::2])) + [('0', 'EOF')]:
        if code == '0':
            if in_poly and layer.startswith('B001') and xs:
                c = int((np.mean(ys) - y0) / cell), int((np.mean(xs) - x0) / cell)
                if 0 <= c[0] < dem.shape[0] and 0 <= c[1] < dem.shape[1]:
                    built[c] = True
            in_poly, layer, xs, ys = val == 'LWPOLYLINE', '', [], []
        elif in_poly:
            if code == '8':
                layer = val
            elif code == '10':
                xs.append(float(val))
            elif code == '20':
                ys.append(float(val))
print(f'건물 있는 셀: {built.sum():,}')

r = int(RADIUS / cell)
yy, xx = np.mgrid[-r:r + 1, -r:r + 1]
dist = np.hypot(yy, xx) * cell
disk = (dist <= RADIUS) & (dist > 0)

path = os.path.join(PROJ, 'data', 'seongnam_stop_frequency.csv')
stops = list(csv.DictReader(open(path, encoding='utf-8-sig')))
out = []
for s in stops:
    x, y = to_tm(float(s['위도']), float(s['경도']))
    ci, cj = int(round((y - y0) / cell)), int(round((x - x0) / cell))
    if not (r <= ci < dem.shape[0] - r and r <= cj < dem.shape[1] - r) or np.isnan(dem[ci, cj]):
        continue
    win = (slice(ci - r, ci + r + 1), slice(cj - r, cj + r + 1))
    m = disk & built[win] & np.isfinite(dem[win])
    if m.sum() < 5:
        continue
    z0 = dem[ci, cj]
    rise = dem[win][m] - z0
    grade = np.abs(rise) / dist[m] * 100          # 집 ↔ 정류장 직선 경사
    out.append({'정류장번호': s['정류장번호'], '정류장명': s['정류장명'], '구': s['구'], '행정동': s['행정동'],
                '미정차': s['미정차'], '도내노선_운행횟수': s['도내노선_운행횟수'], '동_고령비율': s['동_고령비율'],
                '고도_m': round(float(z0), 1),
                '건물수_300m': int(m.sum()),
                '주변지형경사_중앙값': round(float(np.median(slope[win][m])), 1),
                '정류장까지경사_중앙값': round(float(np.median(grade)), 1),
                '정류장까지_8.33초과_비율': round(float((grade > LIMIT).mean() * 100), 1),
                '최대고도차_m': round(float(np.abs(rise).max()), 1)})

dst = os.path.join(PROJ, 'data', 'seongnam_stop_slope.csv')
with open(dst, 'w', encoding='utf-8-sig', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(out[0].keys())); w.writeheader(); w.writerows(out)
print(f'계산된 정류장 {len(out)} / 전체 {len(stops)} | saved {dst}')
