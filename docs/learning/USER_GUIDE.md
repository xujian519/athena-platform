# 学习模块使用指南

> Athena智能工作平台 - 自主学习系统使用指南

版本: 1.0.0
最后更新: 2026-01-28

---

## 目录

- [快速开始](#快速开始)
- [核心概念](#核心概念)
- [基础用法](#基础用法)
- [高级功能](#高级功能)
- [最佳实践](#最佳实践)
- [故障排查](#故障排查)
- [示例代码](#示例代码)

---

## 快速开始

### 5分钟快速上手

```python
import asyncio
from core.learning.autonomous_learning_system import AutonomousLearningSystem

async def quickstart():
    # 创建学习系统
    system = AutonomousLearningSystem(agent_id="my_agent")

    # 从经验中学习
    await system.learn_from_experience(
        context={"task": "搜索专利", "query": "人工智能"},
        action="使用向量搜索",
        result={"found": 15, "relevant": 12},
        reward=0.85
    )

    # 获取学习指标
    metrics = await system.get_learning_metrics()
    print(f"已完成 {metrics['learning']['total_experiences']} 次学习")

asyncio.run(quickstart())
```

---

## 核心概念

### 学习循环

```
┌─────────────────────────────────────────────────────────┐
│                    学习循环                              │
├─────────────────────────────────────────────────────────┤
│  1. 经验采集  →  从交互中收集数据                        │
│  2. 奖励计算  →  评估结果质量                            │
│  3. 策略更新  →  根据奖励调整行为                        │
│  4. 性能分析  →  监控学习效果                            │
│  5. 优化建议  →  生成改进方案                            │
└─────────────────────────────────────────────────────────┘
```

### 学习类型

| 类型 | 说明 | 适用场景 |
|------|------|----------|
| `SUPERVISED` | 监督学习 | 有标注数据 |
| `REINFORCEMENT` | 强化学习 | 通过奖励反馈学习 |
| `UNSUPERVISED` | 无监督学习 | 发现数据模式 |
| `FEW_SHOT` | 少样本学习 | 样本稀缺场景 |
| `TRANSFER` | 迁移学习 | 知识迁移 |

---

## 基础用法

### 1. 自主学习

```python
from core.learning.autonomous_learning_system import AutonomousLearningSystem

async def basic_learning():
    system = AutonomousLearningSystem(agent_id="learner_1")

    # 记录成功的经验
    await system.learn_from_experience(
        context={"task": "文档分析", "pages": 10},
        action="使用高级模型",
        result={"accuracy": 0.95, "time": 2.3},
        reward=0.9  # 高奖励
    )

    # 记录失败的经验
    await system.learn_from_experience(
        context={"task": "文档分析", "pages": 100},
        action="使用高级模型",
        result={"error": "超时"},
        reward=-0.5  # 负奖励
    )

    # 系统会自动从这些经验中学习
    # 成功的动作会被加强，失败的动作会被避免
```

### 2. 并发控制

```python
from core.learning.concurrency_control import (
    ConcurrencyController,
    ConcurrencyConfig
)

async def concurrent_tasks():
    # 配置并发参数
    config = ConcurrencyConfig(
        max_concurrent_tasks=10,    # 最多10个并发任务
        max_operations_per_second=500,
        task_timeout=30.0
    )
    controller = ConcurrencyController(config)

    # 定义任务
    async def process_item(item_id):
        await asyncio.sleep(0.1)  # 模拟工作
        return f"item_{item_id}_processed"

    # 提交任务
    tasks = []
    for i in range(100):
        task = controller.submit_task(
            lambda i=i: process_item(i),
            timeout=5.0
        )
        tasks.append(task)

    # 等待所有任务完成
    results = await asyncio.gather(*tasks)

    # 查看统计
    stats = controller.get_statistics()
    print(f"完成 {stats['tasks']['completed']} 个任务")
    print(f"成功率: {stats['tasks']['success_rate']*100:.1f}%")
```

### 3. 错误处理和重试

```python
from core.learning.error_handling import (
    RetryHandler,
    RetryConfig,
    TransientError,
    PermanentError
)

async def robust_operation():
    # 配置重试策略
    config = RetryConfig(
        max_attempts=5,       # 最多尝试5次
        base_delay=1.0,       # 初始延迟1秒
        max_delay=30.0,       # 最大延迟30秒
        jitter=True          # 添加随机抖动
    )
    handler = RetryHandler(config)

    async def unstable_api_call():
        import random
        if random.random() < 0.3:
            # 30%概率失败（临时性）
            raise TransientError("API暂时不可用")
        return "success"

    # 自动重试
    try:
        result = await handler.execute_with_retry(unstable_api_call)
        print(f"操作成功: {result}")
    except Exception as e:
        print(f"操作失败: {e}")
```

### 4. 数据持久化

```python
from core.learning.persistence_manager import (
    LearningPersistenceManager,
    StorageBackend
)

async def persistent_learning():
    # 创建持久化管理器
    manager = LearningPersistenceManager(StorageBackend.FILE)
    await manager.initialize(base_path="./data/learning")

    # 保存学习经验
    await manager.save_experience(
        agent_id="agent_1",
        experience={
            "task": "专利检索",
            "query": "机器学习",
            "results": 150,
            "satisfaction": 0.9
        }
    )

    # 保存发现的模式
    await manager.save_pattern(
        agent_id="agent_1",
        pattern={
            "type": "查询优化",
            "description": "使用同义词扩展可提高召回率",
            "improvement": 0.15
        }
    )

    # 加载历史经验
    experiences = await manager.load_experiences("agent_1", limit=10)
    print(f"历史经验: {len(experiences)} 条")
```

---

## 高级功能

### 1. A/B测试

```python
async def ab_test_example():
    from core.learning.autonomous_learning_system import AutonomousLearningSystem

    system = AutonomousLearningSystem(agent_id="tester")

    # 创建A/B测试
    experiment_id = await system.create_ab_test(
        name="模型对比实验",
        description="对比基线模型和实验模型的性能",
        control_config={"model": "baseline", "temperature": 0.7},
        treatment_configs=[
            {"model": "experimental", "temperature": 0.9},
            {"model": "experimental", "temperature": 0.5}
        ],
        success_metric="accuracy"
    )

    # 运行测试（通常需要更长时间）
    # results = await system.run_ab_test(experiment_id, test_duration=3600)
    # print(f"获胜者: {results['winner']}")
```

### 2. 断路器模式

```python
async def circuit_breaker_example():
    from core.learning.error_handling import CircuitBreaker

    breaker = CircuitBreaker(
        failure_threshold=5,    # 连续5次失败后打开
        timeout=30.0,           # 30秒后进入半开
        half_open_attempts=2    # 半开时允许2次尝试
    )

    async def protected_service():
        # 可能失败的服务
        import random
        if random.random() < 0.2:
            raise Exception("服务错误")
        return "正常响应"

    # 通过断路器调用
    for i in range(20):
        try:
            result = await breaker.call(protected_service)
            print(f"调用 {i+1}: 成功 - {result}")
        except Exception as e:
            state = breaker.get_state()
            print(f"调用 {i+1}: 失败 - 断路器状态: {state['state']}")
```

### 3. 降级策略

```python
async def fallback_example():
    from core.learning.error_handling import FallbackHandler

    handler = FallbackHandler()

    # 主函数
    async def primary_model():
        # 可能失败的高级模型
        raise Exception("模型不可用")

    # 降级函数
    async def fallback_model():
        return "简化模型结果"

    # 注册降级
    handler.register_fallback("model_inference", fallback_model)

    # 使用降级策略
    result = await handler.execute_with_fallback(
        name="model_inference",
        primary_func=primary_model
    )
    print(f"结果: {result}")
```

### 4. 性能监控

```python
async def monitoring_example():
    from core.learning.autonomous_learning_system import AutonomousLearningSystem

    system = AutonomousLearningSystem(agent_id="monitored_agent")

    # 添加一些学习数据
    for i in range(50):
        await system.learn_from_experience(
            context={"iteration": i},
            action="test_action",
            result={"value": i * 2},
            reward=0.5 + (i % 3) * 0.2
        )

    # 分析性能
    analysis = await system.analyze_performance()

    print("性能趋势:")
    for metric, trend in analysis.get("trends", {}).items():
        print(f"  {metric}: {trend['direction']} ({trend['change']*100:.1f}%)")

    # 检查异常
    if analysis.get("anomalies"):
        print("\n检测到的异常:")
        for anomaly in analysis["anomalies"]:
            print(f"  - {anomaly}")
```

---

## 最佳实践

### 1. 配置调优

```python
# 根据场景调整并发配置
def get_config(use_case):
    configs = {
        "high_throughput": ConcurrencyConfig(
            max_concurrent_tasks=50,
            max_operations_per_second=1000,
            task_timeout=10.0
        ),
        "low_latency": ConcurrencyConfig(
            max_concurrent_tasks=5,
            max_operations_per_second=100,
            task_timeout=5.0
        ),
        "balanced": ConcurrencyConfig(
            max_concurrent_tasks=10,
            max_operations_per_second=500,
            task_timeout=30.0
        )
    }
    return configs.get(use_case, configs["balanced"])
```

### 2. 错误分类

```python
# 正确区分临时错误和永久错误
async def smart_operation():
    try:
        return await some_api_call()
    except (ConnectionError, TimeoutError) as e:
        # 网络问题：临时错误，可以重试
        raise TransientError("网络临时不可用") from e
    except (ValueError, KeyError) as e:
        # 数据问题：永久错误，不应重试
        raise PermanentError("数据格式错误") from e
    except Exception as e:
        # 未知错误：谨慎处理
        raise TransientError("未知错误") from e
```

### 3. 经验积累策略

```python
# 定期保存学习经验
async def periodic_save(system, agent_id, interval=300):
    """每5分钟保存一次学习经验"""
    while True:
        await asyncio.sleep(interval)

        experiences = system.experiences
        manager = LearningPersistenceManager(StorageBackend.FILE)
        await manager.initialize()

        # 批量保存
        for exp in experiences[-100:]:  # 最近100条
            await manager.save_experience(
                agent_id=agent_id,
                experience=exp.to_dict()
            )

        print(f"已保存 {min(100, len(experiences))} 条经验")
```

### 4. 监控和告警

```python
# 设置性能监控
async def monitor_performance(system):
    while True:
        metrics = await system.get_learning_metrics()

        # 检查关键指标
        avg_reward = metrics["performance"]["current_avg_reward"]
        success_rate = metrics["performance"]["current_success_rate"]

        # 告警条件
        if avg_reward < 0.5:
            print(f"⚠️  告警: 平均奖励过低 ({avg_reward:.2f})")

        if success_rate < 0.7:
            print(f"⚠️  告警: 成功率过低 ({success_rate*100:.1f}%)")

        await asyncio.sleep(60)  # 每分钟检查一次
```

---

## 故障排查

### 问题1: 内存占用过高

```python
# 解决方案：限制缓冲区大小
system = AutonomousLearningSystem(agent_id="agent")
# 经验缓冲区已限制在10000条
# 性能历史已限制在1000条/指标

# 定期清理
async def cleanup_old_data(system):
    """清理旧数据"""
    # 保留最近1000条经验
    if len(system.experiences) > 1000:
        # deque会自动处理，但可以手动清理性能历史
        for key in system.performance_history:
            if len(system.performance_history[key]) > 500:
                # 只保留最近500条
                old_data = list(system.performance_history[key])[:-500]
                for _ in old_data:
                    system.performance_history[key].popleft()
```

### 问题2: 并发性能不佳

```python
# 解决方案：调整并发参数
import os

# 根据CPU核心数设置并发数
cpu_count = os.cpu_count() or 4
optimal_concurrent = cpu_count * 2  # 经验值

config = ConcurrencyConfig(
    max_concurrent_tasks=optimal_concurrent,
    max_operations_per_second=optimal_concurrent * 100,
    task_timeout=30.0
)
```

### 问题3: 持久化性能瓶颈

```python
# 解决方案：批量操作 + 异步化
async def batch_persistence(experiences, batch_size=100):
    """批量持久化"""
    manager = LearningPersistenceManager(StorageBackend.FILE)
    await manager.initialize()

    # 分批处理
    for i in range(0, len(experiences), batch_size):
        batch = experiences[i:i+batch_size]
        tasks = [
            manager.save_experience(
                agent_id="agent",
                experience=exp
            )
            for exp in batch
        ]
        await asyncio.gather(*tasks)
        print(f"已保存 {i+len(batch)}/{len(experiences)}")
```

---

## 示例代码

### 完整的智能学习系统

```python
import asyncio
from core.learning.autonomous_learning_system import AutonomousLearningSystem
from core.learning.concurrency_control import ConcurrencyController, ConcurrencyConfig
from core.learning.error_handling import RetryHandler, RetryConfig, TransientError
from core.learning.persistence_manager import LearningPersistenceManager, StorageBackend
from core.learning.input_validator import get_input_validator

class SmartLearningAgent:
    """智能学习代理"""

    def __init__(self, agent_id: str):
        self.agent_id = agent_id

        # 初始化各组件
        self.learning_system = AutonomousLearningSystem(agent_id)
        self.concurrency = ConcurrencyController(ConcurrencyConfig(
            max_concurrent_tasks=10,
            max_operations_per_second=500
        ))
        self.retry = RetryHandler(RetryConfig(max_attempts=3))
        self.persistence = LearningPersistenceManager(StorageBackend.FILE)
        self.validator = get_input_validator()

    async def initialize(self):
        """初始化"""
        await self.persistence.initialize()

    async def process_task(self, task_data: dict) -> dict:
        """处理任务并学习"""
        # 验证输入
        validation = await self.validator.validate_learning_input(
            context=task_data.get("context", {}),
            action=task_data.get("action", "unknown"),
            result=task_data.get("result", {})
        )

        if not validation.is_valid:
            return {"error": "验证失败", "details": validation.errors}

        # 执行任务（带重试）
        async def execute():
            return await self._execute_task(task_data)

        result = await self.retry.execute_with_retry(execute)

        # 学习经验
        await self.learning_system.learn_from_experience(
            context=task_data.get("context", {}),
            action=task_data.get("action", ""),
            result=result,
            reward=self._calculate_reward(result)
        )

        return result

    async def _execute_task(self, task_data: dict) -> dict:
        """实际执行任务"""
        # 模拟任务执行
        await asyncio.sleep(0.1)

        action = task_data.get("action", "")
        if "失败" in action:
            raise TransientError("任务执行失败")

        return {"status": "success", "data": "模拟结果"}

    def _calculate_reward(self, result: dict) -> float:
        """计算奖励值"""
        if result.get("status") == "success":
            return 0.8
        return -0.5

    async def save_learning(self):
        """保存学习数据"""
        experiences = self.learning_system.experiences
        for exp in list(experiences)[-100:]:  # 最近100条
            await self.persistence.save_experience(
                agent_id=self.agent_id,
                experience=exp.to_dict()
            )

    async def get_performance_report(self) -> dict:
        """获取性能报告"""
        learning_metrics = await self.learning_system.get_learning_metrics()
        concurrency_stats = self.concurrency.get_statistics()
        retry_stats = self.retry.get_statistics()

        return {
            "learning": learning_metrics,
            "concurrency": concurrency_stats,
            "retry": retry_stats
        }

# 使用示例
async def main():
    agent = SmartLearningAgent("test_agent")
    await agent.initialize()

    # 处理一批任务
    tasks = [
        {"action": "搜索专利", "context": {"query": "AI"}},
        {"action": "分析文档", "context": {"pages": 5}},
        {"action": "生成报告", "context": {"type": "summary"}},
    ]

    for task in tasks:
        result = await agent.process_task(task)
        print(f"任务: {task['action']}, 结果: {result.get('status', 'error')}")

    # 保存学习数据
    await agent.save_learning()

    # 获取性能报告
    report = await agent.get_performance_report()
    print("\n性能报告:")
    print(f"  学习周期: {report['learning']['learning']['total_cycles']}")
    print(f"  总经验: {report['learning']['learning']['total_experiences']}")

asyncio.run(main())
```

---

## 相关资源

- [API文档](./LEARNING_MODULE_API.md)
- [测试指南](../../tests/core/learning/TEST_GUIDE.md)
- [测试报告](../../tests/core/learning/TEST_REPORT.md)
