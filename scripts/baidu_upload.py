#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
百度网盘自动上传并分享脚本
"""

import os
import sys
import json
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


def get_file_fsid(dir_path, filename, access_token):
    """通过列出目录获取文件的 fs_id"""
    print(f"🔍 正在获取文件 fs_id...")
    
    list_url = "https://pan.baidu.com/rest/2.0/xpan/file"
    params = {
        "method": "list",
        "access_token": access_token,
        "dir": dir_path,
        "web": "1"
    }
    
    try:
        resp = requests.get(list_url, params=params, timeout=15)
        if resp.status_code != 200:
            print(f"⚠️ 获取文件列表失败: HTTP {resp.status_code}")
            print(f"   响应: {resp.text[:500]}")
            return None
        
        result = resp.json()
        if result.get('errno') != 0:
            print(f"⚠️ 列表API返回错误: {result}")
            return None
        
        file_list = result.get('list', [])
        for f in file_list:
            if f.get('server_filename') == filename:
                fs_id = f.get('fs_id')
                print(f"✅ 找到 fs_id: {fs_id}")
                return fs_id
        
        print(f"⚠️ 在列表中未找到文件: {filename}")
        print(f"   目录中共有 {len(file_list)} 个文件")
        return None
        
    except Exception as e:
        print(f"⚠️ 获取fs_id异常: {e}")
        return None


def create_share_link(file_path, access_token, fs_id=None):
    """创建分享链接 - 使用官方新版 apaas API"""
    
    print(f"🔗 正在创建分享链接...")
    print(f"   使用端点: /apaas/1.0/share/set (新版)")
    
    # 如果没有传入 fs_id，先获取
    if fs_id is None:
        dir_path = os.path.dirname(file_path)
        filename = os.path.basename(file_path)
        fs_id = get_file_fsid(dir_path if dir_path else "/apps/autobackup", filename, access_token)
    
    if fs_id is None:
        print(f"❌ 无法获取文件 fs_id，无法创建分享")
        return None
    
    # ====== 新版 api: /apaas/1.0/share/set ======
    # 文档: https://pan.baidu.com/union/doc/Tlaaocmkj
    share_url = "https://pan.baidu.com/apaas/1.0/share/set"
    
    # access_token / appid / product 必须放 URL query 中
    query_params = {
        "access_token": access_token,
        "appid": BAIDU_APP_KEY,
        "product": "netdisk",
    }
    
    # Body 用 multipart/form-data 格式
    # fsid_list: fs_id 列表的 JSON 数组字符串
    # pwd: 必填，4位（数字+小写字母），这里用固定值 "abcd"
    # period: 有效期（天），7=7天
    form_data = {
        "fsid_list": json.dumps([str(fs_id)]),
        "period": "7",
        "pwd": "abcd",
        "remark": "auto_backup_share",
    }
    
    try:
        resp = requests.post(
            share_url,
            params=query_params,
            data=form_data,
            timeout=15
        )
        print(f"   HTTP状态: {resp.status_code}")
        
        # 尝试解析 JSON
        try:
            result = resp.json()
        except Exception:
            print(f"   ⚠️ 响应非JSON: {resp.text[:500]}")
            return None
        
        errno = result.get('errno', -1)
        
        if errno == 0:
            data = result.get('data', {})
            link = data.get('link', '')
            short_url = data.get('short_url', '')
            pwd = data.get('pwd', '')
            
            print(f"✅ 分享链接创建成功!")
            print(f"   链接: {link}")
            if short_url:
                print(f"   短链: {short_url}")
            if pwd:
                print(f"   提取码: {pwd}")
            
            # 返回完整分享信息
            full_link = f"{link} (提取码: {pwd})" if pwd else link
            return link  # 返回短链接或完整链接
        else:
            show_msg = result.get('show_msg', '')
            print(f"❌ 分享失败: errno={errno}, msg={show_msg}")
            print(f"   完整响应: {json.dumps(result, ensure_ascii=False)}")
            
            # 如果是 errno=2，提示可能需要购买分享服务
            if errno == 2:
                print(f"   💡 提示: errno=2 可能表示:")
                print(f"      - 账号未完成实名/手机绑定")
                print(f"      - 应用未开通分享服务（需付费购买）")
                print(f"      - 请访问 https://pan.baidu.com/union/console 检查应用权限")
            return None
            
    except Exception as e:
        print(f"❌ 请求异常: {e}")
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
