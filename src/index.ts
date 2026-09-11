import axios from "axios";
import * as cheerio from "cheerio";

async function crawl(url: string) {
  const res = await axios.get(url);
  const $ = cheerio.load(res.data);
  const title = $("title").text();
  console.log(title);
}

crawl("https://example.com");
