#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UC网盘自动上传脚本
基于抓包分析：登录 + 分片上传
"""

import os
import sys
import json
import glob
import requests

# 从环境变量读取账号密码
UC_USER = os.environ.get('UC_USER', '')
UC_PWD = os.environ.get('UC_PWD', '')

if not UC_USER or not UC_PWD:
    print("❌ 错误: 未设置 UC_USER 或 UC_PWD 环境变量")
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


def login_uc():
    """登录 UC 网盘，返回 session 和 token"""
    
    login_url = "https://api.open.uc.cn/cas/custom/login/commit?custom_login_type=common"
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'https://drive.uc.cn/',
        'Origin': 'https://drive.uc.cn',
        'Content-Type': 'application/x-www-form-urlencoded'
    })
    
    login_data = {
        "login_name": UC_USER,
        "password": UC_PWD,
        "remember": "true"
    }
    
    print(f"🔐 正在登录 UC 网盘...")
    
    resp = session.post(login_url, data=login_data)
    
    if resp.status_code == 200:
        result = resp.json()
        if result.get('status') == 20000:
            token = result.get('data')
            print(f"✅ 登录成功")
            return session, token
        else:
            print(f"❌ 登录失败: {result}")
            return None, None
    else:
        print(f"❌ 登录请求失败: HTTP {resp.status_code}")
        return None, None


def get_upload_pre(session, token, file_path):
    """获取上传预处理信息"""
    
    pre_url = "https://pc-api.uc.cn/1/clouddrive/file/upload/pre?pr=UCBrowser&fr=pc"
    
    session.headers.update({
        'Authorization': f'Bearer {token}',
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


def complete_upload(session, token, upload_info, file_name, file_size):
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

# 1. 登录
session, token = login_uc()
if not session or not token:
    print("❌ 登录失败，退出")
    sys.exit(1)

# 2. 获取上传预处理信息
upload_info = get_upload_pre(session, token, upload_file)
if not upload_info:
    print("❌ 获取上传预处理失败，退出")
    sys.exit(1)

# 3. 上传文件内容
if not upload_file_content(upload_info, upload_file):
    print("❌ 文件内容上传失败，退出")
    sys.exit(1)

# 4. 完成上传确认
complete_upload(session, token, upload_info, file_name, file_size)

print("=" * 50)
print(f"✅ 文件 {file_name} 上传 UC 网盘完成")
print("=" * 50)

sys.exit(0)
