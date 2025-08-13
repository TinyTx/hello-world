#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
改进的页面分析器 - 专门分析弹窗和原图保存流程
"""

import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException

class ImprovedPageAnalyzer:
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
    
    def analyze_all_images(self):
        """分析页面中的所有图片元素"""
        print("\n=== 分析页面图片元素 ===")
        
        # 等待页面加载
        time.sleep(3)
        
        # 查找不同类型的图片元素
        selectors = [
            "img",
            "[style*='background-image']",
            ".photo",
            ".image", 
            ".pic",
            "[data-src]",
            "[data-original]",
            "picture img"
        ]
        
        all_images = []
        for selector in selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                all_images.extend(elements)
                print(f"选择器 '{selector}' 找到 {len(elements)} 个元素")
            except Exception as e:
                print(f"选择器 '{selector}' 查找失败: {e}")
        
        # 去重
        unique_images = list({elem.get_attribute('outerHTML')[:50]: elem for elem in all_images}.values())
        print(f"\n总共找到 {len(unique_images)} 个唯一图片元素")
        
        return unique_images
    
    def test_image_click_workflow(self, img_element, index):
        """测试单张图片的完整点击流程"""
        print(f"\n=== 测试第 {index} 张图片的点击流程 ===")
        
        try:
            # 获取图片基本信息
            src = img_element.get_attribute('src') or img_element.get_attribute('data-src')
            print(f"图片源: {src}")
            
            # 滚动到图片位置
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", img_element)
            time.sleep(1)
            
            # 记录点击前的页面状态
            initial_url = self.driver.current_url
            print(f"点击前URL: {initial_url}")
            
            # 点击图片
            print("正在点击图片...")
            try:
                # 尝试多种点击方式
                ActionChains(self.driver).move_to_element(img_element).click().perform()
            except ElementClickInterceptedException:
                # 如果普通点击被拦截，使用JavaScript点击
                self.driver.execute_script("arguments[0].click();", img_element)
            
            time.sleep(3)  # 等待弹窗加载
            
            # 分析点击后的页面变化
            self.analyze_popup_state()
            
            # 查找并测试"查看原图"按钮
            self.find_and_test_original_button()
            
            # 查找保存按钮
            self.find_save_button()
            
            # 尝试关闭弹窗
            self.close_popup()
            
            return True
            
        except Exception as e:
            print(f"测试图片 {index} 时出错: {e}")
            return False
    
    def analyze_popup_state(self):
        """分析弹窗状态"""
        print("\n--- 分析弹窗状态 ---")
        
        # 查找可能的弹窗容器
        popup_selectors = [
            ".modal",
            ".popup", 
            ".overlay",
            ".dialog",
            ".lightbox",
            "[style*='position: fixed']",
            "[style*='z-index']",
            ".photo-viewer",
            ".image-viewer",
            ".gallery-modal"
        ]
        
        found_popups = []
        for selector in popup_selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for elem in elements:
                    if elem.is_displayed():
                        found_popups.append((selector, elem))
            except:
                pass
        
        if found_popups:
            print(f"找到 {len(found_popups)} 个可能的弹窗元素:")
            for selector, popup in found_popups:
                print(f"  - 选择器: {selector}")
                print(f"    类名: {popup.get_attribute('class')}")
                print(f"    ID: {popup.get_attribute('id')}")
                
                # 查找弹窗内的图片
                popup_imgs = popup.find_elements(By.TAG_NAME, "img")
                if popup_imgs:
                    print(f"    弹窗内图片数量: {len(popup_imgs)}")
                    for i, img in enumerate(popup_imgs[:3]):  # 只显示前3张
                        print(f"      图片{i+1}: {img.get_attribute('src')}")
        else:
            print("未找到明显的弹窗元素")
            print("检查页面是否有其他形式的图片查看器...")
    
    def find_and_test_original_button(self):
        """查找并测试查看原图按钮"""
        print("\n--- 查找查看原图按钮 ---")
        
        # 各种可能的"查看原图"按钮选择器
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
            "//*[contains(@data-action, 'original')]",
            "//*[@title='查看原图']",
            "//*[@alt='查看原图']"
        ]
        
        found_buttons = []
        for selector in original_button_selectors:
            try:
                buttons = self.driver.find_elements(By.XPATH, selector)
                for button in buttons:
                    if button.is_displayed():
                        found_buttons.append(button)
            except:
                pass
        
        if found_buttons:
            print(f"找到 {len(found_buttons)} 个可能的查看原图按钮:")
            for i, button in enumerate(found_buttons):
                print(f"  按钮 {i+1}:")
                print(f"    文本: '{button.text}'")
                print(f"    标签: {button.tag_name}")
                print(f"    类名: {button.get_attribute('class')}")
                print(f"    href: {button.get_attribute('href')}")
                
                # 尝试点击第一个按钮
                if i == 0:
                    try:
                        print(f"    尝试点击按钮...")
                        button.click()
                        time.sleep(2)
                        print(f"    按钮点击成功")
                    except Exception as e:
                        print(f"    按钮点击失败: {e}")
        else:
            print("未找到查看原图按钮")
            # 查找所有可点击元素
            clickable_elements = self.driver.find_elements(By.XPATH, "//*[@onclick or @href]")
            print(f"找到 {len(clickable_elements)} 个可点击元素")
            for elem in clickable_elements[:5]:  # 只显示前5个
                if elem.is_displayed():
                    print(f"  可点击元素: {elem.tag_name} - {elem.text[:20]}")
    
    def find_save_button(self):
        """查找保存到本地按钮"""
        print("\n--- 查找保存按钮 ---")
        
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
        
        found_save_buttons = []
        for selector in save_button_selectors:
            try:
                buttons = self.driver.find_elements(By.XPATH, selector)
                for button in buttons:
                    if button.is_displayed():
                        found_save_buttons.append(button)
            except:
                pass
        
        if found_save_buttons:
            print(f"找到 {len(found_save_buttons)} 个可能的保存按钮:")
            for i, button in enumerate(found_save_buttons):
                print(f"  保存按钮 {i+1}:")
                print(f"    文本: '{button.text}'")
                print(f"    标签: {button.tag_name}")
                print(f"    类名: {button.get_attribute('class')}")
                print(f"    href: {button.get_attribute('href')}")
                
                # 检查是否有下载链接
                href = button.get_attribute('href')
                if href and ('download' in href.lower() or href.endswith(('.jpg', '.jpeg', '.png'))):
                    print(f"    ⭐ 可能的下载链接: {href}")
        else:
            print("未找到保存按钮")
    
    def close_popup(self):
        """尝试关闭弹窗"""
        print("\n--- 尝试关闭弹窗 ---")
        
        close_selectors = [
            "//button[contains(@class, 'close')]",
            "//span[contains(@class, 'close')]",
            "//div[contains(@class, 'close')]",
            "//*[contains(text(), '×')]",
            "//*[contains(text(), '关闭')]",
            "//*[@title='关闭']",
            ".modal-close",
            ".popup-close",
            ".close-btn"
        ]
        
        for selector in close_selectors:
            try:
                if selector.startswith('//'):
                    close_buttons = self.driver.find_elements(By.XPATH, selector)
                else:
                    close_buttons = self.driver.find_elements(By.CSS_SELECTOR, selector)
                
                for button in close_buttons:
                    if button.is_displayed():
                        print(f"找到关闭按钮: {button.tag_name} - {button.text}")
                        try:
                            button.click()
                            time.sleep(1)
                            print("关闭按钮点击成功")
                            return True
                        except Exception as e:
                            print(f"关闭按钮点击失败: {e}")
            except:
                pass
        
        # 尝试按ESC键关闭
        try:
            from selenium.webdriver.common.keys import Keys
            self.driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
            print("尝试使用ESC键关闭")
            time.sleep(1)
        except:
            print("ESC键关闭失败")
        
        # 尝试点击背景关闭
        try:
            self.driver.execute_script("document.querySelector('.modal, .popup, .overlay').click();")
            print("尝试点击背景关闭")
            time.sleep(1)
        except:
            print("点击背景关闭失败")
        
        return False
    
    def run_comprehensive_analysis(self):
        """运行全面分析"""
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
            
            # 分析所有图片
            images = self.analyze_all_images()
            
            if not images:
                print("未找到任何图片，请检查页面是否正确加载")
                return
            
            # 测试前几张图片的点击流程
            test_count = min(3, len(images))
            print(f"\n将测试前 {test_count} 张图片的点击流程")
            
            for i in range(test_count):
                success = self.test_image_click_workflow(images[i], i + 1)
                if success:
                    print(f"图片 {i + 1} 测试完成")
                
                # 等待用户确认
                if i < test_count - 1:
                    input(f"第 {i + 1} 张图片分析完成，按回车继续分析下一张...")
            
            print("\n=== 分析总结 ===")
            print("请根据上述分析结果来优化下载脚本")
            
        finally:
            input("按回车键关闭浏览器...")
            if self.driver:
                self.driver.quit()

def main():
    url = "https://tlwtpbvzb.vzan.com/v3/course/alive/1827403580?v=1755091438866"
    analyzer = ImprovedPageAnalyzer(url)
    analyzer.run_comprehensive_analysis()

if __name__ == "__main__":
    main()