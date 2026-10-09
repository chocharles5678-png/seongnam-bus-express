import { readFileSync } from "fs";
import * as XLSX from "xlsx";

interface TableBlock {
  columns: string[];
  [year: string]: any;
}

interface SourceData {
  접근시간: TableBlock;
  접근수단: TableBlock;
}

const data: SourceData = JSON.parse(
  readFileSync("data/transit_vulnerable_area_data.json", "utf-8")
);

const years = ["2022", "2023", "2024"];

function buildRows(block: TableBlock) {
  const rows: Record<string, string | number>[] = [];
  for (const year of years) {
    const yearData = block[year];
    yearData.regions.forEach((region: string, i: number) => {
      const row: Record<string, string | number> = { 연도: year, 지역: region };
      block.columns.forEach((col, j) => {
        row[col] = yearData.values[i][j];
      });
      rows.push(row);
    });
  }
  return rows;
}

const wb = XLSX.utils.book_new();

const wsTime = XLSX.utils.json_to_sheet(buildRows(data.접근시간));
wsTime["!cols"] = [{ wch: 8 }, { wch: 8 }, { wch: 10 }, { wch: 10 }, { wch: 10 }, { wch: 10 }, { wch: 10 }, { wch: 10 }, { wch: 10 }];
XLSX.utils.book_append_sheet(wb, wsTime, "시도별 대중교통 접근시간");

const wsMode = XLSX.utils.json_to_sheet(buildRows(data.접근수단));
wsMode["!cols"] = [{ wch: 8 }, { wch: 8 }, { wch: 10 }, { wch: 10 }, { wch: 10 }, { wch: 10 }, { wch: 10 }];
XLSX.utils.book_append_sheet(wb, wsMode, "시도별 대중교통 접근수단");

const noteRows = [
  { 항목: "출처", 내용: "국토교통 통계누리(stat.molit.go.kr) - 대중교통현황조사(2011~), 시도별 대중교통 접근시간/접근수단" },
  { 항목: "조사 근거", 내용: "대중교통의 육성 및 이용 촉진에 관한 법률 제16조, 동법 시행규칙 제4~5조 / 매년 1회(5~12월) 실시, 공표는 익년 10월" },
  { 항목: "검색어 안내", 내용: "\"교통취약지역\"이라는 이름의 통계표는 포털에 별도로 존재하지 않습니다. 가장 가까운 공식 지표인 시도별 '대중교통 접근시간(30분 이상 비율)'과 '접근수단'을 대신 수집했습니다." },
  { 항목: "참고 지표", 내용: "국토교통부·한국교통안전공단 「대중교통현황조사 종합보고서(2023)」 기준, 전국 교통취약지역 비율: 읍·면 29.9%, 법정동 16.9% (기준: 도시지역 정류장 400m 초과 / 그외 800m 초과)" },
  { 항목: "데이터 주의사항", 내용: "2024년 '접근수단' 조사에서 도보 비율이 전년 대비 약 10%p 급락하고 택시·기타가 상승했습니다. 실제 행태 변화인지 조사방법 변경 때문인지 원자료(종합보고서)를 통해 별도 확인을 권장합니다." },
];
const wsNote = XLSX.utils.json_to_sheet(noteRows);
wsNote["!cols"] = [{ wch: 14 }, { wch: 90 }];
XLSX.utils.book_append_sheet(wb, wsNote, "출처 및 주의사항");

XLSX.writeFile(wb, "output/교통취약지역_관련데이터_2022_2024.xlsx");
console.log("저장 완료");
