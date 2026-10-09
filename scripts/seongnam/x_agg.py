"""경기도 승하차 데이터에서 성남시 집계 + 마을버스 수 결합 (정류소ID 기준)"""
import io,os,sys,zipfile,tarfile,gzip,csv,tempfile,collections
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8',errors='replace')
ZIP='data/raw/gg_ride/gg_ride_202606.zip'
TARNM='CARD_STATION45_202606.tar'
tarpath=os.path.join(tempfile.gettempdir(),TARNM)
if not os.path.exists(tarpath) or os.path.getsize(tarpath)<1e7:
    print(f'{ZIP} 에서 tar 추출 -> {tarpath}')
    with zipfile.ZipFile(ZIP) as z, open(tarpath,'wb') as o: o.write(z.read(TARNM))
t=tarfile.open(tarpath)
agg=collections.defaultdict(lambda:[0,0,0,0])   # 승차합계,초승,환승,하차
meta={}
gov=collections.Counter(); days=0
for m in t.getmembers():
    if not m.name.endswith('.csv.gz'): continue
    days+=1
    txt=gzip.decompress(t.extractfile(m).read()).decode('cp949',errors='replace')
    for r in csv.DictReader(io.StringIO(txt)):
        g=r['관할관청']; gov[g]+=1
        if '성남' not in g: continue
        k=r['정류소ID']
        a=agg[k]
        for i,c in enumerate(('승차합계','초승','환승','하차')):
            try: a[i]+=int(r[c] or 0)
            except ValueError: pass
        meta[k]=(r['정류소번호'],r['정류소명'],g)
print(f'{days}일치 / 성남 정류소 {len(agg)}개')
print('관할관청 중 성남:', [k for k in gov if '성남' in k])
# 마을버스 수 결합 — 정류소ID로 조인
hub={r['정류소ID']:r for r in csv.DictReader(open('data/seongnam_village_hub.csv',encoding='utf-8-sig'))}
rows=[]; matched=0
for k,(no,nm,g) in meta.items():
    a=agg[k]
    h=hub.get(k)
    if h: matched+=1
    rows.append(dict(정류소ID=k,정류소번호=no,정류소명=nm,관할=g,
        승차합계=a[0],초승=a[1],환승=a[2],하차=a[3],총이용=a[0]+a[3],
        일평균=round((a[0]+a[3])/days,1),
        마을버스수=int(h['마을버스수']) if h else None,
        마을버스=h['마을버스'] if h else '',
        하루운행=int(h['하루운행']) if h else None,
        구=h['구'] if h else '', 행정동=h['행정동'] if h else '',
        위도=h['위도'] if h else '', 경도=h['경도'] if h else ''))
print(f'정류소ID로 매칭된 것 {matched}개 ({matched/len(rows)*100:.0f}%)')
rows.sort(key=lambda x:-x['총이용'])
with open('data/seongnam_ride_202606.csv','w',newline='',encoding='utf-8-sig') as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
print('-> data/seongnam_ride_202606.csv\n')
tot=sum(x['총이용'] for x in rows)
print(f'성남시 30일 총 이용 {tot:,}건 / 일평균 {tot/days:,.0f}건\n')
print('■ 총 이용 상위 15 (승차+하차, 2026년 6월 30일 합계)')
print(f"{'#':>2} {'일평균':>8}{'마을':>5}{'운행':>7}  {'구':<4}{'행정동':<8}정류소명")
for i,x in enumerate(rows[:15],1):
    mb=f"{x['마을버스수']}개" if x['마을버스수'] is not None else '  -'
    op=f"{x['하루운행']}회" if x['하루운행'] is not None else '   -'
    print(f"{i:>2} {x['일평균']:>8,.0f}{mb:>5}{op:>7}  {x['구'][:2]:<4}{x['행정동']:<8}{x['정류소명'][:28]}")
