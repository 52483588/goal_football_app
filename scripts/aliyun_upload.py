#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
import glob
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

# ========== 分享链接创建（多种方法尝试） ==========
print(f"🔗 正在创建分享链接...")
share_url = None

# 方法1: share_file (原始方法)
try:
    share = ali.share_file(file_id=file_id, share_pwd=None, expiration='')
    if hasattr(share, 'share_url') and share.share_url:
        share_url = share.share_url
    elif hasattr(share, 'share_id') and share.share_id:
        share_url = f"https://www.aliyundrive.com/s/{share.share_id}"
except Exception as e:
    print(f"   方法1失败: {e}")

# 方法2: share_files (列表方式)
if not share_url:
    try:
        share = ali.share_files(file_id_list=[file_id], share_pwd=None, expiration='')
        if hasattr(share, 'share_url') and share.share_url:
            share_url = share.share_url
        elif hasattr(share, 'share_id') and share.share_id:
            share_url = f"https://www.aliyundrive.com/s/{share.share_id}"
    except Exception as e:
        print(f"   方法2失败: {e}")

# 方法3: 直接调用创建接口
if not share_url:
    try:
        result = ali.post('/v2/share_link/create', {
            'file_id_list': [file_id],
            'expiration': '',
            'share_pwd': ''
        })
        if result.get('share_id'):
            share_url = f"https://www.aliyundrive.com/s/{result['share_id']}"
    except Exception as e:
        print(f"   方法3失败: {e}")

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
