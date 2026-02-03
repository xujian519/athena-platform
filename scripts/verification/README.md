# Athena模块验证脚本使用说明

## 📋 概述

此目录包含Athena平台各模块的验证脚本，用于在集成到OpenClaw之前验证模块的可用性。

**验证原则**: 每个模块必须验证通过后才能集成到OpenClaw。

## 🚀 快速开始

### 1. 验证所有模块

```bash
cd /Users/xujian/Athena工作平台/scripts/verification
./verify_all.sh
```

### 2. 验证单个模块

```bash
# 验证动态提示词系统
./verify_prompt_system.sh

# 验证权利要求解析
./verify_claim_parser.sh

# 验证IPC分类系统
./verify_ipc_system.sh
```

### 3. 验证指定模块

```bash
# 只验证P0优先级模块
./verify_all.sh prompt_system:动态提示词系统:P0

# 验证多个模块
./verify_all.sh \
    prompt_system:动态提示词系统:P0 \
    claim_parser:权利要求解析:P1 \
    ipc_system:IPC分类系统:P1
```

## 📁 验证脚本列表

| 脚本名称 | 验证模块 | 优先级 | 状态 |
|---------|---------|-------|------|
| `verify_prompt_system.sh` | 动态提示词系统 | P0 | ⏳ 待运行 |
| `verify_claim_parser.sh` | 权利要求解析 | P1 | ⏳ 待运行 |
| `verify_ipc_system.sh` | IPC分类系统 | P1 | 📝 待创建 |
| `verify_figure_recognition.sh` | 附图识别 | P1 | 📝 待创建 |
| `verify_deep_analysis.sh` | 深度分析 | P1 | 📝 待创建 |
| `verify_dolphin_parser.sh` | Dolphin文档解析 | P1 | 📝 待创建 |
| `verify_invalidity_strategy.sh` | 无效宣告策略 | P2 | 📝 待创建 |
| `verify_dual_graph.sh` | 双图构建 | P2 | 📝 待创建 |

## ✅ 验证标准

每个模块需要通过以下标准：

1. **功能可用性** ✅ - 核心功能正常运行
2. **API可访问性** ✅ - 可以通过API调用
3. **结果准确性** ✅ - 返回结果符合预期
4. **性能可接受性** ✅ - 响应时间 < 30秒
5. **错误处理** ✅ - 异常情况有合理处理

## 📊 验证结果

验证完成后，结果会显示：

```
==========================================
 最终验证总结
==========================================

验证模块总数: 8
通过: 5
失败: 3

✅ 成功模块列表:
  - 动态提示词系统
  - 权利要求解析
  ...

❌ 失败模块列表:
  - 附图识别
  - 深度分析
  ...
```

## 🔄 验证流程

### Phase 1: 准备

```bash
# 1. 确保Athena服务运行中
cd /Users/xujian/Athena工作平台/core/api
python main.py

# 2. 检查依赖服务状态
# Neo4j: bolt://localhost:7687
# PostgreSQL: localhost:15432
# Redis: localhost:6379
# Qdrant: localhost:6333
```

### Phase 2: 执行验证

```bash
# 运行所有验证
cd /Users/xujian/Athena工作平台/scripts/verification
./verify_all.sh
```

### Phase 3: 查看结果

```bash
# 查看验证进度文档
cat /Users/xujian/Athena工作平台/docs/OPENCLAW_INTEGRATION_PROGRESS.md
```

### Phase 4: 处理失败

如果某个模块验证失败：

1. 查看详细错误信息
2. 修复问题
3. 重新验证该模块
4. 更新进度文档

## 📝 验证报告

每个模块验证通过后，在进度文档中填写验证报告：

```markdown
### [模块名称] 验证报告

**验证日期**: 2026-02-03
**验证人**: 徐健

#### 验证结果
- ✅ 功能可用性
- ✅ API可访问性
- ✅ 结果准确性
- ✅ 性能可接受性
- ✅ 错误处理

#### 结论
✅ 通过验证，可以集成
```

## 🎯 下一步

验证通过后，进入技能开发阶段：

```bash
# 1. 开发核心技能 athena-legal
# 2. 逐个开发扩展技能
# 3. 集成测试
# 4. 部署到OpenClaw
```

## 📞 帮助

如遇问题，请检查：

1. Athena服务是否运行: `curl http://localhost:8000/health`
2. Python版本: `python3 --version` (需要 >= 3.11)
3. 依赖服务状态: `lsof -i :7687 :15432 :6379 :6333`
4. 错误日志: `/Users/xujian/Athena工作平台/logs/`

---

**最后更新**: 2026-02-03
**维护者**: 徐健 (xujian519@gmail.com)
