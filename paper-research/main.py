#!/usr/bin/env python3
"""
论文调研自动化工具
用法: python main.py --keywords "设计哲学" "历史学" --sites cnki wanfang arxiv
"""

import asyncio
import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

from scrapers import (
    CNKIScraper,
    WanfangScraper,
    VIPScraper,
    GoogleScholarScraper,
    ArxivScraper,
    WOSScraper,
)
from report import generate_report


SCRAPERS = {
    "cnki": CNKIScraper,
    "wanfang": WanfangScraper,
    "vip": VIPScraper,
    "google_scholar": GoogleScholarScraper,
    "arxiv": ArxivScraper,
    "wos": WOSScraper,
}


def load_config(path: str = "config.json") -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_results(results: list[dict], output_dir: str = "results"):
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = os.path.join(output_dir, f"papers_{timestamp}.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n结果已保存到: {out_path}")
    return out_path


async def run_scraper(scraper_cls, config: dict, keywords: list[str]) -> list[dict]:
    scraper = scraper_cls(config)
    return await scraper.run(keywords)


async def main_async(args):
    config = load_config(args.config)

    # 命令行关键词优先，否则从 config.json 读取
    keywords = args.keywords or config.get("keywords", [])
    if not keywords:
        print("错误: 请通过 --keywords 参数或在 config.json 中提供搜索关键词")
        sys.exit(1)

    # 确定要运行的爬虫
    sites = args.sites or [
        k for k, v in config["sites"].items() if v.get("enabled", True)
    ]

    print(f"\n=== 论文调研系统启动 ===")
    print(f"关键词: {keywords}")
    print(f"数据源: {sites}")
    print(f"每站最多: {config['max_results_per_site']} 条")
    print("=" * 30)

    all_results = []

    for site in sites:
        if site not in SCRAPERS:
            print(f"未知数据源: {site}，跳过")
            continue
        print(f"\n>>> 开始抓取: {SCRAPERS[site].display_name}")
        results = await run_scraper(SCRAPERS[site], config, keywords)
        all_results.extend(results)
        print(f">>> 完成: 获取 {len(results)} 篇论文")

    print(f"\n=== 总计获取 {len(all_results)} 篇论文 ===")

    # 保存 JSON
    json_path = save_results(all_results)

    # 生成 HTML 报告
    report_path = json_path.replace(".json", ".html")
    generate_report(all_results, report_path, keywords)
    print(f"HTML 报告已生成: {report_path}")
    print(f"\n用浏览器打开查看: file://{os.path.abspath(report_path)}")


def main():
    parser = argparse.ArgumentParser(description="论文调研自动化工具")
    parser.add_argument(
        "--keywords", "-k", nargs="+", help="搜索关键词（可多个）"
    )
    parser.add_argument(
        "--sites", "-s", nargs="+",
        choices=list(SCRAPERS.keys()),
        help="指定数据源（默认全部）",
    )
    parser.add_argument(
        "--config", "-c", default="config.json", help="配置文件路径"
    )
    args = parser.parse_args()
    asyncio.run(main_async(args))


if __name__ == "__main__":
    main()
