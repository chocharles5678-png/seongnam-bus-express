# 성남 시내버스 55번 급행 재편 — 실측 기반 분석

**AI와 함께하는 교통문제 해결을 위한 데이터 분석 공모전** 제출 코드
주최 (재)숲과나눔 풀씨행동연구소 · 한겨레신문

---

## 무엇을 했나

증차 없이 기존 버스의 일부만 급행으로 돌려 통행시간을 줄일 수 있는지를, **버스위치 API로 운행 대수와
왕복 소요시간을 직접 측정해** 검증했다.

1. **무증차 재편이 가능한 노선은 이미 배차가 촘촘한 노선뿐이다.** 정작 불편한 노선은 나눌 차량이 없다.
2. 그 노선에서조차 **무증차 재편의 순효과는 통행당 +0.6분**이다. 42%가 4.2분을 얻고 58%가 2.1분을 잃는다.
3. **차량 3대(+17%)를 늘리면 아무도 손해 보지 않으면서 +2.3분**이 된다.

보고서: [`output/분석보고서_55번.html`](output/분석보고서_55번.html) (브라우저에서 열고 Ctrl+P → PDF로 저장)
작성 원본: [`보고서_55번.md`](보고서_55번.md)

### 실측값

| 노선 | 왕복 소요(실측) | 관측 대수(실측) | 왕복÷대수 | 급행 분리 |
|---|--:|--:|--:|---|
| 88-1 (마을버스) | 98분 | 4~5대 | 24.5분 | 불가 |
| **55** (일반형시내버스) | **195분** | **18대** | **10.8분** | **가능** |
| 380 (일반형시내버스) | 200분 | 10대 | 20.0분 | 불가 |

**관측 대수는 관측된 차량 수이지 인가·배정 대수가 아니다.**

---

## 준비

```bash
cp .env.example .env     # 발급받은 DATA_GO_KR_KEY 를 넣는다
pip install numpy scipy matplotlib
```

인증키는 [공공데이터포털](https://www.data.go.kr/data/15080648)에서 활용신청 후 발급받는다.
개발계정은 **하루 1,000회** 제한이며, 수집 스크립트에 호출 예산 옵션이 있다.

한글 도면을 그리려면 `Malgun Gothic` 폰트가 필요하다(Windows 기본 포함).

---

## 재현

```bash
# 1. 버스 위치 실측 (API 호출 — 키 필요)
python scripts/seongnam/x_collect_location.py 55 --interval 45 --minutes 225 --budget 300

# 2. 급행 정차역 선정
python scripts/seongnam/x_express_trunk.py 55

# 3. 시뮬레이션 — 무증차 / 증차
python scripts/seongnam/x_sim.py 55 --fleet 18 --cycle 195 --T 20
python scripts/seongnam/x_sim_fleet.py 55

# 4. 도면
python scripts/seongnam/x_express_trunk_fig.py 55
python scripts/seongnam/x_sim_fig.py --T 20
python scripts/seongnam/x_report_fig.py

# 5. 보고서 빌드
python scripts/seongnam/x_build_report.py
```

**1번을 건너뛰어도 2~5번은 돌아간다.** 10/5~10/7 관측 원본이
[`data/raw/bus_location/`](data/raw/bus_location/)에 들어 있다(12,435건).

---

## 핵심 스크립트

| 파일 | 하는 일 |
|---|---|
| [`x_collect_location.py`](scripts/seongnam/x_collect_location.py) | 버스위치 API 폴링 → `data/raw/bus_location/YYYYMMDD.jsonl` |
| [`x_express_trunk.py`](scripts/seongnam/x_express_trunk.py) | 급행 정차역 선정 (거점·대학·환승·20대 거점의 합집합) |
| [`x_sim.py`](scripts/seongnam/x_sim.py) | 무증차 재편 시뮬레이션 — 급행/완행 분할 |
| [`x_sim_fleet.py`](scripts/seongnam/x_sim_fleet.py) | 무증차 대 증차 비교 |
| [`x_corridor.py`](scripts/seongnam/x_corridor.py) | 노선 간 공유 구간 연속성 — 정류소ID 기준 전수 비교 |
| [`x_report_fig.py`](scripts/seongnam/x_report_fig.py) | 보고서 도면 (배차 역설 · 증차 효과) |
| [`x_build_report.py`](scripts/seongnam/x_build_report.py) | 공모전 양식 구조의 인쇄용 HTML 생성 |

---

## 방법 — 여기가 핵심이다

### 운행 대수는 10분 단위로 센다

버스위치 API 응답에 **차량번호(`plateNo`)와 정류소순번(`stationSeq`)**이 들어 있다.
관측된 고유 차량번호를 세면 운행 대수가 나오는데, **집계 단위가 결과를 바꾼다.**

| 집계 단위 | 88-1 | 55 | 380 |
|---|--:|--:|--:|
| 1시간 | 6대 | 22~24대 | 13대 |
| **10분** | **4~5대** | **18대** | **10대** |

1시간으로 세면 그 사이 교대·투입된 차량까지 누적돼 과대 집계된다.

### 왕복 소요시간은 완주 차량으로 확인한다

차량별로 정류소 순번이 단조 증가하는 가장 긴 구간을 찾아 전 구간으로 환산한다.
검증은 **여러 차량이 독립적으로 수렴하는가**로 한다. 55번은 3대가 순번 1→126을 완주했다(191·187·195분).

외삽은 위험하다. 88-1번을 구간 중앙값 × 구간 수로 추정하면 78분인데 **실측은 98분**이다(26% 과소).

---

## 자료

| 활용 데이터 | 제공기관 | 플랫폼 | URL |
|---|---|---|---|
| 경기도 버스위치정보 조회 | 경기도 교통정보과 | 공공데이터포털 | https://www.data.go.kr/data/15080648 |
| 경기도 버스노선 조회 | 경기도 교통정보과 | 공공데이터포털 | https://www.data.go.kr/data/15080662 |
| 경기도 버스정류소 현황 | 경기도 | 공공데이터포털 | https://www.data.go.kr/data/15057894 |
| 경기도 정류소별 승하차 인원 집계 (2026.06) | 경기도 버스관리과 | 경기데이터드림 | https://data.gg.go.kr |
| 주민등록 인구통계 — 행정동별 연령별 인구 (2026.08) | 행정안전부 | 주민등록 인구통계 | https://jumin.mois.go.kr |
| 경기버스정보 노선정보 항목 명세 | 경기도 | GBIS | https://www.gbis.go.kr/gbis2014/publicService.action?cmd=mBusRouteInfo |

전부 **공식 OpenAPI와 공개 파일로 취득**했다. 웹 크롤링이나 비공개 경로 접근은 사용하지 않았다.

### 저장소에 없는 자료

용량 때문에 제외했다. 위 출처에서 받아 같은 경로에 두면 된다.

| 경로 | 내용 | 용량 |
|---|---|--:|
| `data/raw/ngii/` | 수치지도 1:5000 DXF (국토정보플랫폼) | 272MB |
| `data/raw/admdong_20260701.geojson` | 행정동 경계 | 34MB |
| `data/raw/N37E127.hgt` | SRTM 고도 — **폐기한 자료** (건물 높이가 지형으로 잡힘) | 25MB |
| `data/raw/gg_ride/` | 승하차 원본 | 15MB |
| `data/*.npz`, `data/*.npy` | 위 자료로 생성한 중간 산출물 | 36MB |

경사 분석(`1_`~`10_` 스크립트)은 이 자료들이 있어야 돌아간다.
**55번 급행 분석(`x_` 스크립트)은 이 자료 없이 전부 재현된다.**

---

## 알려진 한계

- **18대는 관측 차량 수**이지 인가 대수가 아니다. 실제로 5대를 떼어낼 수 있는지 모른다.
- **정차 1회당 손실시간(T)은 실측에 실패**했다(문헌·역산·회귀 모두). 15~30초 범위로 돌렸다.
- **승하차 원본에 노선 구분 컬럼이 없다.** 커버율 65.1%는 그 정류소 전체 노선의 기록 구성비이며
  "55번 승객의 65%"가 아니다. 인원 환산도 불가능하다.
- **온실가스 배출계수의 1차 출처를 확정하지 못해** tCO₂ 감축량을 제시하지 않는다.

자세한 내용은 보고서의 "분석의 한계"와 [`88-1_55번_분석기록.md`](88-1_55번_분석기록.md)를 보라.

---

## AI 활용

Claude (Anthropic) — Claude Code 환경에서 분석 설계, 코드 작성·실행, 검증, 시각화, 보고서 작성에 사용했다.
AI가 낸 결과를 실측·1차 명세·전수 집계로 반증한 사례와 그 교정 과정을 보고서에 모두 기록했다.
