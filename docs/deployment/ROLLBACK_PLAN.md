# 执行模块生产环境回滚计划

**项目**: Athena工作平台 - 执行模块 (core.execution)
**版本**: v2.0.0
**创建日期**: 2026-01-27
**负责人**: 运维团队

---

## 📋 目录

1. [概述](#概述)
2. [回滚决策标准](#回滚决策标准)
3. [回滚前准备](#回滚前准备)
4. [回滚步骤](#回滚步骤)
5. [回滚后验证](#回滚后验证)
6. [回滚后行动](#回滚后行动)
7. [紧急联系人](#紧急联系人)

---

## 概述

### 目的

本文档定义了执行模块v2.0.0从生产环境回滚到之前版本的详细流程和标准，确保在出现问题时能够快速、安全地恢复服务。

### 范围

- **适用模块**: core.execution (执行模块)
- **回滚目标版本**: v1.x (根据实际部署历史确定)
- **回滚类型**: 完整模块回滚

### 回滚原则

1. **快速优先**: 在满足回滚条件时，立即启动回滚流程
2. **数据安全**: 确保回滚过程中不丢失关键数据
3. **服务连续**: 最小化服务中断时间
4. **可追溯**: 记录所有回滚操作和决策

---

## 回滚决策标准

### 自动触发条件 (P0 - 立即回滚)

满足以下任一条件时，**自动触发紧急回滚**：

| 条件 | 阈值 | 触发时间 | 说明 |
|------|------|----------|------|
| 服务可用性 | down | 2分钟 | 实例完全不可访问 |
| 错误率 | >20% | 2分钟 | 任务失败率超过20% |
| 数据丢失 | 检测到 | 立即 | 任何数据丢失或损坏 |
| 安全漏洞 | 严重 | 立即 | 发现严重安全漏洞 |
| 资源耗尽 | OOM | 检测到 | 内存溢出或资源耗尽 |

### 手动触发条件 (P1 - 评估后回滚)

满足以下条件时，**评估后决定是否回滚**：

| 条件 | 阈值 | 持续时间 | 决策建议 |
|------|------|----------|----------|
| 错误率升高 | >10% | 10分钟 | 强烈建议回滚 |
| 性能严重下降 | P99>10分钟 | 15分钟 | 建议回滚 |
| 队列持续积压 | >95% | 20分钟 | 建议回滚 |
| 内存泄漏 | 持续增长 | 30分钟 | 建议回滚 |
| 功能异常 | 核心功能不可用 | 立即 | 立即回滚 |

### 监控条件 (P2 - 观察并准备)

以下情况需要**密切监控**，准备回滚：

| 条件 | 阈值 | 持续时间 | 行动 |
|------|------|----------|------|
| 错误率轻微上升 | >5% | 20分钟 | 加强监控 |
| 性能轻微下降 | P95>3分钟 | 30分钟 | 分析原因 |
| 资源使用偏高 | >80% | 30分钟 | 准备扩容 |

### 决策流程

```
问题检测 → 评估严重程度 → 查看决策标准
    ↓
是否满足P0条件？
    ├─ 是 → 立即回滚（无需审批）
    └─ 否 → 是否满足P1条件？
            ├─ 是 → 评估影响 → 团队负责人批准 → 回滚
            └─ 否 → 持续监控 → 记录观察
```

### 回滚审批

| 回滚类型 | 审批要求 | 审批人 |
|---------|---------|--------|
| P0紧急回滚 | 无需审批，立即执行 | 值班工程师 |
| P1标准回滚 | 需要审批 | 技术负责人 |
| P2预防性回滚 | 需要评估 | 团队讨论 |

---

## 回滚前准备

### 1. 备份当前状态

在启动回滚前，**必须**备份以下信息：

```bash
# 备份当前配置
cp /opt/athena/config/production.yaml /opt/athena/backup/config_$(date +%Y%m%d_%H%M%S).yaml

# 备份日志
cp -r /var/log/athena/execution /opt/athena/backup/logs_$(date +%Y%m%d_%H%M%S)

# 备份状态文件（如果存在）
cp /var/lib/athena/state/* /opt/athena/backup/state_$(date +%Y%m%d_%H%M%S)/

# 记录当前任务状态
curl http://localhost:8080/api/execution/status > /opt/athena/backup/status_$(date +%Y%m%d_%H%M%S).json
```

### 2. 收集诊断信息

```bash
# 保存当前指标
curl http://localhost:9090/metrics > /opt/athena/backup/metrics_$(date +%Y%m%d_%H%M%S).txt

# 保存错误日志
tail -1000 /var/log/athena/execution/errors.log > /opt/athena/backup/error_tail_$(date +%Y%m%d_%H%M%S).log

# 系统状态
top -b -n 1 > /opt/athena/backup/system_$(date +%Y%m%d_%H%M%S).txt
df -h >> /opt/athena/backup/system_$(date +%Y%m%d_%H%M%S).txt
free -h >> /opt/athena/backup/system_$(date +%Y%m%d_%H%M%S).txt
```

### 3. 通知相关人员

发送回滚通知到：

- ✅ 运维团队（Slack/钉钉群）
- ✅ 开发团队负责人
- ✅ 产品团队（如果影响用户体验）
- ✅ 管理层（如果是P0回滚）

通知模板：

```
【回滚通知】执行模块回滚启动

时间: {timestamp}
回滚版本: v2.0.0 → v1.x
回滚原因: {reason}
负责人: {operator}
预计耗时: 5-10分钟

请关注系统状态和用户反馈。
```

### 4. 准备回滚环境

```bash
# 检查回滚版本可用性
ls -la /opt/athena/versions/v1.x/

# 验证回滚版本配置
/opt/athena/versions/v1.x/bin/athena-exec --version

# 准备回滚脚本
chmod +x /opt/athena/scripts/rollback_execution.sh
```

---

## 回滚步骤

### 方式A: 快速回滚（推荐用于P0紧急情况）

**预计耗时**: 3-5分钟

```bash
#!/bin/bash
# 快速回滚脚本
# 使用方法: ./rollback_execution.sh v1.x.y

ROLLBACK_VERSION=$1
BACKUP_DIR="/opt/athena/backup/rollback_$(date +%Y%m%d_%H%M%S)"
CURRENT_VERSION="v2.0.0"

echo "开始快速回滚: $CURRENT_VERSION → $ROLLBACK_VERSION"

# 1. 创建备份目录
mkdir -p $BACKUP_DIR

# 2. 停止当前服务
echo "停止当前服务..."
systemctl stop athena-execution
sleep 5

# 3. 验证服务已停止
if systemctl is-active --quiet athena-execution; then
    echo "警告: 服务未完全停止，强制终止..."
    systemctl kill athena-execution
    sleep 2
fi

# 4. 备份当前版本
echo "备份当前版本..."
cp -r /opt/athena/core/execution $BACKUP_DIR/
cp /opt/athena/config/production.yaml $BACKUP_DIR/

# 5. 切换到回滚版本
echo "切换到回滚版本..."
rm /opt/athena/core/execution
ln -s /opt/athena/versions/$ROLLBACK_VERSION/core/execution /opt/athena/core/execution

# 6. 恢复配置（如果需要）
# cp $BACKUP_DIR/production.yaml /opt/athena/config/

# 7. 启动服务
echo "启动服务..."
systemctl start athena-execution

# 8. 等待服务就绪
echo "等待服务就绪..."
for i in {1..30}; do
    if curl -s http://localhost:8080/health > /dev/null; then
        echo "服务已就绪"
        break
    fi
    echo "等待中... ($i/30)"
    sleep 2
done

# 9. 验证版本
echo "验证版本..."
/opt/athena/core/execution/bin/version-check

echo "快速回滚完成！"
```

### 方式B: 蓝绿回滚（推荐用于P1标准回滚）

**预计耗时**: 10-15分钟

```bash
#!/bin/bash
# 蓝绿回滚脚本
# 在保留旧版本（绿环境）的情况下部署新版本（蓝环境）

BLUE_PORT=8080
GREEN_PORT=8081
CURRENT_ENV="blue"  # 或 "green"
ROLLBACK_VERSION="v1.x.y"

echo "开始蓝绿回滚..."

# 1. 识别当前环境
if netstat -tuln | grep -q ":$BLUE_PORT "; then
    CURRENT_ENV="blue"
    ROLLBACK_ENV="green"
else
    CURRENT_ENV="green"
    ROLLBACK_ENV="blue"
fi

echo "当前环境: $CURRENT_ENV, 回滚到: $ROLLBACK_ENV"

# 2. 在回滚环境启动旧版本
echo "在$ROLLBACK_ENV环境启动旧版本..."
systemctl start athena-execution@$ROLLBACK_ENV

# 3. 等待回滚环境就绪
echo "等待$ROLLBACK_ENV环境就绪..."
for i in {1..60}; do
    if curl -s http://localhost:$((ROLLBACK_ENV == "green" ? GREEN_PORT : BLUE_PORT))/health > /dev/null; then
        echo "$ROLLBACK_ENV环境已就绪"
        break
    fi
    sleep 2
done

# 4. 切换负载均衡器
echo "切换流量到$ROLLBACK_ENV环境..."
# 这里需要根据实际的负载均衡器配置调整
# 例如: nginx -s reload 或更新负载均衡器配置

# 5. 验证新环境正常
sleep 10
if ! curl -s http://localhost/health > /dev/null; then
    echo "错误: 切换后服务不正常，立即切换回去！"
    systemctl stop athena-execution@$ROLLBACK_ENV
    # 切换回原环境
    exit 1
fi

# 6. 停止原环境
echo "停止$CURRENT_ENV环境..."
systemctl stop athena-execution@$CURRENT_ENV

echo "蓝绿回滚完成！"
```

### 方式C: 金丝雀回滚（用于部分回滚）

**预计耗时**: 20-30分钟

```bash
#!/bin/bash
# 金丝雀回滚脚本
# 逐步将流量从新版本切换回旧版本

# 步骤1: 将10%流量切回旧版本
echo "步骤1: 切换10%流量到旧版本..."
update_canary_weight(old=10, new=90)
sleep 300  # 观察5分钟

# 步骤2: 将50%流量切回旧版本
echo "步骤2: 切换50%流量到旧版本..."
update_canary_weight(old=50, new=50)
sleep 600  # 观察10分钟

# 步骤3: 将100%流量切回旧版本
echo "步骤3: 切换100%流量到旧版本..."
update_canary_weight(old=100, new=0)
sleep 300  # 观察5分钟

# 步骤4: 停止新版本
echo "步骤4: 停止新版本实例..."
systemctl stop athena-execution@new

echo "金丝雀回滚完成！"
```

---

## 回滚后验证

### 1. 基础健康检查

```bash
# 检查服务状态
systemctl status athena-execution

# 检查进程
ps aux | grep athena-execution

# 检查端口
netstat -tuln | grep 8080

# 健康检查
curl http://localhost:8080/health
```

### 2. 功能验证

```bash
# 提交测试任务
curl -X POST http://localhost:8080/api/execution/tasks \
  -H "Content-Type: application/json" \
  -d '{"task_id": "rollback_test_001", "name": "回滚验证任务"}'

# 检查任务状态
curl http://localhost:8080/api/execution/tasks/rollback_test_001

# 验证任务执行
# 预期: 任务能够正常完成
```

### 3. 性能验证

```bash
# 检查关键指标
curl http://localhost:9090/metrics | grep athena_execution

# 验证指标在正常范围:
# - 错误率 < 5%
# - P95延迟 < 3分钟
# - 队列使用率 < 70%
# - 内存使用率 < 80%
```

### 4. 日志验证

```bash
# 检查是否有严重错误
tail -100 /var/log/athena/execution/errors.log

# 检查启动日志
tail -100 /var/log/athena/execution/execution.log

# 验证无异常错误
# 预期: 无ERROR或CRITICAL级别日志
```

### 5. 验证清单

- [ ] 服务运行正常
- [ ] 健康检查通过
- [ ] 测试任务执行成功
- [ ] 错误率 < 5%
- [ ] 性能指标正常
- [ ] 无严重错误日志
- [ ] 监控告警清除
- [ ] 用户反馈正常

---

## 回滚后行动

### 1. 通知回滚完成

发送回滚完成通知：

```
【回滚完成】执行模块回滚完成

时间: {timestamp}
回滚版本: v2.0.0 → v1.x.y
回滚原因: {reason}
负责人: {operator}
回滚耗时: {duration}
验证状态: ✅ 通过

服务已恢复正常。
```

### 2. 问题分析

收集以下信息用于问题分析：

1. **失败现象**
   - 具体错误信息
   - 影响范围
   - 持续时间

2. **诊断数据**
   - 备份的日志文件
   - 备份的指标数据
   - 系统状态信息

3. **时间线**
   - 问题发生时间
   - 回滚触发时间
   - 回滚完成时间

### 3. 创建问题报告

使用模板创建问题报告：

```markdown
# 问题报告: {问题标题}

## 基本信息
- **报告时间**: {timestamp}
- **影响版本**: v2.0.0
- **回滚版本**: v1.x.y
- **严重级别**: {P0/P1/P2}
- **负责人**: {name}

## 问题描述
{详细描述问题现象}

## 影响范围
- 用户影响: {描述}
- 数据影响: {描述}
- 服务影响: {描述}

## 根本原因
{分析结果}

## 临时解决方案
{回滚操作}

## 永久解决方案
{修复计划}

## 预防措施
{如何防止类似问题再次发生}
```

### 4. 后续行动计划

#### 短期（24小时内）

- [ ] 完成问题分析报告
- [ ] 确定根本原因
- [ ] 制定修复方案
- [ ] 更新回滚文档（如果发现问题）

#### 中期（1周内）

- [ ] 实施修复方案
- [ ] 增强测试覆盖
- [ ] 优化监控告警
- [ ] 更新部署文档

#### 长期（1个月内）

- [ ] 完善自动化测试
- [ ] 优化回滚流程
- [ ] 加强代码审查
- [ ] 知识分享和培训

---

## 紧急联系人

### 运维团队

| 角色 | 姓名 | 联系方式 | 值班时间 |
|------|------|----------|----------|
| 运维负责人 | 张三 | +86-138-0000-0001 | 工作日 9:00-18:00 |
| 值班工程师A | 李四 | +86-138-0000-0002 | 7x24 |
| 值班工程师B | 王五 | +86-138-0000-0003 | 7x24 |

### 开发团队

| 角色 | 姓名 | 联系方式 | 值班时间 |
|------|------|----------|----------|
| 技术负责人 | 赵六 | +86-138-0000-0004 | 工作日 9:00-18:00 |
| 执行模块负责人 | 钱七 | +86-138-0000-0005 | 工作日 9:00-18:00 |

### 管理层

| 角色 | 姓名 | 联系方式 | 值班时间 |
|------|------|----------|----------|
| 技术总监 | 孙八 | +86-138-0000-0006 | 工作日 9:00-18:00 |
| 产品负责人 | 周九 | +86-138-0000-0007 | 工作日 9:00-18:00 |

### 通信渠道

- **运维Slack**: #ops-alerts
- **开发Slack**: #dev-emergency
- **钉钉群**: Athena运维团队
- **邮件**: ops-team@example.com

---

## 附录

### A. 回滚决策树

```
问题检测
    ↓
问题严重程度评估
    ├─ P0 (服务down/数据丢失/安全漏洞)
    │   └─ 立即回滚，无需审批
    │
    ├─ P1 (错误率>10%/性能严重下降)
    │   └─ 评估影响
    │       ├─ 影响严重 → 审批后回滚
    │       └─ 影响可控 → 持续监控
    │
    └─ P2 (轻微问题)
        └─ 加强监控，记录观察
            └─ 如果恶化 → 升级到P1
```

### B. 常见回滚场景

#### 场景1: 服务完全不可用

```bash
# 快速诊断
systemctl status athena-execution
journalctl -u athena-execution -n 100

# 快速回滚
/opt/athena/scripts/rollback_execution.sh v1.x.y
```

#### 场景2: 错误率飙升

```bash
# 检查错误日志
tail -f /var/log/athena/execution/errors.log

# 检查指标
curl http://localhost:9090/metrics | grep error_rate

# 如果持续10分钟 >10%，执行回滚
/opt/athena/scripts/rollback_execution.sh v1.x.y
```

#### 场景3: 内存泄漏

```bash
# 检查内存使用
free -h
ps aux | grep athena-execution

# 如果持续增长且接近上限，执行回滚
/opt/athena/scripts/rollback_execution.sh v1.x.y
```

### C. 回滚检查清单

### 回滚前检查 ✅

- [ ] 确认回滚版本可用
- [ ] 备份当前配置和数据
- [ ] 收集诊断信息
- [ ] 通知相关人员
- [ ] 准备回滚脚本

### 回滚中检查 ⚠️

- [ ] 服务成功停止
- [ ] 备份创建成功
- [ ] 版本切换成功
- [ ] 配置恢复成功（如需要）
- [ ] 服务启动成功

### 回滚后检查 ✅

- [ ] 服务状态正常
- [ ] 健康检查通过
- [ ] 测试任务成功
- [ ] 错误率正常
- [ ] 性能指标正常
- [ ] 无严重错误日志
- [ ] 通知回滚完成
- [ ] 创建问题报告

---

**文档版本**: 1.0.0
**最后更新**: 2026-01-27
**审核人**: 技术负责人
**下次审核**: 生产部署后
