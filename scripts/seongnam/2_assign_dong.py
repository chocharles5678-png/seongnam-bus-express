"""성남 정류장에 구·행정동 부여 (행정동 경계 ver20260701, point-in-polygon)."""
import csv, io, json, os, sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
PROJ = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
RAW = os.path.join(PROJ, 'data', 'raw')

feats = [f for f in json.load(open(os.path.join(RAW, 'admdong_20260701.geojson'), encoding='utf-8'))['features']
         if f['properties']['sggnm'].startswith('성남시')]
json.dump({'type': 'FeatureCollection', 'features': feats},
          open(os.path.join(PROJ, 'data', 'seongnam_admdong_20260701.geojson'), 'w', encoding='utf-8'), ensure_ascii=False)


def in_ring(x, y, ring):
    inside = False
    j = len(ring) - 1
    for i in range(len(ring)):
        xi, yi = ring[i][0], ring[i][1]
        xj, yj = ring[j][0], ring[j][1]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi:
            inside = not inside
        j = i
    return inside


def in_feat(x, y, f):
    for poly in f['geometry']['coordinates']:        # MultiPolygon
        if in_ring(x, y, poly[0]) and not any(in_ring(x, y, h) for h in poly[1:]):
            return True
    return False


path = os.path.join(PROJ, 'data', 'seongnam_stop_frequency.csv')
rows = list(csv.DictReader(open(path, encoding='utf-8-sig')))
miss = []
for r in rows:
    x, y = float(r['경도']), float(r['위도'])
    hit = next((f for f in feats if in_feat(x, y, f)), None)
    p = hit['properties'] if hit else {}
    r['구'] = p.get('sggnm', '').replace('성남시', '')
    r['행정동'] = p.get('adm_nm', '').split()[-1] if p else ''
    r['행정동코드'] = p.get('adm_cd2', '')
    if not hit:
        miss.append(r['정류장명'])
print('구 미부여:', len(miss), miss[:10])

with open(path, 'w', encoding='utf-8-sig', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
print('saved', path)
