"""
用户认证 API
"""
from flask import Blueprint, jsonify, request
from utils.database import get_db
from utils.auth import require_super_admin, require_auth, get_current_user
import hashlib
import secrets

bp = Blueprint('auth', __name__, url_prefix='/api/auth')


def hash_password(password):
    """哈希密码"""
    return hashlib.sha256(password.encode()).hexdigest()


def generate_token():
    """生成认证令牌"""
    return secrets.token_urlsafe(32)


@bp.route('/register', methods=['POST'])
def register():
    """用户注册"""
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '')
        display_name = data.get('display_name', '').strip() or username
        department = data.get('department', '').strip()

        if not username or not password:
            return jsonify({'success': False, 'message': '用户名和密码不能为空'}), 400
        if len(password) < 6:
            return jsonify({'success': False, 'message': '密码长度不能少于6位'}), 400

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM users WHERE username=?', (username,))
        if cursor.fetchone():
            conn.close()
            return jsonify({'success': False, 'message': '用户已存在'}), 400

        hashed_password = hash_password(password)
        token = generate_token()

        # 第一个注册的用户自动成为超级管理员
        cursor.execute('SELECT COUNT(*) as cnt FROM users')
        is_first = cursor.fetchone()['cnt'] == 0
        role = 'admin' if is_first else 'user'
        is_super_admin = 1 if is_first else 0

        cursor.execute(
            '''INSERT INTO users (username, password, role, token, display_name, department, is_super_admin)
               VALUES (?, ?, ?, ?, ?, ?, ?)''',
            (username, hashed_password, role, token, display_name, department, is_super_admin)
        )
        user_id = cursor.lastrowid

        cursor.execute(
            '''INSERT INTO audit_logs (user_id, action, resource_type, resource_id, details)
               VALUES (?, ?, ?, ?, ?)''',
            (user_id, 'register', 'users', user_id, f'用户注册: {username} (角色: {role}, 超级管理员: {bool(is_super_admin)})')
        )

        conn.commit()
        conn.close()

        return jsonify({
            'success': True,
            'message': '注册成功' + ('（首个用户，已设为超级管理员）' if is_first else ''),
            'user_id': user_id,
            'token': token,
            'role': role,
            'is_super_admin': bool(is_super_admin),
            'username': username
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'注册失败: {str(e)}'}), 500


@bp.route('/login', methods=['POST'])
def login():
    """用户登录"""
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '')

        if not username or not password:
            return jsonify({'success': False, 'message': '用户名和密码不能为空'}), 400

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username=?', (username,))
        user = cursor.fetchone()

        if not user or user['password'] != hash_password(password):
            conn.close()
            return jsonify({'success': False, 'message': '用户名或密码错误'}), 401

        token = generate_token()
        cursor.execute('UPDATE users SET token=? WHERE id=?', (token, user['id']))

        cursor.execute(
            '''INSERT INTO audit_logs (user_id, action, resource_type, resource_id, details)
               VALUES (?, ?, ?, ?, ?)''',
            (user['id'], 'login', 'users', user['id'], f'用户登录: {username}')
        )

        conn.commit()
        conn.close()

        return jsonify({
            'success': True,
            'message': '登录成功',
            'user_id': user['id'],
            'token': token,
            'role': user['role'],
            'is_super_admin': bool(user['is_super_admin']) if user['is_super_admin'] is not None else False,
            'username': user['username']
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'登录失败: {str(e)}'}), 500


@bp.route('/profile', methods=['GET'])
@require_auth
def get_profile():
    """获取当前用户信息"""
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'message': '未授权'}), 401
    user_copy = dict(user)
    user_copy.pop('password', None)
    return jsonify({'success': True, 'user': user_copy})


@bp.route('/users', methods=['GET'])
@require_super_admin
def list_users():
    """获取用户列表（仅超级管理员）"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        '''SELECT id, username, display_name, role, department, created_at, is_super_admin
           FROM users ORDER BY created_at'''
    )
    users = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify({'users': users})


@bp.route('/users/<int:uid>/role', methods=['PUT'])
@require_super_admin
def update_user_role(uid):
    """更新用户角色（仅超级管理员）"""
    try:
        data = request.get_json()
        new_role = data.get('role')
        if new_role not in ('admin', 'user'):
            return jsonify({'success': False, 'message': '无效角色'}), 400

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET role=? WHERE id=?', (new_role, uid))
        if cursor.rowcount == 0:
            conn.close()
            return jsonify({'success': False, 'message': '用户不存在'}), 404

        admin_id = request.headers.get('X-User-ID')
        cursor.execute(
            '''INSERT INTO audit_logs (user_id, action, resource_type, resource_id, details)
               VALUES (?, ?, ?, ?, ?)''',
            (admin_id, 'update_role', 'users', uid, f'角色变更为: {new_role}')
        )
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': f'用户角色已更新为: {new_role}'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
