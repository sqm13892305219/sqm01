#!/usr/bin/env python3
"""
quotes_scraper.py — 爬虫示例：抓取 Quotes to Scrape (quotes.toscrape.com) 的名言数据

特点：
- 使用 requests + BeautifulSoup 解析 HTML
- 自动翻页抓取多页数据
- 带请求头、超时与重试，礼貌抓取（每页间隔 1 秒）
- 结果保存为 CSV 和 JSON 两种格式

用法：
    python3 quotes_scraper.py              # 抓取全部页面
    python3 quotes_scraper.py --pages 3    # 只抓前 3 页
"""

import argparse
import csv
import json
import sys
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://quotes.toscrape.com/"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) sqm01-demo-scraper/1.0"
}
TIMEOUT = 10
RETRIES = 3
PAGE_DELAY = 1  # 每页之间的间隔（秒），礼貌抓取


def fetch_page(url: str) -> str | None:
    """带重试的页面抓取，返回 HTML 文本"""
    for attempt in range(1, RETRIES + 1):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
            resp.raise_for_status()
            return resp.text
        except requests.RequestException as e:
            print(f"  [重试 {attempt}/{RETRIES}] 抓取 {url} 失败: {e}")
            time.sleep(2 * attempt)
    return None


def parse_quotes(html: str) -> list[dict]:
    """从 HTML 中解析名言列表"""
    soup = BeautifulSoup(html, "html.parser")
    quotes = []
    for item in soup.select("div.quote"):
        quotes.append({
            "text": item.select_one("span.text").get_text(strip=True),
            "author": item.select_one("small.author").get_text(strip=True),
            "tags": [t.get_text(strip=True) for t in item.select("a.tag")],
        })
    return quotes


def scrape(max_pages: int | None = None) -> list[dict]:
    """翻页抓取，返回所有名言"""
    all_quotes = []
    page = 1
    while True:
        url = BASE_URL if page == 1 else f"{BASE_URL}page/{page}/"
        print(f"正在抓取第 {page} 页: {url}")
        html = fetch_page(url)
        if html is None:
            print("  该页抓取失败，停止翻页")
            break

        quotes = parse_quotes(html)
        if not quotes:
            print("  没有更多数据，抓取完成")
            break

        all_quotes.extend(quotes)
        print(f"  本页获取 {len(quotes)} 条，累计 {len(all_quotes)} 条")

        if max_pages and page >= max_pages:
            print(f"  已达到最大页数限制（{max_pages} 页）")
            break
        page += 1
        time.sleep(PAGE_DELAY)
    return all_quotes


def save(quotes: list[dict], out_dir: Path) -> None:
    """保存为 CSV 和 JSON"""
    out_dir.mkdir(parents=True, exist_ok=True)

    json_path = out_dir / "quotes.json"
    json_path.write_text(
        json.dumps(quotes, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"已保存 JSON: {json_path}")

    csv_path = out_dir / "quotes.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["text", "author", "tags"])
        writer.writeheader()
        for q in quotes:
            writer.writerow({**q, "tags": " | ".join(q["tags"])})
    print(f"已保存 CSV: {csv_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="抓取 quotes.toscrape.com 名言数据")
    parser.add_argument("--pages", type=int, default=None, help="最多抓取的页数（默认不限制）")
    args = parser.parse_args()

    quotes = scrape(max_pages=args.pages)
    if not quotes:
        print("未抓取到任何数据", file=sys.stderr)
        sys.exit(1)

    save(quotes, Path(__file__).resolve().parent / "output")
    print(f"\n完成！共抓取 {len(quotes)} 条名言。")


if __name__ == "__main__":
    main()
