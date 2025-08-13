#!/bin/bash

echo "===== 跳水锦标赛照片下载器（增强版）====="
echo ""

# 检查Python依赖
echo "检查Python环境..."
if ! python3 -c "import selenium, requests, bs4" 2>/dev/null; then
    echo "Python依赖缺失，正在安装..."
    pip3 install --break-system-packages selenium beautifulsoup4 requests lxml
fi

# 检查Chrome/ChromeDriver
echo "检查浏览器环境..."
if ! which google-chrome >/dev/null 2>&1 && ! which chromium-browser >/dev/null 2>&1; then
    echo "警告：未找到Chrome浏览器"
    echo "请先运行: sudo ./setup_environment.sh"
    echo ""
fi

if ! which chromedriver >/dev/null 2>&1; then
    echo "警告：未找到ChromeDriver"
    echo "请先运行: sudo ./setup_environment.sh"
    echo ""
fi

echo "选择要运行的脚本："
echo "1. 分析页面结构（推荐先运行此选项）"
echo "2. 增强版下载器（包含登录功能）"
echo "3. 原始版下载器"
echo "4. 简化版下载器（无需浏览器）"
echo ""

read -p "请选择 (1-4): " choice

case $choice in
    1)
        echo "运行页面结构分析器..."
        chmod +x analyze_page_structure.py
        python3 analyze_page_structure.py
        ;;
    2)
        echo "运行增强版下载器..."
        chmod +x diving_photos_downloader_enhanced.py
        python3 diving_photos_downloader_enhanced.py
        ;;
    3)
        echo "运行原始版下载器..."
        chmod +x diving_photos_downloader.py
        python3 diving_photos_downloader.py
        ;;
    4)
        echo "运行简化版下载器..."
        chmod +x diving_photos_downloader_simple.py
        python3 diving_photos_downloader_simple.py
        ;;
    *)
        echo "无效选择"
        exit 1
        ;;
esac

echo ""
echo "脚本执行完成！"