# 小诺提示词外部文档

> **版本**: v2.0-optimized
> **创建时间**: 2025-12-26
> **目的**: 将提示词中的详细内容外部化，减少上下文窗口占用

---

## 📁 目录结构

```
docs/prompts/external/
├── README.md                           # 本文件
├── capabilities/                       # L3能力层详细文档
│   ├── platform_management.md         # 平台管理类能力详解
│   ├── intelligent_decision.md        # 智能决策类能力详解
│   ├── data_processing.md             # 数据处理类能力详解
│   ├── ai_nlp.md                       # AI/NLP类能力详解
│   ├── development_assistance.md      # 开发辅助类能力详解
│   └── family_emotion.md              # 家庭情感类能力详解
│
├── business_scenarios/                 # L4业务层详细文档
│   ├── scenario1_service_start.md     # 场景1: 服务启动管理
│   ├── scenario2_service_monitor.md   # 场景2: 服务监控检查
│   ├── scenario3_agent_coord.md       # 场景3: 智能体调度
│   ├── scenario4_prompt_design.md     # 场景4: 提示词设计
│   ├── scenario5_code_analysis.md     # 场景5: 代码分析
│   ├── scenario6_code_generation.md   # 场景6: 代码生成
│   ├── scenario7_tech_decision.md     # 场景7: 技术决策
│   ├── scenario8_api_test.md          # 场景8: API测试
│   ├── scenario9_db_query.md          # 场景9: 数据库查询
│   ├── scenario10_db_manage.md        # 场景10: 数据库管理
│   ├── scenario11_memory_storage.md   # 场景11: 记忆存储
│   ├── scenario12_data_analysis.md    # 场景12: 数据分析
│   ├── scenario13_emotional_chat.md   # 场景13: 情感陪伴
│   ├── scenario14_family_care.md      # 场景14: 家庭关怀
│   └── scenario15_holiday_greeting.md # 场景15: 节日祝福
│
├── examples/                            # 示例对话库
│   ├── platform_management_examples.md # 平台管理类示例
│   ├── development_examples.md         # 开发辅助类示例
│   ├── data_processing_examples.md     # 数据处理类示例
│   └── family_emotion_examples.md      # 家庭情感类示例
│
└── hitl_guide/                          # HITL人机协作完整指南
    ├── core_principles.md               # 核心原则
    ├── interaction_templates.md        # 交互模板
    ├── interruption_mechanisms.md      # 中断回退机制
    └── quality_assurance.md            # 质量保证
```

---

## 🔗 与提示词的关联

优化后的提示词会引用这些外部文档：

```markdown
## L3能力层详细说明

完整的能力说明请参考：
- 平台管理类: docs/prompts/external/capabilities/platform_management.md
- 智能决策类: docs/prompts/external/capabilities/intelligent_decision.md
- 数据处理类: docs/prompts/external/capabilities/data_processing.md
- AI/NLP类: docs/prompts/external/capabilities/ai_nlp.md
- 开发辅助类: docs/prompts/external/capabilities/development_assistance.md
- 家庭情感类: docs/prompts/external/capabilities/family_emotion.md

## L4业务场景详细流程

完整的场景执行流程请参考：
- 场景1-4: docs/prompts/external/business_scenarios/
- 场景5-15: docs/prompts/external/business_scenarios/

## 示例对话库

完整示例对话请参考：
- docs/prompts/external/examples/

## HITL完整指南

详细的人机协作指南请参考：
- docs/prompts/external/hitl_guide/
```

---

## 💡 使用方式

### 方式1: 手动查阅

当需要了解某个能力或场景的详细信息时，查阅对应的文档。

### 方式2: 动态加载（未来实现）

```python
class PromptLoader:
    def load_capability_detail(self, capability_type: str):
        """动态加载能力详细说明"""
        file_path = f"docs/prompts/external/capabilities/{capability_type}.md"
        with open(file_path) as f:
            return f.read()

    def load_scenario_detail(self, scenario_id: str):
        """动态加载场景详细流程"""
        file_path = f"docs/prompts/external/business_scenarios/scenario{scenario_id}.md"
        with open(file_path) as f:
            return f.read()
```

---

## 📊 优化效果

| 项目 | 优化前 | 优化后 | 节省 |
|-----|-------|-------|-----|
| L1基础层 | ~3.3k | ~2.8k | ~0.5k (15%) |
| L3能力层 | ~24k | ~6k | ~18k (75%) |
| L4业务层 | ~33k | ~12k | ~21k (64%) |
| HITL协议 | ~2.9k | ~2k | ~0.9k (31%) |
| **总计** | **~63k** | **~22.8k** | **~40k (64%)** |

---

**文档版本**: v1.0
**最后更新**: 2025-12-26
