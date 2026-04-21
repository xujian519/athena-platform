# 审查意见答复工作流 - 使用指南

## 快速开始

### 1. 启动新工作流

```bash
cd ~/Athena工作平台/openspec-oa-workflow
python3 scripts/oa_workflow.py start --case-id oa-response-20260326-CN202410001234
```

### 2. 上传审查意见

```bash
python3 scripts/oa_workflow.py step1 \
  --case-id oa-response-20260326-CN202410001234 \
  --oa-file /path/to/审查意见通知书.pdf
```

### 3. 收集材料

```bash
python3 scripts/oa_workflow.py step2 \
  --case-id oa-response-20260326-CN202410001234 \
  --application-file /path/to/申请文件.docx \
  --reference-files /path/to/D1.pdf /path/to/D2.pdf
```

或通过公开号自动下载：
```bash
python3 scripts/oa_workflow.py step2 \
  --case-id oa-response-20260326-CN202410001234 \
  --publication-numbers '{"application": "CN10XXXXXX", "references": ["CN10XXXXXX", "US20XXXXXX"]}'
```

### 4. 查看状态

```bash
python3 scripts/oa_workflow.py status --case-id oa-response-20260326-CN202410001234
```

---

## 在 Claude Code / OpenCode 中使用

### 方式1: 直接对话

```
请根据审查意见通知书开始答复流程。

审查意见文件：/path/to/审查意见通知书.pdf
申请文件：/path/to/申请文件.docx
对比文件：/path/to/D1.pdf, /path/to/D2.pdf
```

### 方式2: 使用 OpenSpec 命令

```bash
# 创建新变更
openspec new change oa-response-20260326-CN202410001234

# 验证规范
openspec validate oa-response-20260326-CN202410001234 --strict

# 归档
openspec archive oa-response-20260326-CN202410001234
```

---

## 工作流步骤详解

### Step 1: 接收指令与解析

**输入**：
- 审查意见通知书（PDF/图片）

**输出**：
- `oa_notification.json` - 结构化的审查意见

**用户操作**：
- 上传审查意见文件
- 确认解析结果

---

### Step 2: 材料收集

**输入**：
- 原始申请文件（PDF/DOC/DOCX）
- 对比文件（PDF）
- 或公开号（自动下载）

**输出**：
- 材料完整性报告

**用户操作**：
- 上传文件 或 提供公开号
- 确认材料齐全

---

### Step 3: 双智能体并行分析

**自动执行**：
- 子智能体1：分析审查意见 + 申请文件
- 子智能体2：分析对比文件

**输出**：
- `agent1_analysis.json` / `.md`
- `reference_D1_analysis.json` / `.md`
- `reference_D2_analysis.json` / `.md`

**用户操作**：
- 查看分析结果
- 确认无误后继续

---

### Step 4: 策略制定

**自动执行**：
- 评估复杂程度
- 选择策略工具（法条 / 法律世界模型）
- 生成策略说明

**输出**：
- `strategy.json`

**用户操作**：
- ⚠️ **必须确认策略后才能继续**

---

### Step 5: 撰写答复

**流程**：
1. 生成提纲 → 用户确认
2. 撰写第1节 → 用户确认
3. 撰写第2节 → 用户确认
4. ...
5. 完成

**输出**：
- `draft_outline.json`
- `draft_section_*.md`

**用户操作**：
- 每完成一节都要确认
- 可提出修改意见

---

### Step 6: 辩论验证

**自动执行**：
- 代理师角色 vs 审查员角色
- 至少5轮辩论
- 主智能体裁决

**输出**：
- `debate_record.json`
- `辩论记录.md`

**用户操作**：
- 查看辩论记录
- 确认裁决结果

---

### Step 7: 输出确认

**自动执行**：
- 根据辩论修改答复
- 生成最终文件包

**输出**：
- `意见陈述书.docx`
- `修改对照表.docx`
- `辩论记录.md`
- `答复策略.md`
- 分析文件（JSON + MD）

**用户操作**：
- 最终确认
- 可进行修改

---

### Step 8: 自我反思与改进

**输入**：
- 用户的修改内容

**自动执行**：
- 识别修改
- 分析原因
- 生成改进建议

**输出**：
- `improvement_suggestions.json`

**用户操作**：
- 确认是否采纳改进建议
- 改进会更新到流程/模板

---

## 文件结构

```
outputs/
└── oa-response-20260326-CN202410001234/
    ├── workflow_state.json          # 工作流状态
    ├── oa_notification.json         # 审查意见解析结果
    ├── agent1_analysis.json         # 子智能体1分析
    ├── agent1_analysis.md
    ├── reference_D1_analysis.json   # 对比文件1分析
    ├── reference_D1_analysis.md
    ├── reference_D2_analysis.json   # 对比文件2分析
    ├── reference_D2_analysis.md
    ├── strategy.json                # 答复策略
    ├── draft_outline.json           # 答复提纲
    ├── draft_section_*.md           # 各章节草稿
    ├── debate_record.json           # 辩论记录
    ├── 辩论记录.md
    ├── 意见陈述书.docx              # 最终答复
    ├── 修改对照表.docx
    ├── 答复策略.md
    └── improvement_suggestions.json # 改进建议
```

---

## 常见问题

### Q: 材料不齐怎么办？

A: 系统会明确告知缺少哪些材料。你可以：
1. 手动上传文件
2. 提供公开号自动下载
3. 跳过可选材料（如某些对比文件）

### Q: 策略不满意怎么办？

A: 在 Step 4，你可以：
1. 要求重新评估复杂程度
2. 指定使用特定策略工具
3. 手动调整策略内容

### Q: 辩论轮数太多怎么办？

A: 系统会在以下情况结束辩论：
1. 达成一致（审查员表示"接受"）
2. 趋于一致（连续3轮"部分接受"）
3. 达到最多轮数（20轮）

### Q: 最终答复不满意怎么办？

A: 你可以：
1. 在任何步骤提出修改意见
2. 要求重新撰写特定章节
3. 手动编辑最终文件
4. 系统会记录你的修改并自我反思

---

## 技术支持

- 工作流规范：`openspec/specs/oa-response-workflow.md`
- 智能体配置：`agents/agent-configs.md`
- 模板目录：`templates/`
- 脚本目录：`scripts/`

问题反馈：在 OpenSpec 项目中创建变更记录
