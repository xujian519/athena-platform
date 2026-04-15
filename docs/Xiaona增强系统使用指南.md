# 小娜增强系统使用指南

## 📋 系统概述

小娜增强系统是为专利法律专家小娜设计的全面智能增强平台，集成了三大核心能力：

1. **增强反思引擎** - 多维度质量评估和专业审核
2. **人机协作框架** - 人类在环的智能决策支持
3. **自适应学习系统** - 持续学习和经验积累

## 🚀 快速启动

### 基础启动
```bash
python dev/scripts/start_xiaona_enhanced.py
```

### 带配置启动
```bash
python dev/scripts/start_xiaona_enhanced.py --config config/xiaona_enhanced.json
```

### 交互模式
```bash
python dev/scripts/start_xiaona_enhanced.py --interactive
```

### 演示模式
```bash
python dev/scripts/start_xiaona_enhanced.py --demo
```

## ⚙️ 配置说明

### 基础配置示例
```json
{
  "enable_reflection": true,
  "enable_collaboration": true,
  "enable_learning": true,
  "reflection_threshold": 0.80,
  "collaboration_threshold": 0.70,
  "learning_threshold": 0.75,
  "auto_refine": true,
  "auto_collaborate": true
}
```

### 模型优化配置
```json
{
  "embedding_optimization": {
    "cache_enabled": true,
    "cache_size": 1000,
    "cache_ttl": 3600,
    "batch_embedding": true,
    "embedding_threshold": 0.8
  },
  "llm_optimization": {
    "use_local_cache": true,
    "response_cache_size": 500,
    "similar_query_threshold": 0.85,
    "max_tokens": 2000
  }
}
```

## 🎯 核心功能

### 1. 增强反思引擎

#### 功能特点
- **多维度评估**: 事实准确性、法律依据、推理逻辑等8个维度
- **专业审核**: 专利和法律领域的专业知识库
- **自动评分**: 智能化的质量评分和改进建议

#### 使用示例
```python
from core.cognition.xiaona_enhanced_reflection_engine import XiaonaEnhancedReflectionEngine

# 创建反思引擎
reflection_engine = XiaonaEnhancedReflectionEngine()

# 执行反思
result = await reflection_engine.reflect_on_legal_analysis(
    task_id="task_001",
    original_prompt="分析专利CN123456789A的新颖性",
    legal_output="分析结果内容",
    task_type="patent_analysis"
)

print(f"总体评分: {result.overall_score:.2f}")
print(f"需要改进: {result.should_refine}")
print(f"建议: {result.recommendations}")
```

### 2. 人机协作框架

#### 功能特点
- **智能任务分配**: 根据任务类型自动选择合适专家
- **灵活协作模式**: 自动、半自动、人类在环等多种模式
- **实时通知**: 专家通知和状态跟踪

#### 使用示例
```python
from core.collaboration.human_ai_collaboration_framework import HumanInTheLoopEngine, HumanExpert

# 创建协作引擎
collaboration_engine = HumanInTheLoopEngine()

# 注册专家
expert = HumanExpert(
    expert_id="expert_001",
    name="张博士",
    title="专利分析师",
    expertise=["专利分析", "新颖性判断"]
)
collaboration_engine.register_expert(expert)

# 创建协作任务
task = await collaboration_engine.create_collaboration_task(
    task_type=TaskType.PATENT_ANALYSIS,
    title="专利新颖性分析",
    description="需要专家审核专利分析结果",
    ai_output="AI分析结果",
    ai_confidence=0.75
)
```

### 3. 自适应学习系统

#### 功能特点
- **持续学习**: 从每个任务中学习和改进
- **知识积累**: 构建专业领域的知识库
- **模式识别**: 识别成功和失败的模式

#### 使用示例
```python
from core.learning.xiaona_adaptive_learning_system import XiaonaAdaptiveLearningSystem

# 创建学习系统
learning_system = XiaonaAdaptiveLearningSystem()

# 处理反思结果进行学习
await learning_system.process_reflection_result(reflection_result)

# 处理人工反馈
await learning_system.process_human_feedback(
    session=collaboration_session,
    human_feedback="专家建议",
    feedback_quality="constructive"
)

# 获取学习总结
summary = learning_system.get_learning_summary()
```

## 📊 性能优化

### 模型调用优化策略

#### 1. 缓存机制
- **嵌入向量缓存**: 避免重复计算相同文本的嵌入
- **响应缓存**: 缓存LLM的响应结果
- **知识缓存**: 缓存已检索的知识内容

#### 2. 批处理优化
- **批量嵌入**: 将多个文本合并为一批进行嵌入计算
- **异步处理**: 并行处理多个任务
- **智能调度**: 根据优先级和资源使用情况调度任务

#### 3. 阈值控制
- **相似度阈值**: 只对差异较大的查询调用模型
- **置信度阈值**: 高置信度结果跳过额外验证
- **质量阈值**: 达到质量标准的结果跳过增强处理

### 优化配置示例

#### 缓存配置
```python
# 在启动脚本中添加
config = EnhancementConfig()
config.embedding_optimization = {
    "cache_enabled": True,
    "cache_size": 1000,
    "cache_ttl": 3600,  # 1小时
    "batch_embedding": True,
    "embedding_threshold": 0.85
}
```

#### 智能阈值配置
```python
config.smart_thresholds = {
    "reflection_auto_skip": 0.90,  # 90分以上跳过反思
    "collaboration_min_score": 0.60,  # 60分以下才触发协作
    "learning_min_impact": 3,  # 影响级别3以上才学习
    "embedding_reuse_threshold": 0.90  # 90%相似度复用嵌入
}
```

## 🔧 高级用法

### 自定义反思标准
```python
from core.cognition.xiaona_enhanced_reflection_engine import ReflectionCriterion

# 添加自定义标准
custom_criterion = ReflectionCriterion(
    category="custom_category",
    name="自定义标准",
    description="特定的评估要求",
    weight=1.0,
    threshold=0.85
)

reflection_engine.add_custom_criterion(custom_criterion)
```

### 扩展专家类型
```python
# 注册技术专家
tech_expert = HumanExpert(
    expert_id="tech_expert_001",
    name="技术专家",
    title="高级工程师",
    expertise=["技术分析", "方案评估"],
    availability={
        "working_hours": {"start": 8, "end": 20},
        "available_days": [0, 1, 2, 3, 4, 5, 6]  # 全天可用
    }
)
```

### 自定义学习策略
```python
# 自定义学习触发条件
learning_system.add_learning_trigger(
    trigger_name="custom_trigger",
    condition=lambda event: event.metadata.get("custom_field") == "trigger_value",
    action=lambda event: process_custom_learning(event)
)
```

## 📈 监控和统计

### 系统状态查看
```python
# 获取完整系统状态
status = enhanced_system.get_system_status()

# 获取反思统计
reflection_stats = reflection_engine.get_reflection_statistics()

# 获取协作统计
collaboration_stats = collaboration_engine.get_collaboration_statistics()

# 获取学习统计
learning_summary = learning_system.get_learning_summary()
```

### 性能指标
- **处理速度**: 平均任务处理时间
- **质量提升**: 反思前后的质量对比
- **协作效率**: 专家响应时间和解决率
- **学习效果**: 知识增长和性能改进

## 🛠️ 故障排查

### 常见问题

1. **系统启动慢**
   - 检查模型初始化配置
   - 优化缓存设置
   - 减少不必要的模块加载

2. **处理速度慢**
   - 启用嵌入向量缓存
   - 调整批处理大小
   - 优化阈值设置

3. **内存使用高**
   - 清理过期缓存
   - 限制知识库大小
   - 优化数据结构

4. **协作不响应**
   - 检查专家配置
   - 验证通知设置
   - 查看日志文件

### 日志查看
```bash
# 查看系统日志
tail -f logs/xiaona_enhanced.log

# 查看特定模块日志
grep "reflection_engine" logs/xiaona_enhanced.log
grep "collaboration" logs/xiaona_enhanced.log
```

## 🔮 未来规划

### 短期优化 (1-2周)
- [ ] 优化模型调用性能
- [ ] 增加更多专业领域支持
- [ ] 完善文档和示例

### 中期发展 (1-3个月)
- [ ] 集成更多LLM模型
- [ ] 支持分布式协作
- [ ] 增强可视化界面

### 长期规划 (3-6个月)
- [ ] 多模态分析支持
- [ ] 跨语言协作能力
- [ ] 智能化自动优化

## 📞 支持和反馈

如有问题或建议，请联系：
- 邮箱: xujian519@gmail.com
- 项目地址: /Users/xujian/Athena工作平台

---

*最后更新: 2025-12-17*