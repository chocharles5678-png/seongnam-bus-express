import { readFileSync } from "fs";
import * as XLSX from "xlsx";

interface BidRow {
  공고명: string;
  발주기관: string;
  공고기관: string;
  추정가격: number | null;
  게시일: string;
  입찰공고번호: string;
}

const raw: BidRow[] = JSON.parse(readFileSync("data/bridge_bids_raw.json", "utf-8"));

const rows = raw.map((r) => ({
  공고명: r.공고명.trim(),
  발주기관: r.발주기관,
  추정가격: r.추정가격,
  게시일: r.게시일,
}));

const ws = XLSX.utils.json_to_sheet(rows);
ws["!cols"] = [{ wch: 60 }, { wch: 30 }, { wch: 15 }, { wch: 18 }];

const wb = XLSX.utils.book_new();
XLSX.utils.book_append_sheet(wb, ws, "교량 입찰공고");

XLSX.writeFile(wb, "output/교량_입찰공고_최근1개월.xlsx");
console.log(`${rows.length}건 저장 완료`);
