# -*- coding: utf-8 -*-
"""원시 관측 자료의 차량번호를 가명으로 바꾼다
사용: python scripts/seongnam/x_pseudonymize.py [--dry-run]

왜 필요한가
  경기도 버스위치정보 API는 실제 차량번호(plateNo)를 내보낸다. 우리는 그 값을 차량 식별
  키로만 쓰므로 분석에 원본이 필요하지 않다. 저장소를 공개하면서 번호판을 그대로 재배포할
  이유가 없다.

어떻게
  노선 안에서 번호판을 정렬해 순번을 붙인다 (350-01, 350-02 ...). 같은 차량은 어느 날짜
  파일에서도 같은 가명을 받으므로 차량별 추적·완주 판정·10분 고유계수가 전부 그대로 나온다.
  대응표는 .plate_map.json 에 남기고 .gitignore 로 제외한다. 저장소만으로는 복원할 수 없다.

  plateNo 값만 문자열 치환한다. 다른 필드·키 순서·공백을 건드리지 않는다.
"""
import argparse, collections, glob, io, json, os, sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

ap = argparse.ArgumentParser()
ap.add_argument('--dir', default='data/raw/bus_location')
ap.add_argument('--dry-run', action='store_true', help='파일을 쓰지 않고 결과만 보여준다')
a = ap.parse_args()

MAP = os.path.join(a.dir, '.plate_map.json')
files = sorted(glob.glob(os.path.join(a.dir, '*.jsonl')))
if not files:
    sys.exit(f'{a.dir} 에 jsonl 이 없다')

# 1. 노선별 번호판 수집 — 이미 가명인 것은 건너뛴다
seen = collections.defaultdict(set)
for f in files:
    for ln in io.open(f, encoding='utf-8'):
        ln = ln.strip()
        if not ln:
            continue
        d = json.loads(ln)
        p, r = d.get('plateNo'), d.get('route')
        if p and r and not p.startswith(f'{r}-'):
            seen[r].add(p)

old = json.load(io.open(MAP, encoding='utf-8')) if os.path.exists(MAP) else {}
m = dict(old)
for r in sorted(seen):
    start = sum(1 for k, v in old.items() if v.startswith(f'{r}-'))
    for i, p in enumerate(sorted(seen[r] - set(old)), start=start + 1):
        m[p] = f'{r}-{i:02d}'
print(f'■ 가명 대응표  노선 {len(seen)}개 / 신규 {len(m) - len(old)}대 / 누적 {len(m)}대')
for r in sorted(seen):
    v = sorted(x for x in m.values() if x.startswith(f'{r}-'))
    print(f'  {r:>6}  {len(v):>2}대   {v[0]} ~ {v[-1]}')

# 2. plateNo 값만 치환
print(f'\n■ 파일 치환{"  (dry-run — 쓰지 않는다)" if a.dry_run else ""}')
tot = 0
for f in files:
    t = io.open(f, encoding='utf-8', newline='').read()
    n = 0
    for p, q in m.items():
        c = t.count(f'"plateNo": "{p}"')
        if c:
            t = t.replace(f'"plateNo": "{p}"', f'"plateNo": "{q}"')
            n += c
    if n and not a.dry_run:
        io.open(f, 'w', encoding='utf-8', newline='').write(t)
    tot += n
    print(f'  {os.path.basename(f):>16}  {n:>6}건')
print(f'  합계 {tot}건')

if not a.dry_run:
    json.dump(m, io.open(MAP, 'w', encoding='utf-8'), ensure_ascii=False, indent=1, sort_keys=True)
    print(f'\n  대응표 -> {MAP}  (.gitignore 로 제외할 것)')

# 3. 검증 — 남은 원본이 없는지, 차량 수가 보존됐는지
print('\n■ 검증')
left = 0
cnt = collections.defaultdict(set)
for f in files:
    for ln in io.open(f, encoding='utf-8'):
        ln = ln.strip()
        if not ln:
            continue
        d = json.loads(ln)
        p, r = d.get('plateNo'), d.get('route')
        if not p:
            continue
        cnt[r].add(p)
        if not p.startswith(f'{r}-'):
            left += 1
print(f'  가명화되지 않은 레코드: {left}건')
for r in sorted(cnt):
    print(f'  {r:>6}  고유 차량 {len(cnt[r]):>2}대  (치환 전 {len(seen.get(r, [])):>2}대)')
