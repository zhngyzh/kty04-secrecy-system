#!/bin/bash
# KTY04 管理系统启动脚本

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "=== KTY04 群签名管理系统 ==="
echo ""

# 检查 pygroupsig 是否安装
echo "检查 pygroupsig 安装..."
if command -v uv >/dev/null 2>&1; then
    PY_CMD="uv run python"
    echo "使用 uv 项目环境"
    uv sync
else
    PY_CMD="python3"
    echo "未检测到 uv，回退到系统 Python"
fi

$PY_CMD -c "from pygroupsig import constants; print('✓ pygroupsig 已安装')" 2>/dev/null || {
    echo "✗ pygroupsig 未安装"
    echo ""
    echo "请先构建和安装 pygroupsig:"
    echo "  1. cd ../libgroupsig"
    echo "  2. mkdir -p build && cd build"
    echo "  3. cmake .. && make"
    echo "  4. cd ../../kty04-secrecy-system"
    echo "  5. uv sync"
    exit 1
}

# 启动应用
echo ""
echo "启动 Flask 应用..."
echo "访问地址: http://localhost:5000"
echo ""
$PY_CMD backend/app.py
