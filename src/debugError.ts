import "dotenv/config";
import axios from "axios";
const ODSAY_KEY = process.env.ODSAY_API_KEY!;
const res = await axios.get("https://api.odsay.com/v1/api/searchPubTransPathT", {
  params: { SX: 127.151991, SY: 37.627604, EX: 127.096971, EY: 37.512691, apiKey: ODSAY_KEY },
});
console.log(JSON.stringify(res.data, null, 2));
