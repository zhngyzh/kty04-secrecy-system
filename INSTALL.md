# 安装指南

## 前置条件

1. Python 3.6 或更高版本
2. CMake 和 Make（用于构建 C 库）
3. C/C++ 编译工具链

## 完整安装步骤

### 步骤 1: 构建 libgroupsig C 库

```bash
cd /home/zhangyzh/projects/groupsig/newlibgroupsig/libgroupsig
mkdir -p build
cd build
cmake ..
make
```

**注意**: 确保构建成功，特别是 `libkty04.a` 文件应该存在于 `build/lib/` 目录下。

### 步骤 2: 安装 pygroupsig Python 包装器

```bash
cd ../src/wrappers/python
pip install -e .
```

**验证安装**:
```bash
python3 -c "from pygroupsig import constants; print('KTY04_CODE:', constants.KTY04_CODE)"
```

如果输出 `KTY04_CODE: 0`，说明安装成功。

### 步骤 3: 安装项目依赖

```bash
cd /home/zhangyzh/projects/groupsig/kty04-management
pip install -r requirements.txt
```

### 步骤 4: 运行系统

**方式一：使用启动脚本（推荐）**
```bash
./start.sh
```

**方式二：手动启动**
```bash
cd backend
python3 app.py
```

然后在浏览器中访问: http://localhost:5000

## 故障排除

### 问题 1: `ModuleNotFoundError: No module named 'pygroupsig'`

**解决方案**: 
- 确保已完成步骤 1 和步骤 2
- 检查是否在正确的 Python 环境中安装
- 尝试重新安装: `cd newlibgroupsig/libgroupsig/src/wrappers/python && pip install -e . --force-reinstall`

### 问题 2: `libkty04.a: No such file or directory`

**解决方案**:
- 确保已完成步骤 1，并且构建成功
- 检查 `newlibgroupsig/libgroupsig/build/lib/libkty04.a` 是否存在
- 如果不存在，重新运行 `make` 命令

### 问题 3: 导入错误或运行时错误

**解决方案**:
- 检查 Python 版本: `python3 --version`（需要 >= 3.6）
- 检查所有依赖是否安装: `pip list | grep -E "Flask|cffi"`
- 查看错误日志，通常会有更详细的错误信息

## 验证安装

运行以下测试脚本验证安装：

```python
# test_install.py
try:
    from pygroupsig import groupsig, constants
    
    code = constants.KTY04_CODE
    groupsig.init(code, 0)
    group = groupsig.setup(code)
    print("✓ KTY04 初始化成功")
    print(f"✓ 群组创建成功 (ID: {group})")
    groupsig.clear(code)
    print("✓ 所有测试通过！")
except Exception as e:
    print(f"✗ 错误: {e}")
    import traceback
    traceback.print_exc()
```

保存为 `test_install.py` 并运行：
```bash
python3 test_install.py
```
