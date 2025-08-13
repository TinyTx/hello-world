#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
网页结构分析器 - 专门分析如何获取原图
"""

import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException

class PageStructureAnalyzer:
    def __init__(self, base_url):
        self.base_url = base_url
        self.driver = None
        
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
            print(f"错误：无法启动Chrome浏览器。{e}")
            return None
    
    def wait_for_login(self):
        """等待用户登录"""
        print("请在浏览器中完成登录...")
        confirmation = input("登录完成后，请输入 'y' 并按回车继续: ").strip().lower()
        while confirmation != 'y':
            confirmation = input("请输入 'y' 确认已登录: ").strip().lower()
        print("登录确认完成")
    
    def analyze_image_click_behavior(self):
        """分析点击图片后的行为"""
        print("开始分析图片点击行为...")
        
        # 等待页面加载
        time.sleep(5)
        
        # 找到所有图片
        img_elements = self.driver.find_elements(By.TAG_NAME, "img")
        print(f"找到 {len(img_elements)} 个图片元素")
        
        if len(img_elements) == 0:
            print("未找到图片元素")
            return
        
        # 分析前几张图片的点击行为
        for i, img in enumerate(img_elements[:5]):  # 只分析前5张图片
            print(f"\n=== 分析第 {i+1} 张图片 ===")
            
            try:
                # 获取图片基本信息
                src = img.get_attribute('src')
                alt = img.get_attribute('alt')
                data_src = img.get_attribute('data-src')
                data_original = img.get_attribute('data-original')
                
                print(f"图片src: {src}")
                print(f"图片alt: {alt}")
                print(f"data-src: {data_src}")
                print(f"data-original: {data_original}")
                
                # 检查父元素
                parent = img.find_element(By.XPATH, "./..")
                parent_tag = parent.tag_name
                parent_href = parent.get_attribute('href') if parent_tag == 'a' else None
                
                print(f"父元素: {parent_tag}")
                if parent_href:
                    print(f"父元素href: {parent_href}")
                
                # 记录当前窗口句柄
                current_window = self.driver.current_window_handle
                print(f"当前窗口数量: {len(self.driver.window_handles)}")
                
                # 尝试点击图片
                print("尝试点击图片...")
                try:
                    # 滚动到图片位置
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", img)
                    time.sleep(1)
                    
                    # 点击图片
                    ActionChains(self.driver).move_to_element(img).click().perform()
                    time.sleep(3)
                    
                    # 检查窗口变化
                    new_windows = self.driver.window_handles
                    print(f"点击后窗口数量: {len(new_windows)}")
                    
                    if len(new_windows) > 1:
                        print("检测到新窗口！")
                        # 切换到新窗口
                        for window in new_windows:
                            if window != current_window:
                                self.driver.switch_to.window(window)
                                print(f"新窗口URL: {self.driver.current_url}")
                                
                                # 查找"查看原图"相关元素
                                self.find_original_image_elements()
                                
                                # 关闭新窗口
                                self.driver.close()
                                break
                        
                        # 切换回原窗口
                        self.driver.switch_to.window(current_window)
                    else:
                        print("没有新窗口，检查当前页面变化...")
                        # 检查是否有弹窗或覆盖层
                        self.find_popup_elements()
                
                except Exception as e:
                    print(f"点击图片时出错: {e}")
                
                # 等待用户确认
                input(f"第 {i+1} 张图片分析完成，按回车继续...")
                
            except Exception as e:
                print(f"分析第 {i+1} 张图片时出错: {e}")
    
    def find_original_image_elements(self):
        """查找原图相关元素"""
        print("查找原图相关元素...")
        
        # 查找所有可能的原图按钮/链接
        original_selectors = [
            "//button[contains(text(), '查看原图')]",
            "//a[contains(text(), '查看原图')]",
            "//button[contains(text(), '原图')]",
            "//a[contains(text(), '原图')]",
            "//div[contains(text(), '原图')]",
            "//span[contains(text(), '原图')]",
            "//*[contains(@class, 'original')]",
            "//*[contains(@class, 'full')]",
            "//*[contains(@class, 'large')]",
            "//*[contains(@class, 'hd')]",
            "//*[contains(@data-action, 'original')]",
            "//*[contains(@onclick, 'original')]"
        ]
        
        found_elements = []
        for selector in original_selectors:
            try:
                elements = self.driver.find_elements(By.XPATH, selector)
                for element in elements:
                    if element.is_displayed():
                        found_elements.append({
                            'element': element,
                            'text': element.text,
                            'tag': element.tag_name,
                            'href': element.get_attribute('href'),
                            'onclick': element.get_attribute('onclick'),
                            'class': element.get_attribute('class')
                        })
            except:
                pass
        
        if found_elements:
            print(f"找到 {len(found_elements)} 个可能的原图元素:")
            for elem_info in found_elements:
                print(f"  - {elem_info['tag']}: {elem_info['text']}")
                print(f"    href: {elem_info['href']}")
                print(f"    class: {elem_info['class']}")
                print(f"    onclick: {elem_info['onclick']}")
        else:
            print("未找到明显的原图按钮/链接")
        
        # 查找所有图片，看是否有高分辨率版本
        print("\n查找当前页面的所有图片:")
        current_imgs = self.driver.find_elements(By.TAG_NAME, "img")
        for i, img in enumerate(current_imgs):
            src = img.get_attribute('src')
            if src:
                print(f"  图片 {i+1}: {src}")
    
    def find_popup_elements(self):
        """查找弹窗元素"""
        print("查找弹窗元素...")
        
        # 查找可能的弹窗/覆盖层
        popup_selectors = [
            "//*[contains(@class, 'modal')]",
            "//*[contains(@class, 'popup')]",
            "//*[contains(@class, 'overlay')]",
            "//*[contains(@class, 'dialog')]",
            "//*[contains(@class, 'lightbox')]",
            "//*[contains(@style, 'position: fixed')]",
            "//*[contains(@style, 'z-index')]"
        ]
        
        found_popups = []
        for selector in popup_selectors:
            try:
                elements = self.driver.find_elements(By.XPATH, selector)
                for element in elements:
                    if element.is_displayed():
                        found_popups.append(element)
            except:
                pass
        
        if found_popups:
            print(f"找到 {len(found_popups)} 个可能的弹窗元素")
            for popup in found_popups:
                print(f"  弹窗类名: {popup.get_attribute('class')}")
                
                # 在弹窗中查找图片和原图链接
                popup_imgs = popup.find_elements(By.TAG_NAME, "img")
                if popup_imgs:
                    print(f"    弹窗中的图片: {len(popup_imgs)} 个")
                    for img in popup_imgs:
                        print(f"      {img.get_attribute('src')}")
                
                # 查找弹窗中的链接
                popup_links = popup.find_elements(By.TAG_NAME, "a")
                for link in popup_links:
                    if link.is_displayed() and link.text:
                        print(f"    链接: {link.text} -> {link.get_attribute('href')}")
        else:
            print("未找到弹窗元素")
    
    def analyze_page_scripts(self):
        """分析页面JavaScript"""
        print("\n=== 分析页面JavaScript ===")
        
        # 执行JavaScript来获取全局变量和函数
        try:
            # 获取所有全局变量
            globals_script = """
            var globals = [];
            for (var key in window) {
                if (key.includes('photo') || key.includes('image') || key.includes('pic')) {
                    globals.push(key + ': ' + typeof window[key]);
                }
            }
            return globals;
            """
            globals_result = self.driver.execute_script(globals_script)
            if globals_result:
                print("找到相关全局变量:")
                for var in globals_result:
                    print(f"  {var}")
            
            # 查找图片相关的事件监听器
            events_script = """
            var images = document.querySelectorAll('img');
            var events = [];
            for (var i = 0; i < images.length; i++) {
                var img = images[i];
                if (img.onclick) {
                    events.push('img ' + i + ' has onclick');
                }
            }
            return events;
            """
            events_result = self.driver.execute_script(events_script)
            if events_result:
                print("找到图片点击事件:")
                for event in events_result:
                    print(f"  {event}")
                    
        except Exception as e:
            print(f"分析JavaScript时出错: {e}")
    
    def analyze_network_requests(self):
        """分析网络请求"""
        print("\n=== 网络请求分析提示 ===")
        print("建议使用浏览器开发者工具的Network标签来监控:")
        print("1. 打开开发者工具 (F12)")
        print("2. 切换到Network标签")
        print("3. 点击图片")
        print("4. 观察新的网络请求，特别是:")
        print("   - XHR/Fetch请求")
        print("   - 图片请求")
        print("   - API调用")
        
    def run_analysis(self):
        """运行完整分析"""
        self.driver = self.setup_driver()
        if not self.driver:
            return
        
        try:
            print(f"正在访问: {self.base_url}")
            self.driver.get(self.base_url)
            
            # 等待页面加载
            time.sleep(5)
            
            # 等待登录
            self.wait_for_login()
            
            # 分析页面脚本
            self.analyze_page_scripts()
            
            # 分析图片点击行为
            self.analyze_image_click_behavior()
            
            # 网络请求分析提示
            self.analyze_network_requests()
            
            print("\n分析完成！请查看上述结果来了解原图获取方式。")
            
        finally:
            input("按回车键关闭浏览器...")
            if self.driver:
                self.driver.quit()

def main():
    url = "https://tlwtpbvzb.vzan.com/v3/course/alive/1827403580?v=1755091438866"
    analyzer = PageStructureAnalyzer(url)
    analyzer.run_analysis()

if __name__ == "__main__":
    main()