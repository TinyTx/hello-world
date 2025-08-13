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
        """设置Chrome浏览器驱动 - 兼容性修复版"""
        chrome_options = Options()
        
        # 基本设置
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # 性能优化设置
        chrome_options.add_argument('--disable-background-timer-throttling')
        chrome_options.add_argument('--disable-backgrounding-occluded-windows')
        chrome_options.add_argument('--disable-renderer-backgrounding')
        chrome_options.add_argument('--disable-features=TranslateUI')
        chrome_options.add_argument('--disable-ipc-flooding-protection')
        
        # 内存管理
        chrome_options.add_argument('--max_old_space_size=4096')
        chrome_options.add_argument('--memory-pressure-off')
        
        # 网络相关设置
        chrome_options.add_argument('--aggressive-cache-discard')
        chrome_options.add_argument('--disable-background-networking')
        
        # 设置用户代理
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        # 图片加载策略
        prefs = {
            "profile.default_content_setting_values": {
                "images": 1,  # 允许加载图片
                "plugins": 1,
                "popups": 0,
                "geolocation": 0,
                "notifications": 0,
                "media_stream": 0,
            },
            "profile.managed_default_content_settings": {
                "images": 1
            }
        }
        chrome_options.add_experimental_option("prefs", prefs)
        
        # 如果需要无头模式，取消下面的注释
        # chrome_options.add_argument('--headless')
        
        try:
            driver = webdriver.Chrome(options=chrome_options)
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            # 设置页面加载超时
            driver.set_page_load_timeout(60)
            driver.implicitly_wait(10)
            
            # 最大化窗口
            driver.maximize_window()
            
            self.log_message("Chrome浏览器启动成功")
            return driver
            
        except Exception as e:
            self.log_message(f"错误：无法启动Chrome浏览器。{e}")
            self.log_message("尝试使用简化配置重新启动...")
            
            # 尝试使用最简配置
            try:
                simple_options = Options()
                simple_options.add_argument('--no-sandbox')
                simple_options.add_argument('--disable-dev-shm-usage')
                simple_options.add_argument('--disable-gpu')
                simple_options.add_argument('--window-size=1920,1080')
                
                driver = webdriver.Chrome(options=simple_options)
                driver.maximize_window()
                self.log_message("使用简化配置启动Chrome浏览器成功")
                return driver
                
            except Exception as e2:
                self.log_message(f"简化配置也失败：{e2}")
                return None
    
    def wait_for_login(self):
        """等待用户手动登录 - 修复版"""
        self.log_message("请在浏览器中完成登录...")
        self.log_message("=" * 50)
        self.log_message("📋 登录步骤：")
        self.log_message("1. 在打开的浏览器窗口中完成登录")
        self.log_message("2. 确保能看到需要登录才能查看的内容")
        self.log_message("3. 登录完成后回到此控制台")
        self.log_message("=" * 50)
        
        max_attempts = 10
        attempt = 0
        
        while attempt < max_attempts:
            try:
                self.log_message(f"\n🔐 等待登录确认 (第 {attempt + 1}/{max_attempts} 次)")
                self.log_message("请输入 'y' 确认已完成登录，输入 'n' 继续等待：")
                
                # 使用更简单的输入方式
                import sys
                sys.stdout.write(">>> ")
                sys.stdout.flush()
                
                confirmation = input().strip().lower()
                
                if confirmation == 'y' or confirmation == 'yes':
                    self.log_message("✅ 用户确认登录完成")
                    self.login_completed = True
                    break
                elif confirmation == 'n' or confirmation == 'no':
                    self.log_message("⏳ 继续等待登录，请完成登录后重试...")
                    time.sleep(3)
                    attempt += 1
                elif confirmation == 'q' or confirmation == 'quit':
                    self.log_message("❌ 用户取消登录")
                    return False
                else:
                    self.log_message("⚠️  请输入 'y'(确认登录) 或 'n'(继续等待) 或 'q'(退出)")
                    
            except KeyboardInterrupt:
                self.log_message("\n❌ 用户中断程序")
                return False
            except Exception as e:
                self.log_message(f"❌ 输入处理出错：{e}")
                time.sleep(2)
                attempt += 1
        
        if not self.login_completed:
            self.log_message("❌ 登录确认超时，程序退出")
            return False
        
        self.log_message("🎉 登录确认完成，开始分析页面...")
        time.sleep(3)  # 等待页面稳定
        return True
    
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
        """滚动页面并加载所有动态内容 - 图片区域滚动版"""
        self.log_message("开始加载所有照片内容...")
        self.log_message("🔄 注意：此网站需要滚动图片区域才能加载更多图片")
        
        # 首先找到图片容器区域
        photo_container = self.find_photo_container()
        if not photo_container:
            self.log_message("❌ 未找到图片容器，尝试滚动整个页面")
            return self.scroll_and_load_all_content_fallback()
        
        self.log_message("✅ 找到图片容器，开始滚动加载")
        
        last_height = 0
        last_img_count = 0
        scroll_attempts = 0
        max_attempts = 300  # 增加最大尝试次数
        no_new_content_count = 0
        stable_count_threshold = 8  # 增加稳定计数阈值
        
        # 启用网络监控
        self.enable_network_monitoring()
        
        while scroll_attempts < max_attempts:
            # 记录当前状态
            current_height = self.get_container_scroll_height(photo_container)
            current_img_count = len(self.driver.find_elements(By.TAG_NAME, "img"))
            current_scroll_position = self.get_container_scroll_position(photo_container)
            
            self.log_message(f"滚动 {scroll_attempts + 1}/{max_attempts}, 容器高度: {current_height}, 图片数量: {current_img_count}, 滚动位置: {current_scroll_position}")
            
            # 滚动图片容器区域
            self.scroll_photo_container(photo_container, scroll_attempts)
            
            # 尝试点击加载更多按钮
            load_more_clicked = self.click_all_load_more_buttons()
            if load_more_clicked:
                self.log_message("发现并点击了加载更多按钮，等待内容加载...")
                time.sleep(5)  # 给更多时间加载新内容
            
            # 等待内容加载
            self.wait_for_dynamic_content()
            
            # 检查是否有新内容
            new_height = self.get_container_scroll_height(photo_container)
            new_img_count = len(self.driver.find_elements(By.TAG_NAME, "img"))
            new_scroll_position = self.get_container_scroll_position(photo_container)
            
            # 多维度检测是否有新内容
            has_new_content = (
                new_height > current_height or 
                new_img_count > current_img_count or
                self.has_pending_network_requests() or
                load_more_clicked
            )
            
            # 检查是否已经滚动到容器底部
            if self.is_container_at_bottom(photo_container):
                self.log_message("🔝 已滚动到图片容器底部")
                # 到达底部后，再次尝试触发加载
                if self.force_trigger_all_loads():
                    self.log_message("在容器底部触发了额外加载")
                    time.sleep(5)
                else:
                    no_new_content_count += 2  # 到达底部时增加计数
            
            if not has_new_content and new_height == last_height and new_img_count == last_img_count:
                no_new_content_count += 1
                self.log_message(f"无新内容计数: {no_new_content_count}/{stable_count_threshold}")
                
                if no_new_content_count >= stable_count_threshold:
                    self.log_message("连续多次无新内容，尝试最后的加载策略...")
                    # 最后的尝试：强制触发所有可能的加载事件
                    if self.force_trigger_all_loads():
                        self.log_message("强制触发加载成功，继续检测...")
                        no_new_content_count = 0  # 重置计数
                        time.sleep(5)
                    else:
                        self.log_message("已尝试所有加载策略，认为内容加载完成")
                        break
            else:
                no_new_content_count = 0
                last_height = new_height
                last_img_count = new_img_count
            
            scroll_attempts += 1
            
            # 每50次滚动保存一次进度
            if scroll_attempts % 50 == 0:
                self.save_progress()
                # 执行垃圾回收，防止内存泄漏
                self.driver.execute_script("window.gc && window.gc();")
        
        # 最终处理 - 确保完全加载
        self.perform_final_container_check(photo_container)
        
        # 获取最终统计
        final_img_count = len(self.driver.find_elements(By.TAG_NAME, "img"))
        self.log_message(f"页面加载完成，共找到 {final_img_count} 个图片元素")
        
        # 禁用网络监控
        self.disable_network_monitoring()
    
    def find_photo_container(self):
        """找到图片容器区域"""
        # 常见的图片容器选择器
        container_selectors = [
            # 微赞平台特定
            ".vzan-photo-container",
            ".vzan-gallery",
            ".photo-gallery",
            ".image-gallery",
            # 通用选择器
            "[class*='photo']",
            "[class*='image']", 
            "[class*='gallery']",
            "[class*='grid']",
            "[class*='list']",
            "[id*='photo']",
            "[id*='image']",
            "[id*='gallery']",
            # 可滚动的容器
            "[style*='overflow']",
            "[style*='scroll']"
        ]
        
        for selector in container_selectors:
            try:
                containers = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for container in containers:
                    # 检查容器是否包含图片
                    imgs_in_container = container.find_elements(By.TAG_NAME, "img")
                    if len(imgs_in_container) >= 5:  # 至少包含5张图片才认为是图片容器
                        self.log_message(f"找到图片容器: {selector}, 包含 {len(imgs_in_container)} 张图片")
                        return container
            except:
                continue
        
        # 如果没找到特定容器，尝试找到包含最多图片的元素
        try:
            all_elements = self.driver.find_elements(By.CSS_SELECTOR, "div")
            best_container = None
            max_img_count = 0
            
            for element in all_elements:
                try:
                    imgs = element.find_elements(By.TAG_NAME, "img")
                    if len(imgs) > max_img_count:
                        max_img_count = len(imgs)
                        best_container = element
                except:
                    continue
            
            if best_container and max_img_count >= 10:
                self.log_message(f"找到最佳图片容器，包含 {max_img_count} 张图片")
                return best_container
        except:
            pass
        
        return None
    
    def get_container_scroll_height(self, container):
        """获取容器的滚动高度"""
        try:
            return self.driver.execute_script("return arguments[0].scrollHeight", container)
        except:
            return self.driver.execute_script("return document.body.scrollHeight")
    
    def get_container_scroll_position(self, container):
        """获取容器的滚动位置"""
        try:
            return self.driver.execute_script("return arguments[0].scrollTop", container)
        except:
            return self.driver.execute_script("return window.pageYOffset")
    
    def is_container_at_bottom(self, container):
        """检查容器是否滚动到底部"""
        try:
            scroll_top = self.driver.execute_script("return arguments[0].scrollTop", container)
            scroll_height = self.driver.execute_script("return arguments[0].scrollHeight", container)
            client_height = self.driver.execute_script("return arguments[0].clientHeight", container)
            return scroll_top + client_height >= scroll_height - 10  # 允许10px误差
        except:
            return False
    
    def scroll_photo_container(self, container, attempt):
        """滚动图片容器"""
        strategies = [
            lambda: self.scroll_container_down(container),
            lambda: self.scroll_container_smooth(container),
            lambda: self.scroll_container_step(container),
            lambda: self.scroll_container_to_images(container)
        ]
        
        # 根据尝试次数选择不同的滚动策略
        strategy_index = attempt % len(strategies)
        try:
            strategies[strategy_index]()
        except Exception as e:
            self.log_message(f"滚动策略 {strategy_index} 失败: {e}")
            # 使用最基本的滚动
            try:
                self.driver.execute_script("arguments[0].scrollTop += 300", container)
            except:
                # 最后的备用方案：滚动整个页面
                self.driver.execute_script("window.scrollBy(0, 300)")
    
    def scroll_container_down(self, container):
        """向下滚动容器"""
        self.driver.execute_script("""
            arguments[0].scrollTop = arguments[0].scrollHeight;
        """, container)
        time.sleep(2)
    
    def scroll_container_smooth(self, container):
        """平滑滚动容器"""
        self.driver.execute_script("""
            arguments[0].scrollBy({
                top: 500,
                behavior: 'smooth'
            });
        """, container)
        time.sleep(2)
    
    def scroll_container_step(self, container):
        """分步滚动容器"""
        current_scroll = self.get_container_scroll_position(container)
        new_scroll = current_scroll + 400
        self.driver.execute_script("arguments[0].scrollTop = arguments[1]", container, new_scroll)
        time.sleep(1.5)
    
    def scroll_container_to_images(self, container):
        """滚动到容器中的图片位置"""
        try:
            # 找到容器中的图片
            images = container.find_elements(By.TAG_NAME, "img")
            if images:
                # 滚动到最后几张图片的位置
                last_images = images[-min(5, len(images)):]
                for img in last_images:
                    try:
                        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", img)
                        time.sleep(1)
                    except:
                        continue
        except:
            # 如果失败，使用基本滚动
            self.scroll_container_step(container)
    
    def perform_final_container_check(self, container):
        """执行最终的容器检查"""
        self.log_message("执行最终容器内容检查...")
        
        try:
            # 滚动到容器顶部
            self.driver.execute_script("arguments[0].scrollTop = 0", container)
            time.sleep(2)
            
            # 滚动到容器底部
            self.driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", container)
            time.sleep(3)
            
            # 分步滚动确保所有内容加载
            scroll_height = self.get_container_scroll_height(container)
            steps = max(5, int(scroll_height / 500))
            
            for i in range(steps):
                scroll_position = (i + 1) * (scroll_height / steps)
                self.driver.execute_script("arguments[0].scrollTop = arguments[1]", container, scroll_position)
                time.sleep(2)
                
                # 尝试点击加载更多按钮
                self.click_all_load_more_buttons()
                time.sleep(1)
        except Exception as e:
            self.log_message(f"最终容器检查出错: {e}")
    
    def scroll_and_load_all_content_fallback(self):
        """备用的整页滚动方法"""
        self.log_message("使用备用的整页滚动方法...")
        
        last_img_count = 0
        scroll_attempts = 0
        max_attempts = 100
        
        while scroll_attempts < max_attempts:
            current_img_count = len(self.driver.find_elements(By.TAG_NAME, "img"))
            self.log_message(f"整页滚动 {scroll_attempts + 1}/{max_attempts}, 图片数量: {current_img_count}")
            
            # 滚动到底部
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)
            
            # 点击加载更多按钮
            self.click_all_load_more_buttons()
            time.sleep(2)
            
            new_img_count = len(self.driver.find_elements(By.TAG_NAME, "img"))
            
            if new_img_count == last_img_count:
                break
            
            last_img_count = new_img_count
            scroll_attempts += 1
    
    def enable_network_monitoring(self):
        """启用网络监控 - 简化版"""
        try:
            # 简化的网络监控，不依赖性能日志
            self.pending_requests = set()
            self.network_monitoring_enabled = True
            self.log_message("网络监控已启用（简化版）")
        except Exception as e:
            self.log_message(f"无法启用网络监控: {e}")
            self.pending_requests = None
            self.network_monitoring_enabled = False
    
    def disable_network_monitoring(self):
        """禁用网络监控 - 简化版"""
        try:
            if hasattr(self, 'network_monitoring_enabled'):
                self.network_monitoring_enabled = False
                self.log_message("网络监控已禁用")
        except Exception as e:
            self.log_message(f"禁用网络监控时出错: {e}")
    
    def has_pending_network_requests(self):
        """检查是否有待处理的网络请求 - 简化版"""
        if not hasattr(self, 'network_monitoring_enabled') or not self.network_monitoring_enabled:
            return False
        
        try:
            # 简化的网络活动检测
            # 通过检查页面加载状态来判断
            ready_state = self.driver.execute_script("return document.readyState")
            return ready_state != "complete"
        except:
            return False
    
    def perform_comprehensive_scroll(self, attempt):
        """执行综合滚动策略"""
        strategies = [
            self.smooth_scroll_to_bottom,
            self.step_scroll_down,
            self.random_scroll_pattern,
            self.focus_scroll_areas
        ]
        
        # 根据尝试次数选择不同的滚动策略
        strategy_index = attempt % len(strategies)
        strategies[strategy_index]()
    
    def smooth_scroll_to_bottom(self):
        """平滑滚动到底部"""
        self.driver.execute_script("""
            window.scrollTo({
                top: document.body.scrollHeight,
                behavior: 'smooth'
            });
        """)
        time.sleep(2)
    
    def step_scroll_down(self):
        """分步滚动"""
        viewport_height = self.driver.execute_script("return window.innerHeight")
        current_scroll = self.driver.execute_script("return window.pageYOffset")
        
        # 滚动一个视窗高度
        new_scroll = current_scroll + viewport_height
        self.driver.execute_script(f"window.scrollTo(0, {new_scroll});")
        time.sleep(1.5)
    
    def random_scroll_pattern(self):
        """随机滚动模式，模拟用户行为"""
        import random
        
        # 随机滚动距离
        scroll_distance = random.randint(300, 800)
        current_scroll = self.driver.execute_script("return window.pageYOffset")
        new_scroll = current_scroll + scroll_distance
        
        self.driver.execute_script(f"window.scrollTo(0, {new_scroll});")
        time.sleep(random.uniform(1, 3))
        
        # 偶尔向上滚动一点
        if random.random() < 0.3:
            back_scroll = new_scroll - random.randint(100, 300)
            self.driver.execute_script(f"window.scrollTo(0, {back_scroll});")
            time.sleep(1)
    
    def focus_scroll_areas(self):
        """聚焦滚动到特定区域"""
        try:
            # 查找可能包含图片的容器
            containers = self.driver.find_elements(By.CSS_SELECTOR, 
                "div[class*='photo'], div[class*='image'], div[class*='gallery'], "
                "div[class*='grid'], div[class*='list'], div[class*='content']")
            
            if containers:
                import random
                container = random.choice(containers)
                self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth'});", container)
                time.sleep(2)
        except:
            # 如果失败，执行普通滚动
            self.driver.execute_script("window.scrollBy(0, 500);")
            time.sleep(1.5)
    
    def click_all_load_more_buttons(self):
        """点击所有可能的加载更多按钮"""
        clicked = False
        
        # 扩展的按钮选择器
        load_more_selectors = [
            "//button[contains(text(), '加载更多')]",
            "//button[contains(text(), '更多')]",
            "//button[contains(text(), '查看更多')]",
            "//button[contains(text(), '展开更多')]",
            "//div[contains(text(), '加载更多')]",
            "//div[contains(text(), '更多')]",
            "//span[contains(text(), '加载更多')]",
            "//span[contains(text(), '更多')]",
            "//a[contains(text(), '更多')]",
            "//a[contains(text(), '加载更多')]",
            "//*[contains(@class, 'load-more')]",
            "//*[contains(@class, 'more')]",
            "//*[contains(@class, 'btn-more')]",
            "//*[contains(@class, 'show-more')]",
            "//*[contains(@class, 'expand')]",
            "//*[contains(@onclick, 'more')]",
            "//*[contains(@onclick, 'load')]",
            "//*[contains(@data-action, 'more')]",
            "//*[contains(@data-action, 'load')]",
            # 微赞平台特定的选择器
            "//*[contains(@class, 'vzan-load')]",
            "//*[contains(@class, 'vzan-more')]",
            "//button[contains(@class, 'vzan')]",
            "//div[contains(@class, 'load') and contains(@class, 'btn')]"
        ]
        
        for selector in load_more_selectors:
            try:
                buttons = self.driver.find_elements(By.XPATH, selector)
                for button in buttons:
                    if button.is_displayed() and button.is_enabled():
                        try:
                            # 滚动到按钮位置
                            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
                            time.sleep(0.5)
                            
                            # 尝试多种点击方式
                            click_methods = [
                                lambda: button.click(),
                                lambda: self.driver.execute_script("arguments[0].click();", button),
                                lambda: ActionChains(self.driver).move_to_element(button).click().perform()
                            ]
                            
                            for click_method in click_methods:
                                try:
                                    click_method()
                                    self.log_message(f"成功点击加载更多按钮: {selector}")
                                    clicked = True
                                    time.sleep(2)
                                    break
                                except:
                                    continue
                            
                            if clicked:
                                break
                        except Exception as e:
                            continue
                if clicked:
                    break
            except:
                continue
        
        return clicked
    
    def wait_for_dynamic_content(self):
        """等待动态内容加载"""
        # 等待基础时间
        time.sleep(2)
        
        # 等待可能的AJAX请求完成
        try:
            WebDriverWait(self.driver, 10).until(
                lambda driver: driver.execute_script("return jQuery.active == 0") if 
                driver.execute_script("return typeof jQuery !== 'undefined'") else True
            )
        except:
            pass
        
        # 等待图片加载
        self.wait_for_images_to_load()
    
    def wait_for_images_to_load(self):
        """等待图片加载完成"""
        try:
            # 等待所有图片加载完成
            WebDriverWait(self.driver, 15).until(
                lambda driver: driver.execute_script("""
                    var images = document.querySelectorAll('img');
                    for (var i = 0; i < images.length; i++) {
                        if (!images[i].complete || images[i].naturalHeight === 0) {
                            return false;
                        }
                    }
                    return true;
                """)
            )
        except TimeoutException:
            self.log_message("等待图片加载超时，继续执行...")
    
    def force_trigger_all_loads(self):
        """强制触发所有可能的加载事件"""
        triggered = False
        
        try:
            # 1. 触发滚动事件
            self.driver.execute_script("""
                window.dispatchEvent(new Event('scroll'));
                window.dispatchEvent(new Event('resize'));
            """)
            
            # 2. 触发懒加载
            self.driver.execute_script("""
                // 触发所有可能的懒加载图片
                var lazyImages = document.querySelectorAll('img[data-src], img[data-lazy], img[loading="lazy"]');
                lazyImages.forEach(function(img) {
                    if (img.dataset.src) {
                        img.src = img.dataset.src;
                    }
                    if (img.dataset.lazy) {
                        img.src = img.dataset.lazy;
                    }
                });
            """)
            
            # 3. 模拟鼠标移动和点击事件
            body = self.driver.find_element(By.TAG_NAME, "body")
            ActionChains(self.driver).move_to_element(body).perform()
            
            # 4. 尝试触发无限滚动
            for _ in range(3):
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                self.driver.execute_script("window.scrollBy(0, -100);")
                time.sleep(1)
                self.driver.execute_script("window.scrollBy(0, 200);")
                time.sleep(2)
            
            # 5. 查找并点击所有可能的隐藏加载按钮
            hidden_buttons = self.driver.find_elements(By.CSS_SELECTOR, 
                "button[style*='display: none'], div[style*='display: none']")
            
            for button in hidden_buttons:
                try:
                    if 'load' in button.get_attribute('outerHTML').lower() or 'more' in button.get_attribute('outerHTML').lower():
                        self.driver.execute_script("arguments[0].style.display = 'block';", button)
                        self.driver.execute_script("arguments[0].click();", button)
                        triggered = True
                        time.sleep(2)
                except:
                    continue
            
            return triggered
            
        except Exception as e:
            self.log_message(f"强制触发加载时出错: {e}")
            return False
    
    def perform_upward_scroll(self, attempt):
        """执行向上滚动策略"""
        strategies = [
            self.smooth_scroll_up,
            self.step_scroll_up,
            self.random_upward_scroll,
            self.focus_scroll_up_areas
        ]
        
        # 根据尝试次数选择不同的滚动策略
        strategy_index = attempt % len(strategies)
        strategies[strategy_index]()
    
    def smooth_scroll_up(self):
        """平滑向上滚动"""
        current_position = self.driver.execute_script("return window.pageYOffset")
        if current_position > 0:
            self.driver.execute_script("""
                window.scrollTo({
                    top: Math.max(0, window.pageYOffset - window.innerHeight),
                    behavior: 'smooth'
                });
            """)
        else:
            # 如果已经在顶部，尝试滚动到底部再向上
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1)
            self.driver.execute_script("window.scrollTo({top: document.body.scrollHeight - window.innerHeight, behavior: 'smooth'});")
        time.sleep(2)
    
    def step_scroll_up(self):
        """分步向上滚动"""
        viewport_height = self.driver.execute_script("return window.innerHeight")
        current_scroll = self.driver.execute_script("return window.pageYOffset")
        
        # 向上滚动一个视窗高度
        new_scroll = max(0, current_scroll - viewport_height)
        self.driver.execute_script(f"window.scrollTo(0, {new_scroll});")
        time.sleep(1.5)
    
    def random_upward_scroll(self):
        """随机向上滚动模式"""
        import random
        
        current_scroll = self.driver.execute_script("return window.pageYOffset")
        
        if current_scroll > 0:
            # 随机向上滚动距离
            scroll_distance = random.randint(300, 800)
            new_scroll = max(0, current_scroll - scroll_distance)
            
            self.driver.execute_script(f"window.scrollTo(0, {new_scroll});")
            time.sleep(random.uniform(1, 3))
            
            # 偶尔向下滚动一点，模拟用户行为
            if random.random() < 0.3:
                back_scroll = min(current_scroll, new_scroll + random.randint(100, 300))
                self.driver.execute_script(f"window.scrollTo(0, {back_scroll});")
                time.sleep(1)
        else:
            # 如果在顶部，滚动到底部重新开始
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1)
    
    def focus_scroll_up_areas(self):
        """聚焦向上滚动到特定区域"""
        try:
            # 查找可能包含图片的容器
            containers = self.driver.find_elements(By.CSS_SELECTOR, 
                "div[class*='photo'], div[class*='image'], div[class*='gallery'], "
                "div[class*='grid'], div[class*='list'], div[class*='content']")
            
            if containers:
                import random
                container = random.choice(containers)
                # 滚动到容器上方
                self.driver.execute_script("""
                    var rect = arguments[0].getBoundingClientRect();
                    var scrollTop = window.pageYOffset + rect.top - window.innerHeight/2;
                    window.scrollTo({top: Math.max(0, scrollTop), behavior: 'smooth'});
                """, container)
                time.sleep(2)
        except:
            # 如果失败，执行普通向上滚动
            current_scroll = self.driver.execute_script("return window.pageYOffset")
            new_scroll = max(0, current_scroll - 500)
            self.driver.execute_script(f"window.scrollTo(0, {new_scroll});")
            time.sleep(1.5)
    
    def perform_final_upward_content_check(self):
        """执行最终的向上内容检查"""
        self.log_message("执行最终内容检查...")
        
        # 滚动到底部
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)
        
        # 从底部向上滚动到顶部，确保所有内容都被触发
        total_height = self.driver.execute_script("return document.body.scrollHeight")
        viewport_height = self.driver.execute_script("return window.innerHeight")
        
        steps = max(5, int(total_height / viewport_height))
        for i in range(steps):
            scroll_position = total_height - (i + 1) * (total_height / steps)
            scroll_position = max(0, scroll_position)
            
            self.driver.execute_script(f"window.scrollTo(0, {scroll_position});")
            time.sleep(2)
            
            # 尝试点击加载更多按钮
            self.click_all_load_more_buttons()
            time.sleep(1)
        
        # 最后回到顶部
        self.driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(3)
        
        # 再滚动到底部确认
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
    
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
        """提取所有照片URL - 增强版"""
        self.log_message("开始提取照片链接...")
        
        photo_urls = []
        processed_elements = set()
        
        # 方法1：从img元素提取
        img_urls = self.extract_urls_from_img_elements()
        photo_urls.extend(img_urls)
        
        # 方法2：从页面源代码提取
        source_urls = self.extract_urls_from_page_source()
        photo_urls.extend(source_urls)
        
        # 方法3：从背景图片样式提取
        bg_urls = self.extract_urls_from_background_images()
        photo_urls.extend(bg_urls)
        
        # 方法4：从JavaScript变量提取
        js_urls = self.extract_urls_from_javascript()
        photo_urls.extend(js_urls)
        
        # 方法5：从data属性和自定义属性提取
        data_urls = self.extract_urls_from_data_attributes()
        photo_urls.extend(data_urls)
        
        # 去重并过滤
        unique_urls = list(set(photo_urls))
        valid_urls = []
        
        for url in unique_urls:
            if self.is_valid_image_url(url) and self.is_competition_photo(url):
                enhanced_url = self.enhance_image_url_quality(url)
                valid_urls.append(enhanced_url)
        
        self.log_message(f"去重后共找到 {len(valid_urls)} 个有效照片链接")
        return valid_urls
    
    def extract_urls_from_img_elements(self):
        """从img元素提取URL"""
        urls = []
        img_elements = self.driver.find_elements(By.TAG_NAME, "img")
        self.log_message(f"找到 {len(img_elements)} 个图片元素")
        
        for i, img_element in enumerate(img_elements, 1):
            try:
                if i % 500 == 0:
                    self.log_message(f"正在处理第 {i}/{len(img_elements)} 个图片元素")
                
                # 检查各种可能的URL属性
                url_attrs = [
                    'src', 'data-src', 'data-original', 'data-large', 'data-big',
                    'data-full', 'data-origin', 'data-raw', 'data-url', 'data-lazy',
                    'data-srcset', 'srcset', 'data-image', 'data-photo'
                ]
                
                for attr in url_attrs:
                    url = img_element.get_attribute(attr)
                    if url:
                        # 处理srcset格式
                        if 'srcset' in attr and ',' in url:
                            srcset_urls = self.parse_srcset(url)
                            urls.extend(srcset_urls)
                        else:
                            urls.append(url)
                
                # 检查父元素的链接
                try:
                    parent = img_element.find_element(By.XPATH, "./..")
                    if parent.tag_name.lower() == 'a':
                        href = parent.get_attribute('href')
                        if href:
                            urls.append(href)
                except:
                    pass
                
            except Exception as e:
                continue
        
        self.log_message(f"从img元素提取到 {len(urls)} 个URL")
        return urls
    
    def extract_urls_from_page_source(self):
        """从页面源代码提取URL"""
        urls = []
        page_source = self.driver.page_source
        
        # 多种URL匹配模式
        url_patterns = [
            # 微赞平台特定模式
            r'"(https?://[^"]*i\d*cut\.vzan\.com[^"]*\.(?:jpg|jpeg|png|webp|gif)(?:\?[^"]*)?)"',
            r"'(https?://[^']*i\d*cut\.vzan\.com[^']*\.(?:jpg|jpeg|png|webp|gif)(?:\?[^']*)?)'",
            # 通用图片URL模式
            r'"(https?://[^"]*\.(?:jpg|jpeg|png|webp|gif)(?:\?[^"]*)?)"',
            r"'(https?://[^']*\.(?:jpg|jpeg|png|webp|gif)(?:\?[^']*)?)'",
            # JavaScript中的图片URL
            r'src:\s*["\']([^"\']*\.(?:jpg|jpeg|png|webp|gif)(?:\?[^"\']*)?)["\']',
            r'image:\s*["\']([^"\']*\.(?:jpg|jpeg|png|webp|gif)(?:\?[^"\']*)?)["\']',
            r'photo:\s*["\']([^"\']*\.(?:jpg|jpeg|png|webp|gif)(?:\?[^"\']*)?)["\']',
            # data-* 属性中的URL
            r'data-[^=]*=["\']([^"\']*\.(?:jpg|jpeg|png|webp|gif)(?:\?[^"\']*)?)["\']',
        ]
        
        for pattern in url_patterns:
            matches = re.findall(pattern, page_source, re.IGNORECASE)
            urls.extend(matches)
        
        self.log_message(f"从页面源代码提取到 {len(urls)} 个URL")
        return urls
    
    def extract_urls_from_background_images(self):
        """从背景图片样式提取URL"""
        urls = []
        
        try:
            # 查找所有有背景图片的元素
            elements_with_bg = self.driver.find_elements(By.CSS_SELECTOR, "[style*='background-image']")
            
            for element in elements_with_bg:
                style = element.get_attribute('style')
                if style:
                    # 提取background-image中的URL
                    matches = re.findall(r'background-image:\s*url\(["\']?(.*?)["\']?\)', style, re.IGNORECASE)
                    for match in matches:
                        if match.startswith('http') or match.startswith('//'):
                            urls.append(match if match.startswith('http') else 'https:' + match)
                        else:
                            urls.append(urljoin(self.base_url, match))
            
            # 查找CSS样式表中的背景图片
            css_elements = self.driver.find_elements(By.TAG_NAME, "style")
            for css_element in css_elements:
                css_content = css_element.get_attribute('innerHTML')
                if css_content:
                    matches = re.findall(r'background-image:\s*url\(["\']?(.*?)["\']?\)', css_content, re.IGNORECASE)
                    for match in matches:
                        if self.is_valid_image_url(match):
                            if match.startswith('http') or match.startswith('//'):
                                urls.append(match if match.startswith('http') else 'https:' + match)
                            else:
                                urls.append(urljoin(self.base_url, match))
        
        except Exception as e:
            self.log_message(f"提取背景图片URL时出错: {e}")
        
        self.log_message(f"从背景图片提取到 {len(urls)} 个URL")
        return urls
    
    def extract_urls_from_javascript(self):
        """从JavaScript变量和对象中提取URL"""
        urls = []
        
        try:
            # 执行JavaScript来查找图片URL
            js_code = """
            var urls = [];
            
            // 查找全局变量中的图片URL
            for (var prop in window) {
                try {
                    var value = window[prop];
                    if (typeof value === 'string' && value.match(/\\.(jpg|jpeg|png|webp|gif)/i)) {
                        urls.push(value);
                    } else if (typeof value === 'object' && value !== null) {
                        // 递归查找对象中的图片URL
                        function findUrls(obj, depth) {
                            if (depth > 3) return; // 限制递归深度
                            for (var key in obj) {
                                try {
                                    var val = obj[key];
                                    if (typeof val === 'string' && val.match(/\\.(jpg|jpeg|png|webp|gif)/i)) {
                                        urls.push(val);
                                    } else if (typeof val === 'object' && val !== null) {
                                        findUrls(val, depth + 1);
                                    }
                                } catch(e) {}
                            }
                        }
                        findUrls(value, 0);
                    }
                } catch(e) {}
            }
            
            // 查找所有script标签中的图片URL
            var scripts = document.querySelectorAll('script');
            for (var i = 0; i < scripts.length; i++) {
                var scriptContent = scripts[i].innerHTML;
                var matches = scriptContent.match(/(https?:\\/\\/[^\\s"']*\\.(jpg|jpeg|png|webp|gif)[^\\s"']*)/gi);
                if (matches) {
                    urls = urls.concat(matches);
                }
            }
            
            return urls;
            """
            
            js_urls = self.driver.execute_script(js_code)
            if js_urls:
                urls.extend(js_urls)
        
        except Exception as e:
            self.log_message(f"从JavaScript提取URL时出错: {e}")
        
        self.log_message(f"从JavaScript提取到 {len(urls)} 个URL")
        return urls
    
    def extract_urls_from_data_attributes(self):
        """从data属性和自定义属性提取URL"""
        urls = []
        
        try:
            # 查找所有有data-*属性的元素
            elements = self.driver.find_elements(By.CSS_SELECTOR, "[data-src], [data-original], [data-image], [data-photo], [data-url]")
            
            for element in elements:
                # 获取所有属性
                attributes = self.driver.execute_script("""
                    var items = {};
                    for (index = 0; index < arguments[0].attributes.length; ++index) {
                        items[arguments[0].attributes[index].name] = arguments[0].attributes[index].value;
                    }
                    return items;
                """, element)
                
                for attr_name, attr_value in attributes.items():
                    if attr_value and ('data-' in attr_name or 'src' in attr_name.lower()):
                        if self.is_valid_image_url(attr_value):
                            urls.append(attr_value)
        
        except Exception as e:
            self.log_message(f"从data属性提取URL时出错: {e}")
        
        self.log_message(f"从data属性提取到 {len(urls)} 个URL")
        return urls
    
    def parse_srcset(self, srcset_value):
        """解析srcset属性值"""
        urls = []
        if not srcset_value:
            return urls
        
        # srcset格式: "url1 1x, url2 2x" 或 "url1 100w, url2 200w"
        entries = srcset_value.split(',')
        for entry in entries:
            entry = entry.strip()
            # 提取URL部分（去除尺寸描述符）
            url = entry.split()[0] if entry else ''
            if url and self.is_valid_image_url(url):
                urls.append(url)
        
        return urls
    
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
            login_success = self.wait_for_login()
            
            if not login_success or not self.login_completed:
                self.log_message("❌ 登录失败或用户取消，程序退出")
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