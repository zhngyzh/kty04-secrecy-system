# 快速参考指南

## 一、常用命令

### 1) 启动后端

```bash
uv run python backend/app.py
```

### 2) 功能测试

```bash
uv run pytest tests/functional
```

### 3) 性能测试

```bash
uv run pytest tests/performance --run-performance
```

### 4) 非空数据库下运行管理员相关测试

```bash
uv run pytest tests/functional --admin-username <admin> --admin-password <password>
uv run pytest tests/performance --run-performance --admin-username <admin> --admin-password <password>
```

### 5) 环境检查

```bash
bash scripts/env-check.sh
```

## 二、测试目录规范

```text
tests/
├── conftest.py
├── functional/
│   ├── test_auth_and_permissions.py
│   └── test_document_flow.py
└── performance/
    └── test_api_performance.py
```

说明:
- 功能测试关注正确性与权限边界。
- 性能测试默认跳过，需显式传入 --run-performance。

## 三、高频 API 路径

- 认证: /api/auth/register, /api/auth/login, /api/auth/profile
- 群组: /api/groups
- 成员: /api/members
- 文件: /api/documents, /api/documents/<id>/sign, /api/documents/<id>/verify
- 追踪: /api/documents/<id>/signatures/<sig_id>/trace
- 审计: /api/audit/logs, /api/audit/stats

## 四、排障要点

- 若启动失败，先检查 uv 环境与 pygroupsig 导入。
- 若问题涉及群签名库使用或构建细节，请直接参考: https://github.com/IBM/libgroupsig
- 若权限测试失败，确认测试用户角色与请求头中的 X-User-ID/X-Token 对应。
- 若性能测试被跳过，确认已添加 --run-performance 参数。

## 五、文档入口

- 总览: README.md
- 安装: INSTALL.md
- 权限: PERMISSIONS.md
- 实现摘要: IMPLEMENTATION_SUMMARY.md
- 文档索引: docs/README.md
