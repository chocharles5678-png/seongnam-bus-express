"""두 조건 교차: 마을버스 공통 정차 × 승하차 많음"""
import csv,io,sys
import numpy as np
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8',errors='replace')
rows=[r for r in csv.DictReader(open('data/seongnam_ride_202606.csv',encoding='utf-8-sig')) if r['마을버스수']]
for r in rows:
    r['마을버스수']=int(r['마을버스수']); r['일평균']=float(r['일평균']); r['하루운행']=int(r['하루운행'] or 0)
print(f'매칭된 정류소 {len(rows)}개\n')
v=np.array([r['마을버스수'] for r in rows],float)
u=np.array([r['일평균'] for r in rows],float)
# 백분위 순위
rv=(v.argsort().argsort()/ (len(v)-1))*100
ru=(u.argsort().argsort()/ (len(u)-1))*100
for r,a,b in zip(rows,rv,ru):
    r['마을버스_백분위']=round(a,1); r['이용_백분위']=round(b,1); r['교차점수']=round(min(a,b),1)
rows.sort(key=lambda x:(-x['교차점수'],-x['일평균']))
print('■ 두 조건 교차 상위 20 (교차점수 = 두 백분위 중 낮은 쪽)')
print(f"{'#':>2} {'교차':>5}{'마을':>5}{'일평균':>8}{'운행':>7}  {'구':<4}{'행정동':<8}{'정류소명':<24}마을버스")
for i,x in enumerate(rows[:20],1):
    print(f"{i:>2} {x['교차점수']:>5.0f}{x['마을버스수']:>4}개{x['일평균']:>8,.0f}{x['하루운행']:>6}회  "
          f"{x['구'][:2]:<4}{x['행정동']:<8}{x['정류소명'][:22]:<24}{x['마을버스'][:30]}")
print()
print('■ 단순 조건 교차 (마을버스 4개 이상 AND 일평균 이용 상위 10%)')
cut=np.percentile(u,90)
sel=[x for x in rows if x['마을버스수']>=4 and x['일평균']>=cut]
print(f'  기준: 마을버스 4개 이상, 일평균 {cut:,.0f}건 이상 → {len(sel)}곳\n')
print(f"{'#':>2} {'마을':>5}{'일평균':>8}{'운행':>7}  {'구':<4}{'행정동':<8}{'정류소명':<26}마을버스")
for i,x in enumerate(sel,1):
    print(f"{i:>2} {x['마을버스수']:>4}개{x['일평균']:>8,.0f}{x['하루운행']:>6}회  {x['구'][:2]:<4}{x['행정동']:<8}{x['정류소명'][:24]:<26}{x['마을버스'][:28]}")
with open('data/seongnam_hub_cross.csv','w',newline='',encoding='utf-8-sig') as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
print('\n-> data/seongnam_hub_cross.csv')
