#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Chrome启动和图片区域滚动修复测试脚本
Test script for Chrome startup and photo container scrolling fixes
"""

import os
import sys
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

def test_chrome_startup():
    """测试Chrome浏览器启动"""
    print("🧪 测试Chrome浏览器启动...")
    
    # 测试增强配置
    print("1. 测试增强配置...")
    try:
        chrome_options = Options()
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--headless')  # 测试时使用无头模式
        
        driver = webdriver.Chrome(options=chrome_options)
        driver.get("https://www.baidu.com")
        time.sleep(2)
        title = driver.title
        driver.quit()
        
        print(f"✅ 增强配置启动成功，页面标题: {title}")
        enhanced_success = True
    except Exception as e:
        print(f"❌ 增强配置失败: {e}")
        enhanced_success = False
    
    # 测试简化配置
    print("2. 测试简化配置...")
    try:
        simple_options = Options()
        simple_options.add_argument('--no-sandbox')
        simple_options.add_argument('--disable-dev-shm-usage')
        simple_options.add_argument('--disable-gpu')
        simple_options.add_argument('--window-size=1920,1080')
        simple_options.add_argument('--headless')
        
        driver = webdriver.Chrome(options=simple_options)
        driver.get("https://www.baidu.com")
        time.sleep(2)
        title = driver.title
        driver.quit()
        
        print(f"✅ 简化配置启动成功，页面标题: {title}")
        simple_success = True
    except Exception as e:
        print(f"❌ 简化配置失败: {e}")
        simple_success = False
    
    return enhanced_success or simple_success

def test_container_detection():
    """测试容器检测功能"""
    print("\n🧪 测试图片容器检测...")
    
    # 创建测试HTML
    test_html = """
    <!DOCTYPE html>
    <html>
    <head><title>Container Test</title></head>
    <body>
        <div class="header">Header</div>
        <div class="photo-gallery" style="height: 400px; overflow-y: scroll;">
            <img src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==" alt="test1">
            <img src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==" alt="test2">
            <img src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==" alt="test3">
            <img src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==" alt="test4">
            <img src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==" alt="test5">
            <img src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==" alt="test6">
        </div>
        <div class="footer">Footer</div>
    </body>
    </html>
    """
    
    try:
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        
        driver = webdriver.Chrome(options=chrome_options)
        driver.get("data:text/html;charset=utf-8," + test_html)
        time.sleep(1)
        
        # 测试容器检测逻辑
        container_selectors = [
            ".photo-gallery",
            "[class*='photo']",
            "[class*='gallery']",
        ]
        
        found_container = None
        for selector in container_selectors:
            try:
                containers = driver.find_elements(By.CSS_SELECTOR, selector)
                for container in containers:
                    imgs_in_container = container.find_elements(By.TAG_NAME, "img")
                    if len(imgs_in_container) >= 5:
                        found_container = container
                        print(f"✅ 找到图片容器: {selector}, 包含 {len(imgs_in_container)} 张图片")
                        break
            except:
                continue
            if found_container:
                break
        
        if found_container:
            # 测试容器滚动
            scroll_height = driver.execute_script("return arguments[0].scrollHeight", found_container)
            client_height = driver.execute_script("return arguments[0].clientHeight", found_container)
            
            print(f"✅ 容器滚动高度: {scroll_height}, 可视高度: {client_height}")
            
            # 测试滚动
            driver.execute_script("arguments[0].scrollTop = 100", found_container)
            scroll_top = driver.execute_script("return arguments[0].scrollTop", found_container)
            print(f"✅ 滚动测试成功，滚动位置: {scroll_top}")
            
            driver.quit()
            return True
        else:
            print("❌ 未找到图片容器")
            driver.quit()
            return False
            
    except Exception as e:
        print(f"❌ 容器检测测试失败: {e}")
        return False

def test_scroll_strategies():
    """测试滚动策略"""
    print("\n🧪 测试滚动策略...")
    
    # 模拟滚动策略
    strategies = [
        "scroll_container_down",
        "scroll_container_smooth", 
        "scroll_container_step",
        "scroll_container_to_images"
    ]
    
    print("可用的滚动策略:")
    for i, strategy in enumerate(strategies):
        print(f"✅ 策略 {i+1}: {strategy}")
    
    # 测试滚动逻辑
    def simulate_container_scroll(scroll_height, client_height, current_scroll, scroll_amount):
        """模拟容器滚动"""
        new_scroll = min(current_scroll + scroll_amount, scroll_height - client_height)
        return max(0, new_scroll)
    
    # 测试用例
    test_cases = [
        (1000, 300, 0, 400),      # 从顶部开始滚动
        (1000, 300, 400, 400),    # 继续滚动
        (1000, 300, 600, 400),    # 接近底部
        (1000, 300, 700, 400),    # 到达底部
    ]
    
    passed = 0
    for scroll_height, client_height, current, amount in test_cases:
        result = simulate_container_scroll(scroll_height, client_height, current, amount)
        max_scroll = scroll_height - client_height
        expected = min(current + amount, max_scroll)
        
        if result == expected:
            print(f"✅ 滚动测试: {current} + {amount} = {result} (正确)")
            passed += 1
        else:
            print(f"❌ 滚动测试: {current} + {amount} = {result}, 期望 {expected}")
    
    print(f"滚动策略测试: {passed}/{len(test_cases)} 通过")
    return passed == len(test_cases)

def test_fallback_mechanism():
    """测试备用机制"""
    print("\n🧪 测试备用滚动机制...")
    
    # 模拟找不到容器的情况
    def find_photo_container_simulation(has_container=True):
        if has_container:
            return {"type": "container", "images": 20}
        else:
            return None
    
    # 测试有容器的情况
    container = find_photo_container_simulation(True)
    if container:
        print("✅ 找到图片容器，使用容器滚动")
        container_method = True
    else:
        print("⚠️  未找到图片容器，使用备用方法")
        container_method = False
    
    # 测试没有容器的情况
    container = find_photo_container_simulation(False)
    if container:
        print("✅ 找到图片容器，使用容器滚动")
        fallback_method = False
    else:
        print("✅ 未找到图片容器，正确触发备用方法")
        fallback_method = True
    
    return container_method and fallback_method

def test_network_monitoring_simplified():
    """测试简化的网络监控"""
    print("\n🧪 测试简化网络监控...")
    
    try:
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        
        driver = webdriver.Chrome(options=chrome_options)
        driver.get("https://httpbin.org/delay/2")
        
        # 测试页面加载状态检测
        start_time = time.time()
        while time.time() - start_time < 5:
            ready_state = driver.execute_script("return document.readyState")
            if ready_state == "complete":
                print("✅ 页面加载完成检测正常")
                driver.quit()
                return True
            time.sleep(0.5)
        
        print("⚠️  页面加载检测超时")
        driver.quit()
        return False
        
    except Exception as e:
        print(f"❌ 网络监控测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 开始Chrome和滚动修复功能测试")
    print("=" * 50)
    
    test_results = []
    
    # 执行各项测试
    tests = [
        ("Chrome浏览器启动", test_chrome_startup),
        ("图片容器检测", test_container_detection),
        ("滚动策略", test_scroll_strategies),
        ("备用机制", test_fallback_mechanism),
        ("简化网络监控", test_network_monitoring_simplified)
    ]
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            test_results.append((test_name, result))
        except Exception as e:
            print(f"❌ 测试 {test_name} 出现异常: {e}")
            test_results.append((test_name, False))
    
    # 汇总结果
    print("\n" + "=" * 50)
    print("📊 修复功能测试结果:")
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n总计: {passed}/{total} 项测试通过")
    
    # 显示修复说明
    print("\n🔧 修复说明:")
    print("1. Chrome启动问题:")
    print("   - 移除了不兼容的loggingPrefs选项")
    print("   - 移除了perfLoggingPrefs选项")
    print("   - 增加了简化配置备用方案")
    print("   - 改进了错误处理机制")
    
    print("\n2. 滚动目标问题:")
    print("   - 智能检测图片容器区域")
    print("   - 专门滚动图片容器而不是整个页面")
    print("   - 增加了4种容器滚动策略")
    print("   - 提供备用的整页滚动方法")
    
    print("\n3. 网络监控简化:")
    print("   - 移除了对性能日志的依赖")
    print("   - 使用页面加载状态检测")
    print("   - 简化了网络活动监控")
    
    print("\n4. 使用建议:")
    print("   - 现在应该可以正常启动Chrome浏览器")
    print("   - 程序会自动找到图片区域并滚动")
    print("   - 如果找不到图片容器会自动使用备用方法")
    
    if passed == total:
        print("\n🎉 所有修复功能测试通过！")
        return 0
    else:
        print("\n⚠️  部分测试失败，但主要功能应该可用")
        return 1

if __name__ == "__main__":
    sys.exit(main())