#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
2025年全国少年儿童跳水锦标赛照片下载器 (增强版)
Enhanced version with login support and original image detection
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
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException
from bs4 import BeautifulSoup
import hashlib

class EnhancedDivingPhotosDownloader:
    def __init__(self, base_url, download_dir="diving_championship_photos_original"):
        self.base_url = base_url
        self.download_dir = download_dir
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        self.downloaded_hashes = set()
        self.downloaded_files = set()
        self.driver = None
        self.login_completed = False
        
        # 创建主下载目录
        if not os.path.exists(self.download_dir):
            os.makedirs(self.download_dir)
        
        # 创建日志文件
        self.log_file = os.path.join(self.download_dir, "download_log.txt")
        self.progress_file = os.path.join(self.download_dir, "progress.json")
        
        # 加载之前的进度
        self.load_progress()
    
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
            'last_update': datetime.now().isoformat()
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
        
        # 基本设置
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # 设置用户代理
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        # 如果需要无头模式，取消下面的注释
        # chrome_options.add_argument('--headless')
        
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
        
        # 检测登录状态的常见元素
        login_indicators = [
            "//button[contains(text(), '登录')]",
            "//button[contains(text(), '登录账号')]",
            "//a[contains(text(), '登录')]",
            "//input[@placeholder*='手机号' or @placeholder*='账号' or @placeholder*='用户名']",
            "//input[@type='password']"
        ]
        
        logout_indicators = [
            "//button[contains(text(), '退出')]",
            "//a[contains(text(), '退出')]",
            "//span[contains(text(), '个人中心')]",
            "//div[contains(@class, 'avatar')]",
            "//div[contains(@class, 'user')]"
        ]
        
        while True:
            try:
                # 检查是否还有登录按钮（表示未登录）
                login_elements = []
                for xpath in login_indicators:
                    try:
                        elements = self.driver.find_elements(By.XPATH, xpath)
                        login_elements.extend(elements)
                    except:
                        pass
                
                # 检查是否有登录后的元素（表示已登录）
                logout_elements = []
                for xpath in logout_indicators:
                    try:
                        elements = self.driver.find_elements(By.XPATH, xpath)
                        logout_elements.extend(elements)
                    except:
                        pass
                
                # 如果没有登录元素且有登录后的元素，可能已经登录
                if not login_elements and logout_elements:
                    self.log_message("检测到可能已登录")
                    confirmation = input("是否已完成登录？(y/n): ").strip().lower()
                    if confirmation == 'y':
                        self.login_completed = True
                        break
                
                # 让用户确认登录状态
                confirmation = input("请确认是否已完成登录 (y/n): ").strip().lower()
                if confirmation == 'y':
                    self.login_completed = True
                    break
                elif confirmation == 'n':
                    self.log_message("请继续完成登录...")
                    time.sleep(5)
                else:
                    self.log_message("请输入 'y' 或 'n'")
                    
            except Exception as e:
                self.log_message(f"检测登录状态时出错：{e}")
                time.sleep(2)
        
        self.log_message("登录确认完成，开始分析页面...")
        time.sleep(3)  # 等待页面稳定
    
    def wait_for_page_load(self, timeout=10):
        """等待页面加载完成"""
        try:
            WebDriverWait(self.driver, timeout).until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )
            time.sleep(2)  # 额外等待动态内容
        except TimeoutException:
            self.log_message("页面加载超时，继续执行...")
    
    def scroll_and_load_all_content(self):
        """滚动页面并加载所有动态内容"""
        self.log_message("开始加载所有照片内容...")
        
        last_height = 0
        scroll_attempts = 0
        max_attempts = 200  # 增加最大尝试次数以处理1万多张照片
        no_new_content_count = 0
        
        while scroll_attempts < max_attempts:
            # 记录当前页面高度
            current_height = self.driver.execute_script("return document.body.scrollHeight")
            
            # 获取当前页面中的图片数量
            try:
                img_count = len(self.driver.find_elements(By.TAG_NAME, "img"))
                self.log_message(f"滚动 {scroll_attempts + 1}/{max_attempts}, 当前图片数量: {img_count}")
            except:
                img_count = 0
            
            # 滚动到页面底部
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            
            # 等待内容加载
            time.sleep(3)
            
            # 尝试点击"加载更多"或类似的按钮
            load_more_buttons = [
                "//button[contains(text(), '加载更多')]",
                "//button[contains(text(), '更多')]",
                "//div[contains(text(), '加载更多')]",
                "//span[contains(text(), '加载更多')]",
                "//a[contains(text(), '更多')]",
                "//*[contains(@class, 'load-more')]",
                "//*[contains(@class, 'more')]",
                "//*[contains(@onclick, 'more')]"
            ]
            
            for button_xpath in load_more_buttons:
                try:
                    buttons = self.driver.find_elements(By.XPATH, button_xpath)
                    for button in buttons:
                        if button.is_displayed() and button.is_enabled():
                            try:
                                self.driver.execute_script("arguments[0].click();", button)
                                self.log_message("点击了加载更多按钮")
                                time.sleep(3)
                                break
                            except:
                                pass
                except:
                    pass
            
            # 检查是否有新内容加载
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            
            if new_height == current_height and new_height == last_height:
                no_new_content_count += 1
                if no_new_content_count >= 5:  # 连续5次没有新内容
                    self.log_message("连续多次无新内容，可能已加载完成")
                    break
            else:
                no_new_content_count = 0
                last_height = new_height
            
            scroll_attempts += 1
            
            # 每50次滚动保存一次进度
            if scroll_attempts % 50 == 0:
                self.save_progress()
        
        # 最后滚动到顶部
        self.driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(3)
        
        # 获取最终的图片数量
        final_img_count = len(self.driver.find_elements(By.TAG_NAME, "img"))
        self.log_message(f"页面加载完成，共找到 {final_img_count} 个图片元素")
    
    def find_original_image_url(self, img_element):
        """查找原图URL"""
        original_urls = []
        
        try:
            # 方法1：检查各种可能的原图属性
            attrs_to_check = [
                'data-original', 'data-src', 'data-large', 'data-big', 
                'data-full', 'data-origin', 'data-raw', 'src', 'data-url'
            ]
            
            for attr in attrs_to_check:
                url = img_element.get_attribute(attr)
                if url and self.is_valid_image_url(url):
                    original_urls.append(url)
            
            # 方法2：检查父元素的链接
            try:
                parent = img_element.find_element(By.XPATH, "./..")
                if parent.tag_name.lower() == 'a':
                    href = parent.get_attribute('href')
                    if href and self.is_valid_image_url(href):
                        original_urls.append(href)
            except:
                pass
            
            # 方法3：模拟点击获取原图（谨慎使用）
            try:
                # 记录当前窗口句柄
                current_window = self.driver.current_window_handle
                
                # 尝试点击图片
                ActionChains(self.driver).move_to_element(img_element).click().perform()
                time.sleep(2)
                
                # 检查是否有新窗口或弹窗
                all_windows = self.driver.window_handles
                if len(all_windows) > 1:
                    # 切换到新窗口
                    for window in all_windows:
                        if window != current_window:
                            self.driver.switch_to.window(window)
                            
                            # 查找原图链接
                            try:
                                # 查找"查看原图"按钮或链接
                                original_buttons = [
                                    "//button[contains(text(), '查看原图')]",
                                    "//a[contains(text(), '查看原图')]",
                                    "//button[contains(text(), '原图')]",
                                    "//a[contains(text(), '原图')]",
                                    "//*[contains(@class, 'original')]",
                                    "//*[contains(@data-action, 'original')]"
                                ]
                                
                                for button_xpath in original_buttons:
                                    try:
                                        button = self.driver.find_element(By.XPATH, button_xpath)
                                        if button.is_displayed():
                                            href = button.get_attribute('href')
                                            if href and self.is_valid_image_url(href):
                                                original_urls.append(href)
                                    except:
                                        pass
                                
                                # 查找当前页面的高分辨率图片
                                high_res_imgs = self.driver.find_elements(By.TAG_NAME, "img")
                                for hr_img in high_res_imgs:
                                    hr_src = hr_img.get_attribute('src')
                                    if hr_src and self.is_valid_image_url(hr_src):
                                        # 检查图片尺寸或文件大小相关参数
                                        if any(param in hr_src.lower() for param in ['large', 'big', 'full', 'original', 'raw']):
                                            original_urls.append(hr_src)
                            except:
                                pass
                            
                            # 关闭新窗口
                            self.driver.close()
                            break
                    
                    # 切换回原窗口
                    self.driver.switch_to.window(current_window)
                
            except Exception as e:
                # 如果点击失败，继续处理其他图片
                pass
            
        except Exception as e:
            self.log_message(f"查找原图URL时出错：{e}")
        
        return original_urls
    
    def enhance_image_url_quality(self, url):
        """尝试将URL转换为高质量版本"""
        if not url:
            return url
        
        # 移除尺寸限制参数
        quality_patterns = [
            (r'[?&]w=\d+', ''),
            (r'[?&]h=\d+', ''),
            (r'[?&]q=\d+', ''),
            (r'[?&]quality=\d+', ''),
            (r'[?&]size=\w+', ''),
            (r'_thumb\.|_small\.|_medium\.', '.'),
            (r'@\d+w\.|@\d+h\.', '.'),
            (r'/thumb/', '/'),
            (r'/small/', '/'),
            (r'/medium/', '/'),
        ]
        
        enhanced_url = url
        for pattern, replacement in quality_patterns:
            enhanced_url = re.sub(pattern, replacement, enhanced_url)
        
        # 尝试添加高质量参数
        quality_suffixes = ['?quality=100', '?w=2000', '?original=true']
        
        # 测试哪个URL返回最大的文件
        best_url = enhanced_url
        max_size = 0
        
        for suffix in [''] + quality_suffixes:
            test_url = enhanced_url + suffix
            try:
                response = self.session.head(test_url, timeout=10)
                if response.status_code == 200:
                    content_length = int(response.headers.get('content-length', 0))
                    if content_length > max_size:
                        max_size = content_length
                        best_url = test_url
            except:
                continue
        
        return best_url
    
    def extract_all_photo_urls(self):
        """提取所有照片URL"""
        self.log_message("开始提取照片链接...")
        
        photo_urls = []
        processed_elements = set()
        
        # 获取所有图片元素
        img_elements = self.driver.find_elements(By.TAG_NAME, "img")
        self.log_message(f"找到 {len(img_elements)} 个图片元素")
        
        for i, img_element in enumerate(img_elements, 1):
            try:
                # 避免重复处理同一个元素
                element_id = img_element.get_attribute('outerHTML')[:100]
                if element_id in processed_elements:
                    continue
                processed_elements.add(element_id)
                
                if i % 100 == 0:
                    self.log_message(f"正在处理第 {i}/{len(img_elements)} 个图片元素")
                
                # 获取原图URL
                original_urls = self.find_original_image_url(img_element)
                
                # 如果没找到原图，使用当前src
                if not original_urls:
                    src = img_element.get_attribute('src')
                    if src and self.is_valid_image_url(src):
                        original_urls = [src]
                
                # 处理找到的URL
                for url in original_urls:
                    if self.is_competition_photo(url):
                        enhanced_url = self.enhance_image_url_quality(url)
                        photo_urls.append(enhanced_url)
                
            except Exception as e:
                self.log_message(f"处理第 {i} 个图片元素时出错：{e}")
                continue
        
        # 去重
        unique_urls = list(set(photo_urls))
        self.log_message(f"去重后共找到 {len(unique_urls)} 个有效照片链接")
        
        return unique_urls
    
    def is_valid_image_url(self, url):
        """检查是否为有效的图片URL"""
        if not url or len(url) < 10:
            return False
        
        url_lower = url.lower()
        
        # 检查图片扩展名
        has_image_ext = any(ext in url_lower for ext in ['.jpg', '.jpeg', '.png', '.webp', '.gif'])
        
        # 检查图片相关关键词
        has_image_pattern = any(pattern in url_lower for pattern in ['image', 'photo', 'img', 'pic', 'upload'])
        
        # 检查是否为http链接
        is_http = url.startswith(('http://', 'https://', '//'))
        
        return (has_image_ext or has_image_pattern) and is_http
    
    def is_competition_photo(self, url):
        """判断是否为比赛照片"""
        exclude_keywords = [
            'logo', 'icon', 'avatar', 'profile', 'header', 'footer',
            'banner', 'ad', 'advertisement', 'sponsor', 'button'
        ]
        
        url_lower = url.lower()
        return not any(keyword in url_lower for keyword in exclude_keywords)
    
    def extract_date_from_url(self, url):
        """从URL中提取日期"""
        date_patterns = [
            r'(\d{4})[/-](\d{1,2})[/-](\d{1,2})',
            r'(\d{4})(\d{2})(\d{2})',
            r'(\d{2})[/-](\d{2})[/-](\d{4})',
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, url)
            if match:
                try:
                    groups = match.groups()
                    if len(groups[0]) == 4:
                        year, month, day = groups
                    else:
                        month, day, year = groups
                    
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
            # 检查是否已下载过这个URL
            if url in self.downloaded_files:
                return False
            
            response = self.session.get(url, timeout=30, stream=True)
            response.raise_for_status()
            
            content = response.content
            
            # 检查文件大小
            if len(content) < 5120:  # 小于5KB，可能是占位符
                return False
            
            # 检查是否为重复内容
            file_hash = self.get_file_hash(content)
            if file_hash in self.downloaded_hashes:
                return False
            
            # 确定文件名
            parsed_url = urlparse(url)
            filename = os.path.basename(parsed_url.path)
            
            if not filename or '.' not in filename:
                content_type = response.headers.get('content-type', '')
                if 'jpeg' in content_type or 'jpg' in content_type:
                    filename = f"photo_{int(time.time() * 1000)}.jpg"
                elif 'png' in content_type:
                    filename = f"photo_{int(time.time() * 1000)}.png"
                elif 'webp' in content_type:
                    filename = f"photo_{int(time.time() * 1000)}.webp"
                else:
                    filename = f"photo_{int(time.time() * 1000)}.jpg"
            
            # 清理文件名
            filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
            
            # 创建完整路径
            filepath = os.path.join(date_folder, filename)
            
            # 处理文件名冲突
            base_name, ext = os.path.splitext(filename)
            counter = 1
            while os.path.exists(filepath):
                new_filename = f"{base_name}_{counter}{ext}"
                filepath = os.path.join(date_folder, new_filename)
                counter += 1
            
            # 保存文件
            with open(filepath, 'wb') as f:
                f.write(content)
            
            # 记录下载信息
            self.downloaded_files.add(url)
            self.downloaded_hashes.add(file_hash)
            
            file_size = len(content) / 1024  # KB
            self.log_message(f"已下载: {filename} ({file_size:.1f} KB)")
            
            return True
            
        except Exception as e:
            self.log_message(f"下载失败: {url} - {str(e)}")
            return False
    
    def download_all_photos(self):
        """下载所有照片的主函数"""
        self.log_message("开始增强版照片下载器...")
        
        # 设置浏览器
        self.driver = self.setup_driver()
        if not self.driver:
            return
        
        try:
            # 打开目标网页
            self.log_message(f"正在访问: {self.base_url}")
            self.driver.get(self.base_url)
            
            # 等待5秒让页面充分加载
            self.log_message("等待页面加载（5秒）...")
            time.sleep(5)
            
            # 等待用户登录
            self.wait_for_login()
            
            if not self.login_completed:
                self.log_message("未完成登录，退出程序")
                return
            
            # 滚动并加载所有内容
            self.scroll_and_load_all_content()
            
            # 提取所有照片URL
            photo_urls = self.extract_all_photo_urls()
            
            if not photo_urls:
                self.log_message("未找到任何照片链接")
                return
            
            self.log_message(f"准备下载 {len(photo_urls)} 张照片")
            
            # 按日期分组
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
            
            # 处理未识别日期的照片
            if unknown_date_photos:
                current_date = datetime.now().strftime('%Y-%m-%d')
                date_groups[f"{current_date}_unknown"] = unknown_date_photos
            
            # 开始下载
            total_downloaded = 0
            total_photos = len(photo_urls)
            
            for date_str, urls in date_groups.items():
                self.log_message(f"\n开始下载 {date_str} 的照片 ({len(urls)} 张)")
                
                # 创建日期文件夹
                date_folder = os.path.join(self.download_dir, date_str)
                if not os.path.exists(date_folder):
                    os.makedirs(date_folder)
                
                downloaded_count = 0
                for i, url in enumerate(urls, 1):
                    if i % 10 == 0 or i == len(urls):
                        self.log_message(f"处理进度: {i}/{len(urls)} (总进度: {total_downloaded}/{total_photos})")
                    
                    if self.download_photo(url, date_folder):
                        downloaded_count += 1
                        total_downloaded += 1
                    
                    # 每100张照片保存一次进度
                    if total_downloaded % 100 == 0:
                        self.save_progress()
                    
                    # 控制下载速度
                    time.sleep(0.5)
                
                self.log_message(f"{date_str} 完成: {downloaded_count}/{len(urls)} 张")
            
            # 保存最终进度
            self.save_progress()
            
            self.log_message(f"\n全部下载完成！")
            self.log_message(f"总共下载: {total_downloaded}/{total_photos} 张照片")
            self.log_message(f"保存位置: {os.path.abspath(self.download_dir)}")
            
        finally:
            if self.driver:
                input("按回车键关闭浏览器...")
                self.driver.quit()

def main():
    url = "https://tlwtpbvzb.vzan.com/v3/course/alive/1827403580?v=1755091438866"
    downloader = EnhancedDivingPhotosDownloader(url)
    downloader.download_all_photos()

if __name__ == "__main__":
    main()