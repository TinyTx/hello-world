#!/bin/bash

# 2025年全国少年儿童跳水锦标赛照片下载器 - 增强版运行脚本
# Enhanced version with improved dynamic loading and comprehensive photo extraction

echo "==================================="
echo "跳水锦标赛照片下载器 - 增强版"
echo "Enhanced Diving Photos Downloader"
echo "==================================="

# 检查Python环境
echo "检查Python环境..."
if ! command -v python3 &> /dev/null; then
    echo "错误：未找到Python3，请先安装Python3"
    exit 1
fi

# 检查pip
if ! command -v pip3 &> /dev/null; then
    echo "错误：未找到pip3，请先安装pip3"
    exit 1
fi

# 检查Chrome/Chromium
echo "检查Chrome浏览器..."
if ! command -v google-chrome &> /dev/null && ! command -v chromium-browser &> /dev/null && ! command -v chromium &> /dev/null; then
    echo "警告：未检测到Chrome浏览器，请确保已安装Chrome或Chromium"
    echo "Ubuntu/Debian: sudo apt-get install google-chrome-stable"
    echo "CentOS/RHEL: sudo yum install google-chrome-stable"
    echo "或访问: https://www.google.com/chrome/"
fi

# 检查ChromeDriver
echo "检查ChromeDriver..."
if ! command -v chromedriver &> /dev/null; then
    echo "警告：未检测到ChromeDriver"
    echo "请从以下地址下载并安装ChromeDriver:"
    echo "https://chromedriver.chromium.org/"
    echo "或使用webdriver-manager自动管理"
fi

# 创建虚拟环境（如果不存在）
if [ ! -d "venv" ]; then
    echo "创建Python虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
echo "激活虚拟环境..."
source venv/bin/activate

# 升级pip
echo "升级pip..."
pip install --upgrade pip

# 安装依赖
echo "安装/更新依赖包..."
pip install -r requirements.txt

# 检查是否有更新的requirements
if [ -f "requirements_enhanced.txt" ]; then
    echo "安装增强版依赖..."
    pip install -r requirements_enhanced.txt
fi

# 设置环境变量
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# 检查下载目录权限
DOWNLOAD_DIR="diving_championship_photos_original"
if [ ! -d "$DOWNLOAD_DIR" ]; then
    echo "创建下载目录: $DOWNLOAD_DIR"
    mkdir -p "$DOWNLOAD_DIR"
fi

if [ ! -w "$DOWNLOAD_DIR" ]; then
    echo "错误：下载目录没有写入权限"
    exit 1
fi

echo ""
echo "环境检查完成！"
echo ""
echo "增强版功能特性："
echo "✓ 多维度动态加载检测"
echo "✓ 智能滚动策略（4种模式）"
echo "✓ 网络请求监控"
echo "✓ 多种图片URL提取方法"
echo "✓ 原图质量增强"
echo "✓ 断点续传支持"
echo "✓ 详细日志记录"
echo ""

# 显示使用说明
echo "使用说明："
echo "1. 脚本将自动打开浏览器并访问目标网页"
echo "2. 请在浏览器中手动完成登录"
echo "3. 登录完成后，在控制台输入 'y' 确认"
echo "4. 脚本将自动滚动页面并加载所有照片"
echo "5. 然后自动下载所有原图到本地文件夹"
echo ""

# 询问是否继续
read -p "是否开始运行增强版下载器？(y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "启动增强版下载器..."
    echo "=================================="
    
    # 运行增强版下载器
    python3 diving_photos_downloader_enhanced.py
    
    # 检查运行结果
    if [ $? -eq 0 ]; then
        echo ""
        echo "=================================="
        echo "下载完成！"
        echo "照片保存在: $(pwd)/$DOWNLOAD_DIR"
        echo ""
        
        # 显示统计信息
        if [ -d "$DOWNLOAD_DIR" ]; then
            TOTAL_FILES=$(find "$DOWNLOAD_DIR" -type f -name "*.jpg" -o -name "*.jpeg" -o -name "*.png" -o -name "*.webp" | wc -l)
            TOTAL_SIZE=$(du -sh "$DOWNLOAD_DIR" | cut -f1)
            echo "统计信息："
            echo "- 下载文件数量: $TOTAL_FILES"
            echo "- 总占用空间: $TOTAL_SIZE"
            
            # 显示日志文件位置
            if [ -f "$DOWNLOAD_DIR/download_log.txt" ]; then
                echo "- 详细日志: $DOWNLOAD_DIR/download_log.txt"
            fi
            
            if [ -f "$DOWNLOAD_DIR/progress.json" ]; then
                echo "- 进度文件: $DOWNLOAD_DIR/progress.json"
            fi
        fi
        
        echo ""
        echo "感谢使用增强版下载器！"
    else
        echo ""
        echo "=================================="
        echo "下载过程中出现错误，请检查日志文件"
        if [ -f "$DOWNLOAD_DIR/download_log.txt" ]; then
            echo "错误日志: $DOWNLOAD_DIR/download_log.txt"
            echo ""
            echo "最近的错误信息："
            tail -n 10 "$DOWNLOAD_DIR/download_log.txt"
        fi
    fi
else
    echo "已取消运行"
fi

# 停用虚拟环境
deactivate

echo "脚本执行完毕"