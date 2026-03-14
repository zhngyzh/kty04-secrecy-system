"""
涉密文件管理 API
"""
from flask import Blueprint, jsonify, request
from utils.database import get_db
from utils.key_manager import KeyManager
from utils.auth import require_admin, require_auth, get_current_user, ROLE_ADMIN
from pygroupsig import groupsig, constants
import hashlib

bp = Blueprint('documents', __name__, url_prefix='/api/documents')
key_manager = KeyManager()

UINT_MAX = 2**32 - 1


def _gen_doc_number():
    """生成文件编号"""
    import datetime
    conn = get_db()
    cursor = conn.cursor()
    today = datetime.date.today().strftime('%Y%m%d')
    cursor.execute(
        "SELECT COUNT(*) as cnt FROM documents WHERE doc_number LIKE ?",
        (f'DOC-{today}-%',)
    )
    seq = cursor.fetchone()['cnt'] + 1
    conn.close()
    return f'DOC-{today}-{seq:03d}'


@bp.route('', methods=['GET'])
@require_auth
def list_documents():
    """获取涉密文件列表（非管理员仅可查看所属群组的文件）"""
    group_id = request.args.get('group_id', type=int)
    status = request.args.get('status')

    user = get_current_user()
    conn = get_db()
    cursor = conn.cursor()

    sql = '''SELECT d.*, g.name as group_name, u.username as creator_name,
                    (SELECT COUNT(*) FROM signatures s WHERE s.document_id=d.id) as sig_count
             FROM documents d
             LEFT JOIN groups g ON d.group_id = g.id
             LEFT JOIN users u ON d.created_by = u.id
             WHERE 1=1'''
    params = []

    # 非管理员只能查看所属群组的文件
    if user and user.get('role') != ROLE_ADMIN:
        sql += ' AND d.group_id IN (SELECT group_id FROM members WHERE user_id=?)'
        params.append(user['id'])

    if group_id:
        sql += ' AND d.group_id=?'
        params.append(group_id)
    if status:
        sql += ' AND d.status=?'
        params.append(status)

    sql += ' ORDER BY d.created_at DESC'
    cursor.execute(sql, params)
    documents = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify({'documents': documents})


@bp.route('', methods=['POST'])
@require_admin
def create_document():
    """创建涉密文件（仅管理员）"""
    try:
        data = request.get_json()
        title = data.get('title', '').strip()
        content = data.get('content', '').strip()
        classification_level = data.get('classification_level', '秘密')
        group_id = data.get('group_id')

        if not title or not content or not group_id:
            return jsonify({'success': False, 'message': '标题、内容和群组不能为空'}), 400

        if classification_level not in ('秘密', '机密', '绝密'):
            return jsonify({'success': False, 'message': '无效的密级'}), 400

        user_id = request.headers.get('X-User-ID')
        doc_number = _gen_doc_number()

        conn = get_db()
        cursor = conn.cursor()

        # 检查群组是否存在
        cursor.execute('SELECT id FROM groups WHERE id=?', (group_id,))
        if not cursor.fetchone():
            conn.close()
            return jsonify({'success': False, 'message': '群组不存在'}), 404

        cursor.execute(
            '''INSERT INTO documents (title, doc_number, content, classification_level,
                                      status, group_id, created_by)
               VALUES (?, ?, ?, ?, 'pending', ?, ?)''',
            (title, doc_number, content, classification_level, group_id, user_id)
        )
        doc_id = cursor.lastrowid

        cursor.execute(
            '''INSERT INTO audit_logs (user_id, action, resource_type, resource_id, details)
               VALUES (?, ?, ?, ?, ?)''',
            (user_id, 'create_document', 'documents', doc_id,
             f'创建涉密文件: {title} [{classification_level}]')
        )

        conn.commit()
        conn.close()

        return jsonify({
            'success': True,
            'message': '文件创建成功',
            'document_id': doc_id,
            'doc_number': doc_number
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'创建失败: {str(e)}'}), 500


@bp.route('/<int:doc_id>', methods=['GET'])
@require_auth
def get_document(doc_id):
    """获取文件详情（含签名列表，非管理员需为所属群组成员）"""
    user = get_current_user()
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        '''SELECT d.*, g.name as group_name, u.username as creator_name
           FROM documents d
           LEFT JOIN groups g ON d.group_id = g.id
           LEFT JOIN users u ON d.created_by = u.id
           WHERE d.id=?''',
        (doc_id,)
    )
    doc = cursor.fetchone()
    if not doc:
        conn.close()
        return jsonify({'success': False, 'message': '文件不存在'}), 404

    # 非管理员需为所属群组成员才能查看
    if user and user.get('role') != ROLE_ADMIN:
        cursor.execute(
            'SELECT COUNT(*) as cnt FROM members WHERE user_id=? AND group_id=?',
            (user['id'], doc['group_id'])
        )
        if cursor.fetchone()['cnt'] == 0:
            conn.close()
            return jsonify({'success': False, 'message': '无权访问该群组的文件'}), 403

    # 获取文件关联的签名
    cursor.execute(
        '''SELECT s.id, s.created_at, s.verified, s.opened, s.signer_index,
                  s.signer_name, s.message
           FROM signatures s
           WHERE s.document_id=?
           ORDER BY s.created_at''',
        (doc_id,)
    )
    sigs = [dict(row) for row in cursor.fetchall()]
    conn.close()

    doc_dict = dict(doc)
    doc_dict['signatures'] = sigs
    return jsonify({'success': True, 'document': doc_dict})


@bp.route('/<int:doc_id>/sign', methods=['POST'])
@require_auth
def sign_document(doc_id):
    """签署涉密文件（群成员匿名签名）"""
    try:
        user = get_current_user()
        if not user:
            return jsonify({'success': False, 'message': '未授权'}), 401

        conn = get_db()
        cursor = conn.cursor()

        # 获取文件信息
        cursor.execute('SELECT * FROM documents WHERE id=?', (doc_id,))
        doc = cursor.fetchone()
        if not doc:
            conn.close()
            return jsonify({'success': False, 'message': '文件不存在'}), 404

        if doc['status'] == 'archived':
            conn.close()
            return jsonify({'success': False, 'message': '已归档的文件不能签署'}), 400

        # 查找用户在该群组中的成员身份
        cursor.execute(
            'SELECT * FROM members WHERE user_id=? AND group_id=?',
            (user['id'], doc['group_id'])
        )
        member = cursor.fetchone()
        if not member:
            conn.close()
            return jsonify({'success': False, 'message': '您不是该文件所属群组的成员'}), 403

        if not member['memkey_path']:
            conn.close()
            return jsonify({'success': False, 'message': '成员密钥不存在，请联系管理员'}), 403

        # 检查是否已签署
        cursor.execute(
            'SELECT id FROM signatures WHERE document_id=? AND member_id=?',
            (doc_id, member['id'])
        )
        if cursor.fetchone():
            conn.close()
            return jsonify({'success': False, 'message': '您已签署过该文件'}), 400

        # 初始化方案并签名
        key_manager.init_scheme()
        grpkey_obj, _, _ = key_manager.load_group_keys(doc['group_id'])
        memkey_obj = key_manager.load_member_key(doc['group_id'], member['id'])

        # 构造签名消息：文件编号 + 标题 + 内容哈希
        content_hash = hashlib.sha256(doc['content'].encode()).hexdigest()[:16]
        sign_message = f"[签署] 文件#{doc['id']} {doc['doc_number']} {doc['title']} 摘要:{content_hash}"

        sig_obj = groupsig.sign(sign_message, memkey_obj, grpkey_obj, UINT_MAX)
        sig_data = key_manager.save_signature(sig_obj, sign_message)

        # 保存签名
        cursor.execute(
            '''INSERT INTO signatures (group_id, member_id, document_id, message, signature_data)
               VALUES (?, ?, ?, ?, ?)''',
            (doc['group_id'], member['id'], doc_id, sign_message, sig_data)
        )
        sig_id = cursor.lastrowid

        # 更新文件状态
        if doc['status'] == 'pending':
            cursor.execute(
                "UPDATE documents SET status='signed', updated_at=CURRENT_TIMESTAMP WHERE id=?",
                (doc_id,)
            )

        # 审计日志
        cursor.execute(
            '''INSERT INTO audit_logs (user_id, action, resource_type, resource_id, details)
               VALUES (?, ?, ?, ?, ?)''',
            (user['id'], 'sign_document', 'documents', doc_id,
             f'匿名签署文件: {doc["title"]}')
        )

        conn.commit()
        conn.close()
        key_manager.clear_scheme()

        return jsonify({
            'success': True,
            'message': '文件签署成功（群签名，身份匿名）',
            'signature_id': sig_id
        })
    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'message': f'签署失败: {str(e)}',
            'traceback': traceback.format_exc()
        }), 500


@bp.route('/<int:doc_id>/verify', methods=['POST'])
@require_auth
def verify_document(doc_id):
    """验证文件上所有签名"""
    try:
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM documents WHERE id=?', (doc_id,))
        doc = cursor.fetchone()
        if not doc:
            conn.close()
            return jsonify({'success': False, 'message': '文件不存在'}), 404

        cursor.execute(
            'SELECT * FROM signatures WHERE document_id=?', (doc_id,)
        )
        sigs = cursor.fetchall()
        if not sigs:
            conn.close()
            return jsonify({'success': False, 'message': '该文件暂无签名'}), 400

        key_manager.init_scheme()
        grpkey_obj, _, _ = key_manager.load_group_keys(doc['group_id'])

        results = []
        all_valid = True
        for sig_record in sigs:
            sig_obj = key_manager.load_signature(sig_record['signature_data'])
            is_valid = groupsig.verify(sig_obj, sig_record['message'], grpkey_obj)
            cursor.execute(
                'UPDATE signatures SET verified=? WHERE id=?',
                (1 if is_valid else 0, sig_record['id'])
            )
            results.append({'sig_id': sig_record['id'], 'valid': is_valid})
            if not is_valid:
                all_valid = False

        # 更新文件状态
        if all_valid and doc['status'] == 'signed':
            cursor.execute(
                "UPDATE documents SET status='verified', updated_at=CURRENT_TIMESTAMP WHERE id=?",
                (doc_id,)
            )

        user_id = request.headers.get('X-User-ID')
        cursor.execute(
            '''INSERT INTO audit_logs (user_id, action, resource_type, resource_id, details)
               VALUES (?, ?, ?, ?, ?)''',
            (user_id, 'verify_document', 'documents', doc_id,
             f'验证文件签名: {len(results)}个签名, 全部有效={all_valid}')
        )

        conn.commit()
        conn.close()
        key_manager.clear_scheme()

        return jsonify({
            'success': True,
            'all_valid': all_valid,
            'results': results,
            'message': '所有签名验证通过' if all_valid else '部分签名验证失败'
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'验证失败: {str(e)}'}), 500


@bp.route('/<int:doc_id>/signatures/<int:sig_id>/trace', methods=['POST'])
@require_admin
def trace_document_signature(doc_id, sig_id):
    """追踪文件签名者真实身份（仅管理员，核心功能）"""
    try:
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute(
            'SELECT * FROM signatures WHERE id=? AND document_id=?',
            (sig_id, doc_id)
        )
        sig_record = cursor.fetchone()
        if not sig_record:
            conn.close()
            return jsonify({'success': False, 'message': '签名记录不存在'}), 404

        if sig_record['opened']:
            conn.close()
            return jsonify({
                'success': True,
                'message': '该签名已被追踪过',
                'signer_name': sig_record['signer_name'],
                'signer_index': sig_record['signer_index']
            })

        key_manager.init_scheme()
        grpkey_obj, mgrkey_obj, gml_obj = key_manager.load_group_keys(sig_record['group_id'])
        sig_obj = key_manager.load_signature(sig_record['signature_data'])

        # 核心操作：打开群签名，揭示签名者身份
        gsopen = groupsig.open(sig_obj, mgrkey_obj, grpkey_obj, gml=gml_obj)
        signer_index = gsopen.get('index')

        # 通过 GML 索引映射到成员
        cursor.execute(
            'SELECT * FROM members WHERE group_id=? AND gml_index=?',
            (sig_record['group_id'], signer_index)
        )
        member = cursor.fetchone()
        signer_name = member['name'] if member else f'未知成员 (索引: {signer_index})'

        # 更新签名记录
        cursor.execute(
            'UPDATE signatures SET opened=1, signer_index=?, signer_name=? WHERE id=?',
            (signer_index, signer_name, sig_id)
        )

        admin_id = request.headers.get('X-User-ID')
        cursor.execute(
            '''INSERT INTO audit_logs (user_id, action, resource_type, resource_id, details)
               VALUES (?, ?, ?, ?, ?)''',
            (admin_id, 'trace_signature', 'signatures', sig_id,
             f'追踪签名者身份: {signer_name} (GML索引: {signer_index})')
        )

        conn.commit()
        conn.close()
        key_manager.clear_scheme()

        return jsonify({
            'success': True,
            'message': f'追踪成功，签名者: {signer_name}',
            'signer_name': signer_name,
            'signer_index': signer_index
        })
    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'message': f'追踪失败: {str(e)}',
            'traceback': traceback.format_exc()
        }), 500


@bp.route('/<int:doc_id>/status', methods=['PUT'])
@require_admin
def update_document_status(doc_id):
    """更新文件状态（仅管理员）"""
    try:
        data = request.get_json()
        new_status = data.get('status')
        valid_statuses = ('pending', 'signed', 'verified', 'archived')
        if new_status not in valid_statuses:
            return jsonify({'success': False, 'message': f'无效状态，可选: {valid_statuses}'}), 400

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE documents SET status=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (new_status, doc_id)
        )
        if cursor.rowcount == 0:
            conn.close()
            return jsonify({'success': False, 'message': '文件不存在'}), 404

        admin_id = request.headers.get('X-User-ID')
        cursor.execute(
            '''INSERT INTO audit_logs (user_id, action, resource_type, resource_id, details)
               VALUES (?, ?, ?, ?, ?)''',
            (admin_id, 'update_doc_status', 'documents', doc_id, f'状态变更为: {new_status}')
        )

        conn.commit()
        conn.close()

        return jsonify({'success': True, 'message': f'文件状态已更新为: {new_status}'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'更新失败: {str(e)}'}), 500
