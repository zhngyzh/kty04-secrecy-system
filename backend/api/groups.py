"""
群组管理 API
"""
from flask import Blueprint, jsonify, request
from utils.database import get_db
from utils.key_manager import KeyManager
from utils.auth import require_super_admin, require_auth
from pygroupsig import groupsig, constants
import os

bp = Blueprint('groups', __name__, url_prefix='/api/groups')
key_manager = KeyManager()


@bp.route('', methods=['GET'])
@require_auth
def list_groups():
    """获取所有群组列表"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM groups ORDER BY created_at DESC')
    groups = []
    for row in cursor.fetchall():
        group = dict(row)
        cursor.execute('SELECT COUNT(*) as count FROM members WHERE group_id=?', (group['id'],))
        group['member_count'] = cursor.fetchone()['count']
        cursor.execute('SELECT COUNT(*) as count FROM documents WHERE group_id=?', (group['id'],))
        group['doc_count'] = cursor.fetchone()['count']
        groups.append(group)
    conn.close()
    return jsonify({'groups': groups})


@bp.route('', methods=['POST'])
@require_super_admin
def create_group():
    """创建新群组（仅超级管理员）"""
    try:
        data = request.get_json()
        group_name = data.get('name', '未命名群组').strip()
        description = data.get('description', '').strip()
        classification_level = data.get('classification_level', '秘密')

        if not group_name:
            return jsonify({'success': False, 'message': '群组名称不能为空'}), 400

        key_manager.init_scheme()

        group = groupsig.setup(constants.KTY04_CODE)
        grpkey_obj = group['grpkey']
        mgrkey_obj = group['mgrkey']
        gml_obj = group['gml']

        conn = get_db()
        cursor = conn.cursor()
        user_id = request.headers.get('X-User-ID')
        cursor.execute(
            '''INSERT INTO groups (name, description, classification_level, created_by)
               VALUES (?, ?, ?, ?)''',
            (group_name, description, classification_level, user_id)
        )
        group_id = cursor.lastrowid

        key_paths = key_manager.save_group_keys(group_id, grpkey_obj, mgrkey_obj, gml_obj)

        cursor.execute(
            '''UPDATE groups SET grpkey_path=?, mgrkey_path=?, gml_path=? WHERE id=?''',
            (key_paths['grpkey_path'], key_paths['mgrkey_path'],
             key_paths['gml_path'], group_id)
        )

        cursor.execute(
            '''INSERT INTO audit_logs (user_id, action, resource_type, resource_id, details)
               VALUES (?, ?, ?, ?, ?)''',
            (user_id, 'create_group', 'groups', group_id,
             f'创建群组: {group_name} [{classification_level}]')
        )

        conn.commit()
        conn.close()
        key_manager.clear_scheme()

        return jsonify({
            'success': True,
            'message': '群组创建成功',
            'group_id': group_id,
            'name': group_name
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'创建群组失败: {str(e)}'}), 500


@bp.route('/<int:group_id>', methods=['GET'])
@require_auth
def get_group(group_id):
    """获取群组详情（含成员列表）"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM groups WHERE id=?', (group_id,))
    group = cursor.fetchone()
    if not group:
        conn.close()
        return jsonify({'success': False, 'message': '群组不存在'}), 404

    group_dict = dict(group)

    cursor.execute('SELECT COUNT(*) as count FROM members WHERE group_id=?', (group_id,))
    group_dict['member_count'] = cursor.fetchone()['count']

    cursor.execute(
        '''SELECT m.*, u.username FROM members m
           LEFT JOIN users u ON m.user_id = u.id
           WHERE m.group_id=? ORDER BY m.created_at''',
        (group_id,)
    )
    group_dict['members'] = [dict(row) for row in cursor.fetchall()]

    cursor.execute('SELECT COUNT(*) as count FROM documents WHERE group_id=?', (group_id,))
    group_dict['doc_count'] = cursor.fetchone()['count']

    conn.close()
    return jsonify({'group': group_dict})
