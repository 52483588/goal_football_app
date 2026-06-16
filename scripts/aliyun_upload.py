#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
import glob
import requests
from aligo import Aligo

ALIYUN_REFRESH_TOKEN = os.environ.get('ALIYUN_REFRESH_TOKEN', '')

if not ALIYUN_REFRESH_TOKEN:
    print("❌ 错误: 未设置 ALIYUN_REFRESH_TOKEN")
    sys.exit(1)

upload_dir = "./to_upload"
files_to_upload = glob.glob(f"{upload_dir}/*.zip")

if not files_to_upload:
    print("❌ 错误: 没有找到要上传的zip文件")
    sys.exit(1)

upload_file = files_to_upload[0]
file_size = os.path.getsize(upload_file)
file_name = os.path.basename(upload_file)
print(f"📦 找到文件: {file_name} ({file_size / 1024 / 1024:.2f} MB)")

print("=" * 50)
print("阿里云盘自动上传脚本启动")
print("=" * 50)

print("🔐 正在连接阿里云盘...")
ali = Aligo(refresh_token=ALIYUN_REFRESH_TOKEN)

user = ali.get_user()
print(f"✅ 登录成功，用户: {user.user_name}")

print(f"📤 正在上传到阿里云盘...")
remote_file = ali.upload_file(upload_file, parent_file_id='root')
print(f"✅ 上传成功")

file_id = remote_file.file_id if hasattr(remote_file, 'file_id') else str(remote_file)
print(f"   文件ID: {file_id}")

# ========== 获取 access_token ==========
access_token = None

# 尝试多种方式获取 token
if hasattr(ali, '_auth') and hasattr(ali._auth, 'access_token'):
    access_token = ali._auth.access_token
elif hasattr(ali, 'auth') and hasattr(ali.auth, 'access_token'):
    access_token = ali.auth.access_token
elif hasattr(ali, 'default_auth') and hasattr(ali.default_auth, 'access_token'):
    access_token = ali.default_auth.access_token
elif hasattr(ali, 'token'):
    access_token = ali.token

# 如果还是获取不到，直接打印 ali 的所有属性来调试
if not access_token:
    print(f"   ⚠️ 无法获取 access_token，ali 对象的属性: {dir(ali)}")
    print(f"   尝试使用备用方案...")
    
    # 备用方案：直接使用 refresh_token 重新获取
    token_url = "https://api.aliyundrive.com/v2/account/token"
    token_data = {
        "grant_type": "refresh_token",
        "refresh_token": ALIYUN_REFRESH_TOKEN
    }
    try:
        token_resp = requests.post(token_url, json=token_data)
        if token_resp.status_code == 200:
            token_result = token_resp.json()
            access_token = token_result.get('access_token')
            print(f"   ✅ 通过备用方案获取到 access_token")
    except Exception as e:
        print(f"   ❌ 备用方案也失败: {e}")

# ========== 创建分享链接 ==========
print(f"🔗 正在创建分享链接...")
share_url = None

if access_token:
    official_share_url = "https://api.aliyundrive.com/adrive/v2/share_link/create"
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    
    payload = {
        "file_id_list": [file_id],
        "expiration": "",
        "share_pwd": "",
    }
    
    try:
        response = requests.post(official_share_url, headers=headers, json=payload)
        print(f"   HTTP 状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            share_id = result.get('share_id')
            if share_id:
                share_url = f"https://www.aliyundrive.com/s/{share_id}"
                print(f"   ✅ 分享链接创建成功")
            else:
                print(f"   ⚠️ API返回但未包含share_id: {result}")
        else:
            print(f"   ❌ 分享API失败: {response.text}")
    except Exception as e:
        print(f"   ❌ 请求异常: {e}")
else:
    print(f"   ❌ 无法获取 access_token，跳过分享创建")

# 输出结果
github_env = os.environ.get('GITHUB_ENV')
if github_env and share_url:
    with open(github_env, 'a') as f:
        f.write(f"SHARE_LINK={share_url}\n")

print("=" * 50)
if share_url:
    print(f"✅ 文件 {file_name} 处理完成")
    print(f"🔗 分享链接: {share_url}")
else:
    print(f"⚠️ 文件 {file_name} 上传完成，但分享链接创建失败")
    print(f"💡 请手动登录阿里云盘，在根目录找到该文件创建分享")
print("=" * 50)

sys.exit(0)
