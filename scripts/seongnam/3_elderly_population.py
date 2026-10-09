"""성남 행정동별 65세 이상 인구 × 정류장 운행횟수 결합."""
import csv, io, json, os, re, sys
from collections import defaultdict

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
PROJ = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
RAW = os.path.join(PROJ, 'data', 'raw')

# 1) 행정동 인구 (행정안전부 주민등록, 2026-08-31)
rows = list(csv.reader(open(os.path.join(RAW, 'pop_dong_202608.csv'), encoding='cp949')))
head = rows[0]
old_cols = [i for i, h in enumerate(head) if (m := re.match(r'(\d+)세', h)) and int(m.group(1)) >= 65]
pop = {}
for r in rows[1:]:
    if r[3].startswith('성남시') and r[4]:
        total = int(r[5].replace(',', ''))
        old = sum(int(r[i].replace(',', '') or 0) for i in old_cols)
        pop[r[0]] = {'구': r[3].replace('성남시 ', ''), '행정동': r[4], '총인구': total, '65세이상': old}

# 2) 경계 코드와 대조
codes = {f['properties']['adm_cd2']: f['properties']['adm_nm'].split()[-1] for f in
         json.load(open(os.path.join(PROJ, 'data', 'seongnam_admdong_20260701.geojson'), encoding='utf-8'))['features']}
print('인구 동:', len(pop), '/ 경계 동:', len(codes),
      '/ 경계에만:', [codes[c] for c in codes if c not in pop], '/ 인구에만:', [pop[c]['행정동'] for c in pop if c not in codes])

# 3) 정류장에 동 인구 부착 + 동별 집계
path = os.path.join(PROJ, 'data', 'seongnam_stop_frequency.csv')
stops = list(csv.DictReader(open(path, encoding='utf-8-sig')))
agg = defaultdict(list)
for s in stops:
    p = pop.get(s['행정동코드'])
    s['동_총인구'] = p['총인구'] if p else ''
    s['동_65세이상'] = p['65세이상'] if p else ''
    s['동_고령비율'] = round(p['65세이상'] / p['총인구'] * 100, 1) if p else ''
    if p and s['미정차'] == 'N':
        agg[s['행정동코드']].append(int(s['도내노선_운행횟수']))
with open(path, 'w', encoding='utf-8-sig', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(stops[0].keys())); w.writeheader(); w.writerows(stops)

out = []
for code, p in pop.items():
    v = sorted(agg.get(code, []))
    out.append({'행정동코드': code, '구': p['구'], '행정동': p['행정동'], '총인구': p['총인구'],
                '65세이상': p['65세이상'], '고령비율(%)': round(p['65세이상'] / p['총인구'] * 100, 1),
                '정류장수': len(v), '운행횟수_중앙값': v[len(v) // 2] if v else 0,
                '노인천명당_정류장수': round(len(v) / p['65세이상'] * 1000, 1) if p['65세이상'] else ''})
out.sort(key=lambda o: -o['고령비율(%)'])
dst = os.path.join(PROJ, 'data', 'seongnam_dong_elderly_bus.csv')
with open(dst, 'w', encoding='utf-8-sig', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(out[0].keys())); w.writeheader(); w.writerows(out)
print('saved', dst)

tot = sum(o['총인구'] for o in out); old = sum(o['65세이상'] for o in out)
print(f'성남 합계: 인구 {tot:,} / 65세이상 {old:,} ({old / tot * 100:.1f}%)')
for g in ('수정구', '중원구', '분당구'):
    t = sum(o['총인구'] for o in out if o['구'] == g); e = sum(o['65세이상'] for o in out if o['구'] == g)
    print(f'  {g}: 인구 {t:,} / 65세이상 {e:,} ({e / t * 100:.1f}%)')
print(f"\n{'구':<5}{'행정동':<7}{'고령%':>6}{'65+':>7}{'정류장':>5}{'운행중앙':>7}{'노인천명당정류장':>9}")
for o in out[:15]:
    print(f"{o['구']:<5}{o['행정동']:<7}{o['고령비율(%)']:>6}{o['65세이상']:>7,}{o['정류장수']:>5}{o['운행횟수_중앙값']:>7}{o['노인천명당_정류장수']:>9}")
print('...하위 5')
for o in out[-5:]:
    print(f"{o['구']:<5}{o['행정동']:<7}{o['고령비율(%)']:>6}{o['65세이상']:>7,}{o['정류장수']:>5}{o['운행횟수_중앙값']:>7}{o['노인천명당_정류장수']:>9}")
