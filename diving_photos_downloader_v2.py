#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
跳水锦标赛照片下载器 V2 - 针对弹窗和保存流程优化
Optimized for popup workflow and save button interaction
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
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException
import hashlib

class DivingPhotosDownloaderV2:
    def __init__(self, base_url, download_dir="diving_championship_photos_v2"):
        self.base_url = base_url
        self.download_dir = download_dir
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        self.downloaded_hashes = set()
        self.downloaded_files = set()
        self.processed_images = set()
        self.driver = None
        self.login_completed = False
        
        # 创建主下载目录
        if not os.path.exists(self.download_dir):
            os.makedirs(self.download_dir)
        
        # 创建日志文件
        self.log_file = os.path.join(self.download_dir, "download_log_v2.txt")
        self.progress_file = os.path.join(self.download_dir, "progress_v2.json")
        
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
            'processed_images': list(self.processed_images),
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
                self.processed_images = set(progress.get('processed_images', []))
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
        
        # 下载设置
        prefs = {
            "download.default_directory": os.path.abspath(self.download_dir),
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True
        }
        chrome_options.add_experimental_option("prefs", prefs)
        
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
        
        self.log_message("登录确认完成，开始分析页面...")
        time.sleep(3)
    
    def scroll_and_load_all_content(self):
        """滚动页面并加载所有动态内容"""
        self.log_message("开始加载所有照片内容...")
        
        last_height = 0
        scroll_attempts = 0
        max_attempts = 300  # 增加滚动次数以确保加载完整
        no_new_content_count = 0
        
        while scroll_attempts < max_attempts:
            current_height = self.driver.execute_script("return document.body.scrollHeight")
            
            # 获取当前页面中的图片数量
            img_count = len(self.driver.find_elements(By.TAG_NAME, "img"))
            if scroll_attempts % 10 == 0:
                self.log_message(f"滚动 {scroll_attempts + 1}/{max_attempts}, 当前图片数量: {img_count}")
            
            # 缓慢滚动
            self.driver.execute_script("window.scrollBy(0, 800);")
            time.sleep(2)
            
            # 尝试点击"加载更多"按钮
            if scroll_attempts % 5 == 0:  # 每5次滚动尝试一次
                self.click_load_more_buttons()
            
            # 检查是否有新内容加载
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            
            if new_height == current_height and new_height == last_height:
                no_new_content_count += 1
                if no_new_content_count >= 8:  # 连续8次没有新内容
                    self.log_message("连续多次无新内容，可能已加载完成")
                    break
            else:
                no_new_content_count = 0
                last_height = new_height
            
            scroll_attempts += 1
            
            # 每50次滚动保存一次进度
            if scroll_attempts % 50 == 0:
                self.save_progress()
        
        # 滚动到顶部
        self.driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(3)
        
        final_img_count = len(self.driver.find_elements(By.TAG_NAME, "img"))
        self.log_message(f"页面加载完成，共找到 {final_img_count} 个图片元素")
    
    def click_load_more_buttons(self):
        """点击加载更多按钮"""
        load_more_selectors = [
            "//button[contains(text(), '加载更多')]",
            "//button[contains(text(), '更多')]",
            "//div[contains(text(), '加载更多')]",
            "//span[contains(text(), '加载更多')]",
            "//a[contains(text(), '更多')]",
            "//*[contains(@class, 'load-more')]",
            "//*[contains(@class, 'more')]"
        ]
        
        for selector in load_more_selectors:
            try:
                buttons = self.driver.find_elements(By.XPATH, selector)
                for button in buttons:
                    if button.is_displayed() and button.is_enabled():
                        try:
                            self.driver.execute_script("arguments[0].click();", button)
                            self.log_message("点击了加载更多按钮")
                            time.sleep(3)
                            return True
                        except:
                            pass
            except:
                pass
        return False
    
    def find_all_images(self):
        """查找页面中的所有图片"""
        selectors = [
            "img",
            "[style*='background-image']",
            ".photo img",
            ".image img", 
            ".pic img",
            "[data-src]",
            "[data-original]",
            "picture img"
        ]
        
        all_images = []
        for selector in selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                all_images.extend(elements)
            except:
                pass
        
        # 去重
        unique_images = []
        seen_sources = set()
        
        for img in all_images:
            try:
                src = img.get_attribute('src') or img.get_attribute('data-src') or img.get_attribute('data-original')
                if src and src not in seen_sources and self.is_valid_image(src):
                    seen_sources.add(src)
                    unique_images.append(img)
            except:
                pass
        
        self.log_message(f"找到 {len(unique_images)} 个有效图片元素")
        return unique_images
    
    def is_valid_image(self, src):
        """检查是否为有效的比赛图片"""
        if not src or len(src) < 10:
            return False
        
        # 排除明显的非比赛照片
        exclude_keywords = [
            'logo', 'icon', 'avatar', 'profile', 'header', 'footer',
            'banner', 'ad', 'advertisement', 'sponsor', 'button', 'bg'
        ]
        
        src_lower = src.lower()
        return not any(keyword in src_lower for keyword in exclude_keywords)
    
    def process_single_image(self, img_element, index, total):
        """处理单张图片的完整流程"""
        try:
            # 获取图片标识符
            src = img_element.get_attribute('src') or img_element.get_attribute('data-src')
            img_id = f"{src}_{index}" if src else f"img_{index}"
            
            # 检查是否已处理过
            if img_id in self.processed_images:
                self.log_message(f"跳过已处理的图片 {index}/{total}")
                return False
            
            self.log_message(f"处理图片 {index}/{total}: {src[:100] if src else 'unknown'}")
            
            # 滚动到图片位置
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", img_element)
            time.sleep(1)
            
            # 点击图片打开弹窗
            success = self.click_image_and_wait_popup(img_element)
            if not success:
                self.log_message(f"图片 {index} 点击失败或无弹窗")
                self.processed_images.add(img_id)
                return False
            
            # 查找并点击"查看原图"按钮
            original_clicked = self.click_original_image_button()
            if not original_clicked:
                self.log_message(f"图片 {index} 未找到查看原图按钮")
                self.close_popup()
                self.processed_images.add(img_id)
                return False
            
            # 查找并点击"保存到本地"按钮或下载链接
            download_success = self.handle_save_to_local()
            
            # 关闭弹窗
            self.close_popup()
            
            # 记录处理状态
            self.processed_images.add(img_id)
            
            if download_success:
                self.log_message(f"图片 {index} 处理成功")
            else:
                self.log_message(f"图片 {index} 下载失败")
            
            return download_success
            
        except Exception as e:
            self.log_message(f"处理图片 {index} 时出错: {e}")
            self.close_popup()  # 确保关闭可能的弹窗
            return False
    
    def click_image_and_wait_popup(self, img_element):
        """点击图片并等待弹窗出现"""
        try:
            # 尝试多种点击方式
            try:
                ActionChains(self.driver).move_to_element(img_element).click().perform()
            except ElementClickInterceptedException:
                self.driver.execute_script("arguments[0].click();", img_element)
            
            # 等待弹窗出现
            time.sleep(3)
            
            # 检查是否有弹窗
            popup_selectors = [
                ".modal", ".popup", ".overlay", ".dialog", ".lightbox",
                "[style*='position: fixed']", ".photo-viewer", ".image-viewer"
            ]
            
            for selector in popup_selectors:
                try:
                    popup = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if popup.is_displayed():
                        return True
                except:
                    pass
            
            return False
            
        except Exception as e:
            self.log_message(f"点击图片失败: {e}")
            return False
    
    def click_original_image_button(self):
        """查找并点击查看原图按钮"""
        original_button_selectors = [
            "//button[contains(text(), '查看原图')]",
            "//a[contains(text(), '查看原图')]",
            "//div[contains(text(), '查看原图')]",
            "//span[contains(text(), '查看原图')]",
            "//button[contains(text(), '原图')]",
            "//a[contains(text(), '原图')]",
            "//*[contains(@class, 'original')]",
            "//*[contains(@class, 'full')]",
            "//*[contains(@class, 'hd')]",
            "//*[@title='查看原图']"
        ]
        
        for selector in original_button_selectors:
            try:
                buttons = self.driver.find_elements(By.XPATH, selector)
                for button in buttons:
                    if button.is_displayed():
                        try:
                            # 滚动到按钮位置
                            self.driver.execute_script("arguments[0].scrollIntoView();", button)
                            time.sleep(0.5)
                            
                            # 点击按钮
                            button.click()
                            time.sleep(2)
                            
                            self.log_message("成功点击查看原图按钮")
                            return True
                        except Exception as e:
                            self.log_message(f"点击查看原图按钮失败: {e}")
                            continue
            except:
                pass
        
        self.log_message("未找到查看原图按钮")
        return False
    
    def handle_save_to_local(self):
        """处理保存到本地功能"""
        save_button_selectors = [
            "//button[contains(text(), '保存')]",
            "//a[contains(text(), '保存')]",
            "//button[contains(text(), '下载')]",
            "//a[contains(text(), '下载')]",
            "//button[contains(text(), '保存到本地')]",
            "//a[contains(text(), '保存到本地')]",
            "//*[contains(@class, 'save')]",
            "//*[contains(@class, 'download')]",
            "//*[@title='保存']",
            "//*[@title='下载']"
        ]
        
        # 查找保存按钮
        for selector in save_button_selectors:
            try:
                buttons = self.driver.find_elements(By.XPATH, selector)
                for button in buttons:
                    if button.is_displayed():
                        try:
                            # 检查是否有直接的下载链接
                            href = button.get_attribute('href')
                            if href and self.is_download_link(href):
                                return self.download_from_url(href)
                            
                            # 点击保存按钮
                            self.driver.execute_script("arguments[0].scrollIntoView();", button)
                            time.sleep(0.5)
                            button.click()
                            time.sleep(2)
                            
                            self.log_message("点击了保存按钮")
                            
                            # 等待下载开始
                            time.sleep(3)
                            return True
                            
                        except Exception as e:
                            self.log_message(f"点击保存按钮失败: {e}")
                            continue
            except:
                pass
        
        # 如果没有找到保存按钮，尝试右键保存
        return self.try_right_click_save()
    
    def is_download_link(self, url):
        """检查是否为下载链接"""
        if not url:
            return False
        return url.lower().endswith(('.jpg', '.jpeg', '.png', '.webp', '.gif')) or 'download' in url.lower()
    
    def download_from_url(self, url):
        """从URL直接下载图片"""
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            content = response.content
            if len(content) < 5120:  # 小于5KB
                return False
            
            # 检查重复
            file_hash = hashlib.md5(content).hexdigest()
            if file_hash in self.downloaded_hashes:
                return False
            
            # 保存文件
            filename = self.generate_filename(url, content)
            filepath = os.path.join(self.download_dir, filename)
            
            with open(filepath, 'wb') as f:
                f.write(content)
            
            self.downloaded_files.add(url)
            self.downloaded_hashes.add(file_hash)
            
            file_size = len(content) / 1024
            self.log_message(f"直接下载成功: {filename} ({file_size:.1f} KB)")
            return True
            
        except Exception as e:
            self.log_message(f"直接下载失败: {e}")
            return False
    
    def try_right_click_save(self):
        """尝试右键保存图片"""
        try:
            # 查找当前显示的原图
            large_images = self.driver.find_elements(By.CSS_SELECTOR, "img[src*='large'], img[src*='original'], img[src*='full']")
            if not large_images:
                large_images = self.driver.find_elements(By.TAG_NAME, "img")
            
            for img in large_images:
                if img.is_displayed():
                    try:
                        src = img.get_attribute('src')
                        if src and self.is_valid_image(src):
                            return self.download_from_url(src)
                    except:
                        continue
            
            return False
            
        except Exception as e:
            self.log_message(f"右键保存失败: {e}")
            return False
    
    def generate_filename(self, url, content):
        """生成文件名"""
        # 从URL提取文件名
        parsed_url = urlparse(url)
        filename = os.path.basename(parsed_url.path)
        
        if not filename or '.' not in filename:
            # 根据内容类型生成文件名
            timestamp = int(time.time() * 1000)
            filename = f"diving_photo_{timestamp}.jpg"
        
        # 清理文件名
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        
        # 处理重复文件名
        base_name, ext = os.path.splitext(filename)
        counter = 1
        original_filename = filename
        
        while os.path.exists(os.path.join(self.download_dir, filename)):
            filename = f"{base_name}_{counter}{ext}"
            counter += 1
        
        return filename
    
    def close_popup(self):
        """关闭弹窗"""
        close_methods = [
            # ESC键
            lambda: self.driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE),
            
            # 关闭按钮
            lambda: self.click_close_button(),
            
            # 点击背景
            lambda: self.click_background()
        ]
        
        for method in close_methods:
            try:
                method()
                time.sleep(1)
                return True
            except:
                pass
        
        return False
    
    def click_close_button(self):
        """点击关闭按钮"""
        close_selectors = [
            "//button[contains(@class, 'close')]",
            "//span[contains(@class, 'close')]",
            "//*[contains(text(), '×')]",
            "//*[contains(text(), '关闭')]",
            "//*[@title='关闭']"
        ]
        
        for selector in close_selectors:
            try:
                buttons = self.driver.find_elements(By.XPATH, selector)
                for button in buttons:
                    if button.is_displayed():
                        button.click()
                        return True
            except:
                pass
        return False
    
    def click_background(self):
        """点击背景关闭弹窗"""
        try:
            # 点击页面左上角（通常是背景区域）
            ActionChains(self.driver).move_by_offset(100, 100).click().perform()
            return True
        except:
            return False
    
    def download_all_photos(self):
        """下载所有照片的主函数"""
        self.log_message("开始V2版照片下载器...")
        
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
            self.scroll_and_load_all_content()
            
            # 查找所有图片
            images = self.find_all_images()
            
            if not images:
                self.log_message("未找到任何图片链接")
                return
            
            self.log_message(f"准备处理 {len(images)} 张照片")
            
            # 处理每张图片
            total_processed = 0
            total_downloaded = 0
            
            for i, img_element in enumerate(images, 1):
                success = self.process_single_image(img_element, i, len(images))
                total_processed += 1
                if success:
                    total_downloaded += 1
                
                # 每处理10张照片保存一次进度
                if total_processed % 10 == 0:
                    self.save_progress()
                    self.log_message(f"已处理: {total_processed}/{len(images)}, 成功下载: {total_downloaded}")
                
                # 短暂延迟避免操作过快
                time.sleep(1)
            
            # 保存最终进度
            self.save_progress()
            
            self.log_message(f"\n全部处理完成！")
            self.log_message(f"总共处理: {total_processed}/{len(images)} 张照片")
            self.log_message(f"成功下载: {total_downloaded} 张照片")
            self.log_message(f"保存位置: {os.path.abspath(self.download_dir)}")
            
        finally:
            input("按回车键关闭浏览器...")
            if self.driver:
                self.driver.quit()

def main():
    url = "https://tlwtpbvzb.vzan.com/v3/course/alive/1827403580?v=1755091438866"
    downloader = DivingPhotosDownloaderV2(url)
    downloader.download_all_photos()

if __name__ == "__main__":
    main()