# Athena Remote Control via iMessage

通过 iMessage 远程控制 Athena 工作平台和小诺智能体的模块。

## 功能特性

- ✅ 通过 iMessage 发送自然语言命令
- ✅ 支持语音指令（通过语音转文字）
- ✅ 智能体自动路由（默认小诺，可指定Athena）
- ✅ 结果摘要通过 iMessage 反馈
- ✅ 详细结果自动写入 Obsidian 仓库
- ✅ 安全验证和权限控制

## 架构设计

```
┌─────────────┐
│   iPhone    │ (iMessage)
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────────┐
│         Message Gateway                 │
│  (iMessage RPC + Command Parser)        │
└───────────────┬─────────────────────────┘
                │
       ┌────────┴────────┐
       │                 │
       ▼                 ▼
┌──────────────┐  ┌──────────────┐
│  Xiaonuo     │  │   Athena     │
│  (默认)      │  │  (指定时)    │
└──────┬───────┘  └──────┬───────┘
       │                 │
       └────────┬────────┘
                ▼
┌─────────────────────────────────────────┐
│         Result Processing               │
│  (摘要生成 + Obsidian写入)              │
└───────┬──────────────────┬──────────────┘
        │                  │
        ▼                  ▼
┌──────────────┐  ┌──────────────┐
│ iMessage     │  │   Obsidian   │
│ (摘要反馈)   │  │ (详细记录)   │
└──────────────┘  └──────────────┘
```

## 配置说明

### 1. 安装依赖

```bash
# 安装 imsg (iMessage RPC 工具)
npm install -g imsg

# 或使用 Homebrew
brew install imsg
```

### 2. 配置文件

编辑 `config/config.yaml`:

```yaml
imessage:
  enabled: true
  allowed_senders:
    - "+8613800138000"  # 允许的发件人号码
  default_agent: "xiaonuo"
  max_message_length: 4000

agents:
  xiaonuo:
    enabled: true
    endpoint: "http://localhost:8000/xiaonuo"
    timeout: 300
  athena:
    enabled: true
    endpoint: "http://localhost:8000/athena"
    timeout: 600

obsidian:
  vault_path: "/Users/xujian/Library/Mobile Documents/iCloud~md~obsidian/Documents/Athena"
  organize_by: "task_type"  # task_type | date | agent
  create_daily_note: true
```

### 3. 启动服务

```bash
# 开发模式
python -m imessage_remote.main --dev

# 生产模式
python -m imessage_remote.main --daemon
```

## 使用方法

### 发送命令

通过 iMessage 发送自然语言命令：

```
# 基础命令（默认使用小诺）
小诺，帮我检索关于"人工智能"的专利

# 指定智能体
@Athena 分析这个专利的创造性：CN202310123456.7

# 语音指令（自动转文字）
"小诺，查询曹新乐的联系信息"
```

### 反馈格式

智能模式会根据任务复杂度自动调整：

**简单任务（极简）：**
```
✅ 专利检索完成
结果：找到 23 件相关专利
详情：📊 专利检索/2026-01-31/人工智能专利检索.md
```

**复杂任务（详细）：**
```
✅ 专利分析完成

📋 执行摘要：
- 分析专利：CN202310123456.7
- 创造性评分：75/100
- 主要创新点：3项

🎯 关键发现：
1. 技术领域：属于人工智能+医疗交叉领域
2. 现有技术：存在3件高度相关专利
3. 创新性评估：中等

📁 详细报告：🧠 Athena对话/2026-01-31/专利创造性分析_CN202310123456.md
💡 后续建议：建议补充对比实验数据
```

## 目录结构

```
imessage-remote/
├── src/
│   ├── core/
│   │   ├── imessage_client.py      # iMessage RPC 客户端
│   │   ├── command_parser.py       # 命令解析器
│   │   ├── command_router.py       # 命令路由器
│   │   └── security.py             # 安全验证
│   ├── agents/
│   │   ├── base_agent.py           # 智能体基类
│   │   ├── xiaonuo_agent.py        # 小诺智能体
│   │   └── athena_agent.py         # Athena智能体
│   ├── obsidian/
│   │   ├── writer.py               # Obsidian 写入器
│   │   └── formatter.py            # 格式化工具
│   └── utils/
│       ├── logger.py               # 日志工具
│       └── config.py               # 配置加载
├── config/
│   ├── config.yaml                 # 主配置文件
│   └── commands.yaml               # 命令模式配置
├── tests/
│   ├── test_parser.py
│   └── test_router.py
└── docs/
    ├── API.md                      # API 文档
    └── ARCHITECTURE.md             # 架构文档
```

## 开发计划

- [x] 架构设计
- [x] 目录结构创建
- [ ] iMessage RPC 客户端实现
- [ ] 命令解析器实现（支持自然语言）
- [ ] 智能体路由器实现
- [ ] 小诺智能体集成
- [ ] Athena 智能体集成
- [ ] Obsidian 写入器实现
- [ ] 智能反馈机制实现
- [ ] 安全验证层实现
- [ ] 测试用例编写
- [ ] 部署脚本编写

## 许可证

MIT License
