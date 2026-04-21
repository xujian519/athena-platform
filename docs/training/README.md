# Agent统一接口标准培训

> **版本**: v1.0
> **更新日期**: 2026-04-21
> **目标受众**: Agent开发者

---

## 📚 培训内容

### 1. 培训PPT

**文件**: `slides/AGENT_STANDARD_TRAINING.pptx` (45页)

**内容结构**:

| 模块 | 页数 | 内容 |
|------|------|------|
| 模块1：Agent基础概念 | 第1-10页 | Agent定义、平台关系、生命周期、类型分类 |
| 模块2：核心接口详解 | 第11-25页 | BaseAgent、数据类、接口方法 |
| 模块3：Agent开发实践 | 第26-40页 | 创建步骤、代码示例、LLM集成、错误处理 |
| 模块4：测试与验证 | 第41-50页 | 单元测试、Mock、覆盖率、合规性检查 |
| 模块5：最佳实践 | 第51-60页 | 能力设计、错误处理、性能优化、部署 |

**生成命令**:
```bash
cd slides
node create_presentation.js
```

### 2. 动手练习

**目录**: `exercises/`

| 练习 | 文件 | 目标 | 难度 |
|------|------|------|------|
| 练习1 | `exercise_1.py` | 创建简单Agent | ⭐ 入门 |
| 练习2 | `exercise_2.py` | 添加LLM调用能力 | ⭐⭐ 中级 |
| 练习3 | `exercise_3.py` | 编写测试套件 | ⭐⭐⭐ 高级 |

---

## 🎯 学习路径

### 第1步：学习基础（30分钟）

1. 阅读 `docs/guides/QUICK_START_AGENT_DEVELOPMENT.md`
2. 阅读 `docs/design/UNIFIED_AGENT_INTERFACE_STANDARD.md`
3. 观看培训PPT模块1-2

### 第2步：动手实践（1小时）

1. 完成练习1：创建简单Agent
2. 运行测试验证功能
3. 完成练习2：添加LLM调用

### 第3步：测试验证（30分钟）

1. 完成练习3：编写测试
2. 运行测试覆盖率检查
3. 使用InterfaceComplianceChecker验证

### 第4步：深入学习（可选）

1. 阅读 `docs/guides/AGENT_INTERFACE_IMPLEMENTATION_GUIDE.md`
2. 阅读 `docs/guides/AGENT_DEVELOPMENT_FAQ.md`
3. 查看示例Agent代码：`examples/agents/`

---

## 📝 练习指南

### 练习1：创建简单Agent

**目标**: 从零创建一个符合统一接口标准的Agent

**步骤**:
1. 打开 `exercises/exercise_1.py`
2. 按照TODO注释完成代码
3. 运行测试：`python exercises/exercise_1.py`

**验证标准**:
- ✅ Agent成功初始化
- ✅ 能力正确注册
- ✅ execute方法返回正确结果

### 练习2：添加LLM调用

**目标**: 扩展Agent，添加LLM调用能力

**步骤**:
1. 打开 `exercises/exercise_2.py`
2. 完成LLM初始化和调用代码
3. 运行测试：`python exercises/exercise_2.py`

**验证标准**:
- ✅ LLM正确初始化
- ✅ 成功调用LLM并获得响应
- ✅ 响应正确解析

### 练习3：编写测试

**目标**: 为Agent编写完整的测试套件

**步骤**:
1. 打开 `exercises/exercise_3.py`
2. 替换MyAgent为你的Agent类
3. 完成所有测试方法
4. 运行测试：`pytest exercises/exercise_3.py -v`

**验证标准**:
- ✅ 所有测试通过
- ✅ 测试覆盖率 > 80%
- ✅ 接口合规性检查通过

---

## 🧪 运行测试

```bash
# 运行单个练习
python exercises/exercise_1.py
python exercises/exercise_2.py

# 运行测试套件
pytest exercises/exercise_3.py -v

# 生成覆盖率报告
pytest exercises/exercise_3.py --cov=core.agents.my_agent --cov-report=html
```

---

## 📖 相关文档

### 核心文档
- [统一Agent接口标准](../design/UNIFIED_AGENT_INTERFACE_STANDARD.md)
- [Agent通信协议规范](../design/AGENT_COMMUNICATION_PROTOCOL_SPEC.md)
- [Agent接口版本控制](../design/AGENT_INTERFACE_VERSION_CONTROL.md)

### 指南文档
- [快速开始指南](../guides/QUICK_START_AGENT_DEVELOPMENT.md)
- [接口实现指南](../guides/AGENT_INTERFACE_IMPLEMENTATION_GUIDE.md)
- [最佳实践](../guides/AGENT_INTERFACE_BEST_PRACTICES.md)
- [常见问题FAQ](../guides/AGENT_DEVELOPMENT_FAQ.md)
- [合规性检查清单](../guides/AGENT_INTERFACE_COMPLIANCE_CHECKLIST.md)
- [迁移指南](../guides/AGENT_INTERFACE_MIGRATION_GUIDE.md)

### 示例代码
- [示例Agent](../../examples/agents/example_agent.py)
- [检索者Agent](../../core/agents/xiaona/retriever_agent.py)
- [分析者Agent](../../core/agents/xiaona/analyzer_agent.py)

---

## 🔧 开发环境

### 环境要求

- Python 3.11+
- Node.js 18+ (用于生成PPT)
- pytest 7.0+
- pytest-asyncio 0.21+

### 安装依赖

```bash
# Python依赖
pip install -r requirements.txt

# Node.js依赖（生成PPT）
cd slides
npm install
```

---

## 📊 培训效果评估

### 自检清单

完成培训后，你应该能够：

- [ ] 解释Agent的生命周期
- [ ] 列出核心接口方法
- [ ] 创建一个符合标准的Agent
- [ ] 在Agent中调用LLM
- [ ] 在Agent中使用工具
- [ ] 编写单元测试
- [ ] 使用Mock模拟外部依赖
- [ ] 进行接口合规性检查

### 能力评估

| 能力 | 入门 | 中级 | 高级 |
|------|------|------|------|
| 创建Agent | ✅ 练习1 | | |
| LLM集成 | | ✅ 练习2 | |
| 测试编写 | | | ✅ 练习3 |
| 工具使用 | | ✅ 练习2 | |
| 错误处理 | | ✅ 练习2 | |
| 性能优化 | | | ✅ 高级 |

---

## 🆘 获取帮助

### 问题排查

1. **Agent初始化失败**
   - 检查是否正确继承BaseXiaonaComponent
   - 检查_initialize是否正确实现

2. **execute方法报错**
   - 检查输入验证
   - 查看日志输出
   - 检查异常处理

3. **测试失败**
   - 检查Mock配置
   - 验证上下文参数
   - 查看详细错误信息

### 联系方式

- 提交Issue：项目GitHub仓库
- 查看FAQ：`docs/guides/AGENT_DEVELOPMENT_FAQ.md`

---

**培训维护**: 本培训材料会持续更新，欢迎贡献内容和改进建议。

**最后更新**: 2026-04-21
