#!/usr/bin/env python3
"""
简单的 API 测试脚本
"""
import requests
import json

BASE_URL = 'http://localhost:5000'

def test_api():
    print("=== 测试 KTY04 管理系统 API ===\n")
    
    # 1. 健康检查
    print("1. 测试健康检查...")
    try:
        response = requests.get(f'{BASE_URL}/api/health')
        print(f"   状态码: {response.status_code}")
        print(f"   响应: {response.json()}\n")
    except Exception as e:
        print(f"   ✗ 失败: {e}\n")
        return
    
    # 2. 获取群组列表
    print("2. 测试获取群组列表...")
    try:
        response = requests.get(f'{BASE_URL}/api/groups')
        print(f"   状态码: {response.status_code}")
        data = response.json()
        print(f"   群组数量: {len(data.get('groups', []))}")
        if data.get('groups'):
            print(f"   群组: {json.dumps(data['groups'], indent=2, ensure_ascii=False)}")
        print()
    except Exception as e:
        print(f"   ✗ 失败: {e}\n")
    
    # 3. 获取成员列表
    print("3. 测试获取成员列表...")
    try:
        response = requests.get(f'{BASE_URL}/api/members')
        print(f"   状态码: {response.status_code}")
        data = response.json()
        print(f"   成员数量: {len(data.get('members', []))}\n")
    except Exception as e:
        print(f"   ✗ 失败: {e}\n")
    
    # 4. 获取签名列表
    print("4. 测试获取签名列表...")
    try:
        response = requests.get(f'{BASE_URL}/api/signatures')
        print(f"   状态码: {response.status_code}")
        data = response.json()
        print(f"   签名数量: {len(data.get('signatures', []))}\n")
    except Exception as e:
        print(f"   ✗ 失败: {e}\n")
    
    print("=== 测试完成 ===")
    print("\n提示: 如果所有 API 都返回空数组，这是正常的（数据库为空）")
    print("     请通过 Web 界面创建群组、添加成员和签名来测试完整功能")

if __name__ == '__main__':
    test_api()
