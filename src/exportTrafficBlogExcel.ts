import { readFileSync } from "fs";
import * as XLSX from "xlsx";

interface BlogRow {
  제목: string;
  블로그명: string;
  게시일: string;
  URL: string;
}

const rows: BlogRow[] = JSON.parse(readFileSync("data/traffic_blog_posts.json", "utf-8"));

const ws = XLSX.utils.json_to_sheet(rows);
ws["!cols"] = [{ wch: 55 }, { wch: 28 }, { wch: 12 }, { wch: 45 }];

const wb = XLSX.utils.book_new();
XLSX.utils.book_append_sheet(wb, ws, "교통문제 블로그");

XLSX.writeFile(wb, "output/교통문제_블로그_2024_2026.xlsx");
console.log(`${rows.length}건 저장 완료`);
