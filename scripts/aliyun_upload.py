#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
import glob
from aligo import Aligo
import requests

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

# ========== 分享链接创建（直接调用官方API） ==========
print(f"🔗 正在创建分享链接...")
share_url = None

# 1. 首先从 aligo 实例中获取有效的 access_token
try:
    # aligo 实例在初始化后已经包含了 token 信息
    access_token = ali.auth.access_token
except AttributeError:
    # 如果直接获取不到，尝试另一种方式
    access_token = ali.default_auth.access_token

if not access_token:
    print("   ❌ 无法获取 access_token，请检查 aligo 登录状态")
else:
    # 2. 手动构造官方分享接口的请求
    official_share_url = "https://api.aliyundrive.com/adrive/v2/share_link/create"
    
    # 请求头
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    
    # 请求体 - 创建分享链接的核心参数
    payload = {
        "file_id_list": [file_id],   # 要分享的文件ID列表
        "expiration": "",             # 空字符串表示永久有效
        "share_pwd": "",              # 空字符串表示无提取码
    }
    
    try:
        # 发送POST请求
        response = requests.post(official_share_url, headers=headers, json=payload)
        
        if response.status_code == 200:
            result = response.json()
            # 从返回结果中提取 share_id
            share_id = result.get('share_id')
            if share_id:
                share_url = f"https://www.aliyundrive.com/s/{share_id}"
                print(f"   ✅ 分享链接创建成功 (直接调用API)")
            else:
                print(f"   ⚠️ API返回成功但未包含share_id，完整响应: {result}")
        else:
            print(f"   ❌ 分享API请求失败，状态码: {response.status_code}")
            print(f"      响应内容: {response.text}")
            
    except Exception as e:
        print(f"   ❌ 调用分享API时发生异常: {e}")

# ... (后续的 share_url 判断和输出保持不变)

if share_url:
    print(f"✅ 分享链接创建成功")
    print(f"🔗 链接: {share_url}")
else:
    print(f"⚠️ 所有分享创建方法均失败")

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
