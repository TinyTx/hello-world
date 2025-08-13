# 跳水锦标赛照片下载器使用指南

## 当前状态

✅ **已完成**：
- 创建了完整的照片下载脚本
- 安装了所有Python依赖
- 测试确认网页可以访问
- 确认网页使用JavaScript动态加载内容

❌ **需要完成**：
- 安装Chrome浏览器和ChromeDriver以支持动态内容加载

## 脚本说明

### 1. diving_photos_downloader_enhanced.py（增强版本 - 推荐）
- **功能**：最新的增强版下载器，支持登录和原图检测
- **特点**：
  - ✅ 等待用户手动登录
  - ✅ 智能检测原图链接
  - ✅ 模拟点击获取高清原图
  - ✅ 进度保存和断点续传
  - ✅ 详细日志记录
  - ✅ 支持1万多张照片的完整下载

### 2. analyze_page_structure.py（页面分析器）
- **功能**：分析网页结构，了解原图获取方式
- **用途**：调试和了解网站的图片显示机制
- **建议**：在正式下载前先运行此脚本

### 3. diving_photos_downloader.py（标准版本）
- **功能**：标准的照片下载器，支持JavaScript动态加载
- **要求**：需要Chrome浏览器和ChromeDriver
- **特点**：能够处理动态内容，滚动加载

### 4. diving_photos_downloader_simple.py（简化版本）
- **功能**：仅使用HTTP请求的简化版本
- **要求**：只需要Python和requests库
- **限制**：无法处理JavaScript动态加载的内容

## 环境设置

### 自动安装（推荐）
```bash
# 设置执行权限
chmod +x setup_environment.sh

# 运行安装脚本（需要sudo权限）
sudo ./setup_environment.sh
```

### 手动安装

#### 1. 安装Chrome浏览器
```bash
# 添加Google GPG密钥
wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | sudo apt-key add -

# 添加Chrome源
echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" | sudo tee /etc/apt/sources.list.d/google-chrome.list

# 更新包列表并安装Chrome
sudo apt-get update
sudo apt-get install -y google-chrome-stable
```

#### 2. 安装ChromeDriver
```bash
# 获取Chrome版本
CHROME_VERSION=$(google-chrome --version | sed 's/Google Chrome //' | cut -d. -f1)

# 下载对应版本的ChromeDriver
CHROMEDRIVER_VERSION=$(curl -s "https://chromedriver.storage.googleapis.com/LATEST_RELEASE_${CHROME_VERSION}")
wget -O /tmp/chromedriver.zip "https://chromedriver.storage.googleapis.com/${CHROMEDRIVER_VERSION}/chromedriver_linux64.zip"

# 安装ChromeDriver
sudo unzip /tmp/chromedriver.zip -d /usr/local/bin/
sudo chmod +x /usr/local/bin/chromedriver
rm /tmp/chromedriver.zip
```

#### 3. Python依赖（已安装）
```bash
pip3 install --break-system-packages selenium beautifulsoup4 requests lxml
```

## 使用方法

### 方法1：使用增强版便捷脚本（推荐）
```bash
# 运行增强版脚本选择器
./run_enhanced_downloader.sh
```

该脚本会提供以下选项：
1. **分析页面结构**（推荐先运行）- 了解网站原图获取方式
2. **增强版下载器**（主要功能）- 包含登录和原图检测
3. **标准版下载器** - 基础功能版本
4. **简化版下载器** - 无需浏览器版本

### 方法2：直接运行特定脚本
```bash
# 运行增强版下载器（推荐）
python3 diving_photos_downloader_enhanced.py

# 分析页面结构
python3 analyze_page_structure.py

# 运行标准版本
python3 diving_photos_downloader.py

# 运行简化版本（功能有限）
python3 diving_photos_downloader_simple.py
```

### 推荐使用流程
1. **首次使用**：运行 `analyze_page_structure.py` 了解网站结构
2. **正式下载**：运行 `diving_photos_downloader_enhanced.py`
3. **中断续传**：重新运行增强版脚本，会自动加载之前的进度

## 无头模式（服务器环境）

如果在没有图形界面的服务器上运行，需要启用无头模式：

1. 编辑 `diving_photos_downloader.py`
2. 找到这一行：`# chrome_options.add_argument('--headless')`
3. 取消注释：`chrome_options.add_argument('--headless')`

## 预期结果

### 增强版下载器结果
成功运行后，照片会按以下结构保存：

```
diving_championship_photos_original/
├── 2025-01-15/          # 按日期分类的文件夹
│   ├── photo_001.jpg    # 高质量原图
│   ├── photo_002.jpg
│   └── ...
├── 2025-01-16/
│   ├── photo_003.jpg
│   └── ...
├── 2025-01-20_unknown/  # 无法识别日期的照片
│   ├── photo_004.jpg
│   └── ...
├── download_log.txt     # 详细下载日志
└── progress.json        # 进度保存文件
```

### 功能特色
- **原图质量**：自动检测并下载最高质量的原图
- **断点续传**：支持中断后继续下载
- **去重处理**：基于文件内容哈希避免重复下载
- **进度监控**：实时显示下载进度和统计信息
- **日志记录**：详细的操作日志便于问题排查

## 故障排除

### 问题1：找不到Chrome浏览器
```
错误：无法启动Chrome浏览器
```
**解决方案**：确保已安装Chrome浏览器和ChromeDriver

### 问题2：权限问题
```
Error: Unable to acquire the dpkg frontend lock
```
**解决方案**：使用sudo运行安装脚本

### 问题3：简化版本找不到照片
```
未找到任何照片链接
```
**说明**：网站使用JavaScript动态加载，需要使用完整版本

### 问题4：网络连接问题
**解决方案**：
- 检查网络连接
- 尝试使用VPN（如果被地理限制）
- 增加请求延迟

## 技术细节

### 网站分析结果
- **网站类型**：Vue.js单页应用
- **内容加载**：JavaScript动态加载
- **API端点**：需要浏览器执行JavaScript才能获取
- **反爬虫**：使用标准浏览器请求头可以正常访问

### 脚本特性
- **智能滚动**：自动滚动并点击"加载更多"
- **质量优化**：自动获取最高质量的原图
- **重复检测**：基于文件哈希防止重复下载
- **错误处理**：完善的异常处理和重试机制
- **进度显示**：实时显示下载进度

## 下一步

1. 安装Chrome浏览器和ChromeDriver
2. 运行完整版本的脚本
3. 享受自动下载的跳水锦标赛照片！

---

**注意**：请遵守网站的使用条款，仅将下载的照片用于个人学习目的。