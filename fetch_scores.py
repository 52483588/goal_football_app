import json
import sys
from playwright.sync_api import sync_playwright

def main():
    # 用于存放拦截到的 API 响应数据
    api_response = None

    with sync_playwright() as p:
        # 启动 Chromium（无头模式）
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # 监听所有响应，找到目标 API
        def handle_response(response):
            nonlocal api_response
            if "/infoApi/sc/D/FB/matchs/results" in response.url:
                try:
                    # 尝试解析 JSON
                    data = response.json()
                    if data:
                        api_response = data
                        print("✅ 成功拦截到 API 数据！")
                except Exception as e:
                    print(f"⚠️ 解析 API 响应失败: {e}")

        page.on("response", handle_response)

        # 访问目标页面（比分结果页面）
        print("🔄 正在加载页面，等待数据...")
        page.goto("https://www.macauslot.com/sc/soccer/matchResult.html", wait_until="networkidle")
        
        # 额外等待，确保数据完全加载（最多 10 秒）
        for _ in range(20):
            if api_response:
                break
            page.wait_for_timeout(500)
        else:
            print("❌ 未能在 10 秒内捕获到 API 响应，可能页面结构已变化。")
            browser.close()
            sys.exit(1)

        browser.close()

    # 保存数据
    if api_response:
        with open('scores.json', 'w', encoding='utf-8') as f:
            json.dump(api_response, f, indent=2, ensure_ascii=False)
        print("✅ 比分数据已保存到 scores.json")
    else:
        print("❌ 未获取到任何数据")
        sys.exit(1)

if __name__ == "__main__":
    main()
