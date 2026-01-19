"""
成员管理 API
"""
from flask import Blueprint, jsonify, request
from utils.database import get_db
from utils.key_manager import KeyManager
from pygroupsig import groupsig, constants, memkey
from base64 import b64encode

bp = Blueprint('members', __name__, url_prefix='/api/members')
key_manager = KeyManager()

@bp.route('', methods=['GET'])
def list_members():
    """获取成员列表"""
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
def add_member():
    """添加新成员"""
    try:
        data = request.get_json()
        group_id = data.get('group_id')
        member_name = data.get('name', '未命名成员')
        
        if not group_id:
            return jsonify({
                'success': False,
                'message': '缺少 group_id 参数'
            }), 400
        
        # 初始化方案
        key_manager.init_scheme()
        
        # 加载群组密钥
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT grpkey_path, mgrkey_path, gml_path FROM groups WHERE id=?', (group_id,))
        group_row = cursor.fetchone()
        conn.close()
        
        if not group_row:
            return jsonify({
                'success': False,
                'message': f'群组不存在 (ID: {group_id})'
            }), 404
        
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
        
        # 保存到数据库
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO members (group_id, name) VALUES (?, ?)',
            (group_id, member_name)
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
        
        conn.commit()
        conn.close()
        
        # 清理
        key_manager.clear_scheme()
        
        return jsonify({
            'success': True,
            'message': '成员添加成功',
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
def get_member(member_id):
    """获取成员详情"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM members WHERE id=?', (member_id,))
    member = cursor.fetchone()
    conn.close()
    
    if not member:
        return jsonify({'success': False, 'message': '成员不存在'}), 404
    
    return jsonify({'member': dict(member)})
