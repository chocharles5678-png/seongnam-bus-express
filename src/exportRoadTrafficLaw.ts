import { readFileSync } from "fs";
import * as XLSX from "xlsx";

interface FullRow {
  조번호: string;
  제목: string;
  조문내용: string;
}

interface RelevantRow extends FullRow {
  관련키워드: string;
}

const full: FullRow[] = JSON.parse(readFileSync("data/law_full.json", "utf-8"));
const relevant: RelevantRow[] = JSON.parse(readFileSync("data/law_relevant.json", "utf-8"));

const wb = XLSX.utils.book_new();

const wsRelevant = XLSX.utils.json_to_sheet(relevant);
wsRelevant["!cols"] = [{ wch: 14 }, { wch: 30 }, { wch: 90 }, { wch: 30 }];
XLSX.utils.book_append_sheet(wb, wsRelevant, "공모전 관련 조문");

const wsFull = XLSX.utils.json_to_sheet(full);
wsFull["!cols"] = [{ wch: 14 }, { wch: 30 }, { wch: 100 }];
XLSX.utils.book_append_sheet(wb, wsFull, "도로교통법 전체 조문");

XLSX.writeFile(wb, "output/도로교통법_교통문제공모전_관련조문.xlsx");
console.log(`전체 ${full.length}개 조문, 관련 조문 ${relevant.length}개 저장 완료`);
