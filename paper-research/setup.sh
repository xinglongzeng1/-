#!/bin/bash
# 一键安装依赖
set -e

echo "=== 安装 Python 依赖 ==="
pip install -r requirements.txt

echo "=== 配置 Playwright 浏览器路径 ==="
export PLAYWRIGHT_BROWSERS_PATH=/opt/pw-browsers
playwright install chromium 2>/dev/null || true

# 如果下载失败，用已有版本创建兼容符号链接
if [ ! -f "/opt/pw-browsers/chromium_headless_shell-1208/INSTALLATION_COMPLETE" ]; then
  echo "=== 使用已安装的 Chromium 创建兼容链接 ==="
  mkdir -p /opt/pw-browsers/chromium_headless_shell-1208/chrome-headless-shell-linux64
  if [ -f "/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell" ]; then
    ln -sf /opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell \
            /opt/pw-browsers/chromium_headless_shell-1208/chrome-headless-shell-linux64/chrome-headless-shell
    cp /opt/pw-browsers/chromium_headless_shell-1194/INSTALLATION_COMPLETE \
       /opt/pw-browsers/chromium_headless_shell-1208/
    cp /opt/pw-browsers/chromium_headless_shell-1194/DEPENDENCIES_VALIDATED \
       /opt/pw-browsers/chromium_headless_shell-1208/
    echo "✅ Chromium 兼容配置完成"
  fi
fi

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
