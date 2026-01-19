#!/bin/bash
# KTY04 管理系统启动脚本

echo "=== KTY04 群签名管理系统 ==="
echo ""

# 检查 pygroupsig 是否安装
echo "检查 pygroupsig 安装..."
python3 -c "from pygroupsig import constants; print('✓ pygroupsig 已安装')" 2>/dev/null || {
    echo "✗ pygroupsig 未安装"
    echo ""
    echo "请先构建和安装 pygroupsig:"
    echo "  1. cd newlibgroupsig/libgroupsig"
    echo "  2. mkdir -p build && cd build"
    echo "  3. cmake .. && make"
    echo "  4. cd ../src/wrappers/python"
    echo "  5. pip install -e ."
    exit 1
}

# 检查依赖
echo "检查 Python 依赖..."
pip show Flask > /dev/null 2>&1 || {
    echo "安装依赖..."
    pip install -r requirements.txt
}

# 启动应用
echo ""
echo "启动 Flask 应用..."
echo "访问地址: http://localhost:5000"
echo ""
cd backend
python3 app.py
