#!/bin/bash
# 一键安装依赖
set -e

echo "=== 安装 Python 依赖 ==="
pip install -r requirements.txt

echo "=== 安装 Playwright 浏览器 ==="
playwright install chromium

echo ""
echo "✅ 安装完成！"
echo ""
echo "使用方法："
echo "  1. 编辑 config.json，填写各平台账号密码"
echo "  2. 运行搜索："
echo "     python main.py --keywords '设计哲学' '历史学' '社会学'"
echo ""
echo "  或指定部分网站："
echo "     python main.py --keywords '设计哲学' --sites cnki wanfang arxiv"
echo ""
echo "  搜索完成后用浏览器打开 results/ 目录下的 .html 文件即可浏览"
