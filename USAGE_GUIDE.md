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

### 1. diving_photos_downloader.py（完整版本）
- **功能**：完整的照片下载器，支持JavaScript动态加载
- **要求**：需要Chrome浏览器和ChromeDriver
- **特点**：能够处理动态内容，滚动加载，获取所有照片

### 2. diving_photos_downloader_simple.py（简化版本）
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

### 方法1：使用便捷脚本
```bash
# 直接运行（会自动处理环境）
./run_downloader.sh
```

### 方法2：直接运行Python脚本
```bash
# 运行完整版本（推荐）
python3 diving_photos_downloader.py

# 或运行简化版本（功能有限）
python3 diving_photos_downloader_simple.py
```

## 无头模式（服务器环境）

如果在没有图形界面的服务器上运行，需要启用无头模式：

1. 编辑 `diving_photos_downloader.py`
2. 找到这一行：`# chrome_options.add_argument('--headless')`
3. 取消注释：`chrome_options.add_argument('--headless')`

## 预期结果

成功运行后，照片将保存在以下结构中：

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