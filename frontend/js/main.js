/* ========================================================
   涉密文件群签名管理系统 - 前端主逻辑
   ======================================================== */

const API = '/api';

// ── 全局状态 ──
const state = {
    user: null,
    token: null,
    userId: null,
    role: null,
    isSuperAdmin: false,  // 是否为超级管理员
    groups: []       // 缓存群组列表供各处下拉选使用
};

// 超级管理员可访问所有页面，普通管理员只能访问文件和签名
const ROLE_PAGES = {
    super_admin: ['dashboard', 'documents', 'groups', 'members', 'signatures', 'audit', 'admin'],
    admin: ['dashboard', 'documents', 'signatures'],
    user: ['dashboard', 'documents', 'signatures']
};

function getAllowedPages() {
    if (state.role === 'admin' && state.isSuperAdmin) {
        return ROLE_PAGES['super_admin'];
    }
    return ROLE_PAGES[state.role] || ['dashboard', 'documents'];
}

function isPageAllowed(page) {
    return getAllowedPages().includes(page);
}

function applyRoleView() {
    const allowed = getAllowedPages();
    const isAdmin = state.role === 'admin';
    const isSuperAdmin = state.role === 'admin' && state.isSuperAdmin;

    // 控制侧边栏导航项可见性
    document.querySelectorAll('.sidebar-nav li[data-page]').forEach(li => {
        const page = li.getAttribute('data-page');
        li.style.display = allowed.includes(page) ? '' : 'none';
    });

    // 控制超级管理员专属按钮（super-admin-only class）
    document.querySelectorAll('.super-admin-only').forEach(el => {
        el.style.display = isSuperAdmin ? '' : 'none';
    });

    // 控制普通管理员可用按钮（admin-only class）
    document.querySelectorAll('.admin-only').forEach(el => {
        el.style.display = isAdmin ? '' : 'none';
    });

    // 设置 body class 供 CSS 使用
    document.body.classList.toggle('is-admin', isAdmin);
    document.body.classList.toggle('is-super-admin', isSuperAdmin);
}

// ════════════════════════════════════════════
// API 请求封装
// ════════════════════════════════════════════

function authHeaders() {
    const h = { 'Content-Type': 'application/json' };
    if (state.userId) h['X-User-ID'] = String(state.userId);
    if (state.token) h['X-Token'] = state.token;
    return h;
}

async function api(path, opts = {}) {
    const res = await fetch(API + path, {
        headers: authHeaders(),
        ...opts
    });
    const data = await res.json();
    // 不拦截 /auth/ 路径下的 401，让调用方自行处理（如登录密码错误）
    if (res.status === 401 && !path.startsWith('/auth/')) {
        showToast('登录已过期，请重新登录', 'danger');
        doLogout();
        throw new Error('Unauthorized');
    }
    return data;
}

async function apiGet(path) { return api(path); }
async function apiPost(path, body) {
    return api(path, { method: 'POST', body: JSON.stringify(body) });
}
async function apiPut(path, body) {
    return api(path, { method: 'PUT', body: JSON.stringify(body) });
}

// ════════════════════════════════════════════
// 认证
// ════════════════════════════════════════════

function toggleAuthForm(showLogin) {
    document.getElementById('loginForm').style.display = showLogin ? '' : 'none';
    document.getElementById('registerForm').style.display = showLogin ? 'none' : '';
}

async function doLogin() {
    const username = document.getElementById('loginUsername').value.trim();
    const password = document.getElementById('loginPassword').value;
    if (!username || !password) return showToast('请输入姓名和密码', 'warning');
    try {
        const data = await apiPost('/auth/login', { username, password });
        if (data.success) {
            saveAuth(data);
            showApp();
            showToast('登录成功', 'success');
        } else {
            showToast(data.message, 'danger');
        }
    } catch (e) { showToast('登录失败: ' + e.message, 'danger'); }
}

async function doRegister() {
    const username = document.getElementById('regUsername').value.trim();
    const department = document.getElementById('regDepartment').value.trim();
    const password = document.getElementById('regPassword').value;
    if (!username || !password) return showToast('请填写姓名和密码', 'warning');
    if (password.length < 6) return showToast('密码至少6位', 'warning');
    try {
        const data = await apiPost('/auth/register', { username, password, department });
        if (data.success) {
            saveAuth(data);
            showApp();
            showToast(data.message, 'success');
        } else {
            showToast(data.message, 'danger');
        }
    } catch (e) { showToast('注册失败: ' + e.message, 'danger'); }
}

function saveAuth(data) {
    state.userId = data.user_id;
    state.token = data.token;
    state.role = data.role;
    state.isSuperAdmin = data.is_super_admin || false;
    state.user = { username: data.username, role: data.role, is_super_admin: data.is_super_admin };
    localStorage.setItem('auth', JSON.stringify({ 
        userId: data.user_id, 
        token: data.token, 
        role: data.role, 
        isSuperAdmin: data.is_super_admin || false,
        username: data.username 
    }));
}

function loadAuth() {
    try {
        const saved = JSON.parse(localStorage.getItem('auth'));
        // role 字段必须存在，旧版本缓存没有 role 则强制重新登录
        if (saved && saved.token && saved.role) {
            state.userId = saved.userId;
            state.token = saved.token;
            state.role = saved.role;
            state.isSuperAdmin = saved.isSuperAdmin || false;
            state.user = { username: saved.username, role: saved.role, is_super_admin: saved.isSuperAdmin };
            return true;
        }
    } catch (_) {}
    localStorage.removeItem('auth');  // 清除无效缓存
    return false;
}

function doLogout() {
    state.user = null;
    state.token = null;
    state.userId = null;
    state.role = null;
    state.isSuperAdmin = false;
    localStorage.removeItem('auth');
    document.body.classList.remove('is-admin');
    document.getElementById('authPage').style.display = '';
    document.getElementById('mainApp').style.display = 'none';
}

function showApp() {
    document.getElementById('authPage').style.display = 'none';
    document.getElementById('mainApp').style.display = 'flex';
    // 更新侧边栏用户信息
    document.getElementById('sidebarUsername').textContent = state.user.username;
    let roleText = state.role === 'admin' 
        ? (state.isSuperAdmin ? '超级管理员' : '管理员') 
        : '涉密人员';
    document.getElementById('sidebarRole').textContent = roleText;
    // 管理员显示
    if (state.role === 'admin') {
        document.body.classList.add('is-admin');
    } else {
        document.body.classList.remove('is-admin');
    }
    applyRoleView();
    // 加载数据
    loadGroupsCache();
    navigateTo('dashboard');
}

// ════════════════════════════════════════════
// 导航
// ════════════════════════════════════════════

function navigateTo(page) {
    if (!isPageAllowed(page)) {
        showToast('权限不足，无法访问该页面', 'warning');
        page = state.role === 'admin' ? 'dashboard' : 'documents';
    }

    // 隐藏所有页面
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    const target = document.getElementById('page' + page.charAt(0).toUpperCase() + page.slice(1));
    if (target) target.classList.add('active');
    // 更新侧边栏
    document.querySelectorAll('.sidebar-nav li').forEach(li => li.classList.remove('active'));
    const navItem = document.querySelector(`.sidebar-nav li[data-page="${page}"]`);
    if (navItem) navItem.classList.add('active');
    // 加载页面数据
    switch (page) {
        case 'dashboard': loadDashboard(); break;
        case 'documents': showDocumentList(); loadDocuments(); break;
        case 'groups': showGroupList(); loadGroups(); break;
        case 'members': loadMembers(); break;
        case 'signatures': loadSignatures(); break;
        case 'audit': loadAuditLogs(); break;
        case 'admin': loadUsers(); break;
    }
}

// ════════════════════════════════════════════
// 群组缓存 (供下拉选用)
// ════════════════════════════════════════════

async function loadGroupsCache() {
    try {
        const data = await apiGet('/groups');
        state.groups = data.groups || [];
        updateAllGroupSelects();
    } catch (_) {}
}

function updateAllGroupSelects() {
    const selects = ['docGroupFilter', 'docGroupInput', 'memberGroupFilter',
                     'sigGroupFilter', 'addMemberGroupSelect'];
    const opts = state.groups.map(g => `<option value="${g.id}">${g.name}</option>`).join('');
    selects.forEach(id => {
        const el = document.getElementById(id);
        if (!el) return;
        const hasAll = el.querySelector('option[value=""]');
        el.innerHTML = (hasAll ? '<option value="">所有群组</option>' : '') + opts;
    });
}

// ════════════════════════════════════════════
// 仪表盘
// ════════════════════════════════════════════

async function loadDashboard() {
    try {
        const data = await apiGet('/audit/stats');
        const s = data.stats;
        document.getElementById('statGroups').textContent = s.group_count || 0;
        document.getElementById('statMembers').textContent = s.member_count || 0;
        document.getElementById('statDocuments').textContent = s.document_count || 0;
        document.getElementById('statSignatures').textContent = s.signature_count || 0;

        // 文件状态分布
        const statusMap = { pending: { label: '待签署', color: '#2196f3' }, signed: { label: '已签署', color: '#4caf50' }, verified: { label: '已验证', color: '#9c27b0' }, archived: { label: '已归档', color: '#607d8b' } };
        const total = s.document_count || 1;
        let barHtml = '';
        for (const [k, v] of Object.entries(statusMap)) {
            const cnt = (s.doc_by_status && s.doc_by_status[k]) || 0;
            const pct = Math.round(cnt / total * 100);
            barHtml += `<div class="status-bar-item">
                <span class="sbar-label">${v.label}</span>
                <div class="sbar"><div class="sbar-fill" style="width:${pct}%;background:${v.color}"></div></div>
                <span class="sbar-count">${cnt}</span>
            </div>`;
        }
        document.querySelector('#docStatusChart .status-bar-list').innerHTML = barHtml;

        // 最近活动
        const acts = s.recent_activities || [];
        if (acts.length === 0) {
            document.getElementById('recentActivities').innerHTML = '<p class="text-muted">暂无操作记录</p>';
        } else {
            const actionIcons = {
                login: 'bi-box-arrow-in-right', register: 'bi-person-plus',
                create_group: 'bi-people', add_member: 'bi-person-badge',
                create_document: 'bi-file-earmark-plus', sign_document: 'bi-vector-pen',
                verify_document: 'bi-check-circle', trace_signature: 'bi-search',
                create_signature: 'bi-pen', verify_signature: 'bi-shield-check',
                open_signature: 'bi-eye', update_role: 'bi-gear'
            };
            document.getElementById('recentActivities').innerHTML = acts.map(a => `
                <div class="activity-item">
                    <i class="act-icon bi ${actionIcons[a.action] || 'bi-activity'}"></i>
                    <div class="act-text"><strong>${a.username || '系统'}</strong> ${a.details || a.action}</div>
                    <span class="act-time">${formatTime(a.created_at)}</span>
                </div>
            `).join('');
        }
    } catch (e) { console.error('加载仪表盘失败:', e); }
}

// ════════════════════════════════════════════
// 涉密文件管理
// ════════════════════════════════════════════

function showDocumentList() {
    document.getElementById('documentListView').style.display = '';
    document.getElementById('documentDetailView').style.display = 'none';
}

async function loadDocuments() {
    const groupId = document.getElementById('docGroupFilter').value;
    const status = document.getElementById('docStatusFilter').value;
    let url = '/documents?';
    if (groupId) url += `group_id=${groupId}&`;
    if (status) url += `status=${status}&`;
    try {
        const data = await apiGet(url);
        const docs = data.documents || [];
        const tbody = document.getElementById('documentsTableBody');
        if (docs.length === 0) {
            tbody.innerHTML = '<tr><td colspan="8" class="text-center text-muted">暂无涉密文件</td></tr>';
            return;
        }
        tbody.innerHTML = docs.map(d => `<tr>
            <td><code>${d.doc_number || '-'}</code></td>
            <td><a href="#" onclick="viewDocument(${d.id});return false">${esc(d.title)}</a></td>
            <td>${classificationBadge(d.classification_level)}</td>
            <td>${statusBadge(d.status)}</td>
            <td>${esc(d.group_name || '-')}</td>
            <td>${d.sig_count || 0}</td>
            <td>${formatTime(d.created_at)}</td>
            <td><button class="btn btn-sm btn-outline-primary" onclick="viewDocument(${d.id})"><i class="bi bi-eye"></i></button></td>
        </tr>`).join('');
    } catch (e) { showToast('加载文件列表失败', 'danger'); }
}

function showCreateDocModal() {
    document.getElementById('docTitleInput').value = '';
    document.getElementById('docContentInput').value = '';
    document.getElementById('docClassInput').value = '秘密';
    // 更新群组选择
    const sel = document.getElementById('docGroupInput');
    sel.innerHTML = state.groups.map(g => `<option value="${g.id}">${g.name}</option>`).join('');
    new bootstrap.Modal(document.getElementById('createDocModal')).show();
}

async function createDocument() {
    const title = document.getElementById('docTitleInput').value.trim();
    const content = document.getElementById('docContentInput').value.trim();
    const classification_level = document.getElementById('docClassInput').value;
    const group_id = parseInt(document.getElementById('docGroupInput').value);
    if (!title || !content || !group_id) return showToast('请填写完整信息', 'warning');
    try {
        const data = await apiPost('/documents', { title, content, classification_level, group_id });
        if (data.success) {
            showToast('文件创建成功', 'success');
            bootstrap.Modal.getInstance(document.getElementById('createDocModal')).hide();
            loadDocuments();
        } else {
            showToast(data.message, 'danger');
        }
    } catch (e) { showToast('创建失败', 'danger'); }
}

async function viewDocument(docId) {
    document.getElementById('documentListView').style.display = 'none';
    document.getElementById('documentDetailView').style.display = '';
    document.getElementById('documentDetailContent').innerHTML = '<p class="text-center text-muted">加载中...</p>';
    try {
        const data = await apiGet(`/documents/${docId}`);
        const d = data.document;
        const sigs = d.signatures || [];

        let sigsHtml = '';
        if (sigs.length === 0) {
            sigsHtml = '<p class="text-muted">暂无签名记录</p>';
        } else {
            sigsHtml = sigs.map((s, i) => {
                const isTraced = s.opened;
                return `<div class="sig-card">
                    <div class="sig-info">
                        <i class="sig-icon bi ${isTraced ? 'bi-person-fill traced' : 'bi-incognito anonymous'}"></i>
                        <div>
                            <strong>${isTraced ? esc(s.signer_name) : '匿名签署 #' + (i+1)}</strong><br>
                            <small class="text-muted">${formatTime(s.created_at)}</small>
                            ${s.verified ? ' <span class="badge badge-signed">已验证</span>' : ''}
                            ${isTraced ? ' <span class="badge badge-traced">已追踪</span>' : ' <span class="badge badge-anonymous">匿名</span>'}
                        </div>
                    </div>
                    <div>
                        ${!isTraced ? `<button class="btn btn-sm btn-outline-primary me-2" onclick="claimSig(${s.id})"><i class="bi bi-person-check"></i> 声明签名</button>` : ''}
                        ${!isTraced && state.role === 'admin' ? `<button class="btn btn-sm btn-outline-warning" onclick="confirmTrace(${docId},${s.id})"><i class="bi bi-search"></i> 追踪身份</button>` : ''}
                    </div>
                </div>`;
            }).join('');
        }

        // 根据是否已签名显示不同的内容区域
        let contentHtml = '';
        if (d.content_hidden) {
            contentHtml = `
                <div class="alert alert-warning">
                    <i class="bi bi-lock"></i> <strong>文件内容已隐藏</strong><br>
                    <small>您需要先签署此文件才能查看完整内容。签署后将自动显示文件内容。</small>
                </div>
            `;
        } else {
            contentHtml = `<div class="doc-content-box">${esc(d.content || '')}</div>`;
        }

        document.getElementById('documentDetailContent').innerHTML = `
            <div class="doc-info-grid">
                <div class="doc-info-item"><label>文件编号</label><span>${d.doc_number || '-'}</span></div>
                <div class="doc-info-item"><label>密级</label><span>${classificationBadge(d.classification_level)}</span></div>
                <div class="doc-info-item"><label>状态</label><span>${statusBadge(d.status)}</span></div>
                <div class="doc-info-item"><label>所属群组</label><span>${esc(d.group_name || '-')}</span></div>
                <div class="doc-info-item"><label>创建人</label><span>${esc(d.creator_name || '-')}</span></div>
                <div class="doc-info-item"><label>创建时间</label><span>${formatTime(d.created_at)}</span></div>
            </div>
            <h6><i class="bi bi-file-text"></i> 文件内容</h6>
            ${contentHtml}
            <div class="doc-actions">
                ${d.status !== 'archived' ? `<button class="btn btn-primary btn-sm" onclick="signDocument(${d.id})"><i class="bi bi-vector-pen"></i> 签署文件</button>` : ''}
                ${sigs.length > 0 && !d.content_hidden ? `<button class="btn btn-success btn-sm" onclick="verifyDocument(${d.id})"><i class="bi bi-check-circle"></i> 验证签名</button>` : ''}
                ${state.role === 'admin' && d.status !== 'archived' ? `<button class="btn btn-secondary btn-sm" onclick="archiveDocument(${d.id})"><i class="bi bi-archive"></i> 归档</button>` : ''}
            </div>
            <h6><i class="bi bi-vector-pen"></i> 签名记录 <span class="badge bg-secondary">${sigs.length}</span></h6>
            <div class="mb-3">
                <small class="text-muted">群签名特性：签名均为匿名签署，仅管理员可追踪签名者真实身份</small>
            </div>
            ${sigsHtml}
        `;
    } catch (e) {
        document.getElementById('documentDetailContent').innerHTML = '<p class="text-danger">加载失败</p>';
    }
}

async function signDocument(docId) {
    if (!confirm('确定要签署该涉密文件吗？\n\n您的签名将使用群签名方案，签名过程匿名，但管理员可追踪。')) return;
    try {
        const data = await apiPost(`/documents/${docId}/sign`, {});
        if (data.success) {
            showToast(data.message, 'success');
            viewDocument(docId);
        } else {
            showToast(data.message, 'danger');
        }
    } catch (e) { showToast('签署失败', 'danger'); }
}

async function verifyDocument(docId) {
    try {
        const data = await apiPost(`/documents/${docId}/verify`, {});
        if (data.success) {
            showToast(data.message, data.all_valid ? 'success' : 'warning');
            viewDocument(docId);
        } else {
            showToast(data.message, 'danger');
        }
    } catch (e) { showToast('验证失败', 'danger'); }
}

async function archiveDocument(docId) {
    if (!confirm('确定要归档该文件吗？')) return;
    try {
        const data = await apiPut(`/documents/${docId}/status`, { status: 'archived' });
        if (data.success) {
            showToast('文件已归档', 'success');
            viewDocument(docId);
        } else {
            showToast(data.message, 'danger');
        }
    } catch (e) { showToast('归档失败', 'danger'); }
}

function confirmTrace(docId, sigId) {
    const modal = new bootstrap.Modal(document.getElementById('traceConfirmModal'));
    document.getElementById('confirmTraceBtn').onclick = async () => {
        modal.hide();
        try {
            const data = await apiPost(`/documents/${docId}/signatures/${sigId}/trace`, {});
            if (data.success) {
                showToast(`追踪成功！签名者: ${data.signer_name}`, 'success');
                viewDocument(docId);
            } else {
                showToast(data.message, 'danger');
            }
        } catch (e) { showToast('追踪失败', 'danger'); }
    };
    modal.show();
}

// ════════════════════════════════════════════
// 群组管理
// ════════════════════════════════════════════

function showGroupList() {
    document.getElementById('groupListView').style.display = '';
    document.getElementById('groupDetailView').style.display = 'none';
}

async function loadGroups() {
    try {
        const data = await apiGet('/groups');
        const groups = data.groups || [];
        state.groups = groups;
        updateAllGroupSelects();
        const container = document.getElementById('groupCards');
        if (groups.length === 0) {
            container.innerHTML = '<div class="col-12"><p class="text-center text-muted">暂无群组，请管理员创建</p></div>';
            return;
        }
        container.innerHTML = groups.map(g => `
            <div class="col-md-4">
                <div class="group-card" onclick="viewGroup(${g.id})">
                    <h5>${esc(g.name)}</h5>
                    <p class="gc-meta">${esc(g.description || '暂无描述')}</p>
                    <div class="gc-stats">
                        <span><i class="bi bi-people"></i> ${g.member_count || 0} 成员</span>
                        <span><i class="bi bi-file-earmark"></i> ${g.doc_count || 0} 文件</span>
                        <span>${classificationBadge(g.classification_level || '秘密')}</span>
                    </div>
                    <small class="text-muted">${formatTime(g.created_at)}</small>
                </div>
            </div>
        `).join('');
    } catch (e) { showToast('加载群组失败', 'danger'); }
}

function showCreateGroupModal() {
    document.getElementById('groupNameInput').value = '';
    document.getElementById('groupDescInput').value = '';
    new bootstrap.Modal(document.getElementById('createGroupModal')).show();
}

async function createGroup() {
    const name = document.getElementById('groupNameInput').value.trim();
    const description = document.getElementById('groupDescInput').value.trim();
    const classification_level = document.getElementById('groupClassInput').value;
    if (!name) return showToast('请输入群组名称', 'warning');
    try {
        const data = await apiPost('/groups', { name, description, classification_level });
        if (data.success) {
            showToast('群组创建成功（已生成群公钥、管理密钥和GML）', 'success');
            bootstrap.Modal.getInstance(document.getElementById('createGroupModal')).hide();
            loadGroups();
            loadGroupsCache();
        } else {
            showToast(data.message, 'danger');
        }
    } catch (e) { showToast('创建失败', 'danger'); }
}

async function viewGroup(groupId) {
    document.getElementById('groupListView').style.display = 'none';
    document.getElementById('groupDetailView').style.display = '';
    document.getElementById('groupDetailContent').innerHTML = '<p class="text-center text-muted">加载中...</p>';
    try {
        const data = await apiGet(`/groups/${groupId}`);
        const g = data.group;
        const members = g.members || [];
        document.getElementById('groupDetailContent').innerHTML = `
            <div class="card mb-3">
                <div class="card-body">
                    <h5>${esc(g.name)}</h5>
                    <p>${esc(g.description || '暂无描述')}</p>
                    <div class="d-flex gap-3">
                        ${classificationBadge(g.classification_level || '秘密')}
                        <span class="badge bg-primary">${g.member_count} 成员</span>
                        <span class="badge bg-info">${g.doc_count} 文件</span>
                    </div>
                </div>
            </div>
            <div class="card">
                <div class="card-header"><i class="bi bi-people"></i> 群组成员</div>
                <div class="card-body">
                    ${members.length === 0 ? '<p class="text-muted">暂无成员</p>' :
                    `<table class="table table-sm"><thead><tr><th>ID</th><th>姓名</th><th>关联用户</th><th>GML索引</th><th>加入时间</th></tr></thead>
                     <tbody>${members.map(m => `<tr><td>${m.id}</td><td>${esc(m.name)}</td><td>${esc(m.username || '-')}</td><td>${m.gml_index ?? '-'}</td><td>${formatTime(m.created_at)}</td></tr>`).join('')}</tbody></table>`}
                </div>
            </div>
        `;
    } catch (e) { document.getElementById('groupDetailContent').innerHTML = '<p class="text-danger">加载失败</p>'; }
}

// ════════════════════════════════════════════
// 成员管理
// ════════════════════════════════════════════

async function loadMembers() {
    const groupId = document.getElementById('memberGroupFilter').value;
    const url = groupId ? `/members?group_id=${groupId}` : '/members';
    try {
        const data = await apiGet(url);
        const members = data.members || [];
        const tbody = document.getElementById('membersTableBody');
        if (members.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" class="text-center text-muted">暂无成员</td></tr>';
            return;
        }
        tbody.innerHTML = members.map(m => `<tr>
            <td>${m.id}</td>
            <td>${esc(m.name)}</td>
            <td>${m.user_id || '-'}</td>
            <td>${m.group_id}</td>
            <td>${m.gml_index ?? '-'}</td>
            <td><span class="badge ${m.status === 'active' ? 'bg-success' : 'bg-secondary'}">${m.status || 'active'}</span></td>
            <td>${formatTime(m.created_at)}</td>
        </tr>`).join('');
    } catch (e) { showToast('加载成员失败', 'danger'); }
}

async function showAddMemberModal() {
    document.getElementById('memberNameInput').value = '';
    // 加载用户列表
    try {
        if (state.role === 'admin') {
            const data = await apiGet('/auth/users');
            const userSel = document.getElementById('addMemberUserSelect');
            userSel.innerHTML = '<option value="">请选择用户</option>' +
                (data.users || []).map(u => `<option value="${u.id}">${u.username}</option>`).join('');
        }
    } catch (_) {}
    new bootstrap.Modal(document.getElementById('addMemberModal')).show();
}

async function addMember() {
    const groupId = document.getElementById('addMemberGroupSelect').value;
    const name = document.getElementById('memberNameInput').value.trim();
    const userId = document.getElementById('addMemberUserSelect').value || null;
    if (!groupId || !userId) return showToast('请选择群组和用户', 'warning');
    try {
        const data = await apiPost('/members', {
            group_id: parseInt(groupId),
            name,
            user_id: userId ? parseInt(userId) : null
        });
        if (data.success) {
            showToast('成员添加成功（已执行JOIN协议、分发成员密钥）', 'success');
            bootstrap.Modal.getInstance(document.getElementById('addMemberModal')).hide();
            loadMembers();
        } else {
            showToast(data.message, 'danger');
        }
    } catch (e) { showToast('添加失败', 'danger'); }
}

// ════════════════════════════════════════════
// 签名记录
// ════════════════════════════════════════════

async function loadSignatures() {
    const groupId = document.getElementById('sigGroupFilter').value;
    const url = groupId ? `/signatures?group_id=${groupId}` : '/signatures';
    try {
        const data = await apiGet(url);
        const sigs = data.signatures || [];
        const tbody = document.getElementById('signaturesTableBody');
        if (sigs.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" class="text-center text-muted">暂无签名记录</td></tr>';
            return;
        }
        tbody.innerHTML = sigs.map(s => `<tr>
            <td>${s.id}</td>
            <td title="${esc(s.message)}">${esc((s.message || '').substring(0, 40))}${(s.message||'').length > 40 ? '...' : ''}</td>
            <td>${s.document_id ? `<a href="#" onclick="navigateTo('documents');viewDocument(${s.document_id});return false">文件#${s.document_id}</a>` : '-'}</td>
            <td>${s.verified ? '<span class="badge badge-signed">已验证</span>' : '<span class="badge bg-secondary">未验证</span>'}</td>
            <td>${s.opened ? `<span class="badge badge-traced">已追踪: ${esc(s.signer_name || '索引'+s.signer_index)}</span>` : '<span class="badge badge-anonymous">匿名</span>'}</td>
            <td>${formatTime(s.created_at)}</td>
            <td>
                <button class="btn btn-sm btn-outline-success" onclick="verifySig(${s.id})"><i class="bi bi-check"></i></button>
                <button class="btn btn-sm btn-outline-primary" onclick="claimSig(${s.id})"><i class="bi bi-person-check"></i></button>
                ${!s.opened && state.role === 'admin' ? `<button class="btn btn-sm btn-outline-warning" onclick="openSig(${s.id})"><i class="bi bi-search"></i></button>` : ''}
            </td>
        </tr>`).join('');
    } catch (e) { showToast('加载签名失败', 'danger'); }
}

async function verifySig(sigId) {
    try {
        const data = await apiPost(`/signatures/${sigId}/verify`, {});
        if (data.success) {
            showToast(data.valid ? '签名验证通过' : '签名验证失败', data.valid ? 'success' : 'warning');
            loadSignatures();
        } else { showToast(data.message, 'danger'); }
    } catch (e) { showToast('验证失败', 'danger'); }
}

async function openSig(sigId) {
    if (!confirm('确定要追踪该签名的签名者身份吗？\n此操作将被记录到审计日志。')) return;
    try {
        const data = await apiPost(`/signatures/${sigId}/open`, {});
        if (data.success) {
            showToast(`追踪成功！签名者: ${data.signer_name || '索引 ' + data.signer_index}`, 'success');
            loadSignatures();
        } else { showToast(data.message, 'danger'); }
    } catch (e) { showToast('追踪失败', 'danger'); }
}

async function claimSig(sigId) {
    try {
        const data = await apiPost(`/signatures/${sigId}/claim`, {});
        if (!data.success) {
            showToast(data.message || '声明失败', 'danger');
            return;
        }
        showToast(data.message || '声明成功', 'success');
    } catch (e) {
        showToast('声明签名失败', 'danger');
    }
}

// ════════════════════════════════════════════
// 审计日志
// ════════════════════════════════════════════

let auditPage = 1;

async function loadAuditLogs(page) {
    if (page) auditPage = page;
    const action = document.getElementById('auditActionFilter').value;
    let url = `/audit/logs?page=${auditPage}&per_page=15`;
    if (action) url += `&action=${action}`;
    try {
        const data = await apiGet(url);
        const logs = data.logs || [];
        const tbody = document.getElementById('auditTableBody');
        if (logs.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted">暂无日志</td></tr>';
            document.getElementById('auditPagination').innerHTML = '';
            return;
        }
        const actionLabels = {
            login: '用户登录', register: '用户注册', create_group: '创建群组',
            add_member: '添加成员', create_document: '创建文件', sign_document: '签署文件',
            verify_document: '验证签名', trace_signature: '追踪签名', create_signature: '创建签名',
            verify_signature: '验证签名', open_signature: '追踪签名', update_role: '角色变更',
            update_doc_status: '状态变更'
        };
        tbody.innerHTML = logs.map(l => `<tr>
            <td>${formatTime(l.created_at)}</td>
            <td>${esc(l.username || '-')}</td>
            <td><span class="badge bg-info">${actionLabels[l.action] || l.action}</span></td>
            <td>${l.resource_type ? l.resource_type + '#' + l.resource_id : '-'}</td>
            <td>${esc(l.details || '-')}</td>
        </tr>`).join('');
        // 分页
        let pagHtml = '<ul class="pagination pagination-sm justify-content-center mt-3">';
        for (let i = 1; i <= data.total_pages; i++) {
            pagHtml += `<li class="page-item ${i === data.page ? 'active' : ''}"><a class="page-link" href="#" onclick="loadAuditLogs(${i});return false">${i}</a></li>`;
        }
        pagHtml += '</ul>';
        document.getElementById('auditPagination').innerHTML = pagHtml;
    } catch (e) { showToast('加载审计日志失败', 'danger'); }
}

// ════════════════════════════════════════════
// 用户管理 (管理员)
// ════════════════════════════════════════════

async function loadUsers() {
    try {
        const data = await apiGet('/auth/users');
        const users = data.users || [];
        const tbody = document.getElementById('usersTableBody');
        if (users.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="text-center text-muted">暂无用户</td></tr>';
            return;
        }
        tbody.innerHTML = users.map(u => `<tr>
            <td>${u.id}</td>
            <td>${esc(u.username)}</td>
            <td>${esc(u.department || '-')}</td>
            <td><span class="badge ${u.role === 'admin' ? 'bg-danger' : 'bg-primary'}">${u.role === 'admin' ? '管理员' : '涉密人员'}</span></td>
            <td>${formatTime(u.created_at)}</td>
            <td>${u.id !== state.userId ? `<button class="btn btn-sm btn-outline-secondary" onclick="toggleRole(${u.id},'${u.role === 'admin' ? 'user' : 'admin'}')">${u.role === 'admin' ? '降为用户' : '设为管理员'}</button>` : '<span class="text-muted">当前用户</span>'}</td>
        </tr>`).join('');
    } catch (e) { showToast('加载用户列表失败', 'danger'); }
}

async function toggleRole(uid, newRole) {
    if (!confirm(`确定要将用户角色变更为 ${newRole === 'admin' ? '管理员' : '涉密人员'} 吗？`)) return;
    try {
        const data = await apiPut(`/auth/users/${uid}/role`, { role: newRole });
        if (data.success) {
            showToast(data.message, 'success');
            loadUsers();
        } else { showToast(data.message, 'danger'); }
    } catch (e) { showToast('操作失败', 'danger'); }
}

// ════════════════════════════════════════════
// 工具函数
// ════════════════════════════════════════════

function esc(str) {
    if (!str) return '';
    const el = document.createElement('span');
    el.textContent = str;
    return el.innerHTML;
}

function formatTime(ts) {
    if (!ts) return '-';
    try {
        const d = new Date(ts);
        return d.toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' });
    } catch (_) { return ts; }
}

function classificationBadge(level) {
    const map = {
        '秘密': 'badge-secret',
        '机密': 'badge-confidential',
        '绝密': 'badge-top-secret'
    };
    return `<span class="badge ${map[level] || 'bg-secondary'}">${esc(level || '秘密')}</span>`;
}

function statusBadge(status) {
    const map = {
        pending: ['badge-pending', '待签署'],
        signed: ['badge-signed', '已签署'],
        verified: ['badge-verified', '已验证'],
        archived: ['badge-archived', '已归档']
    };
    const [cls, label] = map[status] || ['bg-secondary', status];
    return `<span class="badge ${cls}">${label}</span>`;
}

function showToast(message, type = 'info') {
    const typeMap = { success: 'bg-success', danger: 'bg-danger', warning: 'bg-warning text-dark', info: 'bg-info' };
    const container = document.getElementById('toastContainer');
    const id = 'toast-' + Date.now();
    container.insertAdjacentHTML('beforeend', `
        <div id="${id}" class="toast align-items-center ${typeMap[type] || 'bg-info'} text-white border-0" role="alert">
            <div class="d-flex">
                <div class="toast-body">${esc(message)}</div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        </div>
    `);
    const el = document.getElementById(id);
    const toast = new bootstrap.Toast(el, { delay: 3500 });
    toast.show();
    el.addEventListener('hidden.bs.toast', () => el.remove());
}

// ════════════════════════════════════════════
// 初始化
// ════════════════════════════════════════════

document.addEventListener('DOMContentLoaded', () => {
    // Enter 键登录
    document.getElementById('loginPassword').addEventListener('keydown', e => {
        if (e.key === 'Enter') doLogin();
    });
    document.getElementById('regPassword').addEventListener('keydown', e => {
        if (e.key === 'Enter') doRegister();
    });

    if (loadAuth()) {
        showApp();
    }
});
