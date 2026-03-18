"""
审计日志 API
"""
from flask import Blueprint, jsonify, request
from utils.database import get_db
from utils.auth import require_super_admin, require_auth, get_current_user

bp = Blueprint('audit', __name__, url_prefix='/api/audit')


@bp.route('/logs', methods=['GET'])
@require_super_admin
def list_logs():
    """获取审计日志列表（仅超级管理员）"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    action = request.args.get('action')
    per_page = min(per_page, 100)
    offset = (page - 1) * per_page

    conn = get_db()
    cursor = conn.cursor()

    sql = '''SELECT a.*, u.username
             FROM audit_logs a
             LEFT JOIN users u ON a.user_id = u.id
             WHERE 1=1'''
    count_sql = 'SELECT COUNT(*) as total FROM audit_logs a WHERE 1=1'
    params = []
    count_params = []

    if action:
        sql += ' AND a.action=?'
        count_sql += ' AND a.action=?'
        params.append(action)
        count_params.append(action)

    cursor.execute(count_sql, count_params)
    total = cursor.fetchone()['total']

    sql += ' ORDER BY a.created_at DESC LIMIT ? OFFSET ?'
    params.extend([per_page, offset])
    cursor.execute(sql, params)
    logs = [dict(row) for row in cursor.fetchall()]
    conn.close()

    return jsonify({
        'success': True,
        'logs': logs,
        'total': total,
        'page': page,
        'per_page': per_page,
        'total_pages': (total + per_page - 1) // per_page
    })


@bp.route('/stats', methods=['GET'])
@require_auth
def get_stats():
    """获取系统统计数据（仪表盘使用）"""
    user = get_current_user()
    conn = get_db()
    cursor = conn.cursor()

    stats = {}

    if user and user.get('role') != 'admin':
        # 普通涉密人员只返回与自己相关的最小统计集
        cursor.execute(
            '''SELECT COUNT(DISTINCT m.group_id) as cnt
               FROM members m WHERE m.user_id=?''',
            (user['id'],)
        )
        stats['group_count'] = cursor.fetchone()['cnt']

        cursor.execute(
            '''SELECT COUNT(*) as cnt FROM members WHERE user_id=?''',
            (user['id'],)
        )
        stats['member_count'] = cursor.fetchone()['cnt']

        cursor.execute(
            '''SELECT COUNT(DISTINCT s.document_id) as cnt
               FROM signatures s
               JOIN members m ON s.member_id = m.id
               WHERE m.user_id=? AND s.document_id IS NOT NULL''',
            (user['id'],)
        )
        stats['document_count'] = cursor.fetchone()['cnt']

        cursor.execute(
            '''SELECT COUNT(*) as cnt
               FROM signatures s
               JOIN members m ON s.member_id = m.id
               WHERE m.user_id=?''',
            (user['id'],)
        )
        stats['signature_count'] = cursor.fetchone()['cnt']

        stats['pending_docs'] = 0
        stats['traced_sigs'] = 0
        stats['verified_sigs'] = 0
        stats['doc_by_status'] = {}

        cursor.execute(
            '''SELECT a.*, u.username
               FROM audit_logs a
               LEFT JOIN users u ON a.user_id = u.id
               WHERE a.user_id=?
               ORDER BY a.created_at DESC LIMIT 10''',
            (user['id'],)
        )
        stats['recent_activities'] = [dict(row) for row in cursor.fetchall()]

        conn.close()
        return jsonify({'success': True, 'stats': stats})

    cursor.execute('SELECT COUNT(*) as cnt FROM groups')
    stats['group_count'] = cursor.fetchone()['cnt']

    cursor.execute('SELECT COUNT(*) as cnt FROM members')
    stats['member_count'] = cursor.fetchone()['cnt']

    cursor.execute('SELECT COUNT(*) as cnt FROM documents')
    stats['document_count'] = cursor.fetchone()['cnt']

    cursor.execute('SELECT COUNT(*) as cnt FROM signatures')
    stats['signature_count'] = cursor.fetchone()['cnt']

    cursor.execute("SELECT COUNT(*) as cnt FROM documents WHERE status='pending'")
    stats['pending_docs'] = cursor.fetchone()['cnt']

    cursor.execute("SELECT COUNT(*) as cnt FROM signatures WHERE opened=1")
    stats['traced_sigs'] = cursor.fetchone()['cnt']

    cursor.execute("SELECT COUNT(*) as cnt FROM signatures WHERE verified=1")
    stats['verified_sigs'] = cursor.fetchone()['cnt']

    # 最近操作
    cursor.execute(
        '''SELECT a.*, u.username
           FROM audit_logs a
           LEFT JOIN users u ON a.user_id = u.id
           ORDER BY a.created_at DESC LIMIT 10'''
    )
    stats['recent_activities'] = [dict(row) for row in cursor.fetchall()]

    # 各状态文件数
    cursor.execute(
        '''SELECT status, COUNT(*) as cnt FROM documents GROUP BY status'''
    )
    stats['doc_by_status'] = {row['status']: row['cnt'] for row in cursor.fetchall()}

    conn.close()
    return jsonify({'success': True, 'stats': stats})
