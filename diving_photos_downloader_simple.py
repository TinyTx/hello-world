#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
2025年全国少年儿童跳水锦标赛照片下载器 (简化版)
Simple version for testing without full browser setup
"""

import os
import re
import time
import requests
from datetime import datetime
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import hashlib

class SimpleDivingPhotosDownloader:
    def __init__(self, base_url, download_dir="diving_championship_photos"):
        self.base_url = base_url
        self.download_dir = download_dir
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        self.downloaded_hashes = set()
        
        # 创建主下载目录
        if not os.path.exists(self.download_dir):
            os.makedirs(self.download_dir)
    
    def get_page_content(self):
        """获取页面内容"""
        try:
            print(f"正在访问: {self.base_url}")
            # 添加更多的请求头
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
            }
            
            response = self.session.get(self.base_url, headers=headers, timeout=30, verify=True)
            print(f"响应状态码: {response.status_code}")
            print(f"响应头: {dict(response.headers)}")
            
            response.raise_for_status()
            content = response.text
            print(f"页面内容长度: {len(content)} 字符")
            
            # 保存页面内容到文件以便调试
            with open('page_content.html', 'w', encoding='utf-8') as f:
                f.write(content)
            print("页面内容已保存到 page_content.html")
            
            return content
        except Exception as e:
            print(f"获取页面失败: {e}")
            print(f"错误类型: {type(e).__name__}")
            return None
    
    def extract_photo_urls_from_html(self, html_content):
        """从HTML中提取照片URL"""
        soup = BeautifulSoup(html_content, 'html.parser')
        photo_urls = []
        
        # 查找各种可能的图片标签和属性
        img_selectors = [
            'img[src]',
            'img[data-src]',
            'img[data-original]',
            'img[data-lazy]',
            '[style*="background-image"]',
        ]
        
        for selector in img_selectors:
            elements = soup.select(selector)
            for element in elements:
                # 提取各种可能的图片URL属性
                for attr in ['src', 'data-src', 'data-original', 'data-lazy', 'data-url']:
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
                    r'src:\s*["\']([^"\']*\.(?:jpg|jpeg|png|webp|gif)(?:\?[^"\']*)?)["\']',
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
        
        return filtered_urls
    
    def is_valid_image_url(self, url):
        """检查是否为有效的图片URL"""
        if not url or len(url) < 10:
            return False
        
        # 检查文件扩展名或图片相关关键词
        url_lower = url.lower()
        
        # 图片扩展名
        has_image_ext = any(ext in url_lower for ext in ['.jpg', '.jpeg', '.png', '.webp', '.gif'])
        
        # 可能的图片URL模式
        has_image_pattern = any(pattern in url_lower for pattern in ['image', 'photo', 'img', 'pic'])
        
        # 检查是否为http(s)链接
        is_http = url.startswith(('http://', 'https://', '//'))
        
        # 排除明显的非图片链接
        exclude_patterns = ['logo', 'icon', 'avatar', 'thumb', 'button', 'banner', '.js', '.css']
        is_excluded = any(pattern in url_lower for pattern in exclude_patterns)
        
        return (has_image_ext or has_image_pattern) and is_http and not is_excluded
    
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
        
        modified_url = url
        for pattern, replacement in quality_patterns:
            modified_url = re.sub(pattern, replacement, modified_url)
        
        # 尝试不同的高质量后缀
        high_quality_suffixes = ['', '?quality=100', '?w=2000', '?original=true']
        
        for suffix in high_quality_suffixes:
            test_url = modified_url + suffix
            try:
                response = self.session.head(test_url, timeout=10)
                if response.status_code == 200:
                    content_length = int(response.headers.get('content-length', 0))
                    if content_length > 0:
                        return test_url
            except:
                continue
        
        return url
    
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
            
            # 检查文件大小，跳过过小的文件（可能是占位符）
            if len(content) < 1024:  # 小于1KB
                print(f"跳过过小文件: {os.path.basename(urlparse(url).path)}")
                return False
            
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
    
    def test_basic_access(self):
        """测试基本网页访问"""
        print("正在测试网页访问...")
        html_content = self.get_page_content()
        if html_content:
            print(f"成功获取页面内容，长度: {len(html_content)} 字符")
            
            # 查看页面中是否包含图片相关内容
            if 'img' in html_content.lower():
                print("页面包含图片标签")
            if 'photo' in html_content.lower() or 'image' in html_content.lower():
                print("页面包含图片相关关键词")
            
            return html_content
        else:
            print("无法访问页面")
            return None
    
    def download_all_photos(self):
        """下载所有照片的主函数"""
        print("开始下载2025年全国少年儿童跳水锦标赛照片...")
        
        # 获取页面内容
        html_content = self.get_page_content()
        if not html_content:
            print("无法获取页面内容")
            return
        
        # 提取照片URL
        photo_urls = self.extract_photo_urls_from_html(html_content)
        
        if not photo_urls:
            print("未找到任何照片链接")
            print("这可能是因为:")
            print("1. 页面使用了复杂的JavaScript动态加载")
            print("2. 需要登录或特殊权限")
            print("3. 反爬虫机制阻止了访问")
            print("建议使用完整版本的脚本（需要安装浏览器）")
            return
        
        print(f"找到 {len(photo_urls)} 个可能的照片链接")
        
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
        
        if total_downloaded == 0:
            print("\n注意：未成功下载任何照片。")
            print("这可能是因为网站使用了复杂的动态加载机制。")
            print("建议使用完整版本的脚本（diving_photos_downloader.py）。")

def main():
    url = "https://tlwtpbvzb.vzan.com/v3/course/alive/1827403580?v=1755091438866"
    downloader = SimpleDivingPhotosDownloader(url)
    
    # 先测试基本访问
    html_content = downloader.test_basic_access()
    
    if html_content:
        # 尝试下载照片
        downloader.download_all_photos()
    else:
        print("无法访问目标网页，请检查网络连接或网址是否正确。")

if __name__ == "__main__":
    main()