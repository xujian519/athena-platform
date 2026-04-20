# Agent-Alpha 任务清单

**角色**: 架构师
**专长**: Skills系统、Query Engine、Hook增强
**开发模式**: TDD (测试驱动开发)

---

## 📋 任务总览

### P0 阶段 (串行)
- ✅ **任务组 1**: Skills 系统 (~500行, 3天)

### P1 阶段 (并行)
- ⏳ **任务组 6**: Hook系统增强 (~400行, 2天)
- ⏳ **任务组 7**: Query Engine (~500行, 3天)

**总计**: ~1,400行代码, 预计8天

---

## 🔴 P0 - Skills系统 (Day 1-3)

### Day 1: 设计与核心实现

#### 上午 (4小时)
- [ ] **1.1 分析OpenHarness Skills系统** (1小时)
  - [ ] 阅读 `/openharness/skills/loader.py`
  - [ ] 阅读 `/openharness/skills/registry.py`
  - [ ] 阅读 `/openharness/skills/types.py`
  - [ ] 总结核心设计模式

- [ ] **1.2 设计Skills系统架构** (1小时)
  - [ ] 定义SkillDefinition数据结构
  - [ ] 设计SkillRegistry接口
  - [ ] 设计技能加载流程
  - [ ] 创建设计文档 `docs/design/SKILLS_SYSTEM_DESIGN.md`

- [ ] **1.3 创建目录结构** (30分钟)
  ```bash
  mkdir -p core/skills/{bundled,user}
  mkdir -p tests/skills
  touch core/skills/__init__.py
  touch core/skills/types.py
  touch core/skills/registry.py
  touch core/skills/loader.py
  ```

- [ ] **1.4 测试先行 - SkillRegistry** (1.5小时)
  - [ ] 创建 `tests/skills/test_skill_registry.py`
  - [ ] 测试: 注册技能
    ```python
    def test_register_skill():
        registry = SkillRegistry()
        skill = SkillDefinition(id="test_skill", name="Test Skill")
        registry.register(skill)
        assert registry.get_skill("test_skill") == skill
    ```
  - [ ] 测试: 查询技能
  - [ ] 测试: 列出技能
  - [ ] 测试: 按类别筛选
  - [ ] 运行测试 (预期失败)
  ```bash
  pytest tests/skills/test_skill_registry.py -v
  ```

#### 下午 (4小时)
- [ ] **1.5 实现types.py** (1小时)
  - [ ] 实现SkillDefinition dataclass
  - [ ] 实现SkillCategory枚�试
  - [ ] 实现SkillMetadata类
  - [ ] 运行测试 (部分通过)

- [ ] **1.6 实现registry.py** (2小时)
  - [ ] 实现SkillRegistry类
  - [ ] 实现register()方法
  - [ ] 实现get_skill()方法
  - [ ] 实现list_skills()方法
  - [ ] 实现find_skills()方法
  - [ ] 运行测试 (全部通过)

- [ ] **1.7 提交代码** (30分钟)
  ```bash
  git add core/skills/
  git commit -m "feat: 实现Skills系统核心功能
  - 实现SkillDefinition数据结构
  - 实现SkillRegistry注册表
  - 测试覆盖率: 100%"
  ```

- [ ] **1.8 编写文档** (30分钟)
  - [ ] 更新 `docs/design/SKILLS_SYSTEM_DESIGN.md`
  - [ ] 创建使用示例

---

### Day 2: 加载器与内置技能

#### 上午 (4小时)
- [ ] **2.1 测试先行 - SkillLoader** (1.5小时)
  - [ ] 创建 `tests/skills/test_skill_loader.py`
  - [ ] 测试: 从目录加载技能
  - [ ] 测试: 解析技能元数据
  - [ ] 测试: 验证技能格式
  - [ ] 测试: 处理无效技能
  - [ ] 运行测试 (预期失败)

- [ ] **2.2 实现loader.py** (2小时)
  - [ ] 实现load_skills_from_directory()
  - [ ] 实现parse_skill_metadata()
  - [ ] 实现validate_skill()
  - [ ] 实现技能YAML解析
  - [ ] 运行测试 (全部通过)

- [ ] **2.3 实现内置技能** (30分钟)
  - [ ] 创建patent_analysis技能
  - [ ] 创建legal_writing技能
  - [ ] 创建case_search技能

#### 下午 (4小时)
- [ ] **2.4 测试先行 - 工具映射** (1.5小时)
  - [ ] 创建 `tests/skills/test_skill_tool_mapping.py`
  - [ ] 测试: 单技能多工具映射
  - [ ] 测试: 多技能组合
  - [ ] 测试: 技能冲突检测

- [ ] **2.5 实现tool_mapper.py** (2小时)
  - [ ] 实现SkillToolMapper类
  - [ ] 实现map_tools_to_skills()
  - [ ] 实现get_tools_for_skill()
  - [ ] 运行测试

- [ ] **2.6 集成测试** (30分钟)
  - [ ] 集成到Agent Loop
  - [ ] 测试技能动态加载
  - [ ] 测试完整流程

---

### Day 3: 集成与文档

#### 上午 (4小时)
- [ ] **3.1 Agent Loop集成** (2小时)
  - [ ] 修改`core/agents/agent_loop_enhanced.py`
  - [ ] 添加skills参数
  - [ ] 实现技能选择逻辑
  - [ ] 集成测试

- [ ] **3.2 端到端测试** (2小时)
  - [ ] 创建`tests/skills/test_e2e.py`
  - [ ] 测试完整对话流程
  - [ ] 测试技能切换
  - [ ] 性能测试

#### 下午 (4小时)
- [ ] **3.3 文档编写** (2小时)
  - [ ] 编写Skills系统API文档
  - [ ] 编写技能开发指南
  - [ ] 创建3个示例技能

- [ ] **3.4 代码审查与重构** (1小时)
  - [ ] 代码审查
  - [ ] 重构优化
  - [ ] 性能调优

- [ ] **3.5 提交最终版本** (1小时)
  ```bash
  git add .
  git commit -m "feat: 完成Skills系统实现
  - 实现技能注册表和加载器
  - 实现3个内置技能
  - 集成到Agent Loop
  - 测试覆盖率: 90%
  - 文档完整"
  ```

---

## 🟡 P1 - Hook系统增强 (Day 11-12)

### Day 11: Hook类型扩展

- [ ] **11.1 扩展Hook类型** (4小时)
  - [ ] 添加AGENT_STARTUP
  - [ ] 添加AGENT_SHUTDOWN
  - [ ] 添加MESSAGE_SEND
  - [ ] 添加ERROR_RECOVERY
  - [ ] 实现Hook优先级

- [ ] **11.2 Hook执行器** (4小时)
  - [ ] 实现HookExecutor类
  - [ ] 实现异常隔离
  - [ ] 实现超时处理
  - [ ] 实现结果聚合

---

## 🟡 P1 - Query Engine (Day 13-15)

### Day 13: QueryEngine核心

- [ ] **13.1 设计QueryEngine** (2小时)
  - [ ] 分析OpenHarness QueryEngine
  - [ ] 设计架构
  - [ ] 创建目录

- [ ] **13.2 测试先行** (2小时)
  - [ ] 创建测试文件
  - [ ] 测试消息提交
  - [ ] 测试历史管理

- [ ] **13.3 实现QueryEngine** (4小时)
  - [ ] 实现核心类
  - [ ] 实现查询循环
  - [ ] 运行测试

### Day 14-15: 对话历史与成本追踪

- [ ] **14.1 对话历史管理** (4小时)
  - [ ] 实现ConversationHistory
  - [ ] 实现消息序列化
  - [ ] 实现历史持久化

- [ ] **14.2 成本追踪** (4小时)
  - [ ] 实现CostTracker
  - [ ] 实现Token计数
  - [ ] 实现成本计算

- [ ] **15.1 集成测试** (4小时)
  - [ ] 集成到Agent Loop
  - [ ] 端到端测试
  - [ ] 性能测试

- [ ] **15.2 文档与提交** (4小时)
  - [ ] 编写文档
  - [ ] 代码审查
  - [ ] 提交代码

---

## 📊 每日检查清单

每个工作日结束前确认：
- [ ] 所有测试通过
- [ ] 代码已提交
- [ ] 文档已更新
- [ ] 进度已记录
- [ ] 明日计划已制定

---

**负责人**: Agent-Alpha
**开始日期**: 2026-04-21
**预计完成**: 2026-05-05 (15天)
