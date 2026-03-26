# KTY04 群签名管理系统

基于 KTY04 方案的涉密文件管理系统，支持匿名签名、可追踪、声明签名与全流程审计。

## 文档导航

- 安装指南: [INSTALL.md](INSTALL.md)
- 快速参考: [QUICK_REFERENCE.md](QUICK_REFERENCE.md)
- 权限说明: [PERMISSIONS.md](PERMISSIONS.md)
- 实现摘要: [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)
- 文档索引: [docs/README.md](docs/README.md)

## 功能特性

- ✅ 群组创建与密钥初始化（grpkey/mgrkey/gml）
- ✅ 成员入群（JOIN 协议）与成员密钥分发
- ✅ 涉密文件创建、签署、验证、归档
- ✅ 匿名群签名与可追踪（Open）
- ✅ 声明签名（Claim）与声明验证（Claim Verify）
- ✅ 审计日志与仪表盘统计

## 角色权限模型

| 功能 | 涉密管理员（admin） | 普通涉密人员（user） |
|---|---|---|
| 创建群组 | ✅ | ❌ |
| 添加成员 | ✅ | ❌ |
| 打开/追踪签名 | ✅ | ❌ |
| 查看审计日志 | ✅ | ❌ |
| 系统用户管理 | ✅ | ❌ |
| 文件签署（群签名） | ✅（可选） | ✅ |
| 签名验证 | ✅ | ✅ |
| 声明签名（Claim） | ✅（调试用途） | ✅ |
| 声明验证（Claim Verify） | ✅ | ✅ |

说明：普通涉密人员登录后仅显示与签名业务相关页面，不显示群组管理、成员管理、审计日志、系统管理面板。

## 技术栈

- **后端**: Flask (Python)
- **前端**: 原生 HTML + JavaScript + Bootstrap 5
- **数据存储**: SQLite + JSON 文件
- **群签名库**: libgroupsig/pygroupsig（库使用细节请参考 https://github.com/IBM/libgroupsig ）

## 安装步骤

### 1. 同步管理系统依赖

```bash
uv sync
```

### 2. 库使用说明（外部参考）

本项目文档聚焦管理系统业务流程，不展开群签名库内部接口与构建细节。
请直接参考：https://github.com/IBM/libgroupsig

### 3. 运行系统

```bash
uv run python backend/app.py
```

然后在浏览器中访问: http://localhost:5000

## 项目结构

```
kty04-management/
├── backend/
│   ├── app.py              # Flask 主应用
│   ├── api/                # API 路由
│   ├── utils/              # 工具函数
├── data/                   # 运行态数据与密钥材料
│   ├── groups/             # 群组密钥
│   ├── members/            # 成员密钥
│   └── signatures/         # 签名记录
├── frontend/
│   ├── index.html          # 主页面
│   ├── css/
│   └── js/
├── docs/                   # 文档
├── pyproject.toml          # uv 依赖定义
└── requirements.txt        # 兼容旧流程的依赖清单
```

## 快速启动

使用启动脚本（推荐）：
```bash
bash start.sh
```

或手动启动：
```bash
uv run python backend/app.py
```

然后在浏览器中访问: http://localhost:5000

## 使用说明（核心流程）

1. 管理员创建群组，系统生成群公钥、管理员密钥和 GML。
2. 管理员添加成员，系统执行 JOIN 协议并分发成员密钥。
3. 普通涉密人员对文件进行匿名签署（群签名）。
4. 业务方验证签名有效性（不暴露签名者身份）。
5. 需要问责时，管理员执行追踪（Open）揭示真实签名者。
6. 签名者可执行声明签名（Claim），第三方可验证声明有效性。

## 测试（pytest）

项目已统一为 pytest 风格，按功能与性能分层：

```text
tests/
├── conftest.py
├── functional/
│   ├── test_auth_and_permissions.py
│   └── test_document_flow.py
└── performance/
    └── test_api_performance.py
```

运行前请先启动后端服务：

```bash
uv run python backend/app.py
```

功能测试：

```bash
uv run pytest tests/functional
```

性能测试（默认跳过，需要显式开启）：

```bash
uv run pytest tests/performance --run-performance
```

如果数据库不是空库，且需要管理员权限测试，请提供管理员账号：

```bash
uv run pytest tests/functional --admin-username <admin> --admin-password <password>
uv run pytest tests/performance --run-performance --admin-username <admin> --admin-password <password>
```

## API 接口

### 认证与用户
- `POST /api/auth/register` - 注册
- `POST /api/auth/login` - 登录
- `GET /api/auth/users` - 获取用户列表（管理员）
- `PUT /api/auth/users/<id>/role` - 变更角色（管理员）

### 群组管理
- `GET /api/groups` - 获取群组列表（登录用户）
- `POST /api/groups` - 创建新群组（管理员）
- `GET /api/groups/<id>` - 获取群组详情（登录用户）

### 成员管理
- `GET /api/members` - 获取成员列表（管理员）
- `POST /api/members` - 添加新成员（管理员）
- `GET /api/members/<id>` - 获取成员详情（管理员）

### 涉密文件管理
- `GET /api/documents` - 获取文件列表（登录用户）
- `POST /api/documents` - 创建文件（管理员）
- `GET /api/documents/<id>` - 获取文件详情（登录用户）
- `POST /api/documents/<id>/sign` - 匿名签署（登录用户，需群成员）
- `POST /api/documents/<id>/verify` - 验证文件签名（登录用户）
- `POST /api/documents/<id>/signatures/<sig_id>/trace` - 追踪签名者（管理员）
- `PUT /api/documents/<id>/status` - 更新文件状态（管理员）

### 签名管理
- `GET /api/signatures` - 获取签名列表（登录用户）
- `POST /api/signatures` - 创建签名（登录用户，普通用户仅能使用自己的成员身份）
- `POST /api/signatures/<id>/verify` - 验证签名（登录用户）
- `POST /api/signatures/<id>/claim` - 声明签名（登录用户）
- `POST /api/signatures/<id>/claim/verify` - 验证声明（预留接口，当前版本建议直接使用 /claim 的服务端验证结果）
- `POST /api/signatures/<id>/open` - 打开签名（管理员）

### 审计
- `GET /api/audit/logs` - 审计日志（管理员）
- `GET /api/audit/stats` - 仪表盘统计（登录用户，普通用户返回个人视图）

## 论文配图（流程图/架构图）

已提供可直接放入论文的 Mermaid 图：
- [docs/THESIS_DIAGRAMS.md](docs/THESIS_DIAGRAMS.md)

包含：系统架构图、角色用例图、签名与追踪时序图、文件状态图、数据库 ER 图。

## 注意事项

- 密钥与运行数据默认存储在 `data/` 目录下，请妥善保管
- 首次运行前请先执行 `uv sync`（见安装步骤 1）
- 确保 Python 版本 >= 3.10
- 如果遇到导入错误，请先执行 `uv sync --reinstall`，库细节参考 https://github.com/IBM/libgroupsig