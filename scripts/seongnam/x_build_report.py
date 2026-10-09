"""붙임2 양식 구조의 인쇄용 보고서 HTML 생성 — 그림을 base64로 묻어 단일 파일로 만든다
사용: python scripts/seongnam/x_build_report.py
출력: output/분석보고서_55번.html  (브라우저에서 Ctrl+P → PDF로 저장)
"""
import base64, io, os, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

FIGS = [
    ('figures/급행_55_노선도.png', '그림 1',
     '55번 급행 재편 — 급행 정차 24지점 / 왕복 정차 127회 → 33회',
     '왼쪽은 노선도(원 크기 = 지점 왕복 일평균 승하차), 오른쪽 위는 정차 횟수 비교, '
     '오른쪽 아래는 정류소 순서별 이용량이며 색칠한 막대가 급행 정차 지점이다.'),
    ('figures/배차역설_3개노선.png', '그림 2',
     '배차 역설 — 나눌 수 있는 노선은 이미 배차가 촘촘한 노선뿐이다',
     '세 노선 모두 급행 대수를 늘릴수록 평균이 떨어진다. '
     '급행 간격 30분 이하(음영)와 평균 순효과 0 이상을 동시에 만족하는 배정은 55번의 급행 6대뿐이고, 그조차 +0.20분이다.'),
    ('figures/시뮬레이션_55_T20초.png', '그림 3',
     '무증차 시뮬레이션 — 급행 배정 대수별 배차 간격과 대기시간 (T=20초)',
     '현행 대기 5.4분. 급행을 떼어낼수록 통과 지점의 대기가 가파르게 늘어난다.'),
    ('figures/증차효과_55.png', '그림 4',
     '증차 3대(+17%)면 아무도 손해 보지 않는다',
     '완행 18대를 그대로 두면 급행을 이용할 수 없는 58%의 순효과가 정확히 0이 된다. '
     '평균은 증차 대수에 둔감하므로, 대수는 평균이 아니라 급행 간격으로 정한다.'),
    ('figures/급행_88_1_전후비교.png', '그림 5',
     '대조 사례 — 88-1번(마을버스)은 정차역 설계가 성립해도 나눌 차량이 없다',
     '급행 정차 14지점 22회로 승하차 기록의 70.6%를 담아 55번(65.1%)보다 높지만, '
     '관측 차량이 4~5대뿐이라 1대만 떼어내도 급행이 98분에 한 대가 된다.'),
]

ROWS = []   # (항목명, HTML 본문, 추가 클래스)


def row(label, html, cls=''):
    ROWS.append((label, html, cls))


row('이름 / 팀명', '<p class="blank">[ 기재 필요 ]</p>')

row('주제', """
<p class="lead">증차 없이 기존 버스의 일부만 급행으로 돌려 통행시간을 줄일 수 있는가 —
성남 시내버스 55번의 실측 검증</p>
<p>노선번호도 경로도 바꾸지 않고, 배차된 차량 중 일부만 주요 정류장에 서게 하는 재편이다.
예산이 들지 않으므로 가장 먼저 검토해야 할 선택지다. 버스위치 API로 운행 대수와 왕복 소요시간을
직접 측정해 검증했고, 결과는 세 문장으로 요약된다.</p>
<ol class="key">
  <li><b>무증차 재편이 가능한 노선은 이미 배차가 촘촘한 노선뿐이다.</b> 정작 불편한 노선은 나눌 차량이 없다.</li>
  <li>그 노선에서조차 <b>무증차 재편의 순효과는 통행당 +0.6분</b>에 그친다. 42%가 4.2분을 얻고 58%가 2.1분을 잃는다.</li>
  <li><b>차량 3대(+17%)를 늘리면 아무도 손해 보지 않으면서 +2.3분</b>이 된다.</li>
</ol>
<p><b>무비용 재편으로는 대중교통 경쟁력을 만들 수 없다는 것, 그리고 필요한 최소 투자의 규모가
노선당 3~6대라는 것</b>이 이 분석의 결론이다.</p>
""")

row('분석 배경<br>및 목적', """
<h4>성남 안을 종일 빠르게 잇는 노선이 사실상 없다</h4>
<p>성남을 지나는 급행 계열(광역급행형·직행좌석형) 노선은 103개다. 그중 <b>모든 정류소가 성남 안에 있는
노선은 3개</b>(반디1·1-1·2)뿐이고 <b>셋 다 심야 노선</b>이다. 여기에 성남시가 운영하는 S1·S2를 더해 5개다.</p>
<table class="d">
<tr><th>노선</th><th>유형</th><th>정차</th><th>평일 운행</th><th>토·일</th></tr>
<tr><td>반디1 / 1-1 / 2</td><td>직행좌석형</td><td>27 / 33 / 30</td><td>23:00~05:00 (심야)</td><td>미운행</td></tr>
<tr><td>S1</td><td>일반형</td><td>14</td><td><b>06:40~09:00</b></td><td>미운행</td></tr>
<tr><td>S2</td><td>일반형</td><td>8</td><td><b>06:20~09:25</b></td><td>미운행</td></tr>
</table>
<p><b>평일 낮과 주말에 성남 안을 빠르게 잇는 노선은 없다.</b> 급행 성격의 서비스는 심야와 평일 아침
2~3시간에만 있고, 목적지도 산업단지·벤처단지 통근 하나에 묶여 있다. 판단 근거는 운행 시각 자체이며,
토·일 미운행은 노선 제원의 첫차·막차 값이 0이라는 사실에서 나왔다(시간표 원문 미확인).</p>

<h4>탄소중립이 이동격차와 만나는 지점</h4>
<p>국내 수송부문 온실가스의 대부분은 도로교통에서 발생하고, 감축은 승용차 통행이 대중교통으로
옮겨갈 때 성립한다. 그런데 <b>옮겨탈 대상에 경쟁력이 없으면 전환은 일어나지 않는다.</b>
"자가용을 버리고 버스를 타라"는 요구는 버스가 모든 정류장에 서는 완행뿐인 조건에서는 작동하지 않으며,
그 요구는 승용차를 선택할 여유가 없는 사람에게 더 무겁게 떨어진다.</p>
<p>이 보고서는 감축량을 주장하지 않는다. <b>감축이 성립할 수 있는 조건을 만드는 조치</b>를 다루고,
그 조치가 무비용으로 가능한지를 검증한다.</p>

<h4>왜 "증차 없이"를 먼저 물었는가</h4>
<p>증차는 예산·인가·기사 채용이 모두 걸린다. 반면 기존 차량의 배분만 바꾸는 재편은 즉시 적용할 수 있다.
<b>무증차 재편이 성립하면 그것이 가장 좋은 답이다.</b> 그래서 이 질문을 먼저 검증했고, 결과는 부정적이었다.</p>
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
    <td>https://data.gg.go.kr<br><span class="s">infId=MZCREO5CKHZM6PJEA55P37391662</span></td></tr>
<tr><td>주민등록 인구통계 — 행정동별 연령별 인구현황 (2026.08)</td><td>행정안전부</td><td>주민등록 인구통계</td>
    <td>https://jumin.mois.go.kr</td></tr>
<tr><td>경기버스정보 노선정보 항목 명세</td><td>경기도</td><td>GBIS</td>
    <td>https://www.gbis.go.kr/gbis2014/publicService.action<br><span class="s">?cmd=mBusRouteInfo</span></td></tr>
</table>

<h4>수집 방법 · 기준시점 · 주요 변수 · 이용조건</h4>
<table class="d">
<tr><th>구분</th><th>내용</th></tr>
<tr><td>수집 방법</td><td><b>공공데이터포털 활용신청 후 발급받은 인증키로 공식 OpenAPI를 호출</b>했다.
  웹페이지 크롤링이나 비공개 경로 접근은 사용하지 않았다. 개발계정 한도(일 1,000회)를 넘기지 않도록
  수집 스크립트에 호출 예산을 두었다(2026-10-07 당일 총 992회).</td></tr>
<tr><td>수집 기간</td><td>버스위치 2026-10-05 ~ 10-07(평일 3일, 폴링 30~45초). 승하차 2026-06-30 기준.
  인구 2026-08-31 기준. 노선·정류소 제원 2026-10 조회분.</td></tr>
<tr><td>주요 변수</td><td>위치 API — <code>ts, route, routeId, plateNo, stationId, stationSeq, endBus, remainSeat</code><br>
  노선 API — 경유 정류소 순서, 기·종점, <code>peekAlloc</code>(평일 최소 배차), <code>nPeekAlloc</code>(평일 최대 배차), 첫차·막차<br>
  승하차 — 정류소ID, 승차합계, 초승, 환승, 하차합계</td></tr>
<tr><td>이용 조건</td><td>승하차 자료는 상업적 이용 및 콘텐츠 변경 허용. OpenAPI는 공공데이터포털 이용약관에 따름.
  인증키는 환경변수로 분리해 코드·대화·제출물에 포함하지 않았다.</td></tr>
</table>

<h4>선정 이유</h4>
<ul>
<li><b>버스위치정보 API</b> — 이 분석의 핵심 자료다. 응답에 차량번호(<code>plateNo</code>)와
  정류소순번(<code>stationSeq</code>)이 있어 <b>운행 대수와 왕복 소요시간을 추정이 아니라 실측</b>할 수 있다.</li>
<li><b>버스노선 조회 API</b> — 노선별 경유 정류소 순서와 배차 범위를 얻었다.</li>
<li><b>승하차 인원 집계</b> — 정류소별 이용량으로 급행 정차역을 선정했다(성남시 1,305개소, 총 24,860,507건).</li>
<li><b>연령별 인구</b> — 행정동별 20대 인구로 통학·통근 축을 식별했다.</li>
<li><b>GBIS 명세</b> — 배차 필드의 정의 확인용. 초기에 <code>peekAlloc</code>을 "첨두 배차"로 오독했고,
  명세 원문에서 <b>"평일 최소 배차시간(분)"</b>임을 확인해 관련 주장을 전부 철회했다.</li>
</ul>
""")

row('분석과정<br>및 방법', """
<div class="flow">
<b>1단계</b> 버스위치 API 폴링 → 차량별 정류소 통과 시각 복원<br>
<b>2단계</b> 운행 대수(고유 차량번호) · 왕복 소요시간(순번 단조증가 구간) 실측<br>
<b>3단계</b> 급행 정차역 선정 — 승하차·인구·환승 기준의 합집합<br>
<b>4단계</b> 무증차 / 증차 시나리오의 대기시간·차내시간 시뮬레이션
</div>

<h4>운행 대수 — 세는 단위가 결과를 바꾼다</h4>
<p>관측된 <b>고유 차량번호를 센다.</b> 집계 단위가 결정적이다.</p>
<table class="d n">
<tr><th>집계 단위</th><th>88-1</th><th>55</th><th>380</th></tr>
<tr><td>1시간</td><td>6대</td><td>22~24대</td><td>13대</td></tr>
<tr class="hl"><td><b>10분</b></td><td><b>4~5대</b></td><td><b>18대</b></td><td><b>10대</b></td></tr>
</table>
<p>1시간으로 세면 그 사이 교대·투입된 차량까지 누적돼 <b>과대 집계된다.</b> 10분이면 차량 교체가 거의 없고
왕복 소요시간(98~200분)에 비해 충분히 짧다. <b>10분 단위 중앙값</b>을 썼다.</p>

<h4>왕복 소요시간 — 완주 차량으로 확인</h4>
<p>차량별로 정류소 순번이 <b>단조 증가하는 가장 긴 구간</b>을 찾아 전 구간으로 환산한다.</p>
<p class="eq">전구간 환산 = 관측 소요시간 × 전체 구간 수 ÷ 관측 구간 수</p>
<p>55번은 추적한 15대 중 <b>3대가 순번 1→126을 완주</b>(진행률 98~99%)해 환산이 거의 필요 없었다
(191분 / 187분 / 195분). <b>검증은 여러 차량이 독립적으로 수렴하는지로 했다.</b> 15대 중앙값 195분이고,
중간 점검(10:30, 8대)과 최종(12:52, 15대)이 모두 195분으로 일치했다.</p>
<p>이 방법은 앞선 추정을 뒤집었다. 88-1번은 구간 소요시간 중앙값 × 구간 수로 <b>78분</b>을 추정했으나
실측은 <b>98분</b>이었다. 회차·회복 시간이 빠져 <b>26% 과소평가</b>였다.</p>

<h4>급행 정차역 선정 규칙 — 합집합</h4>
<div class="rule">
1. 기·종점·회차점 &nbsp;|&nbsp; 2. 거점: 지점 왕복 일평균 ≥ 3,000건 &nbsp;|&nbsp;
3. 대학: 정류소명에 대학·가천대·을지대·신구대 포함 AND ≥ 1,000건<br>
4. 환승거점: 마을버스 5개 이상 경유 &nbsp;|&nbsp; 5. 20대 거점: 행정동 20대 ≥ 2,500명 AND 지점 ≥ 1,500건
</div>
<p>교집합이 아닌 이유는 모든 조건을 만족하는 정류소가 거의 없어 교집합으로는 최대 거점이 탈락하기 때문이다.
모든 집계는 <b>정류소 고유ID 기준</b>으로 했다. 경기도 노선번호는 시·군 간 중복되고 같은 이름의 정류장이
길 양쪽에 따로 있어, 이름으로 집계하면 성남에서 <b>동명 그룹 102곳의 값이 뭉개진다</b>
(판교역서편은 세 ID가 각각 마을버스 6개 / 1개 / 0개).</p>

<h4>시뮬레이션 모형</h4>
<div class="rule">
· 관측 차량을 급행 N대 / 완행 M대로 나눈다<br>
· 완행 왕복 = 195분(실측). 급행 왕복 = 195 − (통과 94회 × T)<br>
· 각 서비스는 자기 왕복시간 ÷ 자기 대수 간격으로 운행한다고 본다<br>
· 승객이 무작위 시각에 도착한다고 보고 평균 대기 = E[gap²] / (2·E[gap])<br>
· 급행 이용 가능 = 출발·도착이 모두 급행 정차 지점인 통행
</div>
<p><b>T(정차 1회당 손실시간)는 가정값이다.</b> 실측을 세 방법으로 시도해 모두 실패했다.
15·20·25·30초로 모두 돌렸으며 본문은 20초 기준이다.</p>
""")

row('AI 기술<br>활용', """
<h4>사용 서비스</h4>
<p><b>Claude (Anthropic) — Claude Code 환경.</b> 분석 설계, 수집·분석 코드 작성과 실행, 결과 검증,
시각화, 보고서 작성 전 과정에 대화형으로 사용했다.</p>

<h4>활용 범위</h4>
<table class="d">
<tr><th>단계</th><th>AI가 한 일</th><th>사람이 한 일</th></tr>
<tr><td>데이터 수집</td><td>API 폴링 스크립트 작성, 호출 예산 관리, 응답 캐싱</td><td>자료 선정, 수집 실행, 수집 시간대 결정</td></tr>
<tr><td>전처리</td><td>차량별 추적표 복원, 정류소ID 기준 집계</td><td>—</td></tr>
<tr><td>분석</td><td>운행 대수·왕복시간 산출, 정차역 선정 구현, 대기시간 시뮬레이션</td><td><b>판정 기준값 결정</b>, 노선 선정</td></tr>
<tr><td>검증</td><td>민감도 분석, 전수 집계, 자기 오류 정정</td><td><b>동료 검토 요청</b>, 지적 수용 판단</td></tr>
<tr><td>시각화</td><td>노선도·시뮬레이션 도면 생성</td><td>—</td></tr>
<tr><td>보고서</td><td>초안 작성, 구조 설계</td><td><b>방향 결정</b>, 결론 표현 수위 조정</td></tr>
</table>

<h4>주요 프롬프트</h4>
<p class="note">아래 ①②는 기록에 남은 실제 지시다. ③④⑤는 분석 방향을 바꾼 지점이며,
<b>실제 입력한 문장으로 교체해야 한다.</b> AI가 문장을 지어내지 않도록 임의 작성하지 않았다.</p>
<p><b>① 검증 강화 요구</b></p>
<blockquote>이제부터 어떠한 정보를 줄 때 제대로 더블체크해서 나한테 보내줘.</blockquote>
<p class="arrow">→ 이후 외부 사실을 1차 명세로 재확인했고, 그 과정에서 배차 필드 오독(<code>peekAlloc</code>)을
발견해 관련 주장을 전부 철회했다.</p>
<p><b>② 가정 점검</b></p>
<blockquote>이 숫자가 맞는지 어떻게 아는가.</blockquote>
<p class="arrow">→ 추정값(88-1 왕복 78분)을 실측으로 대체하게 된 계기다. 실측 98분으로 26% 과소평가였다.</p>
<p><b>③ 실측 방법 설계</b> <span class="blank">[ 실제 입력 문장 기재 필요 ]</span><br>
<b>④ 노선 전환 결정</b> <span class="blank">[ 실제 입력 문장 기재 필요 ]</span><br>
<b>⑤ 선정 규칙 단순화</b> <span class="blank">[ 실제 입력 문장 기재 필요 ]</span></p>

<h4>AI 생성 결과의 직접 검증</h4>
<ol>
<li><b>실측으로 AI의 추정을 반증했다.</b> AI가 외삽으로 낸 88-1 왕복 78분은 실측 98분과 26% 차이였다.
  이후 외삽값은 결론에 쓰지 않는 규칙을 적용했다.</li>
<li><b>1차 명세로 AI의 필드 해석을 반증했다.</b> <code>peekAlloc</code>을 "첨두 배차"로 읽은 것이 오독임을
  GBIS 명세 원문에서 확인하고, 그에 기반한 주장 4건을 철회했다.</li>
<li><b>전수 집계로 AI의 일반화를 반증했다.</b> "성남 시내버스는 22시에 끊긴다"는 서술을 전수로 확인하니
  <b>192개 노선이 23시 이후 운행</b>했다. 몇 개 후보만 보고 단정한 오류였다.</li>
<li><b>탐색 범위를 전수로 돌려 코드의 결함을 찾았다.</b> 시뮬레이션 코드가 급행 대수 후보를 일부 값으로
  고정해 두어 "380번은 무증차로 전부 마이너스"라는 잘못된 결론이 나왔다. 전수로 돌리니
  급행 1대 +1.2분 / 2대 +0.1분이었다.</li>
<li><b>외부 검토를 받아 사실 오류 8건을 수정했다.</b> 동료 검토자가 지적한 내용(배차 필드 정의,
  구성비를 인원으로 오용, 시나리오를 확정으로 서술 등)을 전부 수용하고 문서와 코드를 수정했다.</li>
<li><b>개인정보·비공개 자료는 입력하지 않았다.</b> 전부 공개 데이터이며 인증키는 환경변수로 분리했다.</li>
</ol>
""")

row('분석 내용<br>및 결과', """
<h4>실측 — 세 노선</h4>
<p>2026-10-05 ~ 10-07, 원시 관측 <b>12,435건</b>(10-07 기준).</p>
<table class="d n">
<tr><th>노선</th><th>유형</th><th>왕복<br>정차</th><th>공시 배차<br>(최소~최대)</th><th>왕복 소요<br><b>(실측)</b></th>
    <th>관측 대수<br><b>(실측)</b></th><th>왕복÷대수</th><th>급행 분리</th></tr>
<tr><td>88-1</td><td>마을버스</td><td>71회</td><td>15~25분</td><td><b>98분</b></td><td><b>4~5대</b></td>
    <td>24.5분</td><td class="no">불가</td></tr>
<tr class="hl"><td><b>55</b></td><td>일반형시내버스</td><td>127회</td><td>10~20분</td><td><b>195분</b></td>
    <td><b>18대</b></td><td><b>10.8분</b></td><td class="ok">가능</td></tr>
<tr><td>380</td><td>일반형시내버스</td><td>106회</td><td>15~25분</td><td><b>200분</b></td><td><b>10대</b></td>
    <td>20.0분</td><td class="no">불가</td></tr>
</table>
<p><b>갈림길은 관측 차량 수 하나다.</b> 88-1번은 4대 중 1대만 급행으로 돌려도 급행이 98분에 한 대 오면서
완행 간격이 24.5분 → 32.7분으로 벌어진다. 380번은 급행 간격을 30분 이하로 만들려면 6대가 필요하고
그 경우 평균 순효과가 −5.9분이다. <b>55번만 나눌 여력이 있었다.</b></p>

<h4>핵심 발견 — 배차 역설</h4>
<div class="box">
현행 간격 <b>10.8분</b> → 나눌 여력 있음 (55번)<br>
현행 간격 <b>20.0분</b> → 이미 빠듯 (380번)<br>
현행 간격 <b>24.5분</b> → 불가능 (88-1번)
</div>
<p class="big"><b>자주 다니는 노선만 급행으로 나눌 수 있다. 그런데 그런 노선은 이미 서비스가 괜찮다.
정작 불편한 노선일수록 재편이 안 된다.</b></p>
<p>무증차 재편은 구조적으로 <b>서비스가 좋은 곳에만 적용 가능한 처방</b>이다.</p>

<h4>55번 급행 정차역 — 91지점 중 24지점</h4>
<p>왕복 127회 정차 중 <b>33회만 정차하고 94회를 통과한다.</b></p>
<table class="d">
<tr><th>선정 사유</th><th>지점</th><th>대표 정류소 (지점 왕복 일평균)</th></tr>
<tr><td>거점 (≥3,000건)</td><td>10</td><td>야탑역(16,203) · 모란역2.3번출구(12,346) · 판교역동편(11,173)</td></tr>
<tr><td>20대 거점</td><td>5</td><td>삼평교 · 차그룹컨소시엄 · 성남역.백현마을2단지 · 은행동현대아파트 · 한국무역정보통신</td></tr>
<tr><td>환승거점 (마을버스 5개↑)</td><td>4</td><td>동부.코오롱아파트 · 백현마을1단지 · 상원초교.성남중앙병원 · 상원초등학교</td></tr>
<tr><td>대학</td><td>3</td><td>을지대학교 · 을지대학교.생활관 · 신구대학사거리</td></tr>
<tr><td>기·종점</td><td>2</td><td>금토동삼거리 · 남위례역</td></tr>
<tr class="hl"><td colspan="2"><b>합계 24지점 33회</b></td><td><b>승하차 기록의 65.1%</b></td></tr>
</table>
<p class="warn"><b>65.1%의 분모.</b> 그 정류소에 서는 <b>모든 노선의 승하차 기록</b> 구성비다.
승하차 원본에 노선 구분 컬럼이 없어 "55번 승객의 65%"라고 말할 수 없고 인원으로도 환산할 수 없다.</p>

<h4>무증차 재편의 순효과는 +0.6분이다</h4>
<p>관측 18대를 급행 5대 / 완행 13대로 나눈 경우(T=20초 가정):</p>
<table class="d n">
<tr><th></th><th>현행</th><th>재편 후</th><th></th><th>비중</th><th>순효과</th></tr>
<tr><td>완행 간격</td><td>10.8분</td><td><b>15.0분</b></td>
    <td>급행 이용 가능</td><td>42%</td><td class="ok"><b>+4.2분</b></td></tr>
<tr><td>급행 간격</td><td>—</td><td>32.7분</td>
    <td>급행 이용 불가</td><td>58%</td><td class="no"><b>−2.1분</b></td></tr>
<tr><td>정차 지점 대기</td><td>5.4분</td><td>6.4분</td>
    <td><b>평균</b></td><td></td><td class="hl2"><b>+0.6분</b></td></tr>
<tr><td><b>통과 지점 대기</b></td><td>5.4분</td><td><b>7.5분</b></td><td colspan="3"></td></tr>
</table>
<p><b>대기시간은 모든 지점에서 늘어난다.</b> 급행 정차 지점조차 5.4 → 6.4분이다. 차량 수는 같은데
두 서비스로 나뉘며 도착이 불규칙해지기 때문이다. "18대 그대로니 빈도는 유지된다"는 단순 합산과 다르다.
<b>이득은 전적으로 차내 시간에서 나온다.</b></p>
<p class="warn"><b>42%의 산출 근거.</b> 승하차 기록 구성비 65.1%의 제곱이다. 출발지와 도착지가
독립이라고 가정했다. 노선별 OD 자료가 없어 실제 통행의 분포는 모른다.</p>

<h4>무증차에서는 "쓸 만한 급행"과 "플러스 평균"을 동시에 만족할 수 없다</h4>
<p>급행 대수를 1~17대로 전수 계산하면 <b>평균 순효과는 급행 대수를 줄일수록 커진다</b>
(1대 +1.94분 → 5대 +0.58분 → 7대 −0.31분). 평균만 보면 급행 1대가 최선이지만, 급행이
<b>164분에 한 대</b> 오는 것은 급행이 아니라 특별편이다. 두 조건을 함께 걸면 남는 배정이 거의 없다.</p>
<table class="d n">
<tr><th>노선</th><th>급행 간격 30분 이하가 되는 최소 대수</th><th>그때의 평균 순효과</th></tr>
<tr><td>88-1</td><td>3대 (27.2분) — 완행이 1대만 남는다</td><td class="no"><b>−17.13분</b></td></tr>
<tr class="hl"><td><b>55</b></td><td><b>6대 (27.3분)</b></td><td class="hl2"><b>+0.20분</b></td></tr>
<tr><td>380</td><td>6대 (29.2분) — 완행이 4대로 준다</td><td class="no"><b>−5.65분</b></td></tr>
</table>
<p class="big"><b>세 노선 중 두 조건을 동시에 만족하는 것은 55번뿐이고, 그조차 +0.20분 — 통행당 12초다.</b></p>
<p>이것이 무증차 재편의 구조적 한계다. 급행을 실제로 탈 수 있게 만드는 것과 전체 평균을 지키는 것이
상충한다. 차량 총량이 고정돼 있어 한쪽을 얻으면 반대쪽을 잃는다.</p>

<h4>증차 3대면 아무도 손해 보지 않는다</h4>
<p>완행 18대를 그대로 두고 급행을 <b>더하는</b> 방식이면 통과 지점의 손해가 0이 된다.</p>
<table class="d n">
<tr><th>증차</th><th>총 대수</th><th>증차율</th><th>급행 간격</th><th>완행 간격</th>
    <th>급행 이용 순</th><th>이용 불가 순</th><th><b>평균 순</b></th></tr>
<tr><td>0 (무증차 5대 분리)</td><td>18</td><td>—</td><td>32.7분</td><td>15.0분</td>
    <td>+4.2분</td><td class="no">−2.1분</td><td><b>+0.6분</b></td></tr>
<tr class="hl"><td><b>3</b></td><td>21</td><td><b>+17%</b></td><td>54.6분</td><td><b>10.8분 유지</b></td>
    <td>+5.4분</td><td class="ok"><b>−0.0분</b></td><td class="hl2"><b>+2.3분</b></td></tr>
<tr><td>6</td><td>24</td><td>+33%</td><td>27.3분</td><td>10.8분 유지</td><td>+5.7분</td>
    <td class="ok">−0.0분</td><td><b>+2.5분</b></td></tr>
<tr><td>11</td><td>29</td><td>+61%</td><td>14.9분</td><td>10.8분 유지</td><td>+6.5분</td>
    <td class="ok">−0.0분</td><td><b>+2.8분</b></td></tr>
</table>
<p><b>증차의 본질적 이점은 평균값이 아니라 손해의 소멸이다.</b> 완행 18대가 그대로 남으므로
급행을 이용할 수 없는 58%의 순효과가 <b>정확히 0</b>이 된다.</p>
<p>그리고 <b>평균 순효과는 증차 대수에 거의 둔감하다</b>(1대 +2.27 / 3대 +2.28 / 12대 +2.85분).
이득의 대부분이 대기시간이 아니라 <b>차내 단축</b>에서 나오기 때문이다. 따라서
<b>증차 대수는 평균이 아니라 급행 간격으로 정해야 한다</b> — 3대면 54.6분(완행을 타다가 운 좋으면 급행),
6대면 27.3분(급행을 보고 기다릴 수 있는 수준)이다.</p>

<h4>민감도 — 결론의 방향은 기준값에 흔들리지 않는다</h4>
<table class="d n">
<tr><th>거점 / 20대 기준</th><th>급행 정차</th><th>담는 기록</th></tr>
<tr><td>2,000건 / 1,500명</td><td>32지점 46회</td><td>76.0%</td></tr>
<tr class="hl"><td><b>3,000건 / 2,500명 (본문)</b></td><td><b>24지점 33회</b></td><td><b>65.1%</b></td></tr>
<tr><td>4,000건 / 3,500명</td><td>19지점 27회</td><td>59.4%</td></tr>
</table>
<p>정차 지점 수는 19~32개로 흔들리지만 <b>"무증차로는 효과가 작고 소폭 증차가 필요하다"는 결론의
방향은 바뀌지 않는다.</b> 기준을 낮추면 정차가 늘어 급행 차내 단축이 줄고, 높이면 통과 지점이 늘어
손해 보는 비중이 커진다. 양방향 모두 무증차 재편에 불리하다.</p>
""")

row('정책제안<br>및 기대효과', """
<table class="d">
<tr><th></th><th>제안</th><th>비용</th></tr>
<tr><td><b>1</b></td><td><b>무증차 급행 재편을 단독 처방으로 채택하지 않는다.</b> 55번 기준 평균 순효과 +0.6분이며,
  통행의 58%는 오히려 손해를 본다. 급행 간격을 쓸 만한 수준으로 맞추면 평균은 +0.20분까지 떨어진다</td><td>—</td></tr>
<tr><td><b>2</b></td><td>55번에 <b>차량 3대(+17%)를 증차</b>하고 그 3대를 급행(24지점 정차)으로 운행한다.
  완행 18대는 그대로 두어 <b>기존 이용자의 손해를 0으로 유지</b>한다. 급행을 독립 수단으로 쓰게 하려면 6대(+33%)</td>
  <td>차량 3~6대</td></tr>
<tr><td><b>3</b></td><td>증차 급행의 적용 조건을 <b>"현행 간격 11분 이하 노선"</b>으로 설정한다.
  그 이상인 노선은 무증차 분리가 성립하지 않음을 실측으로 확인했다</td><td>—</td></tr>
<tr><td><b>4</b></td><td>급행 정차역에 <b>환승거점 4곳 · 20대 거점 5곳</b>을 포함해 마을버스 연계와 통학 축을 함께 담는다</td>
  <td>안내체계</td></tr>
<tr><td><b>5</b></td><td>S1·S2의 운행 시간대를 <b>퇴근·주말로 확대</b>하는 방안을 별도 검토한다.
  현재 성남 내부 급행은 심야 3개와 평일 아침 2개뿐이다</td><td>별도 검토</td></tr>
</table>

<h4>기대효과</h4>
<ul>
<li>55번 통행당 평균 <b>+2.3분 단축</b>(증차 3대, T=20초 가정). 급행 이용 가능 통행은 +5.4분</li>
<li><b>기존 이용자의 불이익 없음.</b> 완행 간격 10.8분 유지</li>
<li>급행 정차 24지점이 해당 정류소 승하차 기록의 <b>65.1%</b>를 담음</li>
<li>적용 가능 노선을 <b>실측 기준(현행 간격 11분 이하)</b>으로 판별 가능 — 같은 방법을 타 노선·타 도시에 적용</li>
<li>필요 투자 규모를 <b>노선당 3~6대</b>로 특정</li>
</ul>

<h4>기존 정책과 다른 점</h4>
<p>성남시는 이미 S1·S2로 "정차를 줄여 빠르게 잇는다"는 발상을 실행했다. 그러나 <b>평일 아침 2~3시간,
통근 목적 하나</b>에 한정된다. 또한 마을버스 4개 이상이 서는 성남 전역 거점 65곳 중 S1·S2가 서는 곳은
<b>0곳</b>이다(동일 정류소ID 기준. 환승 가능성 자체를 부정하는 것은 아니다).</p>
<p>이 제안은 <b>종일 운행하는 간선 노선에 급행 층을 더하고, 그 정차역에 마을버스 환승거점을 포함</b>시킨다.
그리고 그것이 무비용으로는 불가능하다는 것을 추정이 아니라 실측으로 보인다.</p>
""")

row('분석의 한계<br><span class="add">(추가 항목)</span>', """
<h4>18대는 관측 차량 수이지 인가 대수가 아니다</h4>
<p>인가·배정 대수는 공개 자료에 없다. <b>실제로 5대를 급행으로 떼어낼 수 있는지 모른다.</b>
인가 조건, 기사 배치, 차고지 운영, 회복시간 요건을 확인하지 못했다. 모든 재편안은 <b>시나리오</b>다.</p>

<h4>정차 1회당 손실시간(T)은 실측에 실패했다</h4>
<table class="d">
<tr><th>시도</th><th>결과</th></tr>
<tr><td>문헌</td><td>접근 가능한 국내 연구가 서울 간선·중앙차로 기준이라 부적합</td></tr>
<tr><td>첫차 시각 역산</td><td>기점·종점 첫차 시각차가 편도거리와 <b>음의 상관(−0.51)</b>. 소요시간이 아니었다</td></tr>
<tr><td>회귀</td><td>구간 소요시간을 거리로 설명 → <b>R² 0.08</b>, 환산 주행속도 61~113km/h로 비현실적</td></tr>
</table>
<p>T는 급행 <b>차내 단축폭</b>을 좌우한다. 다만 T를 15~30초로 바꿔도 권장 급행 대수는 5~6대로 동일하다.
대수 배분 결론은 T에 견고하고, 효과 크기는 가정 위에 있다.</p>

<h4>탄소 감축량을 환산하지 못했다</h4>
<p><b>온실가스 배출계수의 1차 출처를 확정하지 못했다.</b> 검색으로 후보값은 확인했으나 원문 페이지가
열리지 않았거나 기준연도가 2001년이어서 사용을 보류했다. 따라서 이 보고서는 <b>tCO₂ 감축량을
제시하지 않는다.</b> 또한 증차는 버스 운행 배출을 늘리므로 "버스 추가 배출 vs 승용차 전환 감축"의
순효과는 배출계수 없이 계산할 수 없다. 수단 전환 탄력성 자료도 확보하지 못했다.</p>

<h4>선정 기준의 임의성</h4>
<p>20대의 실제 통행 목적지는 자료가 없어 <b>대학·판교 입지로 대리</b>했다. 목적지를 "대학 + 판교 주요
지점"으로 정의한 결과 <b>판교를 경유하는 노선이 구조적으로 유리해졌고</b>, 55번이 선정된 데에는 이 기준의
영향이 있다. 정차역 기준에 대해서는 민감도 분석을 수행했다(위 참조).</p>

<h4>그 밖에 확보하지 못한 자료</h4>
<p>노선별 OD(55번 승객만의 통행), 시간대별 승하차(원본에 시간 구분 없음), 승하차의 연령 구분,
S1·S2 이용 실적.</p>
""")

row('분석도구<br>및 참고문헌', """
<table class="d">
<tr><th>구분</th><th>내용</th></tr>
<tr><td>언어</td><td>Python 3.14 (numpy, scipy, matplotlib)</td></tr>
<tr><td>자료 수집</td><td>공공데이터포털 OpenAPI 폴링(30~45초 간격, 일 1,000회 예산 관리)</td></tr>
<tr><td>주요 산출</td><td>차량별 순번 추적, 10분 단위 고유차량 계수, 단조증가 구간 환산,
  대기시간 분포 E[gap²]/(2·E[gap]), 민감도 분석</td></tr>
<tr><td>버전관리</td><td>Git</td></tr>
<tr><td>AI 도구</td><td>Claude (Anthropic) — Claude Code</td></tr>
<tr><td><b>코드</b></td><td class="blank"><b>[ GitHub 링크 기재 필요 — 저장소 미생성 ]</b></td></tr>
</table>

<h4>재현 절차</h4>
<pre>python scripts/seongnam/x_collect_location.py 55 --interval 45 --minutes 225 --budget 300
python scripts/seongnam/x_express_trunk.py 55
python scripts/seongnam/x_sim.py 55 --fleet 18 --cycle 195 --T 20
python scripts/seongnam/x_sim_fleet.py 55</pre>
<p>원시 관측은 <code>data/raw/bus_location/*.jsonl</code>에 날짜별로 쌓인다.
인증키는 <code>.env</code>에서 읽으며 코드에 포함되지 않는다.</p>

<h4>참고문헌</h4>
<ul>
<li>경기버스정보(GBIS) 노선정보 항목조회 명세 — 배차·운행시간 필드 정의.
  https://www.gbis.go.kr/gbis2014/publicService.action?cmd=mBusRouteInfo</li>
<li>공공데이터포털, 경기도 버스위치정보 조회. https://www.data.go.kr/data/15080648</li>
<li>공공데이터포털, 경기도 버스노선 조회. https://www.data.go.kr/data/15080662</li>
<li>경기데이터드림, 경기도 정류소별 승하차 인원 집계(2026.06). https://data.gg.go.kr</li>
<li>행정안전부, 주민등록 인구통계 — 행정동별 연령별 인구현황(2026.08). https://jumin.mois.go.kr</li>
<li class="blank">[ 정차시간(dwell time) 관련 문헌 — 국내 간선 기준 자료만 확인되어 본문에서 사용하지 않음 ]</li>
<li class="blank">[ 온실가스 배출계수 — 1차 출처 미확정으로 본문에서 사용하지 않음 ]</li>
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
div.flow { line-height:1.95; }
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
<title>분석보고서 — 성남 시내버스 55번 급행 재편</title>
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
out = 'output/분석보고서_55번.html'
open(out, 'w', encoding='utf-8').write(HTML)
print(f'-> {out}  ({len(HTML)/1024/1024:.2f} MB, 그림 {len(FIGS)}장 포함)')
print('   브라우저에서 열고 Ctrl+P → 대상 "PDF로 저장" → 배경 그래픽 켜기')
