#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
2025年全国少年儿童跳水锦标赛照片下载器
Download photos from 2025 National Youth Diving Championship
"""

import os
import re
import time
import json
import requests
from datetime import datetime
from urllib.parse import urljoin, urlparse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup
import hashlib

class DivingPhotosDownloader:
    def __init__(self, base_url, download_dir="diving_championship_photos"):
        self.base_url = base_url
        self.download_dir = download_dir
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        self.downloaded_hashes = set()  # 防止重复下载
        
        # 创建主下载目录
        if not os.path.exists(self.download_dir):
            os.makedirs(self.download_dir)
    
    def setup_driver(self):
        """设置Chrome浏览器驱动"""
        chrome_options = Options()
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        # 如果在无头模式下运行，取消注释下面这行
        # chrome_options.add_argument('--headless')
        
        try:
            driver = webdriver.Chrome(options=chrome_options)
            return driver
        except Exception as e:
            print(f"错误：无法启动Chrome浏览器。请确保已安装Chrome和chromedriver。\n详细错误：{e}")
            return None
    
    def scroll_and_load_all_content(self, driver):
        """滚动页面并加载所有动态内容"""
        print("正在加载页面内容...")
        
        # 等待页面初始加载
        time.sleep(3)
        
        # 获取初始页面高度
        last_height = driver.execute_script("return document.body.scrollHeight")
        
        # 模拟用户逐步滚动
        scroll_attempts = 0
        max_attempts = 20
        
        while scroll_attempts < max_attempts:
            # 滚动到页面底部
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            
            # 等待新内容加载
            time.sleep(2)
            
            # 检查是否有新内容加载
            new_height = driver.execute_script("return document.body.scrollHeight")
            
            if new_height == last_height:
                # 尝试点击"加载更多"按钮（如果存在）
                try:
                    load_more_buttons = driver.find_elements(By.XPATH, 
                        "//button[contains(text(), '加载更多') or contains(text(), '更多') or contains(@class, 'load-more')]")
                    for button in load_more_buttons:
                        if button.is_displayed():
                            driver.execute_script("arguments[0].click();", button)
                            time.sleep(3)
                            break
                except:
                    pass
                
                # 再次检查高度
                newer_height = driver.execute_script("return document.body.scrollHeight")
                if newer_height == new_height:
                    break
                else:
                    last_height = newer_height
            else:
                last_height = new_height
            
            scroll_attempts += 1
            print(f"滚动加载进度: {scroll_attempts}/{max_attempts}")
        
        # 最后滚动到顶部确保所有内容都被加载
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(2)
        
        print("页面内容加载完成")
    
    def extract_photo_urls(self, driver):
        """提取所有照片URL"""
        print("正在提取照片链接...")
        
        # 获取页面源代码
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        photo_urls = []
        
        # 查找各种可能的图片标签和属性
        img_selectors = [
            'img[src]',
            'img[data-src]',
            'img[data-original]',
            '[style*="background-image"]',
            'picture img',
            '.photo img',
            '.image img',
            '.gallery img'
        ]
        
        for selector in img_selectors:
            elements = soup.select(selector)
            for element in elements:
                # 提取src, data-src, data-original等属性
                for attr in ['src', 'data-src', 'data-original', 'data-lazy']:
                    url = element.get(attr)
                    if url and self.is_valid_image_url(url):
                        full_url = urljoin(self.base_url, url)
                        photo_urls.append(full_url)
                
                # 提取background-image中的URL
                style = element.get('style', '')
                if 'background-image' in style:
                    match = re.search(r'url\(["\']?(.*?)["\']?\)', style)
                    if match:
                        url = match.group(1)
                        if self.is_valid_image_url(url):
                            full_url = urljoin(self.base_url, url)
                            photo_urls.append(full_url)
        
        # 查找JavaScript中的图片链接
        scripts = soup.find_all('script')
        for script in scripts:
            if script.string:
                # 查找可能的图片URL模式
                img_patterns = [
                    r'"(https?://[^"]*\.(?:jpg|jpeg|png|webp|gif)(?:\?[^"]*)?)"',
                    r"'(https?://[^']*\.(?:jpg|jpeg|png|webp|gif)(?:\?[^']*)?)'",
                    r'url:\s*["\']([^"\']*\.(?:jpg|jpeg|png|webp|gif)(?:\?[^"\']*)?)["\']',
                ]
                
                for pattern in img_patterns:
                    matches = re.findall(pattern, script.string, re.IGNORECASE)
                    for match in matches:
                        if self.is_valid_image_url(match):
                            full_url = urljoin(self.base_url, match)
                            photo_urls.append(full_url)
        
        # 去重并过滤
        unique_urls = list(set(photo_urls))
        filtered_urls = [url for url in unique_urls if self.is_competition_photo(url)]
        
        print(f"找到 {len(filtered_urls)} 张照片")
        return filtered_urls
    
    def is_valid_image_url(self, url):
        """检查是否为有效的图片URL"""
        if not url or len(url) < 10:
            return False
        
        # 检查文件扩展名
        image_extensions = ['.jpg', '.jpeg', '.png', '.webp', '.gif']
        url_lower = url.lower()
        
        # 检查是否包含图片扩展名
        has_extension = any(ext in url_lower for ext in image_extensions)
        
        # 检查是否为http(s)链接
        is_http = url.startswith(('http://', 'https://', '//'))
        
        # 排除明显的非图片链接
        exclude_patterns = ['logo', 'icon', 'avatar', 'thumb', 'button', 'banner']
        is_excluded = any(pattern in url_lower for pattern in exclude_patterns)
        
        return has_extension and is_http and not is_excluded
    
    def is_competition_photo(self, url):
        """判断是否为比赛照片"""
        # 排除明显的非比赛照片
        exclude_keywords = [
            'logo', 'icon', 'avatar', 'profile', 'header', 'footer',
            'banner', 'ad', 'advertisement', 'sponsor', 'thumb'
        ]
        
        url_lower = url.lower()
        return not any(keyword in url_lower for keyword in exclude_keywords)
    
    def get_highest_quality_url(self, url):
        """尝试获取最高质量的图片URL"""
        # 常见的图片质量参数模式
        quality_patterns = [
            (r'[?&]w=\d+', ''),  # 移除宽度限制
            (r'[?&]h=\d+', ''),  # 移除高度限制
            (r'[?&]q=\d+', ''),  # 移除质量限制
            (r'[?&]quality=\d+', ''),
            (r'[?&]size=\w+', ''),
            (r'_thumb\.|_small\.|_medium\.', '.'),  # 移除缩略图标识
            (r'@\d+w\.|@\d+h\.', '.'),  # 移除尺寸标识
        ]
        
        original_url = url
        for pattern, replacement in quality_patterns:
            url = re.sub(pattern, replacement, url)
        
        # 尝试不同的高质量后缀
        high_quality_suffixes = ['', '?quality=100', '?w=2000', '?original=true']
        
        for suffix in high_quality_suffixes:
            test_url = url + suffix
            try:
                response = self.session.head(test_url, timeout=10)
                if response.status_code == 200:
                    content_length = int(response.headers.get('content-length', 0))
                    if content_length > 0:
                        return test_url
            except:
                continue
        
        return original_url
    
    def extract_date_from_url(self, url):
        """从URL中提取日期"""
        # 尝试从URL中提取日期模式
        date_patterns = [
            r'(\d{4})[/-](\d{1,2})[/-](\d{1,2})',  # YYYY-MM-DD or YYYY/MM/DD
            r'(\d{4})(\d{2})(\d{2})',  # YYYYMMDD
            r'(\d{2})[/-](\d{2})[/-](\d{4})',  # MM-DD-YYYY or MM/DD/YYYY
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, url)
            if match:
                try:
                    groups = match.groups()
                    if len(groups[0]) == 4:  # 年份在前
                        year, month, day = groups
                    else:  # 年份在后
                        month, day, year = groups
                    
                    # 验证日期有效性
                    date_obj = datetime(int(year), int(month), int(day))
                    return date_obj.strftime('%Y-%m-%d')
                except:
                    continue
        
        return None
    
    def get_file_hash(self, content):
        """计算文件内容的哈希值"""
        return hashlib.md5(content).hexdigest()
    
    def download_photo(self, url, date_folder):
        """下载单张照片"""
        try:
            # 获取最高质量的URL
            high_quality_url = self.get_highest_quality_url(url)
            
            response = self.session.get(high_quality_url, timeout=30, stream=True)
            response.raise_for_status()
            
            # 读取内容
            content = response.content
            
            # 检查是否已下载过（基于内容哈希）
            file_hash = self.get_file_hash(content)
            if file_hash in self.downloaded_hashes:
                print(f"跳过重复文件: {os.path.basename(urlparse(url).path)}")
                return False
            
            # 确定文件名
            parsed_url = urlparse(high_quality_url)
            filename = os.path.basename(parsed_url.path)
            
            if not filename or '.' not in filename:
                # 从Content-Type推断文件扩展名
                content_type = response.headers.get('content-type', '')
                if 'jpeg' in content_type or 'jpg' in content_type:
                    filename = f"photo_{int(time.time())}.jpg"
                elif 'png' in content_type:
                    filename = f"photo_{int(time.time())}.png"
                elif 'webp' in content_type:
                    filename = f"photo_{int(time.time())}.webp"
                else:
                    filename = f"photo_{int(time.time())}.jpg"
            
            # 创建完整的文件路径
            filepath = os.path.join(date_folder, filename)
            
            # 如果文件已存在，添加序号
            base_name, ext = os.path.splitext(filename)
            counter = 1
            while os.path.exists(filepath):
                new_filename = f"{base_name}_{counter}{ext}"
                filepath = os.path.join(date_folder, new_filename)
                counter += 1
            
            # 保存文件
            with open(filepath, 'wb') as f:
                f.write(content)
            
            # 记录已下载的文件哈希
            self.downloaded_hashes.add(file_hash)
            
            file_size = len(content) / 1024  # KB
            print(f"已下载: {filename} ({file_size:.1f} KB)")
            return True
            
        except Exception as e:
            print(f"下载失败: {url} - {str(e)}")
            return False
    
    def download_all_photos(self):
        """下载所有照片的主函数"""
        print("开始下载2025年全国少年儿童跳水锦标赛照片...")
        
        # 设置浏览器驱动
        driver = self.setup_driver()
        if not driver:
            return
        
        try:
            # 打开目标网页
            print(f"正在访问: {self.base_url}")
            driver.get(self.base_url)
            
            # 滚动并加载所有内容
            self.scroll_and_load_all_content(driver)
            
            # 提取所有照片URL
            photo_urls = self.extract_photo_urls(driver)
            
            if not photo_urls:
                print("未找到任何照片链接")
                return
            
            print(f"准备下载 {len(photo_urls)} 张照片")
            
            # 按日期组织下载
            date_groups = {}
            unknown_date_photos = []
            
            for url in photo_urls:
                date_str = self.extract_date_from_url(url)
                if date_str:
                    if date_str not in date_groups:
                        date_groups[date_str] = []
                    date_groups[date_str].append(url)
                else:
                    unknown_date_photos.append(url)
            
            # 如果有未识别日期的照片，使用当前日期
            if unknown_date_photos:
                current_date = datetime.now().strftime('%Y-%m-%d')
                date_groups[f"{current_date}_unknown"] = unknown_date_photos
            
            # 下载照片
            total_downloaded = 0
            for date_str, urls in date_groups.items():
                print(f"\n正在下载 {date_str} 的照片 ({len(urls)} 张)")
                
                # 创建日期文件夹
                date_folder = os.path.join(self.download_dir, date_str)
                if not os.path.exists(date_folder):
                    os.makedirs(date_folder)
                
                downloaded_count = 0
                for i, url in enumerate(urls, 1):
                    print(f"下载进度: {i}/{len(urls)}", end=" - ")
                    if self.download_photo(url, date_folder):
                        downloaded_count += 1
                        total_downloaded += 1
                    
                    # 添加延迟避免请求过快
                    time.sleep(0.5)
                
                print(f"{date_str} 文件夹下载完成: {downloaded_count}/{len(urls)} 张")
            
            print(f"\n全部下载完成！总共下载了 {total_downloaded} 张照片")
            print(f"照片保存位置: {os.path.abspath(self.download_dir)}")
            
        finally:
            driver.quit()

def main():
    url = "https://tlwtpbvzb.vzan.com/v3/course/alive/1827403580?v=1755091438866"
    downloader = DivingPhotosDownloader(url)
    downloader.download_all_photos()

if __name__ == "__main__":
    main()