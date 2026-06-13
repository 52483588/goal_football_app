#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
百度网盘自动上传并分享脚本
"""

import os
import sys
import glob
import requests
import time

# 从环境变量读取
BAIDU_APP_KEY = os.environ.get('BAIDU_APP_KEY', '')
BAIDU_SECRET_KEY = os.environ.get('BAIDU_SECRET_KEY', '')
BAIDU_ACCESS_TOKEN = os.environ.get('BAIDU_ACCESS_TOKEN', '')
BAIDU_REFRESH_TOKEN = os.environ.get('BAIDU_REFRESH_TOKEN', '')

if not BAIDU_ACCESS_TOKEN:
    print("❌ 错误: 未设置 BAIDU_ACCESS_TOKEN")
    sys.exit(1)

# 查找要上传的文件
upload_dir = "./to_upload"
files_to_upload = glob.glob(f"{upload_dir}/*.zip")

if not files_to_upload:
    print("❌ 错误: 没有找到要上传的zip文件")
    sys.exit(1)

upload_file = files_to_upload[0]
file_size = os.path.getsize(upload_file)
file_name = os.path.basename(upload_file)
print(f"📦 找到文件: {file_name} ({file_size / 1024 / 1024:.2f} MB)")


def refresh_access_token():
    """刷新Access Token"""
    print("🔄 正在刷新Access Token...")
    
    url = "https://openapi.baidu.com/oauth/2.0/token"
    params = {
        "grant_type": "refresh_token",
        "refresh_token": BAIDU_REFRESH_TOKEN,
        "client_id": BAIDU_APP_KEY,
        "client_secret": BAIDU_SECRET_KEY
    }
    
    resp = requests.post(url, params=params)
    
    if resp.status_code == 200:
        result = resp.json()
        new_token = result.get('access_token')
        new_refresh_token = result.get('refresh_token')
        print(f"✅ Token刷新成功")
        return new_token, new_refresh_token
    else:
        print(f"❌ Token刷新失败: {resp.text}")
        return None, None


def upload_to_baidu(file_path, access_token):
    """上传文件到百度网盘"""
    
    print(f"📤 正在上传到百度网盘...")
    
    upload_url = "https://c.pcs.baidu.com/rest/2.0/pcs/file"
    
    filename = os.path.basename(file_path)
    app_name = "autobackup"
    remote_path = f"/apps/{app_name}/{filename}"
    
    params = {
        "method": "upload",
        "access_token": access_token,
        "path": remote_path,
        "ondup": "overwrite"
    }
    
    try:
        with open(file_path, 'rb') as f:
            files = {'file': (filename, f)}
            resp = requests.post(upload_url, params=params, files=files, timeout=60)
        
        if resp.status_code == 200:
            result = resp.json()
            if result.get('error_code', 0) == 0:
                print(f"✅ 上传成功")
                print(f"   网盘路径: {remote_path}")
                return result.get('path')
            else:
                print(f"❌ 上传失败: {result}")
                return None
        else:
            print(f"❌ 上传请求失败: HTTP {resp.status_code}")
            return None
    except Exception as e:
        print(f"❌ 上传异常: {e}")
        return None


def create_share_link(file_path, access_token):
    """创建分享链接"""
    
    print(f"🔗 正在创建分享链接...")
    
    share_url = "https://pan.baidu.com/rest/2.0/xpan/share"
    
    params = {
        "method": "create",
        "access_token": access_token,
        "path": file_path,
        "schannel": "0",
        "period": "0",
        "pwd": ""
    }
    
    try:
        resp = requests.post(share_url, params=params)
        
        if resp.status_code == 200:
            result = resp.json()
            if result.get('errno') == 0:
                link = result.get('link')
                print(f"✅ 分享链接创建成功")
                print(f"   链接: {link}")
                return link
            else:
                print(f"⚠️ 分享失败: {result}")
                return None
        else:
            print(f"⚠️ 分享请求失败: HTTP {resp.status_code}")
            return None
    except Exception as e:
        print(f"⚠️ 分享异常: {e}")
        return None


def test_token(access_token):
    """测试Token是否有效"""
    test_url = "https://pan.baidu.com/rest/2.0/xpan/nas"
    params = {
        "method": "uinfo",
        "access_token": access_token
    }
    
    resp = requests.get(test_url, params=params)
    
    if resp.status_code == 200:
        result = resp.json()
        if result.get('errno') == 0:
            print(f"✅ Token有效，用户: {result.get('baidu_name')}")
            return True
        elif result.get('errno') == 111:
            print(f"⚠️ Token已过期，需要刷新")
            return False
        else:
            print(f"⚠️ Token测试异常: {result}")
            return False
    else:
        print(f"⚠️ Token测试失败: HTTP {resp.status_code}")
        return False


# ==================== 主流程 ====================

print("=" * 50)
print("百度网盘自动上传脚本启动")
print("=" * 50)

current_token = BAIDU_ACCESS_TOKEN

# 1. 测试Token有效性
if not test_token(current_token):
    if BAIDU_REFRESH_TOKEN:
        new_token, new_refresh = refresh_access_token()
        if new_token:
            current_token = new_token
            print("⚠️ 请在GitHub Secrets中更新BAIDU_ACCESS_TOKEN")
        else:
            print("❌ Token刷新失败，请手动重新获取")
            sys.exit(1)
    else:
        print("❌ Token无效且未配置REFRESH_TOKEN")
        sys.exit(1)

# 2. 上传文件
remote_path = upload_to_baidu(upload_file, current_token)
if not remote_path:
    print("❌ 上传失败，退出")
    sys.exit(1)

# 3. 创建分享链接
share_link = create_share_link(remote_path, current_token)

# 4. 输出结果供通知使用
if share_link:
    github_env = os.environ.get('GITHUB_ENV')
    if github_env:
        with open(github_env, 'a') as f:
            f.write(f"SHARE_LINK={share_link}\n")
            f.write(f"REMOTE_PATH={remote_path}\n")

print("=" * 50)
print(f"✅ 文件 {file_name} 处理完成")
if share_link:
    print(f"🔗 分享链接: {share_link}")
else:
    print(f"⚠️ 文件已上传，但分享链接创建失败")
print("=" * 50)

sys.exit(0)
