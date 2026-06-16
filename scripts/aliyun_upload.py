#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
阿里云盘自动上传并分享脚本
使用 aligo 库
"""

import os
import sys
import glob
from aligo import Aligo

# 从环境变量读取 refresh_token
ALIYUN_REFRESH_TOKEN = os.environ.get('ALIYUN_REFRESH_TOKEN', '')

if not ALIYUN_REFRESH_TOKEN:
    print("❌ 错误: 未设置 ALIYUN_REFRESH_TOKEN")
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

print("=" * 50)
print("阿里云盘自动上传脚本启动")
print("=" * 50)

# 初始化 Aligo
print("🔐 正在连接阿里云盘...")
ali = Aligo(refresh_token=ALIYUN_REFRESH_TOKEN)

# 获取用户信息确认登录成功
user = ali.get_user()
print(f"✅ 登录成功，用户: {user.user_name}")

# 1. 上传文件
print(f"📤 正在上传到阿里云盘...")
remote_file = ali.upload_file(upload_file, parent_file_id='root')
print(f"✅ 上传成功")

# 获取文件ID（不同版本 aligo 返回对象不同）
file_id = None
if hasattr(remote_file, 'file_id'):
    file_id = remote_file.file_id
elif hasattr(remote_file, 'id'):
    file_id = remote_file.id
else:
    file_id = str(remote_file)

print(f"   文件ID: {file_id}")

# 2. 创建分享链接（永久有效，无密码）
print(f"🔗 正在创建分享链接...")
share = ali.share_file(
    file_id=file_id,
    share_pwd=None,
    expiration=''
)

# 获取分享ID构建链接
share_id = None
if hasattr(share, 'share_id'):
    share_id = share.share_id
elif hasattr(share, 'id'):
    share_id = share.id
else:
    share_id = str(share) if share else None

if share_id and share_id != 'None':
    share_url = f"https://www.aliyundrive.com/s/{share_id}"
    print(f"✅ 分享链接创建成功")
    print(f"🔗 链接: {share_url}")
else:
    print(f"⚠️ 分享创建失败，返回对象: {share}")
    share_url = None

# 3. 输出结果供通知使用
github_env = os.environ.get('GITHUB_ENV')
if github_env and share_url:
    with open(github_env, 'a') as f:
        f.write(f"SHARE_LINK={share_url}\n")
        f.write(f"REMOTE_FILE_ID={file_id}\n")

print("=" * 50)
print("脚本版本: v2.0 - 修复分享链接问题")
if share_url:
    print(f"✅ 文件 {file_name} 处理完成")
    print(f"🔗 分享链接: {share_url}")
else:
    print(f"⚠️ 文件 {file_name} 上传完成，但分享链接创建失败")
print("=" * 50)

sys.exit(0)
