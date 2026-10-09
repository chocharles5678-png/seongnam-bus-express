import { readFileSync } from "fs";
import * as XLSX from "xlsx";

const data = JSON.parse(readFileSync("data/gg_seoul_od_202601_03.json", "utf-8"));

const wb = XLSX.utils.book_new();

// Sheet 1: TOP10 요약
const top10Rows = data.top10.map((city: string, i: number) => ({
  순위: i + 1,
  "시군구(원자료 단위)": city,
  "서울행_이동인구_10~40대_합계(명)": Math.round(data.city_total[city]),
}));
const wsTop10 = XLSX.utils.json_to_sheet(top10Rows);
wsTop10["!cols"] = [{ wch: 6 }, { wch: 20 }, { wch: 26 }];
XLSX.utils.book_append_sheet(wb, wsTop10, "TOP10 요약");

// Sheet 2: 목적별 상세
const purposeOrder = ["귀가", "출근", "등교", "쇼핑", "관광", "병원", "기타"];
const purposeRows = data.top10.map((city: string) => {
  const row: Record<string, any> = { 시군구: city };
  const pdata = data.purpose_by_city[city] || {};
  for (const p of purposeOrder) row[p] = Math.round(pdata[p] || 0);
  return row;
});
const wsPurpose = XLSX.utils.json_to_sheet(purposeRows);
wsPurpose["!cols"] = [{ wch: 20 }, ...purposeOrder.map(() => ({ wch: 12 }))];
XLSX.utils.book_append_sheet(wb, wsPurpose, "TOP10 이동목적별");

// Sheet 3: 수단별 상세
const transOrder = ["차량", "노선버스", "지하철", "도보", "고속버스", "기차", "항공", "기타"];
const transRows = data.top10.map((city: string) => {
  const row: Record<string, any> = { 시군구: city };
  const tdata = data.trans_by_city[city] || {};
  for (const t of transOrder) row[t] = Math.round(tdata[t] || 0);
  return row;
});
const wsTrans = XLSX.utils.json_to_sheet(transRows);
wsTrans["!cols"] = [{ wch: 20 }, ...transOrder.map(() => ({ wch: 12 }))];
XLSX.utils.book_append_sheet(wb, wsTrans, "TOP10 이동수단별");

// Sheet 4: 전체 시군구 순위 (수집된 28개 전체)
const allRows = Object.entries(data.city_total)
  .sort((a: any, b: any) => b[1] - a[1])
  .map(([city, cnt]: any, i: number) => ({
    순위: i + 1,
    "시군구(원자료 단위)": city,
    "서울행_이동인구_10~40대_합계(명)": Math.round(cnt),
  }));
const wsAll = XLSX.utils.json_to_sheet(allRows);
wsAll["!cols"] = [{ wch: 6 }, { wch: 20 }, { wch: 26 }];
XLSX.utils.book_append_sheet(wb, wsAll, "수집된 전체 시군구 순위");

// Sheet 5: 출처 및 주의사항
const noteRows = [
  { 항목: "출처", 내용: "공공데이터포털(data.go.kr) 경유 → 경기데이터드림(data.gg.go.kr) '시군구간 성별/연령별 이동목적/수단 OD 데이터' [infId=1OHUUK6IHNFAQBULU3O234999490, infSeq=2]" },
  { 항목: "원본 테이블", 내용: "GG_PURPOSE_TRANS_SEXAGE_SGG_OD (경기도 시군 민간데이터 규격서_통신 기준)" },
  { 항목: "원자료 제공기관", 내용: "경기도 + KT (통신 시그널 기반 추정 데이터, 민간데이터)" },
  { 항목: "다운로드한 파일", 내용: "시군구간 성별연령별 이동목적수단 OD 데이터_202601-202603.zip — 해당 데이터셋에서 2026-09-15 기준 확인 가능한 가장 최근 파일 (2026년 1~3월 데이터)" },
  { 항목: "필터 조건", 내용: "O_MEGA_NM(출발지 시도)=경기도, D_MEGA_NM(도착지 시도)=서울특별시, AGE_GRP(연령대)=02,03,04,05 (즉 10대~40대)만 합산. 성별(SEX_CD)은 남녀 합계, 시간대는 전체 합계, 요일은 전체 합계" },
  { 항목: "AGE_GRP 코드 정의", 내용: "01:0-9세, 02:10-19세, 03:20-29세, 04:30-39세, 05:40-49세, 06:50-59세, 07:60-69세, 08:70세 이상 (규격서 원문 기준)" },
  { 항목: "PURPOSE(이동목적) 코드", 내용: "0:귀가, 1:출근, 2:등교, 3:쇼핑, 4:관광, 5:병원, 6:기타" },
  { 항목: "TRANS_GB(이동수단) 코드", 내용: "0:차량, 1:노선버스, 2:지하철, 3:도보, 4:고속버스, 5:기차, 6:항공, 7:기타" },
  {
    항목: "⚠ 중요 — 데이터 커버리지 한계",
    내용:
      "이 데이터셋은 경기도 31개 시군 중 16개 시군(광명시,김포시,남양주시,성남시,수원시,시흥시,안산시,안양시,여주시,연천군,용인시,의정부시,파주시,포천시,하남시,화성시)만 포함합니다. " +
      "고양시, 부천시, 과천시, 구리시, 광주시, 군포시, 동두천시, 양주시, 양평군, 오산시, 의왕시, 이천시, 가평군, 안성시, 평택시(15개 시군)는 이 파일에 데이터가 없습니다. " +
      "해당 시군들은 '신규참여시군_과거데이터'라는 별도의 대용량 파일(약 4.5GB)에 있으며, 이번 작업에서는 시간 관계상 포함하지 않았습니다. " +
      "따라서 이 TOP10은 '경기도 전체 31개 시군 중 TOP10'이 아니라 '데이터가 제공되는 16개 시군 내에서의 TOP10'입니다. 특히 고양시·부천시는 이전에 다른 데이터(서울시 생활이동)에서 서울행 이동인구 상위권으로 나타난 지역이라, 이 파일만으로 전체 순위를 단정하면 안 됩니다.",
  },
  { 항목: "시군구 표기 방식", 내용: "원자료 그대로 표기함. 성남시(분당구/수정구/중원구), 안양시(동안구/만안구), 용인시(수지구/기흥구/처인구), 화성시(동탄구/만세구/병점구/효행구), 안산시(단원구/상록구), 수원시(영통구/권선구/장안구/팔달구)는 원자료에서 이미 구 단위로 분리되어 있어 그대로 유지함 (임의로 합산하지 않음 — 사용자 요청에 따라 원자료 그대로 제공)" },
  { 항목: "처리한 원자료 규모", 내용: `총 ${data.row_count?.toLocaleString?.() ?? ""}행 처리, 조건에 맞는 ${data.matched_count?.toLocaleString?.() ?? ""}행을 집계에 사용` },
];
const wsNote = XLSX.utils.json_to_sheet(noteRows);
wsNote["!cols"] = [{ wch: 20 }, { wch: 100 }];
XLSX.utils.book_append_sheet(wb, wsNote, "출처 및 주의사항");

XLSX.writeFile(wb, "output/경기도_서울_이동_10대~40대_TOP10_202601_03.xlsx");
console.log("저장 완료");
