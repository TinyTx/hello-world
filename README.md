# 2025年全国少年儿童跳水锦标赛照片下载器

这是一个专门用于下载2025年全国少年儿童跳水锦标赛照片的Python脚本。该脚本能够处理动态加载的网页内容，自动获取最高质量的原图，并按日期分类保存。

## 功能特点

- ✅ **动态内容处理**: 使用Selenium模拟浏览器行为，能够正确处理JavaScript动态加载的内容
- ✅ **智能滚动加载**: 自动滚动页面并点击"加载更多"按钮，确保获取所有照片
- ✅ **最高质量照片**: 自动检测并下载最清晰的原图版本
- ✅ **按日期分类**: 从URL中提取日期信息，自动创建日期文件夹进行分类保存
- ✅ **重复检测**: 基于文件内容哈希值防止重复下载
- ✅ **智能过滤**: 自动过滤掉logo、图标等非比赛照片
- ✅ **错误处理**: 完善的异常处理机制，确保下载过程稳定
- ✅ **进度显示**: 实时显示下载进度和统计信息

## 系统要求

- Python 3.7+
- Linux/Ubuntu 系统
- 网络连接

## 安装和设置

### 方法1: 自动安装（推荐）

1. 运行自动安装脚本：
```bash
chmod +x setup_environment.sh
./setup_environment.sh
```

### 方法2: 手动安装

1. 安装Chrome浏览器：
```bash
wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" | sudo tee /etc/apt/sources.list.d/google-chrome.list
sudo apt-get update
sudo apt-get install -y google-chrome-stable
```

2. 安装ChromeDriver：
```bash
# 获取Chrome版本
CHROME_VERSION=$(google-chrome --version | sed 's/Google Chrome //' | cut -d. -f1)
# 下载对应版本的ChromeDriver
CHROMEDRIVER_VERSION=$(curl -s "https://chromedriver.storage.googleapis.com/LATEST_RELEASE_${CHROME_VERSION}")
wget -O /tmp/chromedriver.zip "https://chromedriver.storage.googleapis.com/${CHROMEDRIVER_VERSION}/chromedriver_linux64.zip"
sudo unzip /tmp/chromedriver.zip -d /usr/local/bin/
sudo chmod +x /usr/local/bin/chromedriver
```

3. 安装Python依赖：
```bash
pip3 install -r requirements.txt
```

## 使用方法

### 基本使用

直接运行脚本下载照片：
```bash
python3 diving_photos_downloader.py
```

### 自定义下载目录

修改脚本中的下载目录：
```python
downloader = DivingPhotosDownloader(url, download_dir="自定义目录名")
```

### 无头模式运行

如果在服务器环境运行，可以启用无头模式。在脚本中取消注释以下行：
```python
chrome_options.add_argument('--headless')
```

## 文件结构

下载完成后，照片会按以下结构保存：
```
diving_championship_photos/
├── 2025-01-15/          # 按日期分类的文件夹
│   ├── photo_001.jpg
│   ├── photo_002.jpg
│   └── ...
├── 2025-01-16/
│   ├── photo_003.jpg
│   └── ...
└── 2025-01-20_unknown/  # 无法识别日期的照片
    ├── photo_004.jpg
    └── ...
```

## 脚本特性详解

### 1. 动态内容加载
- 自动等待页面加载完成
- 模拟用户滚动行为，触发懒加载
- 自动点击"加载更多"按钮
- 最多尝试20次滚动确保完整性

### 2. 照片质量优化
- 自动移除URL中的尺寸和质量限制参数
- 尝试多种高质量URL后缀
- 验证响应状态确保获取有效链接

### 3. 智能分类
- 从URL中提取多种日期格式
- 支持 YYYY-MM-DD、YYYYMMDD 等格式
- 无法识别日期的照片统一归类

### 4. 下载优化
- 使用Session保持连接
- 设置合理的超时时间
- 文件名冲突自动处理
- 基于MD5哈希的重复检测

## 常见问题

### Q: 脚本运行时显示"无法启动Chrome浏览器"
A: 请确保已正确安装Chrome浏览器和ChromeDriver，并且版本匹配。

### Q: 下载的照片数量比预期少
A: 检查网络连接是否稳定，可能需要增加滚动等待时间。

### Q: 某些照片下载失败
A: 这是正常现象，可能是由于网络波动或服务器限制。脚本会自动跳过失败的照片。

### Q: 如何在服务器上运行？
A: 启用无头模式并确保系统有足够的内存。可能需要安装 `xvfb` 虚拟显示器。

## 注意事项

1. **网络礼仪**: 脚本已设置合理的请求间隔，请不要修改得过于频繁
2. **存储空间**: 确保有足够的磁盘空间存储照片
3. **网络稳定**: 建议在网络稳定的环境下运行
4. **版权声明**: 下载的照片仅供个人学习使用，请遵守相关版权法规

## 技术架构

- **Selenium WebDriver**: 处理动态JavaScript内容
- **BeautifulSoup**: HTML解析和内容提取
- **Requests**: HTTP请求和文件下载
- **正则表达式**: URL模式匹配和日期提取
- **哈希算法**: 重复文件检测

## 更新日志

- v1.0.0: 初始版本，支持基本的照片下载功能
- 包含动态内容处理、质量优化、日期分类等完整功能

## 许可证

本项目仅供学习和个人使用，请遵守相关网站的使用条款。
