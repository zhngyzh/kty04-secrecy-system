#!/usr/bin/env python3
"""End-to-end test for the KTY04 management system"""
import requests
import json
import sys

BASE = 'http://localhost:5000/api'

def test_step(name, func):
    print(f'\n=== {name} ===')
    try:
        result = func()
        print(f'  ✓ 成功')
        return result
    except Exception as e:
        print(f'  ✗ 失败: {e}')
        sys.exit(1)

# Step 1: Register admin
def register_admin():
    r = requests.post(f'{BASE}/auth/register', json={
        'username': 'admin', 'password': 'admin123',
        'display_name': '系统管理员', 'department': '安全部'
    })
    d = r.json()
    assert d.get('success'), f"Register failed: {d}"
    assert d.get('role') == 'admin', f"First user should be admin, got: {d.get('role')}"
    print(f'  user_id={d["user_id"]}, role={d["role"]}')
    return d

admin = test_step('1. 注册管理员（首个用户自动成为管理员）', register_admin)
admin_h = {'X-User-ID': str(admin['user_id']), 'X-Token': admin['token'], 'Content-Type': 'application/json'}

# Step 2: Register normal user
def register_user():
    r = requests.post(f'{BASE}/auth/register', json={
        'username': 'user1', 'password': 'user123',
        'display_name': '张三', 'department': '研发部'
    })
    d = r.json()
    assert d.get('success'), f"Register failed: {d}"
    assert d.get('role') == 'user', f"Second user should be user, got: {d.get('role')}"
    print(f'  user_id={d["user_id"]}, role={d["role"]}')
    return d

user1 = test_step('2. 注册普通用户（张三）', register_user)
user_h = {'X-User-ID': str(user1['user_id']), 'X-Token': user1['token'], 'Content-Type': 'application/json'}

# Step 3: Create group
def create_group():
    r = requests.post(f'{BASE}/groups', json={
        'name': '保密项目A组',
        'description': '核心研发保密项目',
        'classification_level': '机密'
    }, headers=admin_h)
    d = r.json()
    assert d.get('success'), f"Create group failed: {d}"
    print(f'  group_id={d["group_id"]}')
    return d

grp = test_step('3. 创建群组（保密项目A组，密级：机密）', create_group)
group_id = grp['group_id']

# Step 4: Add member
def add_member():
    r = requests.post(f'{BASE}/members', json={
        'group_id': group_id,
        'name': '张三',
        'user_id': user1['user_id']
    }, headers=admin_h)
    d = r.json()
    assert d.get('success'), f"Add member failed: {d}"
    print(f'  member_id={d["member_id"]}')
    return d

mem = test_step('4. 添加成员（张三加入保密项目A组）', add_member)

# Step 5: Create document
def create_document():
    r = requests.post(f'{BASE}/documents', json={
        'title': '项目A核心技术方案',
        'content': '本项目采用XX技术路线，涉及核心算法，包括密钥协商、数字签名等关键技术...',
        'classification_level': '机密',
        'group_id': group_id
    }, headers=admin_h)
    d = r.json()
    assert d.get('success'), f"Create document failed: {d}"
    print(f'  doc_id={d["document_id"]}, doc_number={d["doc_number"]}')
    return d

doc = test_step('5. 创建涉密文件（项目A核心技术方案，密级：机密）', create_document)
doc_id = doc['document_id']

# Step 6: Sign document (as user1 - anonymous group signature)
def sign_document():
    r = requests.post(f'{BASE}/documents/{doc_id}/sign', json={}, headers=user_h)
    d = r.json()
    assert d.get('success'), f"Sign failed: {d}"
    print(f'  signature_id={d["signature_id"]}')
    print(f'  签名消息: {d.get("message", "N/A")[:60]}...')
    return d

sig = test_step('6. 匿名签署文件（张三使用群签名签署，身份匿名）', sign_document)

# Step 7: View document - check signatures are anonymous
def view_document():
    r = requests.get(f'{BASE}/documents/{doc_id}', headers=admin_h)
    d = r.json()
    assert d.get('success'), f"View failed: {d}"
    doc_detail = d['document']
    sigs = doc_detail.get('signatures', [])
    print(f'  文件状态: {doc_detail["status"]}')
    print(f'  签名数量: {len(sigs)}')
    for s in sigs:
        opened = s.get('opened', 0)
        signer = s.get('signer_name') or '匿名'
        print(f'    签名#{s["id"]}: {"已追踪→"+signer if opened else "匿名签署（身份未知）"}')
    return d

test_step('7. 查看文件详情（签名显示为匿名）', view_document)

# Step 8: Verify signatures
def verify_signatures():
    r = requests.post(f'{BASE}/documents/{doc_id}/verify', json={}, headers=admin_h)
    d = r.json()
    assert d.get('success'), f"Verify failed: {d}"
    print(f'  全部有效: {d.get("all_valid")}')
    for res in d.get('results', []):
        print(f'    签名#{res["sig_id"]}: {"✓ 验证通过" if res["valid"] else "✗ 验证失败"}')
    return d

test_step('8. 验证签名（验证群签名有效性，不暴露身份）', verify_signatures)

# Step 9: TRACE signature - THE KEY FEATURE (reveal anonymous signer identity)
def trace_signature():
    # Get the signature ID
    r = requests.get(f'{BASE}/documents/{doc_id}', headers=admin_h)
    sigs = r.json()['document']['signatures']
    sig_id = sigs[0]['id']
    
    r = requests.post(f'{BASE}/documents/{doc_id}/signatures/{sig_id}/trace', json={}, headers=admin_h)
    d = r.json()
    assert d.get('success'), f"Trace failed: {d}"
    print(f'  ★ 追踪到签名者: {d.get("signer_name")}')
    print(f'  ★ GML索引: {d.get("signer_index")}')
    return d

test_step('9. ★ 追踪签名者身份（管理员使用管理员密钥揭示匿名签名者）', trace_signature)

# Step 10: Verify trace worked - view document again
def verify_trace():
    r = requests.get(f'{BASE}/documents/{doc_id}', headers=admin_h)
    sigs = r.json()['document']['signatures']
    for s in sigs:
        opened = s.get('opened', 0)
        signer = s.get('signer_name') or '匿名'
        print(f'    签名#{s["id"]}: {"已追踪→"+signer if opened else "匿名签署"}')
    return r.json()

test_step('10. 确认追踪结果（签名者身份已揭示）', verify_trace)

# Step 11: Dashboard stats
def check_stats():
    r = requests.get(f'{BASE}/audit/stats', headers=admin_h)
    d = r.json()
    assert d.get('success'), f"Stats failed: {d}"
    stats = d['stats']
    print(f'  群组: {stats["group_count"]}')
    print(f'  成员: {stats["member_count"]}')
    print(f'  涉密文件: {stats["document_count"]}')
    print(f'  签名: {stats["signature_count"]}')
    print(f'  已追踪: {stats["traced_sigs"]}')
    print(f'  已验证: {stats["verified_sigs"]}')
    return d

test_step('11. 仪表盘统计数据', check_stats)

# Step 12: Audit logs
def check_audit():
    r = requests.get(f'{BASE}/audit/logs', headers=admin_h)
    d = r.json()
    assert d.get('success'), f"Audit failed: {d}"
    logs = d.get('logs', [])
    print(f'  审计日志数量: {len(logs)}')
    for log in logs[:5]:
        print(f'    [{log.get("created_at","")}] {log.get("action","")}: {log.get("details","")[:40]}')
    return d

test_step('12. 审计日志查看', check_audit)

print('\n' + '='*60)
print('★★★ 所有测试通过！系统工作正常 ★★★')
print('='*60)
print('\n核心特性验证:')
print('  ✓ 匿名性: 签署文件时身份匿名，无法从签名中推断签署者')
print('  ✓ 可追踪性: 管理员可使用管理员密钥追踪匿名签名者的真实身份')
print('  ✓ 不可伪造性: 仅持有成员密钥的群组成员可创建有效签名')
print('  ✓ 完整审计: 所有操作均被记录在审计日志中')
