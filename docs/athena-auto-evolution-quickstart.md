# Athena自动进化系统 - 快速使用指南

## 📋 概述

Athena自动进化系统已实现三个阶段的核心功能：

- ✅ **Phase 1: 基础进化** - 参数自动调优
- ✅ **Phase 2: 智能进化** - 突变引擎
- ✅ **Phase 3: 自主进化** - 自动部署（框架）

## 🚀 快速开始

### 方式一：直接使用进化协调器

```python
import asyncio
from core.evolution import get_evolution_coordinator, EvolutionConfig

async def auto_evolve():
    # 获取进化协调器
    coordinator = get_evolution_coordinator()
    await coordinator.initialize()

    # 检查并执行进化
    result = await coordinator.check_and_evolve()

    if result:
        print(f"✅ 进化成功！提升: {result.improvement:.1%}")
    else:
        print("ℹ️ 系统性能良好，无需进化")

asyncio.run(auto_evolve())
```

### 方式二：使用突变引擎

```python
import asyncio
from core.evolution.mutation_engine import get_mutation_engine, MutationType

async def mutate_system():
    # 获取突变引擎
    engine = get_mutation_engine()
    await engine.initialize()

    # 生成和应用突变
    mutation = await engine.generate_mutation(MutationType.PARAMETER_TUNING)
    result = await engine.apply_mutation(mutation)

    if result.success:
        print(f"✅ 突变应用成功: {mutation.target}")

asyncio.run(mutate_system())
```

### 方式三：使用自动部署

```python
import asyncio
from core.evolution.auto_deployment import get_auto_deployment

async def deploy():
    deployment = get_auto_deployment()

    # 部署进化结果
    result = await deployment.deploy_evolution(evolution_result)

    if result.success:
        print("✅ 部署成功")

asyncio.run(deploy())
```

## 📊 系统架构

```
┌─────────────────────────────────────────┐
│        Evolution Coordinator           │
│  (监控 → 触发 → 协调 → 回滚)               │
└─────────────────────────────────────────┘
         │                  │
    ┌────┴────┐        ┌────┴────┐
┌───▼────┐  ┌───▼────┐  ┌───▼────┐
│Mutation│  │Learning│  │Deployment│
│ Engine │  │ System │  │  Module │
└────────┘  └────────┘  └──────────┘
```

## ⚙️ 配置选项

### 进化配置

```python
from core.evolution import EvolutionConfig, EvolutionPhase

config = EvolutionConfig(
    phase=EvolutionPhase.BASIC,
    enabled=True,
    performance_threshold=0.7,
    auto_deploy=False,  # 谨慎使用
    rollback_on_degradation=True,
    max_evolution_per_day=10
)
```

### 部署配置

```python
from core.evolution.auto_deployment import DeploymentConfig, DeploymentStrategy

config = DeploymentConfig(
    strategy=DeploymentStrategy.BLUE_GREEN,
    auto_rollback=True,
    rollback_threshold=0.05,
    validation_time=300
)
```

## 🔧 集成到现有系统

### 1. 定期检查和进化

```python
import asyncio

async def evolution_loop():
    coordinator = get_evolution_coordinator()
    await coordinator.initialize()

    while True:
        # 每小时检查一次
        await coordinator.check_and_evolve()
        await asyncio.sleep(3600)
```

### 2. 事件触发进化

```python
async def on_performance_degrade():
    coordinator = get_evolution_coordinator()
    await coordinator.initialize()

    # 性能下降时触发进化
    result = await coordinator.evolve()
```

### 3. 手动触发进化

```bash
python scripts/test_auto_evolution.py
```

## 📈 监控和日志

### 查看进化历史

```bash
cat data/evolution_history.json
```

### 查看统计信息

```python
stats = coordinator.get_stats()
print(stats)
# {'total_evolutions': 1, 'successful_evolutions': 1, ...}
```

## ⚠️ 注意事项

1. **备份**: 系统会自动备份，但建议定期手动备份
2. **回滚**: 性能下降时系统会自动回滚
3. **监控**: 密切关注进化日志和性能指标
4. **测试**: 在生产环境使用前充分测试

## 📚 相关文件

| 文件 | 功能 |
|------|------|
| `core/evolution/__init__.py` | 模块入口 |
| `core/evolution/types.py` | 类型定义 |
| `core/evolution/evolution_coordinator.py` | 进化协调器 |
| `core/evolution/mutation_engine.py` | 突变引擎 |
| `core/evolution/auto_deployment.py` | 自动部署 |
| `scripts/test_auto_evolution.py` | 测试脚本 |

## 🎯 下一步

1. ✅ Phase 1完成 - 基础参数调优可用
2. ⚠️ Phase 2需要 - 集成演化记忆和参数优化器
3. ⚠️ Phase 3需要 - 完善自动部署和验证

---

**版本**: v1.0.0
**最后更新**: 2026-02-06
**维护者**: Athena平台团队
