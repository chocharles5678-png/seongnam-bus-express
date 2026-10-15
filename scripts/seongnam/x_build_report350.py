"""붙임2 양식 구조의 인쇄용 보고서 HTML 생성 — 350번 무증차 급행 재편 (축약판)
사용: python scripts/seongnam/x_build_report350.py
출력: output/분석보고서_350번.html  (브라우저에서 Ctrl+P → PDF로 저장, 배경 그래픽 켜기)

분량 기준(본문 5장 내외)에 맞추려고 본문을 약 40% 들어낸 판이다.
들어내기 전 상세판은 scripts/seongnam/.x_build_report350_full.py.bak 에 있다.
x_build_report.py(55번판)는 건드리지 않는다.
"""
import base64, io, os, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

FIGS = [
    ('figures/급행_350_노선도.png', '그림 1',
     '350번 급행 재편 — 급행 정차 17지점 / 왕복 정차 90회 → 21회',
     '왼쪽은 노선도(원 크기 = 지점 왕복 일평균 승하차), 오른쪽 위는 정차 횟수 비교, '
     '오른쪽 아래는 정류소 순서별 이용량이며 색칠한 막대가 급행 정차 지점이다.'),
    ('figures/배차역설_4개노선.png', '그림 2',
     '배차 역설 — 나눌 수 있는 노선은 이미 배차가 촘촘한 노선뿐이다',
     '네 노선을 같은 틀로 실측해 비교했다. 급행 간격 30분 이하(음영)와 평균 순효과 0 이상을 '
     '동시에 만족하는 배정은 55번과 350번에만 있고, 배차가 가장 촘촘한 350번이 가장 크다.'),
    ('figures/무증차_350.png', '그림 3',
     '350번 무증차 재편 — 급행 5대에서 평균 +0.51분, 손해는 55번의 절반',
     '왼쪽은 급행 배정 대수별 순효과와 급행 간격, 오른쪽은 같은 조건(급행 간격 30분 이하 최소 대수)에서 '
     '55번과의 비교다. 350번이 이기는 것은 이득이 커서가 아니라 손해가 작아서다.'),
]

ROWS = []


def row(label, html, cls=''):
    ROWS.append((label, html, cls))


row('이름 / 팀명', '<p class="blank">[ 기재 필요 ]</p>')

row('주제', """
<p class="lead">나눌 수 있는 버스는 이미 편한 버스였다<br>
— 버스위치 API 실측으로 찾은 성남 350번 무증차 급행 재편</p>
<p>마을버스가 주거지와 거점을 잇고 시내버스 일부 차량을 급행으로 돌리는 안을 <b>차량을 늘리지 않고</b>
검토했다. 성남 네 노선(88-1·380·55·350)의 <b>운행 대수와 왕복 소요시간을 공개 API로 직접 실측</b>해
같은 틀로 비교하고, 그중 350번을 제안 대상으로 선정했다.</p>
<p class="note"><b>증차(차량 증편)는 제안에서 제외했다.</b> 전수 계산 결과 증차는 효과가 크지만
총 주행거리를 19.9~26.7% 늘려 공모전 주제인 탄소중립과 상충하기 때문이다(§7-5).</p>
""")

row('분석 배경<br>및 목적', """
<p>성남의 주거 생활권에서 판교 업무지역과 야탑·모란 생활거점으로 가는 통행은 정차가 많은 시내버스에
묶여 있다. 급행을 새로 만들려면 차량·기사·차고지가 필요하지만 <b>기존 차량의 배분만 바꾸는 재편</b>은
추가 투입 없이 가능하다. 그 재편이 실제로 이득인지가 이 분석의 질문이다.</p>
<p>효과는 <b>왕복 소요시간</b>과 <b>운행 대수</b>에서 전부 결정되는데 두 값은 공개 자료에 없다.
초기에 구간 소요시간 중앙값×구간 수로 88-1번 왕복을 78분으로 추정했으나 실측은 <b>98분</b>,
회차·회복 시간이 빠져 <b>26% 과소평가</b>였다.</p>
<p class="big">경기도 버스위치정보 API 응답에 <b>차량번호(plateNo)</b>와 <b>정류소순번(stationSeq)</b>이
들어 있다. 이 둘을 추적하면 운행 대수와 왕복 소요시간을 <b>추정이 아니라 실측</b>할 수 있다.
이 분석의 모든 운행 수치는 여기서 나왔다.</p>
<p><b>목적</b> ① 네 노선의 운행 대수·왕복시간을 같은 방법으로 실측한다.
② 무증차 급행 재편이 <b>어떤 조건에서 성립하는지</b> 찾는다. ③ 성립하는 노선에 정차역을 설계하고
<b>이득과 손해를 함께</b> 제시한다.</p>
<p class="warn"><b>연령을 노선 선정 조건으로 쓰지 않았다.</b> 행정동 20대 인구는 정차역 선정의
보조 지표로만 썼고, 노선 선정은 전적으로 실측 배차와 운행 대수로 했다.</p>
""")

row('활용 데이터', """
<table class="d data">
<tr><th>활용 데이터(명)</th><th>제공기관(명)</th><th>출처 플랫폼(명)</th><th>URL</th></tr>
<tr><td>경기도 버스위치정보 조회 (Open API)</td><td>경기도 교통정보과</td><td>공공데이터포털</td>
    <td>https://www.data.go.kr/data/15080648</td></tr>
<tr><td>경기도 버스노선 조회 (Open API)</td><td>경기도 교통정보과</td><td>공공데이터포털</td>
    <td>https://www.data.go.kr/data/15080662</td></tr>
<tr><td>경기도 버스정류소 현황</td><td>경기도</td><td>공공데이터포털</td>
    <td>https://www.data.go.kr/data/15057894</td></tr>
<tr><td>경기도 정류소별 승하차 인원 집계 (2026.06)</td><td>경기도 버스관리과</td><td>경기데이터드림</td>
    <td>https://data.gg.go.kr <span class="s">(infId=MZCREO5CKHZM6PJEA55P37391662)</span></td></tr>
<tr><td>주민등록 인구통계 — 행정동별 연령별 인구현황 (2026.08)</td><td>행정안전부</td><td>주민등록 인구통계</td>
    <td>https://jumin.mois.go.kr</td></tr>
<tr><td>경기버스정보 노선정보 항목 명세</td><td>경기도</td><td>GBIS</td>
    <td>https://www.gbis.go.kr/gbis2014/publicService.action?cmd=mBusRouteInfo</td></tr>
</table>
<table class="d">
<tr><th>구분</th><th>내용</th></tr>
<tr><td>수집 방법</td><td><b>공공데이터포털 활용신청 후 발급받은 인증키로 공식 OpenAPI를 호출</b>했다.
  웹 크롤링이나 비공개 경로 접근은 사용하지 않았다. 개발계정 한도(일 1,000회) 안에서 호출 예산을 두었다.</td></tr>
<tr><td>수집 기간</td><td>버스위치 <b>2026-10-05 ~ 10-14</b>(평일 6일, 폴링 30~45초) — 10-07 88-1·55·380(992회),
  10-12 55(600회), 10-13 350(352회), <b>10-14 350 첨두 480회</b>·357(274회).<br>
  승하차 2026-06-30 / 인구 2026-08-31 / 노선·정류소 제원 2026-10 조회분.</td></tr>
<tr><td>주요 변수</td><td>위치 API — <code>ts, route, plateNo, stationId, stationSeq</code> ·
  노선 API — 경유 순서, 기·종점, <code>peekAlloc</code>(평일 최소 배차) ·
  승하차 — 정류소ID, 승차합계, 초승, 환승, 하차합계</td></tr>
<tr><td>이용 조건</td><td>승하차 자료는 상업적 이용 및 변경 허용. OpenAPI는 포털 이용약관에 따름.
  <b>인증키는 환경변수로 분리해 코드·제출물에 포함하지 않았다.</b></td></tr>
</table>
<p class="s">승하차 집계로 급행 정차역을 선정했고(성남시 1,305개소, 총 24,860,507건), GBIS 명세는
배차 필드 정의 확인에 썼다 — 초기에 <code>peekAlloc</code>을 "첨두 배차"로 오독한 것을 바로잡은 근거다(§9-4).</p>
""")

row('분석과정<br>및 방법', """
<div class="flow">
<b>1</b> 노선·정류소 제원 수집 &nbsp;→&nbsp; <b>2</b> 위치 API 폴링(30~45초) &nbsp;→&nbsp;
<b>3</b> 운행 대수·왕복시간 실측 &nbsp;→&nbsp; <b>4</b> 급행 정차역 선정 &nbsp;→&nbsp;
<b>5</b> 무증차 재편 전수 시뮬레이션 &nbsp;→&nbsp; <b>6</b> 총 주행거리 변화 산출
</div>

<h4>5-1. 운행 대수와 왕복 소요시간</h4>
<p><b>운행 대수</b>는 10분 단위 고유 차량번호의 중앙값이다. 1시간으로 세면 교대·투입 차량까지 누적돼
과대 집계된다(350번 1시간 23대 vs 10분 19대). <b>왕복 소요시간</b>은 정류소 순번이 단조 증가하는
가장 긴 구간을 찾아 진행률 95% 이상인 <b>완주 차량</b>의 중앙값을 쓴다.</p>
<p class="warn"><b>완주 집합은 관측 종료 시각에 절단되어 빠른 차량 쪽으로 치우친다.</b>
350번을 155분만 관측했을 때는 완주 2대에 136분이었으나, 240분을 관측하니 <b>완주 13대에 150분</b>이었다.
본문은 150분을 쓴다. 왕복(150분)이 첨두창(115분)보다 길어 첨두 안에서 완주가 구조적으로 나올 수 없으므로,
첨두 통과 속도는 <b>연속 관측쌍 중 양 끝 시각이 모두 같은 창 안인 것만</b> 모아 집계했다.</p>

<h4>5-2. 급행 정차역 선정 규칙 — 다음의 합집합</h4>
<div class="rule">
① 기·종점·회차점 &nbsp;|&nbsp; ② 거점: 지점 왕복 일평균 승하차 ≥ 3,000건 &nbsp;|&nbsp;
③ 대학: 정류소명에 대학/가천대/을지대/신구대 포함 AND ≥ 1,000건<br>
④ 환승거점: 마을버스 5개 이상 경유 &nbsp;|&nbsp; ⑤ 20대 거점: 행정동 20대 ≥ 2,500명 AND 지점 ≥ 1,500건
</div>
<p>교집합으로는 최대 거점이 탈락해 <b>합집합</b>으로 했다. 집계는 <b>정류소 고유ID 기준</b>이다 —
이름으로 묶으면 성남에서 동명 그룹 102곳의 값이 뭉개진다. <b>이 기준은 55번에 적용한 것과 동일하며
350번에 맞춰 조정하지 않았다</b>(§7-4 민감도).</p>

<h4>5-3. 시뮬레이션 모형</h4>
<div class="box">
완행 왕복 = 150분(실측) &nbsp;·&nbsp; 급행 왕복 = 150 − (통과 69회 × T) = <b>127분</b><br>
각 서비스는 <b>자기 왕복시간 ÷ 자기 대수</b> 간격으로 운행 &nbsp;·&nbsp;
평균 대기 = <b>E[gap²] / (2·E[gap])</b>
</div>
<p>출발·도착이 <b>모두</b> 급행 정차 지점인 통행은 급행·완행 중 먼저 오는 차를 타고,
한쪽이라도 통과 지점이면 완행만 탄다.</p>
<p class="warn"><b>가정 세 가지.</b> <b>① T(정차 1회당 손실) = 20초</b> — 실측 3방법 모두 실패(§9-3).
15·20·25·30초로 모두 돌렸고 권장 급행 대수는 5대로 동일했다.
<b>② 평균 통행 = 편도의 1/3</b> — 차내 단축폭을 <u>선형으로</u> 좌우한다(1/4이면 2.9분, 1/2이면 5.7분).
<b>③ 출발·도착 독립</b> — 급행 이용 가능 42%는 기록 구성비 64.7%의 제곱이다.</p>
""")

row('AI 기술<br>활용', """
<table class="d">
<tr><th>구분</th><th>내용</th></tr>
<tr><td>활용 AI 서비스</td><td>Claude (Anthropic) — Claude Code</td></tr>
<tr><td>활용 범위</td><td>공식 수집처 확인, Python 수집·정제·검증 코드 작성, 시뮬레이션 구현, 도면 생성, 문서 구성</td></tr>
<tr><td>검증 방식</td><td>AI가 낸 수치는 <b>원본 재집계와 재실행으로 대조</b>한 뒤에만 사용했다.
  AI의 설명 자체를 실측 자료로 쓰지 않았다.</td></tr>
</table>
<h4>주요 프롬프트 — 분석 방향을 바꾼 다섯 지점</h4>
<p class="note">아래는 <b>대화 기록에 남은 실제 입력 문장을 그대로</b> 옮긴 것이다.
AI가 문장을 지어내면 이 항목 자체가 무의미해지므로 재구성하거나 다듬지 않았다.</p>
<table class="d">
<tr><th>시점</th><th>입력한 문장</th><th>바뀐 것</th></tr>
<tr><td>10-05</td><td>"경사 고령 취약 이건 이제 배제시켜도 돼, 새로운 방향으로 가고 있으니깐"</td>
    <td><b>선정 조건 정리.</b> 경사·고령을 정차역 선정에서 제외하고 이용량·환승 중심으로 단순화했다</td></tr>
<tr><td>10-06</td><td>"일단 그럼 20대 사람들이 사는 곳에서 어느 노선도를 해야 현명할까,
    우리의 공모전 취지는 차량이 없는 20대들을 위해 급행 노선도를 짜는거야"</td>
    <td><b>목적 확정.</b> 마을버스 단독에서 <b>마을버스 연계 + 시내버스 급행</b>으로 방향을 바꿨다</td></tr>
<tr><td>10-06</td><td>"88-1 첨두 지금 구하자"</td>
    <td><b>실측 착수.</b> 버스위치 API 폴링을 실제로 돌려 추정값(왕복 78분)을 실측(98분)으로 대체했다</td></tr>
<tr><td>10-08</td><td>"350·330·220 연속성 검증부터 하자"</td>
    <td><b>350번 검토 시작.</b> 병행 노선 중첩을 전수 검증해 350번의 독점 구간이 0임을 확인했다</td></tr>
<tr><td>10-15</td><td>"증차는 공모전 취지인 탄소중립과 맞지 않아서 빼자"</td>
    <td><b>증차 배제.</b> 총 주행거리 비율을 산출해 증차안을 기각 사유와 함께 제외했다(§7-5)</td></tr>
</table>

<h4>AI 활용에서 실제로 작동한 것</h4>
<ol class="key">
<li><b>실측으로 AI의 추정을 반증했다.</b> AI가 외삽으로 낸 88-1 왕복 78분은 실측 98분과 26% 차이였다.
  이후 외삽값은 결론에 쓰지 않는 규칙을 적용했다.</li>
<li><b>1차 명세로 AI의 필드 해석을 반증했다.</b> <code>peekAlloc</code>을 "첨두 배차"로 읽은 것이
  오독임을 GBIS 명세 원문에서 확인하고 관련 주장 4건을 철회했다.</li>
<li><b>전수 계산과 표본 확대로 코드·집계 결함을 잡았다.</b> 시뮬레이션이 급행 대수를
  <code>(3,5,6,8,10)</code>으로 하드코딩해 N=1·2를 건너뛰었고, 350번 왕복은 완주 2대 136분에서
  관측창 확대 후 <b>완주 13대 150분</b>으로 바뀌었다.</li>
</ol>
""")

row('분석 내용<br>및 결과', """
<h4>7-1. 네 노선 실측 — 같은 방법, 같은 기간</h4>
<table class="d n">
<tr><th>노선</th><th>왕복<br>정차</th><th>공시 배차</th><th>왕복 소요<br>(실측)</th>
    <th>관측<br>대수</th><th>배차<br>(왕복÷대수)</th><th>공시 대비</th><th>급행 분리</th></tr>
<tr><td>88-1 <span class="s">마을</span></td><td>71회</td><td>15~25분</td><td><b>98분</b></td><td><b>4~5대</b></td>
    <td>24.5분</td><td class="no">최소값의 1.6배</td><td class="no">불가</td></tr>
<tr><td>380</td><td>106회</td><td>15~25분</td><td><b>200분</b></td><td><b>10대</b></td>
    <td>20.0분</td><td>범위 안</td><td class="no">불가</td></tr>
<tr><td>55</td><td>127회</td><td>10~20분</td><td><b>195분</b></td><td><b>18대</b></td>
    <td>10.8분</td><td>범위 안</td><td class="ok">가능(+0.20분)</td></tr>
<tr class="hl"><td><b>350</b></td><td><b>90회</b></td><td><b>7~9분</b></td><td><b>150분</b></td>
    <td><b>19대</b></td><td class="hl2"><b>7.9분</b></td><td>범위 안</td>
    <td class="ok"><b>가능(+0.51분)</b></td></tr>
</table>
<p class="big"><b>갈림길은 배차 하나다.</b> 88-1번은 4대뿐이라 1대만 돌려도 급행이 98분에 한 대가 되고,
380번은 10대라 급행 간격을 30분 이하로 만들면 평균이 −5.7분이 된다. 공시 범위를 크게 벗어난 것은
마을버스 88-1번뿐이다 — <b>공시 배차를 실제 운행으로 간주하면 안 되지만, 배차가 촘촘한 시내버스에서는
공시가 대체로 지켜진다.</b></p>

<h4>7-2. 350번 첨두 실측 (2026-10-14 수 07:04~11:04, 480회 호출)</h4>
<p><b>첨두 운행 19.0대 · 완주 왕복 150분(완주 13대, 142~158분) · 배차 7.9분.</b>
통과 속도는 첨두 0.563 / 비첨두 0.608로 <b>첨두 지체 −7.4%</b>(55번 −14.0%)다.
완주 13대가 모두 첨두 출발(07:04~08:42)이다. <b>배차는 시간대에 둔감하다</b> — 왕복과 대수가
같이 움직여 상쇄된다(비첨두 8.0분, 55번도 첨두 11.1 / 비첨두 10.9분).</p>

<h4>7-3. 급행 정차역 — 17지점, 왕복 90회 → 21회, 기록 커버 64.7%</h4>
<p>축은 <b>상대원차고지 → 모란역 → 성남시청 → 야탑역 → 판교테크노밸리 → 운중동</b>이다.
이용 상위는 야탑역 전면 16,203 · 후면 15,124, 모란역2.3번출구 12,346 · 5번출구 8,444,
성남시청전면 5,391, 운중동행정복지센터 4,232, 유라코퍼레이션.SK케미칼 3,866,
판교유스센터 3,522건이다(왕복 일평균).</p>
<p class="warn"><b>64.7%의 분모.</b> 그 정류소에 서는 <b>모든 노선의 승하차 기록</b> 구성비다.
원본에 노선 구분 컬럼이 없어 "350번 승객의 64.7%"라고 말할 수 없고 인원으로도 환산할 수 없다.</p>
<p class="note"><b>급행이 상대원1동행정복지센터를 통과한다.</b> 왕복 일평균 2,945건으로 거점 기준
3,000건에 <b>55건 미달</b>이다. 상대원 주민을 위한 급행인데 상대원1동을 건너뛰는 모양이 된다.
기준을 2,900으로 낮추면 정차하지만 <b>기준을 결과에 맞춰 조정한 것이 되므로 그대로 두었다.</b>
기점인 상대원차고지에서는 급행을 탈 수 있다.</p>

<h4>7-4. 무증차 재편 결과 — 급행 5대에서 평균 +0.51분</h4>
<table class="d n">
<tr><th>급행 대수</th><th>1</th><th>3</th><th>4</th><th>5</th><th>6</th><th>7</th><th>9</th></tr>
<tr><td>급행 간격</td><td>127분</td><td>42.3분</td><td>31.8분</td><td><b>25.4분</b></td><td>21.2분</td>
    <td>18.1분</td><td>14.1분</td></tr>
<tr><td>평균 순효과</td><td>+1.41분</td><td>+1.00분</td><td>+0.80분</td><td><b>+0.51분</b></td><td>+0.20분</td>
    <td class="no">−0.10분</td><td class="no">−0.80분</td></tr>
</table>
<p>평균만 보면 급행 1대가 최선이지만 <b>127분에 한 대는 급행이 아니라 특별편</b>이다.
급행 간격 30분 이하를 만드는 최소 대수가 <b>5대(25.4분)</b>이고 그때 평균이 <b>+0.51분</b>이다.
이 배정에서 완행 간격은 7.9 → 10.7분, 급행 이용 가능 통행(42%)은 <b>+3.2분</b>,
이용 불가 통행(58%)은 <b>−1.4분</b>(대기 3.9 → 5.4분)이다.</p>
<p class="warn"><b>대기시간은 모든 지점에서 늘어난다.</b> 급행 정차 지점조차 3.9분에서 4.6분이 된다.
차량 수가 같은데 두 서비스로 나뉘며 도착이 불규칙해지기 때문이다. <b>이득은 전적으로 차내 시간에서 나온다.</b></p>
<p><b>민감도</b> — 정차 기준을 2,000/1,500으로 낮추면 24지점·커버 75.9%·평균 +0.9분,
4,000/3,500으로 높이면 14지점·59.3%·+0.3분이다. 세 기준 모두 양수이고 1분을 넘지 않는다.
<b>본문은 더 유리한 기준을 쓰지 않고 55번과 동일한 3,000/2,500을 유지했다.</b></p>

<h4>7-5. 증차를 제외한 이유 — 총 주행거리</h4>
<p>급행은 경로가 같고 정차만 건너뛰므로 왕복 1회 주행거리는 같다. 그러나 급행 왕복시간이 짧아
<b>같은 시간에 더 자주 돈다.</b> 왕복 횟수 = 대수 ÷ 왕복시간이므로 주행거리 비율이 계산된다.</p>
<table class="d n">
<tr><th>노선</th><th>무증차 재편</th><th>증차</th></tr>
<tr><td>350 (급행 5대 / 증차 4대)</td><td><b>+4.8%</b></td><td class="no"><b>+26.7%</b></td></tr>
<tr><td>55 (급행 6대 / 증차 3대)</td><td>+6.4%</td><td class="no">+19.9%</td></tr>
</table>
<p class="big">증차 4대면 통과 지점 손해 없이 평균 +1.7분이 가능하다. <b>그러나 총 주행거리를 26.7% 늘려
공모전 주제인 탄소중립과 상충한다.</b> 무증차도 +4.8%로 같은 방향의 부담을 지지만 <b>5분의 1</b>이다.
따라서 본 보고서는 무증차 재편만을 제안 대상으로 한다.</p>
<p class="note"><b>"증차가 없으니 탄소 변화도 없다"는 쓸 수 없다.</b> 무증차도 주행거리를 4.8% 늘린다.
반대로 급행이 69회 정차를 건너뛰어 가감속이 줄어드는 감축 요인도 있으나, 배출계수를 확보하지 못해
두 효과 모두 산출하지 못했다(§9-5).</p>

<h4>7-6. 350번과 55번 — 같은 조건 비교 (그림 3 오른쪽)</h4>
<p class="big">350번 : +0.51분 = 42%×(+3.2분) + 58%×(−1.4분)<br>
55번 &nbsp;: +0.20분 = 42%×(+4.2분) + 58%×(−2.7분)</p>
<p><b>350번이 이기는 것은 이득이 커서가 아니라 손해가 작아서다.</b> 급행을 타는 개인의 이득은
55번이 더 크다(+4.2 대 +3.2분) — 350번은 노선이 짧아 통과가 69회뿐이고(55번 94회) 차내 단축이 작다.
완행 간격 악화도 55번 10.8→16.2분, 350번 7.9→10.7분으로 350번이 절반이다.
<b>일반 서비스를 보호하는 관점에서 적게 잃는 쪽이 맞다고 판단했다.</b></p>

<h4>7-7. 통과 지점의 손해는 균등하지 않다 — 공장지대 7정차</h4>
<p>350번은 <b>90정차 전부에 병행 노선이 있어 독점 구간이 0</b>이다(중앙값 11개, 야탑역 44개).
다만 <b>상대원 공장지대 7정차</b>만 병행이 <b>357번 하나</b>뿐이어서 357번도 실측했다 —
관측 8.5대, 왕복 환산 170분, <b>배차 20.0분</b>(공시 15~20분의 상한).
공장지대 대기는 현행 3.44분 → 재편 후 <b>4.42분</b>(완행 단독이면 5.35분이므로 357번이 0.93분 보완).</p>
<p>급행화해도 완행 14대는 그 7정차에 계속 서므로 공장지대가 350번을 잃는 것이 아니다. 다만 병행이
중앙값 11개인 다른 통과 지점은 보완이 더 크므로 <b>공장지대 7정차는 통과 지점 중에서도 상대적으로 불리하다.</b></p>
""")

row('정책제안<br>및 기대효과', """
<div class="box">
급행 <b>5대</b> · 간격 <b>25.4분</b> &nbsp;|&nbsp; 완행 <b>14대</b> · 간격 <b>10.7분</b><br>
급행 정차 <b>17지점</b> · 왕복 정차 <b>90회 → 21회</b>(통과 69회)<br>
<b>차량 증편 없음 · 노선 신설 없음 · 총 주행거리 +4.8%</b>
</div>
<p>통행당 평균 <b>+0.51분</b>(급행 이용 가능 42% +3.2분 / 이용 불가 58% −1.4분).
급행 차내 시간은 왕복 150 → <b>127분</b>, 전 구간 이용자는 편도 기준 약 11.5분 단축된다.
비용은 차량 증편 없이 급행 표시체계·정류소 안내·운행계획 변경·인가 검토·기사 교육이다.</p>

<h4>단계적 도입 — 효과가 통행당 31초이기 때문이다</h4>
<p class="big">이 크기의 개선에 노선 전체를 한 번에 바꾸는 것은 위험 대비 이득이 맞지 않는다.
<b>①</b> 출근 방향 첨두(07~09시)에만 급행 5대를 시범 운행하며 통과 지점의 실제 대기·혼잡·승차 거절을 계측하고,
<b>②</b> 악화가 모형(−1.4분)을 넘으면 중단한다. <b>③</b> 공장지대 7정차는 357번(20.0분)이 유일한
보완이므로 따로 계측한다.</p>

<h4>기대효과</h4>
<ul>
<li><b>차량 추가 없이</b> 주거지–판교 접근성을 개선하고 총 주행거리 증가를 <b>+4.8%</b>로 억제한다(증차안 +26.7%).</li>
<li><b>급행 재편의 적용 조건을 수치로 제시</b>한다 — 배차 10분 이하, 관측 대수 18대 이상.
  다른 노선·다른 도시에 그대로 적용할 수 있다.</li>
</ul>
<p class="warn"><b>제시하지 않는 것.</b> 수혜 인원, 승용차 전환 수요, 탄소 감축량은 산출하지 않았다.
노선별 OD와 배출계수를 확보하지 못했기 때문이다. <b>추정값을 제시하지 않는 것이 이 보고서의 원칙이다.</b></p>
""")

row('분석의 한계<br><span class="add">(추가 항목)</span>', """
<h4>9-1. 19대는 관측 차량 수이지 인가·배정 대수가 아니다</h4>
<p>공개 자료에 인가 대수가 없다. 실제로 몇 대를 급행으로 떼어낼 수 있는지는 인가·기사 배치·차고지
운영 조건에 달렸고 그 자료는 확보하지 못했다.</p>

<h4>9-2. 세 가지 가정 위에 있다</h4>
<table class="d">
<tr><th>가정</th><th>값</th><th>영향</th></tr>
<tr><td>정차 1회당 손실 T</td><td>20초</td><td>차내 단축폭을 좌우. 15~30초로 모두 돌렸고 <b>권장 5대로 동일</b></td></tr>
<tr><td>평균 통행 길이</td><td>편도의 1/3</td><td><b>차내 단축폭을 선형으로 좌우</b>. 1/4이면 2.9분, 1/2이면 5.7분</td></tr>
<tr><td>출발·도착 독립</td><td>42% = 64.7%²</td><td>급행 이용 가능 비중. 실제 통행 분포를 모른다</td></tr>
</table>

<h4>9-3. 정차 1회당 손실시간(T)은 실측에 실패했다</h4>
<p>세 방법 모두 실패했다. <b>문헌</b>은 국내 논문이 서울 간선·중앙차로 기준이라 부적합,
<b>첫차 시각 역산</b>은 기점·종점 시각차가 편도거리와 음의 상관(−0.51)이라 소요시간이 아니었으며,
<b>회귀</b>는 R²가 0.11→0.08로 떨어지고 환산 주행속도가 61~113km/h로 비현실적이었다.</p>

<h4>9-4. 분석 과정에서 자체 발견하고 정정한 오류</h4>
<table class="d">
<tr><th>오류</th><th>정정</th></tr>
<tr><td>구간 중앙값×구간수로 88-1 왕복 78분 추정</td><td>실측 98분. <b>26% 과소</b>. 외삽값 사용 금지 규칙 도입</td></tr>
<tr><td><code>peekAlloc</code>을 "첨두 배차"로 오독</td><td>명세상 "평일 최소 배차". 관련 주장 4건 철회</td></tr>
<tr><td>급행 대수를 <code>(3,5,6,8,10)</code>으로 하드코딩</td>
    <td>전수로 교체. "380번 무증차 전부 마이너스"가 틀렸음이 드러남(1대 +1.2분)</td></tr>
<tr><td>350번 왕복을 완주 2대로 136분이라 함</td><td>관측창 확대 후 <b>완주 13대 150분</b>. 절단 편향</td></tr>
<tr><td>첨두를 구간 중간시각으로 분류 / 공장지대가 350번을 잃는다고 서술</td>
    <td>연속 관측쌍 기준으로 교체 / 완행은 계속 정차한다(손해 +0.98분)</td></tr>
</table>

<h4>9-5. 확보하지 못한 자료</h4>
<ul>
<li><b>온실가스 배출계수</b> — 1차 출처 미확정으로 tCO₂ 환산을 하지 못했다. 주행거리 비율만 산출했다.</li>
<li><b>노선별 OD</b> — 수혜·불편 인원을 사람 수로 환산할 수 없다. 64.7%는 기록 구성비다.</li>
<li><b>357번 완주 왕복</b> — 관측 128분이 왕복(170분)보다 짧아 완주가 없다. 170분은 환산값이며
  두 환산 방법이 168·170분으로 수렴한 것에 근거한다.</li>
<li><b>동일 출발·도착지의 기존 대안</b> — 같은 구간을 잇는 다른 노선·철도와의 총 이동시간 비교는
  범위 밖이다. <b>최종 타당성 판단에는 이 비교가 필요하다.</b></li>
</ul>
""")

row('분석도구<br>및 참고문헌', """
<table class="d">
<tr><th>구분</th><th>내용</th></tr>
<tr><td>도구</td><td>Python 3.14 (numpy, matplotlib) · Git · Claude (Anthropic) — Claude Code</td></tr>
<tr><td>주요 산출</td><td>차량별 순번 추적, 10분 단위 고유차량 계수, 단조증가 완주 판정,
  연속 관측쌍 기준 첨두 분리, 대기시간 분포 E[gap²]/(2·E[gap]), 급행 대수 전수 계산, 민감도 분석</td></tr>
<tr><td><b>코드</b></td><td><b>https://github.com/chocharles5678-png/seongnam-bus-express</b><br>
  <span class="s">수집·분석·시뮬레이션·도면·보고서 생성 코드와 원시 관측 자료 전체를 공개했다.
  인증키는 포함되지 않으며 <code>.env.example</code>에 필요한 변수명만 두었다.</span></td></tr>
</table>
<pre>python scripts/seongnam/x_collect_location.py 350 --interval 30 --minutes 240 --budget 500
python scripts/seongnam/x_peak.py 20261014 --route 350
python scripts/seongnam/x_express_trunk.py 350
python scripts/seongnam/x_sim_fleet.py 350 --fleet 19 --cycle 150 --T 20</pre>
<p class="s">원시 관측은 <code>data/raw/bus_location/*.jsonl</code>에 날짜별로 쌓인다.
인증키는 <code>.env</code>에서 읽으며 코드에 포함되지 않는다.</p>

<h4>참고문헌</h4>
<ul>
<li>경기버스정보(GBIS) 노선정보 항목조회 명세. https://www.gbis.go.kr/gbis2014/publicService.action?cmd=mBusRouteInfo</li>
<li>공공데이터포털, 경기도 버스위치정보 조회. https://www.data.go.kr/data/15080648</li>
<li>공공데이터포털, 경기도 버스노선 조회. https://www.data.go.kr/data/15080662</li>
<li>경기데이터드림, 경기도 정류소별 승하차 인원 집계(2026.06). https://data.gg.go.kr</li>
<li>행정안전부, 주민등록 인구통계 — 행정동별 연령별 인구현황(2026.08). https://jumin.mois.go.kr</li>
<li class="blank">[ 정차시간 문헌 · 온실가스 배출계수 — 1차 출처 미확정으로 본문에서 사용하지 않음 ]</li>
</ul>
""")

imgs = []
for path, no, cap, desc in FIGS:
    if not os.path.exists(path):
        imgs.append(f'<p class="blank">[ {no} 파일 없음: {path} ]</p>'); continue
    b64 = base64.b64encode(open(path, 'rb').read()).decode()
    imgs.append(f'<figure><img src="data:image/png;base64,{b64}" alt="{cap}">'
                f'<figcaption><b>{no}.</b> {cap}<br><span class="s">{desc}</span></figcaption></figure>')
row('분석결과<br>이미지<br><span class="add">(필수)</span>', '\n'.join(imgs), 'figs')


CSS = """
@page { size: A4; margin: 15mm 13mm; }
* { box-sizing: border-box; }
body { font-family: "Malgun Gothic","맑은 고딕",sans-serif; color:#111; margin:0;
       font-size:9.4pt; line-height:1.62; -webkit-print-color-adjust:exact; print-color-adjust:exact; }
.wrap { max-width: 184mm; margin: 0 auto; padding: 8mm 0; }
.head { text-align:center; border-bottom:2.2px solid #111; padding-bottom:7px; margin-bottom:12px; }
.head .ev { font-size:9pt; color:#52514e; letter-spacing:.02em; }
.head h1 { font-size:19pt; margin:5px 0 0; letter-spacing:.22em; }
table.form { width:100%; border-collapse:collapse; }
table.form > tbody > tr > th { width:26mm; background:#f4f5f7; border:1px solid #9aa0a6;
       font-size:9.6pt; font-weight:700; vertical-align:middle; text-align:center; padding:9px 4px; line-height:1.45; }
table.form > tbody > tr > td { border:1px solid #9aa0a6; padding:10px 11px; vertical-align:top; }
tr { page-break-inside: avoid; }
tr.figs { page-break-inside: auto; }
h4 { font-size:10.2pt; margin:13px 0 5px; padding-left:7px; border-left:3.4px solid #2a78d6; }
td > h4:first-child { margin-top:2px; }
p { margin:5px 0; }
p.lead { font-size:11pt; font-weight:700; margin:2px 0 7px; line-height:1.5; }
p.big { background:#f2f5fa; border-left:3.4px solid #2a78d6; padding:8px 11px; margin:9px 0; font-size:9.9pt; }
p.note { background:#fff8e6; border:1px solid #e8d9a8; padding:7px 10px; margin:7px 0; font-size:8.9pt; }
p.warn { background:#fdeeea; border-left:3.4px solid #eb6834; padding:7px 10px; margin:8px 0; font-size:8.9pt; }
p.arrow { color:#444; font-size:8.9pt; margin:3px 0 9px 10px; }
p.eq, div.rule, div.flow, div.box, pre { background:#f6f7f9; border:1px solid #e0e2e6;
       padding:8px 11px; margin:7px 0; font-size:8.9pt; line-height:1.78; }
div.box { text-align:center; font-size:10pt; }
div.flow { line-height:1.95; text-align:center; }
pre { font-family:Consolas,"D2Coding",monospace; font-size:8.1pt; white-space:pre-wrap; line-height:1.6; }
code { font-family:Consolas,"D2Coding",monospace; font-size:8.5pt; background:#f0f1f3; padding:0 3px; border-radius:2px; }
blockquote { margin:4px 0 2px 10px; padding:6px 11px; border-left:3px solid #9aa0a6;
       background:#fafafa; font-size:9.3pt; }
ul, ol { margin:5px 0; padding-left:19px; } li { margin:2.5px 0; }
ol.key { counter-reset:k; list-style:none; padding-left:0; }
ol.key li { counter-increment:k; position:relative; padding-left:21px; margin:5px 0; }
ol.key li::before { content:counter(k); position:absolute; left:0; top:1px; width:15px; height:15px;
       background:#2a78d6; color:#fff; border-radius:50%; font-size:8pt; text-align:center; line-height:15px; font-weight:700; }
table.d { width:100%; border-collapse:collapse; margin:7px 0; font-size:8.7pt; }
table.d th { background:#eef0f3; border:1px solid #c3c7cc; padding:5px 6px; text-align:center; line-height:1.4; }
table.d td { border:1px solid #c3c7cc; padding:5px 6px; vertical-align:middle; }
table.d.n td { text-align:center; } table.d.n td:first-child { text-align:left; }
table.d.data td { font-size:8.2pt; word-break:break-all; }
tr.hl td { background:#f2f5fa; } td.hl2 { background:#e6f0fb; }
td.ok { color:#1d6b2c; font-weight:700; } td.no { color:#b4341a; font-weight:700; }
.s { color:#52514e; font-size:8.2pt; }
.blank { color:#b4341a; font-weight:700; }
.add { font-weight:400; font-size:8pt; color:#52514e; }
figure { margin:0 0 13px; page-break-inside:avoid; }
figure img { width:100%; border:1px solid #d8dade; display:block; }
figcaption { font-size:8.5pt; color:#333; padding-top:5px; line-height:1.55; }
"""

body = '\n'.join(
    f'<tr class="{cls}"><th>{lab}</th><td>{html}</td></tr>' for lab, html, cls in ROWS)

HTML = f"""<!doctype html>
<html lang="ko"><head><meta charset="utf-8">
<title>분석보고서 — 성남 시내버스 350번 무증차 급행 재편</title>
<style>{CSS}</style></head>
<body><div class="wrap">
<div class="head">
  <div class="ev">- AI와 함께하는 교통문제 해결을 위한 데이터 분석 공모전 -</div>
  <h1>분석보고서</h1>
</div>
<table class="form"><tbody>
{body}
</tbody></table>
</div></body></html>"""

os.makedirs('output', exist_ok=True)
out = 'output/분석보고서_350번.html'
open(out, 'w', encoding='utf-8').write(HTML)
print(f'-> {out}  ({len(HTML)/1024/1024:.2f} MB, 그림 {len(FIGS)}장 포함)')
print('   브라우저에서 열고 Ctrl+P → 대상 "PDF로 저장" → 배경 그래픽 켜기')
