"""수치지도 1:5000 등고선·표고점 → 10m 격자 지형고도(DEM). 건물 높이 미포함."""
import glob, io, os, sys
import numpy as np
from scipy.interpolate import griddata
from scipy.spatial import cKDTree

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
PROJ = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
RAW = os.path.join(PROJ, 'data', 'raw', 'ngii')
CELL = 10.0          # m
MAX_GAP = 150.0      # 입력점에서 이보다 먼 셀은 비움(도엽 없는 곳)
DENSIFY = 10.0       # 등고선 꼭짓점 간격 최대


def entities(path):
    lines = [l.strip() for l in open(path, encoding='cp949', errors='replace').read().splitlines()]
    ent = None
    for code, val in zip(lines[0::2], lines[1::2]):
        if code == '0':
            if ent:
                yield ent
            ent = {'type': val, 'codes': []}
        elif ent is not None:
            ent['codes'].append((code, val))
    if ent:
        yield ent


contour, spot = [], []
sheets = sorted(glob.glob(os.path.join(RAW, '*.dxf')))
for path in sheets:
    for e in entities(path):
        layer = next((v for c, v in e['codes'] if c == '8'), '')
        if e['type'] == 'LWPOLYLINE' and layer.startswith('F00171'):
            z = next((float(v) for c, v in e['codes'] if c == '38'), 0.0)
            if z <= 0:
                continue
            xs = [float(v) for c, v in e['codes'] if c == '10']
            ys = [float(v) for c, v in e['codes'] if c == '20']
            for i in range(len(xs) - 1):
                n = max(1, int(np.hypot(xs[i + 1] - xs[i], ys[i + 1] - ys[i]) // DENSIFY))
                for k in range(n):
                    t = k / n
                    contour.append((xs[i] + t * (xs[i + 1] - xs[i]), ys[i] + t * (ys[i + 1] - ys[i]), z))
            if xs:
                contour.append((xs[-1], ys[-1], z))
        elif e['type'] == 'TEXT' and layer == 'F0027132':
            try:
                z = float(next(v for c, v in e['codes'] if c == '1'))
                x = float(next(v for c, v in e['codes'] if c == '10'))
                y = float(next(v for c, v in e['codes'] if c == '20'))
            except (StopIteration, ValueError):
                continue
            if z > 0:
                spot.append((x, y, z))

contour, spot = np.array(contour), np.array(spot)
print(f'도엽 {len(sheets)}장 | 등고선 점 {len(contour):,} | 표고점 {len(spot):,}')

xmin, ymin = np.floor(np.r_[contour[:, :2], spot[:, :2]].min(0) / CELL) * CELL
xmax, ymax = np.ceil(np.r_[contour[:, :2], spot[:, :2]].max(0) / CELL) * CELL
gx = np.arange(xmin, xmax + CELL, CELL)
gy = np.arange(ymin, ymax + CELL, CELL)
GX, GY = np.meshgrid(gx, gy)


def build(points):
    dem = griddata(points[:, :2], points[:, 2], (GX, GY), method='linear')
    dist, _ = cKDTree(points[:, :2]).query(np.c_[GX.ravel(), GY.ravel()], distance_upper_bound=MAX_GAP)
    dem[np.isinf(dist).reshape(dem.shape)] = np.nan
    return dem


# 검증: 표고점 20%를 빼고 만든 뒤 빼둔 점에서 오차 측정
rng = np.random.default_rng(0)
hold = rng.random(len(spot)) < 0.2
dem_cv = build(np.r_[contour, spot[~hold]])
hx = ((spot[hold, 0] - xmin) / CELL).round().astype(int)
hy = ((spot[hold, 1] - ymin) / CELL).round().astype(int)
pred = dem_cv[hy, hx]
ok = ~np.isnan(pred)
err = pred[ok] - spot[hold, 2][ok]
print(f'검증(빼둔 표고점 {ok.sum():,}개): 평균오차 {err.mean():+.2f}m | 절대오차 중앙값 {np.median(abs(err)):.2f}m | '
      f'90%가 ±{np.percentile(abs(err), 90):.1f}m 이내')

dem = build(np.r_[contour, spot])
dst = os.path.join(PROJ, 'data', 'seongnam_dem10m.npz')
np.savez_compressed(dst, dem=dem.astype(np.float32), x0=xmin, y0=ymin, cell=CELL)
print(f'격자 {dem.shape[1]}×{dem.shape[0]} | 유효 {np.isfinite(dem).mean() * 100:.0f}% | '
      f'고도 {np.nanmin(dem):.0f}~{np.nanmax(dem):.0f}m | saved {dst}')
