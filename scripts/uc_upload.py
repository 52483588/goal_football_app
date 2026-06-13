#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UC网盘自动上传脚本（使用 Cookie 认证）
"""

import os
import sys
import json
import glob
import requests

# 从环境变量读取 Cookie
UC_COOKIE = os.environ.get('UC_COOKIE', '')

if not UC_COOKIE:
    print("❌ 错误: 未设置 UC_COOKIE 环境变量")
    print("   请按以下步骤获取 Cookie：")
    print("   1. 浏览器登录 UC 网盘")
    print("   2. F12 → Network → 找任意请求")
    print("   3. 复制 Cookie 请求头完整内容")
    print("   4. 添加到 GitHub Secrets: UC_COOKIE")
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

# 创建会话，使用 Cookie 认证
session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Referer': 'https://drive.uc.cn/',
    'Origin': 'https://drive.uc.cn',
    'Cookie': UC_COOKIE
})

def get_upload_pre(file_path):
    """获取上传预处理信息"""
    
    pre_url = "https://pc-api.uc.cn/1/clouddrive/file/upload/pre?pr=UCBrowser&fr=pc"
    
    session.headers.update({
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    })
    
    file_size = os.path.getsize(file_path)
    file_name = os.path.basename(file_path)
    
    payload = {
        "name": file_name,
        "size": file_size,
        "parent_id": "root",
        "check_name_mode": "auto_rename",
        "type": "file",
        "file_struct": {
            "platform_source": "pc"
        }
    }
    
    print(f"📡 获取上传预处理信息...")
    resp = session.post(pre_url, json=payload)
    
    if resp.status_code == 200:
        result = resp.json()
        if result.get('code') == 0:
            data = result.get('data', {})
            print(f"✅ 预处理成功，upload_id: {data.get('upload_id')}")
            return data
        else:
            print(f"❌ 预处理失败: {result}")
            return None
    else:
        print(f"❌ 预处理请求失败: HTTP {resp.status_code}")
        return None

def upload_file_content(upload_info, file_path):
    """上传文件内容到 PDS 存储"""
    
    upload_url = upload_info.get('upload_url')
    obj_key = upload_info.get('obj_key')
    auth_info = upload_info.get('auth_info')
    
    if not upload_url or not obj_key:
        print("❌ 缺少上传必要信息")
        return False
    
    full_upload_url = f"{upload_url}/{obj_key}"
    
    headers = {
        'Authorization': auth_info,
        'Content-Type': 'application/octet-stream',
        'Content-Length': str(os.path.getsize(file_path))
    }
    
    print(f"📤 正在上传文件内容...")
    
    try:
        with open(file_path, 'rb') as f:
            file_data = f.read()
        
        resp = requests.put(full_upload_url, data=file_data, headers=headers)
        
        if resp.status_code in [200, 201]:
            print(f"✅ 文件内容上传成功")
            return True
        else:
            print(f"❌ 上传失败: HTTP {resp.status_code}")
            return False
    except Exception as e:
        print(f"❌ 上传异常: {e}")
        return False

def complete_upload(upload_info, file_name, file_size):
    """完成上传，通知服务器"""
    
    complete_url = "https://pc-api.uc.cn/1/clouddrive/file/upload/complete?pr=UCBrowser&fr=pc"
    
    payload = {
        "upload_id": upload_info.get('upload_id'),
        "obj_key": upload_info.get('obj_key'),
        "name": file_name,
        "parent_id": "root",
        "size": file_size,
        "file_struct": {
            "platform_source": "pc"
        }
    }
    
    print(f"📡 完成上传确认...")
    resp = session.post(complete_url, json=payload)
    
    if resp.status_code == 200:
        result = resp.json()
        if result.get('code') == 0:
            print(f"✅ 上传完成确认成功")
            return True
        else:
            print(f"⚠️ 确认响应: {result}")
            return True
    else:
        print(f"⚠️ 确认请求失败: HTTP {resp.status_code}")
        return True


# ==================== 主流程 ====================

print("=" * 50)
print("UC 网盘自动上传脚本启动")
print("=" * 50)

# 1. 获取上传预处理信息
upload_info = get_upload_pre(upload_file)
if not upload_info:
    print("❌ 获取上传预处理失败，退出")
    sys.exit(1)

# 2. 上传文件内容
if not upload_file_content(upload_info, upload_file):
    print("❌ 文件内容上传失败，退出")
    sys.exit(1)

# 3. 完成上传确认
complete_upload(upload_info, file_name, file_size)

print("=" * 50)
print(f"✅ 文件 {file_name} 上传 UC 网盘完成")
print("=" * 50)

sys.exit(0)
