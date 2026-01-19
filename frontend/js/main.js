const API_BASE = 'http://localhost:5000/api';

// 工具函数
function showAlert(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    document.body.insertBefore(alertDiv, document.body.firstChild);
    setTimeout(() => alertDiv.remove(), 3000);
}

// 群组管理
async function loadGroups() {
    try {
        const response = await fetch(`${API_BASE}/groups`);
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        const data = await response.json();
        const tbody = document.getElementById('groupsTableBody');
        
        if (!data.groups || data.groups.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" class="text-center">暂无群组，请先创建群组</td></tr>';
            return;
        }
        
        tbody.innerHTML = data.groups.map(group => `
            <tr>
                <td>${group.id}</td>
                <td>${group.name}</td>
                <td>${group.member_count || 0}</td>
                <td>${new Date(group.created_at).toLocaleString()}</td>
                <td>
                    <button class="btn btn-sm btn-info" onclick="viewGroup(${group.id})">查看</button>
                </td>
            </tr>
        `).join('');
        
        // 更新过滤器选项
        updateGroupFilters(data.groups);
    } catch (error) {
        console.error('加载群组错误:', error);
        const tbody = document.getElementById('groupsTableBody');
        tbody.innerHTML = `<tr><td colspan="5" class="text-center text-danger">加载失败: ${error.message}</td></tr>`;
        showAlert('加载群组列表失败: ' + error.message, 'danger');
    }
}

function updateGroupFilters(groups) {
    const memberFilter = document.getElementById('memberGroupFilter');
    const signatureFilter = document.getElementById('signatureGroupFilter');
    const addMemberSelect = document.getElementById('addMemberGroupSelect');
    const signatureGroupSelect = document.getElementById('signatureGroupSelect');
    
    const options = groups.map(g => `<option value="${g.id}">${g.name} (ID: ${g.id})</option>`).join('');
    
    [memberFilter, signatureFilter, addMemberSelect, signatureGroupSelect].forEach(select => {
        if (select) {
            const currentValue = select.value;
            select.innerHTML = '<option value="">所有群组</option>' + options;
            if (currentValue) select.value = currentValue;
        }
    });
}

function showCreateGroupModal() {
    document.getElementById('groupNameInput').value = '';
    new bootstrap.Modal(document.getElementById('createGroupModal')).show();
}

async function createGroup() {
    const name = document.getElementById('groupNameInput').value.trim();
    if (!name) {
        showAlert('请输入群组名称', 'warning');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/groups`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name })
        });
        const data = await response.json();
        
        if (data.success) {
            showAlert('群组创建成功', 'success');
            bootstrap.Modal.getInstance(document.getElementById('createGroupModal')).hide();
            loadGroups();
        } else {
            showAlert('创建失败: ' + data.message, 'danger');
        }
    } catch (error) {
        showAlert('创建失败: ' + error.message, 'danger');
    }
}

function viewGroup(groupId) {
    showAlert('查看群组功能待实现', 'info');
}

// 成员管理
async function loadMembers() {
    const groupId = document.getElementById('memberGroupFilter').value;
    const url = groupId ? `${API_BASE}/members?group_id=${groupId}` : `${API_BASE}/members`;
    
    try {
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        const data = await response.json();
        const tbody = document.getElementById('membersTableBody');
        
        if (!data.members || data.members.length === 0) {
            tbody.innerHTML = '<tr><td colspan="4" class="text-center">暂无成员，请先添加成员</td></tr>';
            return;
        }
        
        tbody.innerHTML = data.members.map(member => `
            <tr>
                <td>${member.id}</td>
                <td>${member.name}</td>
                <td>${member.group_id}</td>
                <td>${new Date(member.created_at).toLocaleString()}</td>
            </tr>
        `).join('');
    } catch (error) {
        console.error('加载成员错误:', error);
        const tbody = document.getElementById('membersTableBody');
        tbody.innerHTML = `<tr><td colspan="4" class="text-center text-danger">加载失败: ${error.message}</td></tr>`;
        showAlert('加载成员列表失败: ' + error.message, 'danger');
    }
}

function showAddMemberModal() {
    document.getElementById('memberNameInput').value = '';
    new bootstrap.Modal(document.getElementById('addMemberModal')).show();
}

async function addMember() {
    const groupId = document.getElementById('addMemberGroupSelect').value;
    const name = document.getElementById('memberNameInput').value.trim();
    
    if (!groupId) {
        showAlert('请选择群组', 'warning');
        return;
    }
    if (!name) {
        showAlert('请输入成员名称', 'warning');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/members`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ group_id: parseInt(groupId), name })
        });
        const data = await response.json();
        
        if (data.success) {
            showAlert('成员添加成功', 'success');
            bootstrap.Modal.getInstance(document.getElementById('addMemberModal')).hide();
            loadMembers();
        } else {
            showAlert('添加失败: ' + data.message, 'danger');
        }
    } catch (error) {
        showAlert('添加失败: ' + error.message, 'danger');
    }
}

// 签名管理
async function loadSignatures() {
    const groupId = document.getElementById('signatureGroupFilter').value;
    const url = groupId ? `${API_BASE}/signatures?group_id=${groupId}` : `${API_BASE}/signatures`;
    
    try {
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        const data = await response.json();
        const tbody = document.getElementById('signaturesTableBody');
        
        if (!data.signatures || data.signatures.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="text-center">暂无签名，请先创建签名</td></tr>';
            return;
        }
        
        tbody.innerHTML = data.signatures.map(sig => {
            const verifiedBadge = sig.verified 
                ? '<span class="badge bg-success">已验证</span>' 
                : '<span class="badge bg-danger">未验证</span>';
            const openedBadge = sig.opened 
                ? `<span class="badge bg-info">已打开 (签名者: ${sig.signer_index})</span>` 
                : '<span class="badge bg-secondary">未打开</span>';
            
            return `
                <tr>
                    <td>${sig.id}</td>
                    <td>${sig.message.substring(0, 50)}${sig.message.length > 50 ? '...' : ''}</td>
                    <td>${sig.member_name || '未知'}</td>
                    <td>${verifiedBadge} ${openedBadge}</td>
                    <td>${new Date(sig.created_at).toLocaleString()}</td>
                    <td>
                        <button class="btn btn-sm btn-success" onclick="verifySignature(${sig.id})">验证</button>
                        <button class="btn btn-sm btn-primary" onclick="openSignature(${sig.id})">打开</button>
                    </td>
                </tr>
            `;
        }).join('');
    } catch (error) {
        console.error('加载签名错误:', error);
        const tbody = document.getElementById('signaturesTableBody');
        tbody.innerHTML = `<tr><td colspan="6" class="text-center text-danger">加载失败: ${error.message}</td></tr>`;
        showAlert('加载签名列表失败: ' + error.message, 'danger');
    }
}

function showCreateSignatureModal() {
    document.getElementById('signatureMessageInput').value = '';
    document.getElementById('signatureMemberSelect').innerHTML = '<option value="">请先选择群组</option>';
    new bootstrap.Modal(document.getElementById('createSignatureModal')).show();
}

async function loadGroupMembers() {
    const groupId = document.getElementById('signatureGroupSelect').value;
    const memberSelect = document.getElementById('signatureMemberSelect');
    
    if (!groupId) {
        memberSelect.innerHTML = '<option value="">请先选择群组</option>';
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/members?group_id=${groupId}`);
        const data = await response.json();
        
        if (data.members.length === 0) {
            memberSelect.innerHTML = '<option value="">该群组暂无成员</option>';
            return;
        }
        
        memberSelect.innerHTML = data.members.map(m => 
            `<option value="${m.id}">${m.name} (ID: ${m.id})</option>`
        ).join('');
    } catch (error) {
        showAlert('加载成员失败: ' + error.message, 'danger');
    }
}

async function createSignature() {
    const groupId = document.getElementById('signatureGroupSelect').value;
    const memberId = document.getElementById('signatureMemberSelect').value;
    const message = document.getElementById('signatureMessageInput').value.trim();
    
    if (!groupId || !memberId || !message) {
        showAlert('请填写完整信息', 'warning');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/signatures`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                group_id: parseInt(groupId),
                member_id: parseInt(memberId),
                message
            })
        });
        const data = await response.json();
        
        if (data.success) {
            showAlert('签名创建成功', 'success');
            bootstrap.Modal.getInstance(document.getElementById('createSignatureModal')).hide();
            loadSignatures();
        } else {
            showAlert('创建失败: ' + data.message, 'danger');
        }
    } catch (error) {
        showAlert('创建失败: ' + error.message, 'danger');
    }
}

async function verifySignature(sigId) {
    try {
        const response = await fetch(`${API_BASE}/signatures/${sigId}/verify`, {
            method: 'POST'
        });
        const data = await response.json();
        
        if (data.success) {
            showAlert(data.valid ? '签名验证成功' : '签名验证失败', data.valid ? 'success' : 'warning');
            loadSignatures();
        } else {
            showAlert('验证失败: ' + data.message, 'danger');
        }
    } catch (error) {
        showAlert('验证失败: ' + error.message, 'danger');
    }
}

async function openSignature(sigId) {
    try {
        const response = await fetch(`${API_BASE}/signatures/${sigId}/open`, {
            method: 'POST'
        });
        const data = await response.json();
        
        if (data.success) {
            showAlert(`签名打开成功，签名者索引: ${data.signer_index}`, 'success');
            loadSignatures();
        } else {
            showAlert('打开失败: ' + data.message, 'danger');
        }
    } catch (error) {
        showAlert('打开失败: ' + error.message, 'danger');
    }
}

// 页面加载时初始化
document.addEventListener('DOMContentLoaded', () => {
    console.log('页面加载完成，开始初始化...');
    loadGroups().catch(err => {
        console.error('加载群组失败:', err);
        showAlert('加载群组失败: ' + err.message, 'danger');
    });
    loadMembers().catch(err => {
        console.error('加载成员失败:', err);
        showAlert('加载成员失败: ' + err.message, 'danger');
    });
    loadSignatures().catch(err => {
        console.error('加载签名失败:', err);
        showAlert('加载签名失败: ' + err.message, 'danger');
    });
    
    // 测试 API 连接
    fetch(`${API_BASE}/../health`)
        .then(res => res.json())
        .then(data => console.log('API 健康检查:', data))
        .catch(err => console.error('API 连接失败:', err));
});
