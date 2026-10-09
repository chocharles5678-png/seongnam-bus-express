import { readFileSync } from "fs";
import * as XLSX from "xlsx";

const data = JSON.parse(readFileSync("data/gg_seoul_od_commute_weekday.json", "utf-8"));

const wb = XLSX.utils.book_new();

const dt = (city: string, daytype: string) => data.city_daytype[`${city}|${daytype}`] || 0;
const purposeAt = (city: string, daytype: string) => data.purpose_by_city_daytype[`${city}|${daytype}`] || {};
const transAt = (city: string, daytype: string) => data.trans_by_city_daytype[`${city}|${daytype}`] || {};

// Sheet 1: TOP10 요약 (평일/주말/합계)
const summaryRows = data.top10.map((city: string, i: number) => ({
  순위: i + 1,
  "시군구(원자료 단위)": city,
  평일_합계: Math.round(dt(city, "평일")),
  주말_합계: Math.round(dt(city, "주말")),
  전체_합계: Math.round(dt(city, "평일") + dt(city, "주말")),
}));
const wsSummary = XLSX.utils.json_to_sheet(summaryRows);
wsSummary["!cols"] = [{ wch: 6 }, { wch: 20 }, { wch: 14 }, { wch: 14 }, { wch: 14 }];
XLSX.utils.book_append_sheet(wb, wsSummary, "TOP10 요약(평일주말)");

// Sheet 2: 평일 - 목적별/수단별
const purposeOrder = ["출근", "등교"];
const transOrder = ["노선버스", "지하철", "고속버스", "기차"];

function buildDetailRows(daytype: string) {
  return data.top10.map((city: string) => {
    const p = purposeAt(city, daytype);
    const t = transAt(city, daytype);
    const row: Record<string, any> = { 시군구: city };
    for (const key of purposeOrder) row[`목적_${key}`] = Math.round(p[key] || 0);
    for (const key of transOrder) row[`수단_${key}`] = Math.round(t[key] || 0);
    row["합계"] = Math.round(dt(city, daytype));
    return row;
  });
}

const wsWeekday = XLSX.utils.json_to_sheet(buildDetailRows("평일"));
wsWeekday["!cols"] = [{ wch: 20 }, { wch: 12 }, { wch: 12 }, { wch: 12 }, { wch: 12 }, { wch: 12 }, { wch: 12 }, { wch: 12 }];
XLSX.utils.book_append_sheet(wb, wsWeekday, "평일 상세");

const wsWeekend = XLSX.utils.json_to_sheet(buildDetailRows("주말"));
wsWeekend["!cols"] = [{ wch: 20 }, { wch: 12 }, { wch: 12 }, { wch: 12 }, { wch: 12 }, { wch: 12 }, { wch: 12 }, { wch: 12 }];
XLSX.utils.book_append_sheet(wb, wsWeekend, "주말 상세");

// Sheet 3: 전체 수집 시군구 순위 (16개 시군 전체, 평일/주말/합계)
const allRows = data.all_cities
  .map((city: string) => ({
    city,
    평일: dt(city, "평일"),
    주말: dt(city, "주말"),
    합계: dt(city, "평일") + dt(city, "주말"),
  }))
  .sort((a: any, b: any) => b.합계 - a.합계)
  .map((r: any, i: number) => ({
    순위: i + 1,
    "시군구(원자료 단위)": r.city,
    평일_합계: Math.round(r.평일),
    주말_합계: Math.round(r.주말),
    전체_합계: Math.round(r.합계),
  }));
const wsAll = XLSX.utils.json_to_sheet(allRows);
wsAll["!cols"] = [{ wch: 6 }, { wch: 20 }, { wch: 14 }, { wch: 14 }, { wch: 14 }];
XLSX.utils.book_append_sheet(wb, wsAll, "수집된 전체 시군구 순위");

// Sheet 4: 출처 및 주의사항
const noteRows = [
  { 항목: "출처", 내용: "공공데이터포털(data.go.kr) 경유 → 경기데이터드림(data.gg.go.kr) '시군구간 성별/연령별 이동목적/수단 OD 데이터' [infId=1OHUUK6IHNFAQBULU3O234999490, infSeq=2]" },
  { 항목: "원본 테이블", 내용: "GG_PURPOSE_TRANS_SEXAGE_SGG_OD (경기도 시군 민간데이터 규격서_통신 기준)" },
  { 항목: "다운로드한 파일", 내용: "시군구간 성별연령별 이동목적수단 OD 데이터_202601-202603.zip — 해당 데이터셋의 가장 최근 파일 (2026년 1~3월)" },
  {
    항목: "필터 조건",
    내용:
      "① 출발지 시도(O_MEGA_NM)=경기도, 도착지 시도(D_MEGA_NM)=서울특별시 " +
      "② 연령대(AGE_GRP)=03,04,05 → 20대·30대·40대 " +
      "③ 이동목적(PURPOSE)=1(출근),2(등교) → '학교 출석 및 통근'만 " +
      "④ 이동수단(TRANS_GB)=1(노선버스),2(지하철),4(고속버스),5(기차) → '대중교통'만 (차량·도보·항공·기타는 제외) " +
      "⑤ 요일(DOW)을 평일(월~금)/주말(토,일)로 분리 집계",
  },
  { 항목: "'대중교통' 정의에 대한 판단", 내용: "원자료의 TRANS_GB 8개 코드 중 노선버스·지하철·고속버스·기차 4개를 대중교통으로 분류했습니다(차량=승용차, 도보, 항공, 기타는 제외). 고속버스·기차는 통근/통학 비중이 크지 않을 수 있으나 대중교통 수단이므로 포함했습니다. 이 분류 기준은 저희가 임의로 정한 것이니, 기준을 다르게 원하시면 다시 집계해드릴 수 있습니다." },
  { 항목: "AGE_GRP 코드 정의", 내용: "01:0-9세, 02:10-19세, 03:20-29세, 04:30-39세, 05:40-49세, 06:50-59세, 07:60-69세, 08:70세 이상 (규격서 원문 기준)" },
  {
    항목: "⚠ 중요 — 데이터 커버리지 한계",
    내용:
      "이 데이터셋은 경기도 31개 시군 중 16개 시군(광명시,김포시,남양주시,성남시,수원시,시흥시,안산시,안양시,여주시,연천군,용인시,의정부시,파주시,포천시,하남시,화성시)만 포함합니다. " +
      "고양시,부천시,과천시,구리시,광주시,군포시,동두천시,양주시,양평군,오산시,의왕시,이천시,가평군,안성시,평택시(15개)는 이 파일에 없습니다(별도의 4.5GB '신규참여시군' 파일에 있음, 이번엔 미포함). " +
      "따라서 이 TOP10은 '경기도 전체 TOP10'이 아니라 '데이터가 있는 16개 시군 내 TOP10'입니다.",
  },
  { 항목: "시군구 표기 방식", 내용: "원자료 그대로 표기함 (성남시→분당/수정/중원구, 안양시→동안/만안구, 용인시→수지/기흥/처인구, 화성시→동탄/만세/병점/효행구, 안산시→단원/상록구, 수원시→영통/권선/장안/팔달구는 원자료에서 이미 구 단위로 분리되어 있어 임의로 합산하지 않음)" },
  { 항목: "처리한 원자료 규모", 내용: `총 ${data.row_count.toLocaleString()}행 처리, 조건에 맞는 ${data.matched_count.toLocaleString()}행을 집계에 사용` },
];
const wsNote = XLSX.utils.json_to_sheet(noteRows);
wsNote["!cols"] = [{ wch: 20 }, { wch: 100 }];
XLSX.utils.book_append_sheet(wb, wsNote, "출처 및 주의사항");

XLSX.writeFile(wb, "output/경기도_서울_통학통근_대중교통_20대~40대_평일주말_202601_03.xlsx");
console.log("저장 완료");
