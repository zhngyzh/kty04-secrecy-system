"""
群组管理 API
"""
from flask import Blueprint, jsonify, request
from utils.database import get_db
from utils.key_manager import KeyManager
from pygroupsig import groupsig, constants
import os

bp = Blueprint('groups', __name__, url_prefix='/api/groups')
key_manager = KeyManager()

@bp.route('', methods=['GET'])
def list_groups():
    """获取所有群组列表"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM groups ORDER BY created_at DESC')
    groups = []
    for row in cursor.fetchall():
        group = dict(row)
        # 获取成员数量
        cursor.execute('SELECT COUNT(*) as count FROM members WHERE group_id=?', (group['id'],))
        member_count = cursor.fetchone()['count']
        group['member_count'] = member_count
        groups.append(group)
    conn.close()
    return jsonify({'groups': groups})

@bp.route('', methods=['POST'])
def create_group():
    """创建新群组"""
    try:
        data = request.get_json()
        group_name = data.get('name', '未命名群组')
        
        # 初始化方案
        key_manager.init_scheme()
        
        # 创建群组
        group = groupsig.setup(constants.KTY04_CODE)
        grpkey_obj = group['grpkey']
        mgrkey_obj = group['mgrkey']
        gml_obj = group['gml']
        
        # 保存到数据库
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO groups (name) VALUES (?)',
            (group_name,)
        )
        group_id = cursor.lastrowid
        
        # 保存密钥
        key_paths = key_manager.save_group_keys(
            group_id, grpkey_obj, mgrkey_obj, gml_obj
        )
        
        # 更新数据库
        cursor.execute(
            '''UPDATE groups SET grpkey_path=?, mgrkey_path=?, gml_path=?
               WHERE id=?''',
            (key_paths['grpkey_path'], key_paths['mgrkey_path'],
             key_paths['gml_path'], group_id)
        )
        conn.commit()
        conn.close()
        
        # 清理
        key_manager.clear_scheme()
        
        return jsonify({
            'success': True,
            'message': '群组创建成功',
            'group_id': group_id,
            'name': group_name
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'创建群组失败: {str(e)}'
        }), 500

@bp.route('/<int:group_id>', methods=['GET'])
def get_group(group_id):
    """获取群组详情"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM groups WHERE id=?', (group_id,))
    group = cursor.fetchone()
    conn.close()
    
    if not group:
        return jsonify({'success': False, 'message': '群组不存在'}), 404
    
    # 获取成员数量
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) as count FROM members WHERE group_id=?', (group_id,))
    member_count = cursor.fetchone()['count']
    conn.close()
    
    group_dict = dict(group)
    group_dict['member_count'] = member_count
    
    return jsonify({'group': group_dict})
