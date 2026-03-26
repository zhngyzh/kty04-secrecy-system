# 安装指南

## 前置条件

1. Python 3.10 或更高版本
2. uv（用于项目虚拟环境与依赖管理）

## 完整安装步骤

### 步骤 1: 同步项目依赖

```bash
uv sync
```

### 步骤 2: 库使用说明（外部参考）

本项目文档聚焦管理系统，不展开群签名库内部构建与接口。
请直接参考：https://github.com/IBM/libgroupsig

### 步骤 3: 运行系统

```bash
bash start.sh
```

或手动启动：

```bash
uv run python backend/app.py
```

然后在浏览器中访问: http://localhost:5000

## 故障排除

### 问题 1: `ModuleNotFoundError: No module named 'pygroupsig'`

**解决方案**: 
- 确保已执行 `uv sync`
- 尝试重新同步: `uv sync --reinstall`
- 若仍失败，请按官方库文档排查：https://github.com/IBM/libgroupsig

### 问题 2: 导入错误或运行时错误

**解决方案**:
- 检查 Python 版本: `uv run python --version`（需要 >= 3.10）
- 检查所有依赖是否安装: `uv pip list --python .venv/bin/python | grep -E "Flask|cffi|pygroupsig"`
- 查看错误日志，通常会有更详细的错误信息
