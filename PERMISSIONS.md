# 权限系统说明

## 1. 角色定义

### 管理员（admin）

可执行:
- 创建群组
- 添加成员并分发成员密钥
- 追踪签名者身份
- 查看审计日志与系统统计

### 普通用户（user）

可执行:
- 登录后访问授权资源
- 在所属群组内匿名签名
- 验证签名与声明签名

## 2. 认证机制

请求头使用:
- X-User-ID
- X-Token

后端通过装饰器控制权限边界:
- require_auth: 仅要求登录
- require_admin / require_super_admin: 要求管理员权限

## 3. 关键权限边界

- /api/groups POST: 仅管理员
- /api/members POST: 仅管理员
- /api/documents/<id>/signatures/<sig_id>/trace POST: 仅管理员
- /api/audit/logs GET: 仅管理员
- /api/documents/<id>/sign POST: 登录且属于目标群组成员

## 4. 最小授权原则

- 普通用户默认不可见系统管理与审计能力。
- 文件内容访问可根据业务规则做进一步收敛（例如先签后读）。
- 追踪能力仅在问责场景开放给管理员。

## 5. 测试建议

- 功能测试覆盖正向与越权路径。
- 至少包含以下断言:
  - 普通用户调用管理员接口返回 401 或 403
  - 成员身份不匹配时签名被拒绝
  - 管理员可完成 trace 流程

执行方式参考 README.md 的“测试（pytest）”章节。
