#!/bin/bash

echo "正在设置跳水锦标赛照片下载器环境..."

# 更新包管理器
sudo apt-get update

# 安装Python和pip（如果尚未安装）
sudo apt-get install -y python3 python3-pip python3-venv python3-full

# 安装Chrome浏览器
echo "正在安装Chrome浏览器..."
wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" | sudo tee /etc/apt/sources.list.d/google-chrome.list
sudo apt-get update
sudo apt-get install -y google-chrome-stable

# 获取Chrome版本
CHROME_VERSION=$(google-chrome --version | sed 's/Google Chrome //' | cut -d. -f1)
echo "Chrome版本: $CHROME_VERSION"

# 下载并安装对应版本的ChromeDriver
echo "正在安装ChromeDriver..."
CHROMEDRIVER_VERSION=$(curl -s "https://chromedriver.storage.googleapis.com/LATEST_RELEASE_${CHROME_VERSION}")
wget -O /tmp/chromedriver.zip "https://chromedriver.storage.googleapis.com/${CHROMEDRIVER_VERSION}/chromedriver_linux64.zip"
sudo unzip /tmp/chromedriver.zip -d /usr/local/bin/
sudo chmod +x /usr/local/bin/chromedriver
rm /tmp/chromedriver.zip

# 创建虚拟环境并安装Python依赖
echo "正在创建Python虚拟环境..."
python3 -m venv diving_env
echo "正在激活虚拟环境并安装依赖..."
source diving_env/bin/activate
pip install -r requirements.txt

# 设置权限
sudo chmod +x diving_photos_downloader.py

echo "环境设置完成！"
echo "使用方法:"
echo "1. 激活虚拟环境: source diving_env/bin/activate"
echo "2. 运行脚本: python diving_photos_downloader.py"
echo "或者使用运行脚本: ./run_downloader.sh"