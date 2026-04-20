# 多级权限系统增强 - 检查清单

> **任务ID**: #3
> **预计时间**: 1周
> **优先级**: 🔴 高

---

## 📋 Phase 1: 研究与设计（Day 1）

### 1.1 研究现有权限系统
- [ ] 阅读 `core/tools/permissions.py` 现有实现
- [ ] 理解当前权限检查流程
- [ ] 分析现有 PermissionRule 结构
- [ ] 识别待改进点

### 1.2 研究 OpenHarness 权限系统
- [ ] 阅读 `/Users/xujian/Downloads/OpenHarness-main/permissions/` 目录
- [ ] 分析三种权限模式的实现
- [ ] 研究路径级规则配置
- [ ] 理解权限检查流程

### 1.3 设计增强方案
- [ ] 定义 PermissionMode 枚举（DEFAULT/AUTO/PLAN）
- [ ] 设计路径规则配置结构
- [ ] 设计权限模式切换接口
- [ ] 确定向后兼容策略
- [ ] 编写设计文档

**输出**：
- `docs/api/PERMISSION_MODES_DESIGN.md`

---

## 📋 Phase 2: 核心组件实现（Day 2-4）

### 2.1 创建目录结构
- [ ] 创建 `core/tools/permissions/` 目录（如果不存在）
- [ ] 创建 `tests/tools/test_permission_modes.py` 测试文件

### 2.2 实现权限模式定义
- [ ] 定义 `PermissionMode` 枚举类
- [ ] 实现 `DEFAULT` 模式行为
- [ ] 实现 `AUTO` 模式行为
- [ ] 实现 `PLAN` 模式行为
- [ ] 添加模式转换逻辑

**文件**：`core/tools/permissions/modes.py`

### 2.3 实现路径规则配置
- [ ] 定义 `PathRule` 数据类
- [ ] 实现模式匹配逻辑（支持通配符）
- [ ] 实现规则优先级排序
- [ ] 实现规则冲突解决
- [ ] 添加规则验证

**文件**：`core/tools/permissions/path_rules.py`

### 2.4 增强权限检查器
- [ ] 扩展 `PermissionChecker` 类
- [ ] 集成权限模式检查
- [ ] 集成路径规则检查
- [ ] 实现命令黑名单检查
- [ ] 优化检查性能

**文件**：`core/tools/permissions/permission_checker.py`

### 2.5 实现权限模式管理器
- [ ] 定义 `PermissionManager` 类
- [ ] 实现 `set_mode()` 方法
- [ ] 实现 `get_mode()` 方法
- [ ] 实现 `add_path_rule()` 方法
- [ ] 实现 `remove_path_rule()` 方法
- [ ] 实现持久化配置

**文件**：`core/tools/permissions/manager.py`

---

## 📋 Phase 3: 集成与迁移（Day 5）

### 3.1 更新现有权限上下文
- [ ] 在 `ToolPermissionContext` 中集成权限模式
- [ ] 保持向后兼容性
- [ ] 添加模式切换方法
- [ ] 更新 `check_permission()` 方法

### 3.2 迁移现有权限配置
- [ ] 分析现有权限配置文件
- [ ] 转换为新的权限模式格式
- [ ] 创建默认配置模板
- [ ] 提供迁移工具脚本

**脚本**：`scripts/migrate_permissions.py`

### 3.3 集成到工具调用流程
- [ ] 更新 `tool_call_manager.py`
- [ ] 在工具调用前检查权限模式
- [ ] 实现 PLAN 模式的写入阻止
- [ ] 添加权限模式提示

### 3.4 集成到 Gateway
- [ ] 更新 Gateway 权限中间件
- [ ] 添加权限模式 API 端点
- [ ] 实现权限模式切换接口
- [ ] 更新 Gateway 配置

---

## 📋 Phase 4: 测试与验证（Day 6）

### 4.1 单元测试
- [ ] 测试 PermissionMode 枚举
- [ ] 测试路径规则匹配
- [ ] 测试权限模式行为（DEFAULT/AUTO/PLAN）
- [ ] 测试权限模式切换
- [ ] 测试路径规则优先级
- [ ] 测试规则冲突解决
- [ ] 测试权限检查性能

**目标覆盖率**：>85%

### 4.2 集成测试
- [ ] 测试 DEFAULT 模式工具调用
- [ ] 测试 AUTO 模式工具调用
- [ ] 测试 PLAN 模式写入阻止
- [ ] 测试路径规则应用
- [ ] 测试权限模式切换
- [ ] 测试配置持久化

### 4.3 安全测试
- [ ] 测试路径绕过攻击
- [ ] 测试命令注入防护
- [ ] 测试权限提升攻击
- [ ] 测试竞态条件
- [ ] 测试并发访问

### 4.4 性能测试
- [ ] 基准测试权限检查性能
- [ ] 测试高并发场景
- [ ] 测试大量规则场景
- [ ] 优化性能瓶颈

**目标**：权限检查延迟 <1ms

---

## 📋 Phase 5: 文档与部署（Day 7）

### 5.1 编写文档
- [ ] 更新 `CLAUDE.md` 权限系统说明
- [ ] 编写 `PERMISSION_MODES_API.md` API 文档
- [ ] 编写 `PERMISSION_MODES_GUIDE.md` 使用指南
- [ ] 编写 `PERMISSION_MIGRATION.md` 迁移指南
- [ ] 更新配置文件示例

### 5.2 代码审查
- [ ] 自我代码审查
- [ ] 运行 ruff 格式检查
- [ ] 运行 mypy 类型检查
- [ ] 运行 pytest 测试套件
- [ ] 修复所有警告和错误

### 5.3 部署准备
- [ ] 准备配置文件模板
- [ ] 准备迁移脚本
- [ ] 准备回滚方案
- [ ] 通知团队成员

### 5.4 部署与验证
- [ ] 部署到测试环境
- [ ] 执行权限模式切换测试
- [ ] 验证安全防护有效
- [ ] 监控性能指标
- [ ] 收集用户反馈

---

## ✅ 验收标准

### 功能验收
- [ ] 三种权限模式正确实现
- [ ] 路径规则正确匹配和优先级排序
- [ ] 权限模式切换无缝
- [ ] 向后兼容性保持
- [ ] 配置持久化正常

### 安全验收
- [ ] 路径绕过攻击防护有效
- [ ] 命令注入防护有效
- [ ] 权限提升攻击防护有效
- [ ] 并发访问安全
- [ ] 通过安全测试

### 性能验收
- [ ] 权限检查延迟 <1ms
- [ ] 高并发场景无明显下降
- [ ] 大量规则场景性能可接受
- [ ] 内存占用增加可控

### 质量验收
- [ ] 单元测试覆盖率 >85%
- [ ] 所有测试通过
- [ ] 代码审查通过
- [ ] 文档完整
- [ ] 无已知安全漏洞

---

## 🚨 风险与缓解

| 风险 | 影响 | 概率 | 缓解措施 |
|------|------|------|----------|
| 破坏向后兼容性 | 高 | 中 | 保留旧接口，渐进式迁移 |
| 性能下降 | 中 | 低 | 性能基准测试，优化检查逻辑 |
| 安全漏洞 | 高 | 低 | 安全测试，代码审查 |
| 配置迁移失败 | 中 | 中 | 提供迁移工具，充分测试 |

---

## 📊 进度跟踪

- **Phase 1 完成度**：___ / 5
- **Phase 2 完成度**：___ / 20
- **Phase 3 完成度**：___ / 12
- **Phase 4 完成度**：___ / 20
- **Phase 5 完成度**：___ / 14

**总体完成度**：___ / 71 (___%)

---

## 📝 配置示例

### 权限模式配置
```yaml
# config/permissions.yaml
permission:
  mode: default  # default | auto | plan

  path_rules:
    - pattern: "/etc/*"
      allow: false
      priority: 100
      reason: "系统目录禁止访问"

    - pattern: "/Users/xujian/Athena工作平台/**"
      allow: true
      priority: 50
      reason: "项目目录允许访问"

    - pattern: "/tmp/*"
      allow: true
      priority: 10
      reason: "临时目录允许访问"

  denied_commands:
    - "rm -rf /"
    - "DROP TABLE *"
    - "shutdown -h now"

  plan_mode_writes:
    - "file:write"
    - "file:edit"
    - "bash:execute"
```

### 权限模式行为
| 模式 | 未匹配规则 | 匹配允许规则 | 匹配拒绝规则 |
|------|-----------|------------|------------|
| DEFAULT | 询问用户 | 允许执行 | 拒绝执行 |
| AUTO | 自动拒绝 | 允许执行 | 拒绝执行 |
| PLAN | 自动拒绝 | 允许读取/拒绝写入 | 拒绝执行 |

---

**创建时间**：2026-04-20
**最后更新**：2026-04-20
**负责人**：徐健
