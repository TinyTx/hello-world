#!/bin/bash

echo "正在启动跳水锦标赛照片下载器..."

# 检查虚拟环境是否存在
if [ ! -d "diving_env" ]; then
    echo "虚拟环境不存在，正在创建..."
    python3 -m venv diving_env
    source diving_env/bin/activate
    echo "正在安装依赖..."
    pip install -r requirements.txt
else
    echo "激活虚拟环境..."
    source diving_env/bin/activate
fi

# 运行下载器
echo "开始下载照片..."
python diving_photos_downloader.py

echo "下载完成！"