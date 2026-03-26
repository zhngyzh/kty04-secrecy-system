# 文档导航

本项目文档按用途分层，避免重复维护与信息冲突。

## 1. 入门与运行

- 项目总览与核心流程: ../README.md
- 安装与环境排查: ../INSTALL.md
- 快速命令与常见操作: ../QUICK_REFERENCE.md

## 2. 设计与实现

- 权限模型与认证边界: ../PERMISSIONS.md
- 实现状态与架构摘要: ../IMPLEMENTATION_SUMMARY.md
- 论文配图与 Mermaid 图: THESIS_DIAGRAMS.md

## 3. 文档规范

- 单一事实来源原则:
  - 系统能力、API 范围以 ../README.md 为准。
  - 安装细节以 ../INSTALL.md 为准。
  - 权限策略以 ../PERMISSIONS.md 为准。
- 变更同步原则:
  - 代码修改涉及接口/权限/测试命令时，需同步更新对应文档。
- 过时信息处理:
  - 不保留历史脚本命令（例如已删除的根目录测试脚本）。
  - 优先保留当前可执行命令与可复现流程。

## 4. 当前测试体系

已统一为 pytest 风格：

- 功能测试目录: ../tests/functional
- 性能测试目录: ../tests/performance
- 共享夹具与参数: ../tests/conftest.py

运行方式见 ../README.md 的“测试（pytest）”章节。
