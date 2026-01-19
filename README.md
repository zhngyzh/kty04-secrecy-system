# KTY04 群签名管理系统

基于 newlibgroupsig 中 KTY04 方案的简单管理系统。

## 功能特性

- ✅ 群组创建和管理
- ✅ 成员加入
- ✅ 消息签名
- ✅ 签名验证
- ✅ 签名追踪（打开签名）
- ✅ 成员撤销和追踪

## 技术栈

- **后端**: Flask (Python)
- **前端**: 原生 HTML + JavaScript + Bootstrap 5
- **数据存储**: SQLite + JSON 文件
- **群签名库**: pygroupsig (KTY04)

## 安装步骤

### 1. 构建 libgroupsig C 库

```bash
cd newlibgroupsig/libgroupsig
mkdir -p build
cd build
cmake ..
make
```

### 2. 安装 pygroupsig Python 包装器

```bash
cd ../src/wrappers/python
pip install -e .
```

### 3. 安装项目依赖

```bash
cd ../../../../kty04-management
pip install -r requirements.txt
```

### 4. 运行系统

```bash
cd backend
python app.py
```

然后在浏览器中访问: http://localhost:5000

## 项目结构

```
kty04-management/
├── backend/
│   ├── app.py              # Flask 主应用
│   ├── api/                # API 路由
│   ├── utils/              # 工具函数
│   └── data/               # 数据存储目录
│       ├── groups/         # 群组密钥
│       ├── members/        # 成员密钥
│       └── signatures/     # 签名记录
├── frontend/
│   ├── index.html          # 主页面
│   ├── css/
│   └── js/
├── docs/                   # 文档
└── requirements.txt        # Python 依赖
```

## 快速启动

使用启动脚本（推荐）：
```bash
./start.sh
```

或手动启动：
```bash
cd backend
python3 app.py
```

然后在浏览器中访问: http://localhost:5000

## 使用说明

1. **创建群组**: 点击"创建群组"按钮，系统会生成群公钥和管理员密钥
2. **添加成员**: 选择群组并输入成员信息，系统会执行加入协议并生成成员密钥
3. **签名消息**: 选择群组、成员和输入消息，生成群签名
4. **验证签名**: 点击"验证"按钮验证签名的有效性
5. **追踪签名**: 管理员可以点击"打开"按钮，查看签名者身份

## API 接口

### 群组管理
- `GET /api/groups` - 获取所有群组
- `POST /api/groups` - 创建新群组
- `GET /api/groups/<id>` - 获取群组详情

### 成员管理
- `GET /api/members` - 获取成员列表（可选参数: `group_id`）
- `POST /api/members` - 添加新成员
- `GET /api/members/<id>` - 获取成员详情

### 签名管理
- `GET /api/signatures` - 获取签名列表（可选参数: `group_id`）
- `POST /api/signatures` - 创建签名
- `POST /api/signatures/<id>/verify` - 验证签名
- `POST /api/signatures/<id>/open` - 打开签名（追踪）

## 注意事项

- 密钥文件存储在 `backend/data/` 目录下，请妥善保管
- 首次运行前需要先构建 C 库（见安装步骤 1）
- 确保 Python 版本 >= 3.6
- 如果遇到导入错误，请确保已正确安装 pygroupsig