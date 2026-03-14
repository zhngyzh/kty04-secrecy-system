"""
认证和权限管理模块
"""
from functools import wraps
from flask import request, jsonify
from utils.database import get_db

# 用户角色常量
ROLE_ADMIN = 'admin'      # 管理员：可以初始化、添加成员、追踪签名
ROLE_USER = 'user'        # 普通用户：只能签名

def get_current_user():
    """从请求头获取当前用户信息"""
    user_id = request.headers.get('X-User-ID')
    token = request.headers.get('X-Token')
    
    if not user_id:
        return None
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE id=? AND token=?', (user_id, token))
    user = cursor.fetchone()
    conn.close()
    
    return dict(user) if user else None

def require_auth(f):
    """要求认证装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = get_current_user()
        if not user:
            return jsonify({
                'success': False,
                'message': '未授权，请先登录'
            }), 401
        return f(*args, **kwargs)
    return decorated_function

def require_admin(f):
    """要求管理员权限装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = get_current_user()
        if not user:
            return jsonify({
                'success': False,
                'message': '未授权，请先登录'
            }), 401
        
        if user['role'] != ROLE_ADMIN:
            return jsonify({
                'success': False,
                'message': '权限不足，需要管理员权限'
            }), 403
        
        return f(*args, **kwargs)
    return decorated_function

def check_user_in_group(user_id, group_id):
    """检查用户是否在指定群组中"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        'SELECT COUNT(*) as count FROM members WHERE user_id=? AND group_id=?',
        (user_id, group_id)
    )
    result = cursor.fetchone()
    conn.close()
    return result['count'] > 0
