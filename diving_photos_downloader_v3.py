#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
跳水锦标赛照片下载器 V3 - 直接下载原图版本
Direct download version bypassing popup workflow
"""

import os
import re
import time
import json
import requests
from datetime import datetime
from urllib.parse import urljoin, urlparse, parse_qs
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import hashlib

class DivingPhotosDownloaderV3:
    def __init__(self, base_url, download_dir="diving_championship_photos_v3"):
        self.base_url = base_url
        self.download_dir = download_dir
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Referer': base_url
        })
        self.downloaded_hashes = set()
        self.downloaded_files = set()
        self.driver = None
        self.login_completed = False
        
        # 创建主下载目录
        if not os.path.exists(self.download_dir):
            os.makedirs(self.download_dir)
        
        # 按日期创建子目录
        self.create_date_folders()
        
        # 创建日志文件
        self.log_file = os.path.join(self.download_dir, "download_log_v3.txt")
        self.progress_file = os.path.join(self.download_dir, "progress_v3.json")
        
        # 加载之前的进度
        self.load_progress()
    
    def create_date_folders(self):
        """创建按日期分类的文件夹"""
        # 根据赛事时间创建可能的日期文件夹
        dates = [
            "2025-08-13", "2025-08-14", "2025-08-15", "2025-08-16", 
            "2025-08-17", "2025-08-18", "2025-08-19", "2025-08-20"
        ]
        
        for date in dates:
            date_dir = os.path.join(self.download_dir, date)
            if not os.path.exists(date_dir):
                os.makedirs(date_dir)
        
        # 创建未知日期文件夹
        unknown_dir = os.path.join(self.download_dir, "unknown_date")
        if not os.path.exists(unknown_dir):
            os.makedirs(unknown_dir)
    
    def log_message(self, message):
        """记录日志"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        print(log_entry)
        
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(log_entry + '\n')
    
    def save_progress(self):
        """保存下载进度"""
        progress = {
            'downloaded_files': list(self.downloaded_files),
            'downloaded_hashes': list(self.downloaded_hashes),
            'last_update': datetime.now().isoformat(),
            'total_downloaded': len(self.downloaded_files)
        }
        with open(self.progress_file, 'w', encoding='utf-8') as f:
            json.dump(progress, f, ensure_ascii=False, indent=2)
    
    def load_progress(self):
        """加载之前的进度"""
        if os.path.exists(self.progress_file):
            try:
                with open(self.progress_file, 'r', encoding='utf-8') as f:
                    progress = json.load(f)
                self.downloaded_files = set(progress.get('downloaded_files', []))
                self.downloaded_hashes = set(progress.get('downloaded_hashes', []))
                self.log_message(f"已加载之前的进度：{len(self.downloaded_files)} 个文件")
            except Exception as e:
                self.log_message(f"加载进度失败：{e}")
    
    def setup_driver(self):
        """设置Chrome浏览器驱动"""
        chrome_options = Options()
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        try:
            driver = webdriver.Chrome(options=chrome_options)
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            return driver
        except Exception as e:
            self.log_message(f"错误：无法启动Chrome浏览器。{e}")
            return None
    
    def wait_for_login(self):
        """等待用户手动登录"""
        self.log_message("请在浏览器中完成登录...")
        self.log_message("登录完成后，请在控制台输入 'y' 并按回车继续")
        
        while True:
            confirmation = input("请确认是否已完成登录 (y/n): ").strip().lower()
            if confirmation == 'y':
                self.login_completed = True
                break
            elif confirmation == 'n':
                self.log_message("请继续完成登录...")
                time.sleep(5)
            else:
                self.log_message("请输入 'y' 或 'n'")
        
        self.log_message("登录确认完成，开始提取图片链接...")
        time.sleep(3)
    
    def scroll_and_load_all_content(self):
        """滚动页面并加载所有动态内容"""
        self.log_message("开始加载所有照片内容...")
        
        last_height = 0
        scroll_attempts = 0
        max_attempts = 500  # 增加滚动次数确保加载完整
        no_new_content_count = 0
        
        while scroll_attempts < max_attempts:
            current_height = self.driver.execute_script("return document.body.scrollHeight")
            
            # 获取当前页面中的图片数量
            img_count = len(self.driver.find_elements(By.TAG_NAME, "img"))
            if scroll_attempts % 20 == 0:
                self.log_message(f"滚动 {scroll_attempts + 1}/{max_attempts}, 当前图片数量: {img_count}")
            
            # 缓慢滚动，确保所有内容都被加载
            self.driver.execute_script("window.scrollBy(0, 600);")
            time.sleep(1.5)
            
            # 尝试点击"加载更多"按钮
            if scroll_attempts % 3 == 0:
                self.click_load_more_buttons()
            
            # 检查是否有新内容加载
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            
            if new_height == current_height and new_height == last_height:
                no_new_content_count += 1
                if no_new_content_count >= 10:
                    self.log_message("连续多次无新内容，可能已加载完成")
                    break
            else:
                no_new_content_count = 0
                last_height = new_height
            
            scroll_attempts += 1
            
            # 每100次滚动保存一次进度
            if scroll_attempts % 100 == 0:
                self.save_progress()
        
        # 滚动到顶部，再次确保所有内容加载
        self.driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(3)
        
        final_img_count = len(self.driver.find_elements(By.TAG_NAME, "img"))
        self.log_message(f"页面加载完成，共找到 {final_img_count} 个图片元素")
        
        return final_img_count
    
    def click_load_more_buttons(self):
        """点击加载更多按钮"""
        load_more_selectors = [
            "//button[contains(text(), '加载更多')]",
            "//button[contains(text(), '更多')]",
            "//div[contains(text(), '加载更多')]",
            "//span[contains(text(), '加载更多')]",
            "//a[contains(text(), '更多')]",
            "//*[contains(@class, 'load-more')]",
            "//*[contains(@class, 'more')]",
            "//*[contains(@class, 'btn-more')]"
        ]
        
        for selector in load_more_selectors:
            try:
                buttons = self.driver.find_elements(By.XPATH, selector)
                for button in buttons:
                    if button.is_displayed() and button.is_enabled():
                        try:
                            self.driver.execute_script("arguments[0].scrollIntoView();", button)
                            time.sleep(0.5)
                            self.driver.execute_script("arguments[0].click();", button)
                            self.log_message("点击了加载更多按钮")
                            time.sleep(2)
                            return True
                        except:
                            pass
            except:
                pass
        return False
    
    def extract_all_image_urls(self):
        """提取所有图片URL"""
        self.log_message("开始提取所有图片URL...")
        
        # 多种方式查找图片
        image_urls = []
        
        # 方法1：从img标签提取
        img_elements = self.driver.find_elements(By.TAG_NAME, "img")
        for img in img_elements:
            for attr in ['src', 'data-src', 'data-original', 'data-lazy']:
                url = img.get_attribute(attr)
                if url and self.is_valid_image_url(url):
                    image_urls.append(url)
        
        # 方法2：从background-image样式提取
        elements_with_bg = self.driver.find_elements(By.CSS_SELECTOR, "[style*='background-image']")
        for element in elements_with_bg:
            style = element.get_attribute('style')
            if style:
                matches = re.findall(r'background-image:\s*url\(["\']?(.*?)["\']?\)', style)
                for match in matches:
                    if self.is_valid_image_url(match):
                        image_urls.append(urljoin(self.base_url, match))
        
        # 方法3：从页面源代码中提取图片URL
        page_source = self.driver.page_source
        url_patterns = [
            r'"(https?://[^"]*i\d*cut\.vzan\.com[^"]*\.(?:jpg|jpeg|png|webp|gif)(?:\?[^"]*)?)"',
            r"'(https?://[^']*i\d*cut\.vzan\.com[^']*\.(?:jpg|jpeg|png|webp|gif)(?:\?[^']*)?)'",
            r'src:\s*["\']([^"\']*i\d*cut\.vzan\.com[^"\']*\.(?:jpg|jpeg|png|webp|gif)(?:\?[^"\']*)?)["\']'
        ]
        
        for pattern in url_patterns:
            matches = re.findall(pattern, page_source, re.IGNORECASE)
            for match in matches:
                if self.is_valid_image_url(match):
                    image_urls.append(match)
        
        # 去重并排序
        unique_urls = list(set(image_urls))
        valid_urls = [url for url in unique_urls if self.is_competition_photo(url)]
        
        self.log_message(f"提取到 {len(valid_urls)} 个有效图片URL")
        
        return valid_urls
    
    def is_valid_image_url(self, url):
        """检查是否为有效的图片URL"""
        if not url or len(url) < 20:
            return False
        
        # 检查是否为图片URL
        url_lower = url.lower()
        has_image_ext = any(ext in url_lower for ext in ['.jpg', '.jpeg', '.png', '.webp', '.gif'])
        
        # 检查是否为vzan域名的图片
        is_vzan_image = 'vzan.com' in url_lower and ('imagelive' in url_lower or 'live' in url_lower)
        
        return has_image_ext and is_vzan_image
    
    def is_competition_photo(self, url):
        """判断是否为比赛照片"""
        exclude_keywords = [
            'logo', 'icon', 'avatar', 'profile', 'header', 'footer',
            'banner', 'ad', 'advertisement', 'sponsor', 'button', 'bg'
        ]
        
        url_lower = url.lower()
        return not any(keyword in url_lower for keyword in exclude_keywords)
    
    def enhance_image_url_quality(self, url):
        """尝试获取最高质量的图片URL"""
        original_url = url
        
        # 移除可能的质量限制参数
        quality_patterns = [
            (r'[?&]imageMogr2/auto-orient[^&]*', ''),
            (r'[?&]imageMogr2/format/[^&]*', ''),
            (r'[?&]imageMogr2/quality/[^&]*', ''),
            (r'[?&]imageMogr2/thumbnail/[^&]*', ''),
            (r'[?&]w=\d+', ''),
            (r'[?&]h=\d+', ''),
            (r'[?&]q=\d+', ''),
            (r'[?&]quality=\d+', ''),
            (r'[?&]size=\w+', ''),
        ]
        
        enhanced_url = url
        for pattern, replacement in quality_patterns:
            enhanced_url = re.sub(pattern, replacement, enhanced_url)
        
        # 清理末尾的多余符号
        enhanced_url = re.sub(r'[?&]+$', '', enhanced_url)
        
        # 如果URL被过度清理，返回原始URL
        if not enhanced_url or len(enhanced_url) < 30:
            return original_url
        
        return enhanced_url
    
    def extract_date_from_url(self, url):
        """从URL中提取日期"""
        # 从URL中提取日期，特别是vzan的URL格式
        date_patterns = [
            r'(\d{4})(\d{2})(\d{2})',  # YYYYMMDD
            r'(\d{4})[/-](\d{1,2})[/-](\d{1,2})',  # YYYY-MM-DD
            r'/(\d{4})/(\d{2})/(\d{2})/',  # /YYYY/MM/DD/
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, url)
            if match:
                try:
                    groups = match.groups()
                    if len(groups[0]) == 4:  # 年份在前
                        year, month, day = groups
                    else:  # 可能是其他格式
                        continue
                    
                    # 验证日期有效性
                    date_obj = datetime(int(year), int(month), int(day))
                    return date_obj.strftime('%Y-%m-%d')
                except:
                    continue
        
        return "unknown_date"
    
    def get_file_hash(self, content):
        """计算文件内容的哈希值"""
        return hashlib.md5(content).hexdigest()
    
    def download_single_image(self, url, index, total):
        """下载单张图片"""
        try:
            # 检查是否已下载过
            if url in self.downloaded_files:
                self.log_message(f"跳过已下载的图片 {index}/{total}")
                return True
            
            # 获取最高质量的URL
            enhanced_url = self.enhance_image_url_quality(url)
            
            self.log_message(f"下载 {index}/{total}: {enhanced_url}")
            
            # 下载图片
            response = self.session.get(enhanced_url, timeout=30, stream=True)
            response.raise_for_status()
            
            content = response.content
            
            # 检查文件大小
            if len(content) < 10240:  # 小于10KB，可能不是真实照片
                self.log_message(f"文件过小，跳过: {len(content)} bytes")
                return False
            
            # 检查是否为重复内容
            file_hash = self.get_file_hash(content)
            if file_hash in self.downloaded_hashes:
                self.log_message(f"跳过重复内容")
                return False
            
            # 确定保存路径
            date_str = self.extract_date_from_url(url)
            date_folder = os.path.join(self.download_dir, date_str)
            
            # 生成文件名
            filename = self.generate_filename(enhanced_url, content)
            filepath = os.path.join(date_folder, filename)
            
            # 保存文件
            with open(filepath, 'wb') as f:
                f.write(content)
            
            # 记录下载信息
            self.downloaded_files.add(url)
            self.downloaded_hashes.add(file_hash)
            
            file_size = len(content) / 1024  # KB
            self.log_message(f"下载成功: {filename} ({file_size:.1f} KB)")
            
            return True
            
        except Exception as e:
            self.log_message(f"下载失败: {url} - {str(e)}")
            return False
    
    def generate_filename(self, url, content):
        """生成文件名"""
        # 从URL中提取原始文件名
        parsed_url = urlparse(url)
        original_filename = os.path.basename(parsed_url.path)
        
        if original_filename and '.' in original_filename:
            # 清理文件名
            filename = re.sub(r'[<>:"/\\|?*]', '_', original_filename)
        else:
            # 生成基于时间戳的文件名
            timestamp = int(time.time() * 1000)
            content_type = self.session.head(url).headers.get('content-type', '')
            if 'jpeg' in content_type or 'jpg' in content_type:
                filename = f"diving_photo_{timestamp}.jpg"
            elif 'png' in content_type:
                filename = f"diving_photo_{timestamp}.png"
            elif 'webp' in content_type:
                filename = f"diving_photo_{timestamp}.webp"
            else:
                filename = f"diving_photo_{timestamp}.jpg"
        
        return filename
    
    def download_all_photos(self):
        """下载所有照片的主函数"""
        self.log_message("开始V3版照片下载器...")
        
        # 设置浏览器
        self.driver = self.setup_driver()
        if not self.driver:
            return
        
        try:
            # 打开目标网页
            self.log_message(f"正在访问: {self.base_url}")
            self.driver.get(self.base_url)
            
            # 等待页面加载
            self.log_message("等待页面加载（5秒）...")
            time.sleep(5)
            
            # 等待用户登录
            self.wait_for_login()
            
            # 滚动并加载所有内容
            total_images = self.scroll_and_load_all_content()
            
            # 提取所有图片URL
            image_urls = self.extract_all_image_urls()
            
            if not image_urls:
                self.log_message("未找到任何图片链接")
                return
            
            self.log_message(f"准备下载 {len(image_urls)} 张照片")
            
            # 下载所有图片
            total_downloaded = 0
            total_failed = 0
            
            for i, url in enumerate(image_urls, 1):
                success = self.download_single_image(url, i, len(image_urls))
                if success:
                    total_downloaded += 1
                else:
                    total_failed += 1
                
                # 每下载20张照片保存一次进度
                if i % 20 == 0:
                    self.save_progress()
                    self.log_message(f"进度报告: 成功 {total_downloaded}, 失败 {total_failed}, 剩余 {len(image_urls) - i}")
                
                # 控制下载速度
                time.sleep(0.3)
            
            # 保存最终进度
            self.save_progress()
            
            self.log_message(f"\n全部下载完成！")
            self.log_message(f"成功下载: {total_downloaded} 张照片")
            self.log_message(f"下载失败: {total_failed} 张照片")
            self.log_message(f"保存位置: {os.path.abspath(self.download_dir)}")
            
        finally:
            input("按回车键关闭浏览器...")
            if self.driver:
                self.driver.quit()

def main():
    url = "https://tlwtpbvzb.vzan.com/v3/course/alive/1827403580?v=1755091438866"
    downloader = DivingPhotosDownloaderV3(url)
    downloader.download_all_photos()

if __name__ == "__main__":
    main()