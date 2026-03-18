"""
成员管理 API
"""
from flask import Blueprint, jsonify, request
from utils.database import get_db
from utils.key_manager import KeyManager
from utils.auth import require_super_admin
from pygroupsig import groupsig, constants, memkey
from base64 import b64encode

bp = Blueprint('members', __name__, url_prefix='/api/members')
key_manager = KeyManager()

@bp.route('', methods=['GET'])
@require_super_admin
def list_members():
    """获取成员列表（仅超级管理员）"""
    group_id = request.args.get('group_id', type=int)
    
    conn = get_db()
    cursor = conn.cursor()
    
    if group_id:
        cursor.execute(
            'SELECT * FROM members WHERE group_id=? ORDER BY created_at',
            (group_id,)
        )
    else:
        cursor.execute('SELECT * FROM members ORDER BY created_at')
    
    members = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify({'members': members})

@bp.route('', methods=['POST'])
@require_super_admin
def add_member():
    """添加新成员（仅超级管理员）"""
    try:
        data = request.get_json()
        group_id = data.get('group_id')
        member_name = data.get('name', '').strip()
        user_id = data.get('user_id')
        
        if not group_id or not user_id:
            return jsonify({
                'success': False,
                'message': '缺少 group_id 或 user_id 参数'
            }), 400
        
        # 初始化方案
        key_manager.init_scheme()
        
        # 加载群组密钥
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT grpkey_path, mgrkey_path, gml_path FROM groups WHERE id=?', (group_id,))
        group_row = cursor.fetchone()
        
        if not group_row:
            conn.close()
            return jsonify({
                'success': False,
                'message': f'群组不存在 (ID: {group_id})'
            }), 404

        # 检查用户是否已在该群组中
        cursor.execute(
            'SELECT id FROM members WHERE user_id=? AND group_id=?',
            (user_id, group_id)
        )
        if cursor.fetchone():
            conn.close()
            return jsonify({
                'success': False,
                'message': '该用户已是该群组的成员'
            }), 400

        # 若未提供成员名称，使用用户的 username
        if not member_name:
            cursor.execute('SELECT username FROM users WHERE id=?', (user_id,))
            user_row = cursor.fetchone()
            member_name = user_row['username'] if user_row else '未命名成员'
        
        # 加载密钥
        from pygroupsig import grpkey, mgrkey, gml
        import json
        
        # 加载 grpkey
        with open(group_row['grpkey_path'], 'r') as f:
            grpkey_data = json.load(f)['data']
        grpkey_obj = grpkey.grpkey_import(constants.KTY04_CODE, grpkey_data)
        
        # 加载 mgrkey
        with open(group_row['mgrkey_path'], 'r') as f:
            mgrkey_data = json.load(f)['data']
        mgrkey_obj = mgrkey.mgrkey_import(constants.KTY04_CODE, mgrkey_data)
        
        # 尝试加载现有的 GML，如果失败则创建新的
        gml_obj = None
        try:
            with open(group_row['gml_path'], 'r') as f:
                gml_data = json.load(f)['data']
            gml_obj = gml.gml_import(constants.KTY04_CODE, gml_data)
        except:
            # GML 导入失败，创建新的初始 GML
            gml_obj = gml.gml_init(constants.KTY04_CODE)
        
        # 执行 JOIN 协议（KTY04 采用 2 轮）
        # Round 1: 成员生成 msg1 和初始成员密钥
        msg1_result = groupsig.join_mem(0, grpkey_obj)
        msg1 = msg1_result['msgout']
        memkey_tmp = msg1_result['memkey']
        
        # Round 2: 管理员处理 msg1，获取成员密钥数据，更新 GML
        msg2 = groupsig.join_mgr(1, mgrkey_obj, grpkey_obj, gml=gml_obj, msgin=msg1)
        
        # 从 msg2 中提取成员密钥（参考官方测试代码）
        # msg2 是一个 message_t 对象，包含序列化的成员密钥数据
        mekeyb64 = b64encode(
            b''.join([msg2.bytes[idx].to_bytes(1, 'big') for idx in range(msg2.length)])
        )
        memkey_obj = memkey.memkey_import(constants.KTY04_CODE, mekeyb64)
        
        # 计算 GML 索引（成员在群组中的序号）
        cursor.execute('SELECT COUNT(*) as cnt FROM members WHERE group_id=?', (group_id,))
        gml_index = cursor.fetchone()['cnt']

        # 保存到数据库
        cursor.execute(
            'INSERT INTO members (user_id, group_id, name, gml_index) VALUES (?, ?, ?, ?)',
            (user_id, group_id, member_name, gml_index)
        )
        member_id = cursor.lastrowid
        
        # 保存成员密钥
        memkey_path = key_manager.save_member_key(group_id, member_id, memkey_obj)
        cursor.execute(
            'UPDATE members SET memkey_path=? WHERE id=?',
            (memkey_path, member_id)
        )
        
        # 保存更新后的 GML
        key_manager.save_group_keys(group_id, grpkey_obj, mgrkey_obj, gml_obj)
        
        # 记录审计日志
        admin_id = request.headers.get('X-User-ID')
        cursor.execute(
            '''INSERT INTO audit_logs (user_id, action, resource_type, resource_id, details)
               VALUES (?, ?, ?, ?, ?)''',
            (admin_id, 'add_member', 'members', member_id, f'为用户 {member_name} 分配密钥')
        )
        
        conn.commit()
        conn.close()
        
        # 清理
        key_manager.clear_scheme()
        
        return jsonify({
            'success': True,
            'message': '成员添加成功，密钥已分发',
            'member_id': member_id,
            'name': member_name
        })
    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'message': f'添加成员失败: {str(e)}',
            'traceback': traceback.format_exc()
        }), 500

@bp.route('/<int:member_id>', methods=['GET'])
@require_super_admin
def get_member(member_id):
    """获取成员详情（仅超级管理员）"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM members WHERE id=?', (member_id,))
    member = cursor.fetchone()
    conn.close()
    
    if not member:
        return jsonify({'success': False, 'message': '成员不存在'}), 404
    
    return jsonify({'member': dict(member)})
