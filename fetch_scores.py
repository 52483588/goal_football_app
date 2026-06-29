import requests
import json
import os
import sys

url = "https://www.macauslot.com/infoApi/sc/D/FB/matchs/results"

# 从系统环境变量中读取 Cookie（安全！不写在代码里）
cookie_string = os.environ.get("COOKIE_STRING")
if not cookie_string:
    print("❌ 错误：未找到 COOKIE_STRING 环境变量，请在 GitHub Secrets 中配置。")
    sys.exit(1)

headers = {
    "Cookie": cookie_string,
    "Host": "www.macauslot.com",
    "Origin": "https://www.macauslot.com",
    "Referer": "https://www.macauslot.com/sc/soccer/matchResult.html",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Content-Type": "application/json"
}

try:
    response = requests.post(url, headers=headers, json={}, timeout=15)
    print(f"状态码: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        if data:  # 如果返回了数据
            with open('scores.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print("✅ 比分数据已成功保存到 scores.json")
        else:
            print("⚠️ 返回数据为空，可能是 Cookie 已过期，请更新 Secrets。")
            sys.exit(1)
    else:
        print(f"❌ 请求失败，状态码: {response.status_code}")
        print(response.text)
        sys.exit(1)
        
except Exception as e:
    print(f"❌ 网络请求异常: {e}")
    sys.exit(1)