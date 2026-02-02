# Athena平台AI伦理框架使用指南

## 📋 概述

本框架基于Anthropic Constitutional AI + 维特根斯坦逻辑哲学 + 东方智慧，为平台所有智能体提供统一的伦理约束。

**版本**: 1.0.0
**创建日期**: 2025-01-15

---

## 🏗️ 架构

```
core/ethics/
├── __init__.py              # 模块入口
├── constitution.py          # 宪法原则定义（18条原则）
├── wittgenstein_guard.py    # 维特根斯坦防幻觉模块
├── evaluator.py             # 伦理评估器
├── constraints.py           # 约束执行器
├── monitoring.py            # 伦理监控系统
├── agent_integration.py     # 智能体集成示例
├── xiaonuo_ethics_patch.py  # 小诺伦理补丁
└── README.md                # 本文档
```

---

## 🎯 核心特性

### 1. 多元哲学融合

| 哲学传统 | 原则数 | 核心概念 |
|---------|--------|----------|
| Anthropic Constitutional AI | 6 | Helpful, Harmless, Honest |
| 维特根斯坦逻辑哲学 | 4 | 语言游戏、认识论诚实 |
| 罗尔斯正义论 | 2 | 无知之幕、差异原则 |
| 康德义务论 | 2 | 人类尊严、普遍法则 |
| 儒家思想 | 2 | 仁爱共情、中庸之道 |
| 道家思想 | 2 | 知止不殆、道法自然 |

### 2. 防幻觉机制

**基于维特根斯坦的"公共正确性标准"**:
- 语言游戏边界检查
- 置信度阈值验证
- 家族相似性识别
- 私人语言拒绝

### 3. 实时监控

- 合规率追踪
- 违规检测与告警
- 仪表板数据生成
- 审计日志记录

---

## 🚀 快速开始

### 安装

```bash
# 模块已位于 core/ethics/
# 无需额外安装，确保Python路径包含项目根目录
export PYTHONPATH="/Users/xujian/Athena工作平台:$PYTHONPATH"
```

### 基础使用

```python
from core.ethics import (
    AthenaConstitution,
    EthicsEvaluator,
    WittgensteinGuard
)

# 1. 创建宪法
constitution = AthenaConstitution()

# 2. 查看原则摘要
summary = constitution.get_summary()
print(summary)

# 3. 创建评估器
evaluator = EthicsEvaluator(constitution)

# 4. 评估行动
result = evaluator.evaluate_action(
    agent_id="my_agent",
    action="回答用户问题",
    context={
        "query": "如何检索专利？",
        "confidence": 0.85,
        "domain": "patent"
    }
)

print(f"合规: {result.status.value}")
print(f"评分: {result.overall_score:.2f}")
```

---

## 🎮 为智能体集成伦理约束

### 方法1: 使用装饰器

```python
from core.ethics.constraints import ethical_action

class MyAgent:
    @ethical_action(agent_id="my_agent")
    def answer_question(self, query: str, confidence: float = 0.8):
        return f"回答: {query}"

# 使用
agent = MyAgent()
result = agent.answer_question("问题", confidence=0.9)
```

### 方法2: 使用混入类

```python
from core.ethics.agent_integration import EthicalAgentMixin

class MyEthicalAgent(EthicalAgentMixin):
    def _generate_response(self, query: str, context: dict) -> str:
        # 实现响应逻辑
        return f"响应: {query}"

# 使用
agent = MyEthicalAgent()
result = agent.respond_with_ethics(
    query="专利检索",
    confidence=0.85,
    domain="patent"
)
```

### 方法3: 为小诺添加补丁

```python
from core.ethics.xiaonuo_ethics_patch import patch_xiaonuo

# 假设已有小诺实例
xiaonuo = XiaonuoMain()

# 应用伦理补丁
wrapper = patch_xiaonuo(xiaonuo)

# 查看状态
wrapper.print_ethics_status()
```

---

## 📊 监控与告警

### 设置监控

```python
from core.ethics import EthicsMonitor, setup_logging_alert_handler

monitor = EthicsMonitor(evaluator)

# 设置日志告警
setup_logging_alert_handler(
    monitor,
    log_file="/Users/xujian/Athena工作平台/logs/ethics_alerts.log"
)

# 获取仪表板数据
dashboard = monitor.generate_dashboard_data()
print(dashboard)
```

### 自定义告警处理器

```python
def my_alert_handler(alert):
    # 发送邮件、Slack通知等
    print(f"告警: {alert.level.value} - {alert.message}")

monitor.add_alert_handler(my_alert_handler)
```

---

## 🔧 配置

### 调整置信度阈值

```python
from core.ethics.wittgenstein_guard import WittgensteinGuard, LanguageGame

guard = WittgensteinGuard()

# 修改专利检索游戏的阈值
patent_game = guard.get_game("patent_search")
if patent_game:
    patent_game.confidence_threshold = 0.80  # 提高阈值
```

### 禁用特定原则

```python
constitution = AthenaConstitution()
constitution.disable_principle("taoist_naturalness")
```

### 添加自定义原则

```python
from core.ethics.constitution import EthicalPrinciple, PrincipleSource, PrinciplePriority

custom_principle = EthicalPrinciple(
    id="custom_rule",
    name="自定义规则",
    description="我的自定义伦理规则",
    source=PrincipleSource.CUSTOM,
    priority=PrinciplePriority.MEDIUM
)

constitution.add_principle(custom_principle)
```

---

## 📈 监控指标说明

| 指标 | 说明 | 正常范围 |
|------|------|----------|
| compliance_rate | 合规率 | > 0.90 |
| violation_rate | 违规率 | < 0.10 |
| critical_violations | 关键违规数 | = 0 |
| active_alerts | 活跃告警数 | < 5 |

---

## 🛡️ 防幻觉原理

### 维特根斯坦"语言游戏"理论

1. **意义即使用**: 词的意义在于它在语言游戏中的使用
2. **公共标准**: 所有主张必须有公共可验证的标准
3. **家族相似性**: 概念通过重叠相似性连接，而非严格定义
4. **拒绝私人语言**: 无法被公共验证的主张应被拒绝

### 实现机制

```python
# 1. 语言游戏边界检查
evaluation = guard.evaluate_query(query, game_id="patent_search")

# 2. 认识论诚实检查
if confidence < threshold:
    return express_uncertainty()  # 表达不确定性

# 3. 协商或升级
if not confident:
    return negotiate()  # 请求澄清
    # 或
    return escalate()   # 升级给专家
```

---

## 📚 参考文献

### 学术资源
- [Claude's Constitution - Anthropic Official](https://www.anthropic.com/news/claudes-constitution)
- [Grounding AI with Wittgenstein - Medium](https://marcoeg.medium.com/grounding-ai-with-wittgenstein-from-language-games-to-epistemic-honesty-e3a34a791c38)
- [Anthropic Constitutional AI Paper - arXiv](https://arxiv.org/abs/2212.08073)

### 哲学原著
- 维特根斯坦. 《哲学研究》 (1953)
- 约翰·罗尔斯. 《正义论》 (1971)
- 伊曼努尔·康德. 《道德形而上学奠基》 (1785)

---

## 🔍 故障排查

### 问题: 导入错误

```bash
# 确保Python路径正确
export PYTHONPATH="/Users/xujian/Athena工作平台:$PYTHONPATH"
```

### 问题: 日志文件无法创建

```bash
# 创建日志目录
mkdir -p /Users/xujian/Athena工作平台/logs
```

### 问题: 高违规率

1. 检查置信度阈值是否过高
2. 查看具体违规原则
3. 考虑调整原则优先级
4. 查看告警日志了解详情

---

## 📞 支持

如有问题或建议，请联系：
- 项目维护者: 徐健 (xujian519@gmail.com)
- GitHub Issues: [项目地址]

---

**版本**: 1.0.0
**最后更新**: 2025-01-15
**维护者**: Athena Platform Team
